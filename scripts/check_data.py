"""데이터셋 무결성 점검.

강의가 세운 데이터 원칙을 하나씩 검사한다.
  ① data.yaml의 경로·클래스가 실제 폴더와 맞는다 (2주차 14쪽)
  ② 영상과 라벨이 1:1로 대응한다 (2주차 13쪽)
  ③ 라벨이 YOLO segmentation 포맷이다: 클래스 ID는 data.yaml의 범위, 좌표는 0~1, 폴리곤 점 3개 이상 (2주차 11·13쪽)
  ④ 영상을 읽을 수 있다 (크기 0, 손상 파일)
  ⑤ val·test에는 증강 영상이 없다 (2주차 3쪽)
  ⑥ 같은 원본에서 나온 영상은 같은 split에만 있다 (2주차 14쪽)
  ⑦ 같은 사진이 두 번 들어 있지 않다 — 중복 영상 (2주차 9쪽, 본 강의 25쪽)

실행: python scripts/check_data.py [data 폴더] [-v]   (기본 data/, -v는 문제 파일 전체 목록 출력)
문제가 하나라도 있으면 종료 코드 1.
"""
import hashlib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import yaml

ROOT = Path(__file__).resolve().parent.parent
SPLITS = ["train", "val", "test"]
EXPECTED_NAMES = {0: "crack", 1: "efflorescence", 2: "spall_detach"}  # 강의 2주차 14쪽 순서


# ---- 이 데이터셋 전용: 파일 이름 규칙 -------------------------------------------
AUG_SUFFIX = re.compile(r"_aug|_efflo_")  # 증강본 이름에 붙는 꼬리의 시작
def get_origin_id(stem: str) -> str:
    """파일 이름(확장자 제외)에서 원본 ID를 돌려준다.

    꼬리 두 종류를 뗀다.
      Roboflow 내보내기: ..._jpg.rf.<해시>        (val·test 일부 원본)
      증강: ..._aug_<n>_<번호>, ..._augfill_<번호>_<종류>, ..._efflo_<bright|contrast|hflip>   (train)
    예) URT002_2021_01_10_001_1636_aug_1_00064_augfill_01382_brightness -> URT002_2021_01_10_001_1636
        URT007_2022_01_03_001_5324_efflo_hflip -> URT007_2022_01_03_001_5324
    """
    stem = re.sub(r"_jpg\.rf\.[0-9a-f]+$", "", stem)
    return AUG_SUFFIX.split(stem, maxsplit=1)[0]  # 강의 2주차 12쪽 split("_aug")에 _efflo_ 추가


def is_augmented(stem: str) -> bool:
    return AUG_SUFFIX.search(stem) is not None


# ---- 검사 ------------------------------------------------------------------------
def check_labels(lbl_paths, class_ids):
    """빈 라벨, 형식 오류 파일 이름과 클래스별 인스턴스 수를 돌려준다."""
    empty, bad, inst = [], [], Counter()
    for p in lbl_paths:
        lines = [ln.split() for ln in p.read_text().splitlines() if ln.strip()]
        if not lines:
            empty.append(p.stem)
            continue
        for v in lines:
            try:
                cid = int(v[0])
                coords = [float(x) for x in v[1:]]
                ok = (cid in class_ids and len(coords) >= 6 and len(coords) % 2 == 0
                      and all(0.0 <= c <= 1.0 for c in coords))
            except ValueError:
                ok = False
            if not ok:
                bad.append(p.stem)
                break
            inst[cid] += 1
    return empty, bad, inst


def check_images(img_paths):
    """크기 0, 읽기 실패 파일 이름과 해상도 분포, 내용 해시를 돌려준다."""
    zero, unreadable, sizes, hashes = [], [], Counter(), {}
    for p in img_paths:
        if p.stat().st_size == 0:
            zero.append(p.stem)
            continue
        im = cv2.imread(str(p))
        if im is None:
            unreadable.append(p.stem)
            continue
        sizes[(im.shape[1], im.shape[0])] += 1
        hashes[p.stem] = hashlib.md5(p.read_bytes()).hexdigest()
    return zero, unreadable, sizes, hashes


class Report:
    """문제를 모아 두고 사람이 읽을 수 있게 출력한다."""

    def __init__(self, verbose):
        self.verbose = verbose
        self.counts = Counter()  # 항목 이름 -> 문제 수

    def problem(self, title, items, meaning, action, unit="개"):
        """items가 비어 있지 않으면 문제로 기록하고 뜻·조치·예시를 출력한다."""
        if not items:
            return
        items = sorted(items)
        self.counts[title] += len(items)
        print(f"  ✗ {title}: {len(items)}{unit}")
        print(f"      뜻: {meaning}")
        print(f"      조치: {action}")
        shown = items if self.verbose else items[:3]
        for it in shown:
            print(f"      - {it}")
        if len(items) > len(shown):
            print(f"      - ... 외 {len(items) - len(shown)}{unit} (-v 로 전체 출력)")

    def total(self):
        return sum(self.counts.values())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    verbose = "-v" in sys.argv
    data = Path(args[0]) if args else ROOT / "data"
    rep = Report(verbose)
    print(f"=== 데이터 무결성 점검: {data} ===")
    print("✗ 가 없는 항목은 통과. 각 ✗ 아래에 뜻과 조치가 있다.\n")

    # ① data.yaml
    print("① data.yaml — 학습·평가 때 YOLO에 넘기는 데이터 설정 파일")
    yaml_path = data / "data.yaml"
    cfg = yaml.safe_load(yaml_path.read_text()) if yaml_path.exists() else {}
    names = cfg.get("names", {})
    names = dict(enumerate(names)) if isinstance(names, list) else {int(k): v for k, v in names.items()}
    class_ids = set(names) or set(EXPECTED_NAMES)
    if not cfg:
        rep.problem("data.yaml 없음", [str(yaml_path)],
                    "YOLO가 데이터 위치와 클래스 이름을 알 수 없다.",
                    "강의 2주차 15쪽 형식으로 data.yaml을 만든다.")
    else:
        if names != EXPECTED_NAMES:
            rep.problem("names가 강의 순서와 다름", [str(names)],
                        "라벨 파일의 클래스 ID(0·1·2)와 이름이 어긋나면 모델이 엉뚱한 이름을 배운다.",
                        "names를 0: crack, 1: efflorescence, 2: spall_detach 로 맞춘다.")
        yaml_root = Path(cfg.get("path", "."))
        if not yaml_root.is_absolute():
            yaml_root = (yaml_path.parent / yaml_root).resolve()
        if yaml_root != data.resolve():
            rep.problem("path가 이 폴더를 가리키지 않음", [f"data.yaml의 path = {cfg.get('path')}"],
                        "YOLO는 path 아래에서 images/train 등을 찾는다. 지금은 다른 컴퓨터의 경로라 이 기기에서 영상을 못 찾는다.",
                        f"path를 '{data.resolve()}' 또는 상대 경로 '.' 로 고친다.")
        missing = [f"{s}: {cfg[s]}" for s in SPLITS if s in cfg and not (data / cfg[s]).is_dir()]
        rep.problem("split 폴더 없음", missing,
                    "data.yaml에 적힌 train/val/test 폴더가 실제로 없다.",
                    "폴더 이름을 맞추거나 data.yaml의 경로를 고친다.")
    print()

    # ②~⑤ split별
    print("②~⑤ split별 — 영상·라벨 대응, 라벨 형식, 영상 읽기, 증강 여부")
    stems_by_split, hash_by_split = {}, {}
    for s in SPLITS:
        imgs = {p.stem: p for p in (data / "images" / s).glob("*.jpg")}
        lbls = {p.stem: p for p in (data / "labels" / s).glob("*.txt")}
        stems_by_split[s] = set(imgs)
        empty, bad, inst = check_labels(lbls.values(), class_ids)
        zero, unreadable, sizes, hashes = check_images(imgs.values())
        hash_by_split[s] = hashes
        inst_txt = " / ".join(f"{names.get(c, c)} {inst[c]}" for c in sorted(class_ids))
        size_txt = " · ".join(f"{w}x{h} {n}장" for (w, h), n in sizes.most_common(3))
        print(f"[{s}] 영상 {len(imgs)}장, 라벨 {len(lbls)}개, 인스턴스 {inst_txt}, 해상도 {size_txt}")
        rep.problem("라벨 없는 영상", set(imgs) - set(lbls),
                    "영상은 있는데 같은 이름의 라벨 .txt가 없다. YOLO는 이런 영상을 '결함 없음(배경)'으로 학습한다.",
                    "의도한 배경 영상이 아니면 라벨을 만들거나 영상을 뺀다.", "장")
        rep.problem("영상 없는 라벨", set(lbls) - set(imgs),
                    "라벨 .txt는 있는데 같은 이름의 영상이 없다. 학습에 쓰이지 않는 라벨이다.",
                    "영상이 빠진 것인지 확인하고, 아니면 라벨을 지운다.")
        rep.problem("빈 라벨", empty,
                    "라벨 파일이 있지만 줄이 하나도 없다. YOLO는 '결함 없음(배경)'으로 본다.",
                    "의도한 배경 영상인지 확인한다. 이 데이터셋은 모든 영상에 결함이 있어야 한다.")
        rep.problem("형식 오류 라벨", bad,
                    "줄이 '클래스ID x1 y1 x2 y2 ...' 꼴이 아니다. 클래스 ID가 범위 밖이거나, 좌표가 0~1을 벗어나거나, 점이 3개 미만이다. YOLO가 학습 중 오류를 내거나 그 줄을 버린다.",
                    "강의 2주차 11쪽대로 Segmentation 포맷으로 다시 내보내거나 해당 줄을 고친다.")
        rep.problem("크기 0 영상", zero,
                    "파일 이름은 있지만 내용이 0바이트다. 학습 때 읽을 수 없어 건너뛰거나 오류가 난다. 다운로드가 끊겼거나 배포본부터 비어 있는 것.",
                    "원본에서 다시 받는다. 원본도 비어 있으면 영상·라벨을 함께 빼고 목록을 남긴다.", "장")
        rep.problem("읽기 실패 영상", unreadable,
                    "크기는 있지만 OpenCV가 열지 못한다. 손상됐거나 JPEG가 아닌 파일이다.",
                    "원본에서 다시 받거나 뺀다.", "장")
        if s != "train":
            rep.problem(f"{s}에 증강 영상", [x for x in imgs if is_augmented(x)],
                        "검증·테스트셋에는 원본만 있어야 한다(강의 2주차 3쪽). 증강본이 있으면 평가 기준이 흐려지고 train과 원본을 공유할 가능성이 크다.",
                        "해당 영상을 train으로 옮기거나 뺀다.", "장")
    print()

    # ⑥ 원본 단위 분할
    print("⑥ 원본 단위 분할 — 같은 사진에서 나온 영상(원본 + 증강본)은 한 split에만 있어야 한다")
    origin_splits = defaultdict(set)
    for s, stems in stems_by_split.items():
        for x in stems:
            origin_splits[get_origin_id(x)].add(s)
    print("  원본 ID 수: " + " · ".join(f"{s} {sum(1 for sp in origin_splits.values() if s in sp)}" for s in SPLITS))
    leaks = []
    for o, sp in origin_splits.items():
        if len(sp) > 1:
            per = {s: sum(1 for st in stems_by_split[s] if get_origin_id(st) == o) for s in sorted(sp)}
            leaks.append(f"{o} -> " + ", ".join(f"{s} {n}장" for s, n in per.items()))
    rep.problem("여러 split에 걸친 원본 ID", leaks,
                "같은 사진에서 나온 영상이 두 split에 같이 있다. 모델이 학습 때 본 사진으로 평가하게 되어 성능이 부풀려진다(데이터 누수, 강의 2주차 14·21쪽).",
                "한쪽 split에서 그 원본의 파일을 모두 뺀다. 테스트셋은 고정하는 것이 원칙이므로 보통 train 쪽을 뺀다.")
    print()

    # ⑦ 사본
    print("⑦ 중복 영상 — 내용이 완전히 같은 사진이 두 장 이상 들어 있는지")
    by_hash = defaultdict(list)
    for s, hashes in hash_by_split.items():
        for stem, h in hashes.items():
            by_hash[h].append(f"{s}/{stem}")
    dups = [" = ".join(sorted(v)) for v in by_hash.values() if len(v) > 1]
    extra = sum(len(v) - 1 for v in by_hash.values() if len(v) > 1)
    rep.problem("중복 영상 묶음", dups,
                f"같은 사진이 이름만 다르게 두 장 이상 들어 있다. 묶음마다 1장만 남기면 지울 수 있는 중복이 {extra}장. 같은 split 안이면 그 샘플이 학습에 두 번 세어지고, 다른 split 사이면 누수다. "
                "이 데이터셋에서는 증강 스크립트가 같은 회전·뒤집기를 두 번 저장한 것.",
                "묶음마다 1장만 남기고 나머지 영상·라벨을 뺀다. 뺀 목록은 남긴다.", "묶음")
    print()

    # 요약
    if rep.total() == 0:
        print("결과: 문제 없음")
    else:
        print(f"결과: 문제 {rep.total()}건")
        for title, n in rep.counts.most_common():
            print(f"  - {title}: {n}")
    sys.exit(1 if rep.total() else 0)


if __name__ == "__main__":
    main()
