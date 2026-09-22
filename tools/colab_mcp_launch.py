"""colab-mcp 를 띄우되, 붙을 노트를 고정한다.

colab-mcp 는 연결할 때 `webbrowser.open_new()` 로 스크래치 노트
(`/notebooks/empty.ipynb`) 를 새 탭에 열어 거기 붙는다. 그 노트는 저장되지 않으니
런타임 유형이 남지 않고, 세션마다 T4 를 손으로 다시 골라야 한다.

여는 주소의 프래그먼트(`#mcpProxyToken=...&mcpProxyPort=...`)만 그대로 옮겨
`TARGET` 노트로 바꿔치기한다. Drive 에 저장된 노트는 런타임 유형이 노트에
남으므로 T4 가 계속 붙어 있다.

이 파일은 colab-mcp 가 깔린 uv 도구 가상환경의 파이썬으로 실행해야 한다.
`tools/colab_mcp_shim.py` 가 그렇게 실행한다.
"""

import os
import webbrowser

# 붙을 노트는 사람마다 다르고 Drive 문서 ID 라 저장소에 박아 두지 않는다.
# `.mcp.json` 의 env 로 준다. 안 주면 colab-mcp 의 원래 동작(스크래치 노트)이 된다.
TARGET = os.environ.get("COLAB_MCP_NOTEBOOK", "")
LOG = os.environ.get("COLAB_MCP_SHIM_LOG") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "shim-debug.log")

_open_new = webbrowser.open_new


def open_new(url, *args, **kwargs):
    if not TARGET:
        return _open_new(url)
    frag = url.split("#", 1)[1] if "#" in url else ""
    fixed = TARGET + ("#" + frag if frag else "")
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("launcher: 스크래치 대신 고정 노트로 연다\n")
    except OSError:
        pass
    return _open_new(fixed)


# open_new 만 바꾼다. webbrowser.open 까지 같은 함수로 덮으면, 원본 open_new 가
# 내부에서 open(url, 1) 을 부르므로 인자 개수가 어긋나 TypeError 가 난다.
webbrowser.open_new = open_new

from colab_mcp import main          # noqa: E402  (패치가 먼저 걸려야 한다)

main()
