"""colab-mcp stdio 중계기.

클라이언트가 tools/list 를 처음 보낼 때, 먼저 open_colab_browser_connection 을
대신 호출해 브라우저 연결이 살아난 뒤에 목록을 넘긴다. colab-mcp 는 연결 전에는
빈 목록을 주고 뒤늦은 tools/list_changed 알림은 이 클라이언트가 처리하지 않아,
연결을 목록 조회보다 앞세우지 않으면 셀 조작 도구가 영원히 안 보인다.

주의할 것 둘.
- 주입하는 요청의 id 를 문자열로 주면 자식이 즉시 에러를 돌려준다. 숫자를 쓴다.
- 자식은 연결에 실패해도 정상 응답으로 result=false 를 돌려준다. 값을 봐야 한다.
  "result 가 있으면 성공" 으로 치면 실패를 성공으로 오해한다.
"""

import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# colab-mcp 를 직접 부르지 않고 실행기를 거친다. 실행기가 붙을 노트를 고정한다.
# colab_mcp 는 uv 도구 가상환경에만 깔려 있으므로 그 파이썬으로 실행해야 한다.
# 경로를 하드코딩하지 않는다 — 기계마다 다르고 공개 저장소에 사용자명이 박힌다.
VENV_PY = os.environ.get("COLAB_MCP_VENV_PYTHON") or os.path.join(
    os.environ.get("APPDATA", ""), "uv", "tools", "colab-mcp", "Scripts", "python.exe")
LAUNCHER = os.environ.get("COLAB_MCP_LAUNCHER") or os.path.join(HERE, "colab_mcp_launch.py")
CHILD = [VENV_PY, "-u", LAUNCHER]
SHIM_ID = 2147483600
ATTEMPT_TIMEOUT = 70      # 자식 안쪽 대기가 60초라 그보다 넉넉히
ATTEMPTS = 2
DEBUG = os.environ.get("COLAB_MCP_SHIM_LOG") or os.path.join(HERE, "shim-debug.log")

proc = subprocess.Popen(CHILD, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
answered = threading.Event()
outcome = {}


def note(what):
    with open(DEBUG, "a", encoding="utf-8") as f:
        f.write("%.3f %s\n" % (time.time(), what))


def parse(line):
    try:
        return json.loads(line)
    except ValueError:
        return None


def is_connected(msg):
    """자식이 돌려준 tools/call 응답에서 실제 연결 여부를 꺼낸다."""
    res = msg.get("result")
    if not isinstance(res, dict):
        return False
    sc = res.get("structuredContent")
    if isinstance(sc, dict) and "result" in sc:
        return sc["result"] is True
    for part in res.get("content", []):
        if isinstance(part, dict) and part.get("type") == "text":
            return part.get("text", "").strip().lower() == "true"
    return False


def from_child():
    while True:
        line = proc.stdout.readline()
        if not line:
            note("child stdout closed")
            answered.set()
            break
        msg = parse(line)
        if msg is not None and msg.get("id") == SHIM_ID:
            outcome["ok"] = is_connected(msg)
            note("shim reply ok=%s: %s"
                 % (outcome["ok"], line.decode("utf-8", "replace").strip()[:600]))
            answered.set()
            continue
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()


def send_child(line):
    proc.stdin.write(line)
    proc.stdin.flush()


def try_connect():
    answered.clear()
    outcome.pop("ok", None)
    send_child(
        json.dumps({
            "jsonrpc": "2.0",
            "id": SHIM_ID,
            "method": "tools/call",
            "params": {"name": "open_colab_browser_connection", "arguments": {}},
        }).encode() + b"\n"
    )
    answered.wait(timeout=ATTEMPT_TIMEOUT)
    return outcome.get("ok", False)


def to_child():
    gated = False
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            break
        msg = parse(line)
        if not gated and msg is not None and msg.get("method") == "tools/list":
            gated = True
            for i in range(1, ATTEMPTS + 1):
                note("gate: connect attempt %d/%d" % (i, ATTEMPTS))
                if try_connect():
                    note("gate: connected on attempt %d" % i)
                    break
            else:
                note("gate: giving up, 도구 목록이 비어 나간다. "
                     "크롬이 떠 있는지 확인하고 Claude Code 를 다시 시작한다")
        send_child(line)
    proc.stdin.close()


note("=== shim start ===")
threading.Thread(target=from_child, daemon=True).start()
to_child()
