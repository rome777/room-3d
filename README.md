# room-3d

폰으로 찍은 영상 하나에서 3차원 장면을 만들어 웹에 올리는 작업의 도구와 기록.
모두의연구소 "공간을 다루는 AI" 과정을 따라가며 만들었다.

```
영상 → 사진 24장 → 점 → 알갱이 → 줄인 파일 → 웹 주소
```

가운데 점을 만드는 일만 AI 가 하고(MapAnything), 나머지는 파일을 바꾸는 일이다.

## 보기

https://rome777.github.io/room-3d/my-open-space/

**직접 찍은 영상이 아니다.** 공개 데이터셋 [mip-NeRF 360](https://jonbarron.info/mipnerf360/)
의 `garden` 장면(CC BY 4.0, Barron 외)으로 돌린 연습 실행이고, 그 사실과 못 한 걸음을
[`my-open-space/README.md`](my-open-space/README.md) 에 밝혀 두었다.

## 들어 있는 것

| 파일 | 무엇 |
|---|---|
| `tools/colab_mcp_shim.py` | Claude Code 와 colab-mcp 를 붙이는 중계기 |
| `tools/colab_mcp_launch.py` | colab-mcp 가 붙을 코랩 노트를 고정하는 실행기 |
| `tools/splat_ply.py` | 점 구름을 가우시안 스플랫 `.ply` 로 쓰는 코드 |
| `my-open-space/index.html` | 알갱이를 브라우저에 띄우는 페이지 |
| `STATUS.md` | 현재 상태, 실측 수치, 알려진 함정, 사건 기록 |
| `CLAUDE.md` | 작업 규칙 (`AGENTS.md`·`GEMINI.md` 는 축약판) |

## 왜 중계기가 필요한가

구글의 `colab-mcp` 를 Claude Code 에 그냥 등록하면 **셀 조작 도구가 열리지 않는다.**
연결은 되는데 도구가 하나뿐이다.

colab-mcp 는 프록시다. 실제 셀 도구는 브라우저 쪽 코랩 페이지가 WebSocket 으로
내려준다. 그런데 클라이언트의 `tools/list` 가 연결보다 먼저 도착해 빈 목록을 받아
가고, 연결된 뒤 서버가 보내는 `tools/list_changed` 알림을 클라이언트가 처리하지
않아 목록을 다시 안 가져간다.

중계기가 `tools/list` 를 가로채 먼저 연결을 붙여 놓고 목록을 넘긴다.
자세한 내용과 밟은 지뢰는 `STATUS.md` 에 있다.

## 조용히 실패하는 자리들

`STATUS.md` 의 "알려진 함정" 에 재현 조건까지 적어 두었다. 요약하면 이렇다.

- `amp_dtype` 기본값이 `bf16` 이다. T4 에는 bf16 이 없어 메모리가 넘친다.
  **8장까지는 통과하고 본 실행에서 터진다.**
- `img_no_norm` 은 0~255 가 아니라 **0~1** 이다.
- `f_rest` 45칸을 헤더에 넣으면 파일만 3.6배가 된다. 알갱이 하나에 68바이트를 지킨다.
- `SparkRenderer` 를 장면에 넣지 않으면 오류 없이 화면만 까맣다.
- `.sog` 의 Spark 안쪽 이름은 `pcsogszip` 이다.
- `.spz` 는 splat-transform 이 판 4 로 쓰는데 Spark 는 판 3 까지만 읽는다.

## 쓰는 것들

MapAnything Apache-2.0, three.js MIT, Spark MIT, splat-transform MIT.

`.claude/skills/room-3d/` 의 작업 지침은
[SunCreation/room-3d-demo](https://github.com/SunCreation/room-3d-demo) 에서 가져온 것이라
이 저장소에 담지 않았다. 그쪽에서 받아 `.claude/skills/` 아래에 두면 된다.
