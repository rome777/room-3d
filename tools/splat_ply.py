"""점 구름을 가우시안 스플랫 .ply 로 쓴다.

각도별 색 45칸(f_rest)은 헤더에 아예 넣지 않는다. 학습을 걸어야 채워지는 칸이라
0 으로 채워 적으면 파일만 3.6배가 된다. 빼면 칸이 17개, 알갱이 하나에 68바이트다.
"""

import numpy as np

SH_C0 = 0.28209479177387814

HEADER_FIELDS = (
    ["x", "y", "z"]
    + ["nx", "ny", "nz"]
    + ["f_dc_0", "f_dc_1", "f_dc_2"]
    + ["opacity"]
    + ["scale_0", "scale_1", "scale_2"]
    + ["rot_0", "rot_1", "rot_2", "rot_3"]
)
BYTES_PER_SPLAT = len(HEADER_FIELDS) * 4  # 68


def splat_radius(xyz, k=1.4):
    """알갱이가 덮는 넓이가 반지름의 제곱에 비례하니, 점 N 개로 표면을 덮으려면
    반지름이 N 의 제곱근에 반비례해야 한다. 이웃 점까지의 거리는 기준이 못 된다 —
    점이 사진마다의 깊이에서 나와 가장 가까운 이웃이 늘 같은 사진 안의 옆 화소다."""
    span = float((xyz.max(axis=0) - xyz.min(axis=0)).max())
    return k * span / np.sqrt(len(xyz))


def write_splat_ply(path, xyz, rgb, k=1.4, opacity=0.9, flip_yz=True):
    xyz = np.asarray(xyz, dtype=np.float32).reshape(-1, 3).copy()
    rgb = np.asarray(rgb, dtype=np.float32).reshape(-1, 3)
    if len(xyz) != len(rgb):
        raise ValueError("점 개수와 색 개수가 다릅니다: %d vs %d" % (len(xyz), len(rgb)))

    # 이 모델은 Y 가 아래를 향하고 three.js 는 Y 가 위다. 안 뒤집으면 거꾸로 선다.
    if flip_yz:
        xyz[:, 1] *= -1
        xyz[:, 2] *= -1

    n = len(xyz)
    r = splat_radius(xyz, k)

    out = np.zeros((n, len(HEADER_FIELDS)), dtype=np.float32)
    out[:, 0:3] = xyz
    # 3:6 법선은 안 쓴다. 0 으로 둔다.
    out[:, 6:9] = (rgb / 255.0 - 0.5) / SH_C0
    out[:, 9] = np.log(opacity / (1.0 - opacity))   # 로짓으로 저장한다
    out[:, 10:13] = np.log(r)                       # 크기는 로그로 저장한다
    out[:, 13] = 1.0                                # 안 돌린 사원수 (1,0,0,0)

    header = "ply\nformat binary_little_endian 1.0\nelement vertex %d\n" % n
    header += "".join("property float %s\n" % f for f in HEADER_FIELDS)
    header += "end_header\n"

    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(out.tobytes())

    return {"splats": n, "radius": r, "bytes_per_splat": BYTES_PER_SPLAT}


def camera_spread_ratio(cam_xyz, scene_xyz):
    """걸어 다닌 폭을 방 크기로 나눈 값. 0.1 아래면 사실상 한자리에서 찍은 것이다."""
    cam = np.asarray(cam_xyz, dtype=np.float64).reshape(-1, 3)
    pts = np.asarray(scene_xyz, dtype=np.float64).reshape(-1, 3)
    cam_span = np.linalg.norm(cam.max(axis=0) - cam.min(axis=0))
    diag = np.linalg.norm(pts.max(axis=0) - pts.min(axis=0))
    return float(cam_span / diag) if diag > 0 else 0.0


def drop_outliers(xyz, rgb, lo=0.5, hi=99.5):
    """창밖과 거울에 비친 것이 엉뚱하게 먼 거리로 잡힌다. 두면 장면이 한없이 커지고
    알갱이 크기 기준이 망가진다."""
    xyz = np.asarray(xyz).reshape(-1, 3)
    rgb = np.asarray(rgb).reshape(-1, 3)
    keep = np.ones(len(xyz), dtype=bool)
    for axis in range(3):
        a, b = np.percentile(xyz[:, axis], [lo, hi])
        keep &= (xyz[:, axis] >= a) & (xyz[:, axis] <= b)
    return xyz[keep], rgb[keep], int(keep.sum())
