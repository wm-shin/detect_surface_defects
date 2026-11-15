"""2주차 리포트 PDF를 만든다. 강의 2주차 17쪽의 제출물 여섯 가지만 담는다.

입력: component/ 아래 curve.png, format_check.txt, check_data_output.txt
      scripts/check_data.py (원본 ID 코드를 그대로 옮겨 싣는다)
출력: scripts/report/week_2/week2_report.pdf
실행: python scripts/report/week_2/build_week2_report.py
"""
import inspect
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
COMP = HERE / "component"
OUT = HERE / "week2_report.pdf"
sys.path.insert(0, str(HERE.parent.parent))  # scripts/
import check_data  # noqa: E402

pdfmetrics.registerFont(TTFont("KR", "/System/Library/Fonts/Supplemental/AppleGothic.ttf"))
BASE = ParagraphStyle("base", fontName="KR", fontSize=9.5, leading=14, alignment=TA_LEFT)
SMALL = ParagraphStyle("small", parent=BASE, fontSize=8.5, leading=12)
H0 = ParagraphStyle("h0", parent=BASE, fontSize=16, leading=22, spaceAfter=4)
H1 = ParagraphStyle("h1", parent=BASE, fontSize=12.5, leading=18, spaceBefore=10, spaceAfter=4)
CODE = ParagraphStyle("code", parent=BASE, fontSize=7.5, leading=10.5)  # 한글이 섞여 있어 본문 글꼴을 쓴다
W = A4[0] - 4 * cm  # 본문 폭


def P(text, style=BASE):
    return Paragraph(text, style)


def bullets(items, style=SMALL):
    return [Paragraph(f"• {t}", ParagraphStyle("b", parent=style, leftIndent=10, firstLineIndent=-8)) for t in items]


def table(rows, widths):
    t = Table([[P(str(c), SMALL) for c in r] for r in rows], colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def block(text):
    """코드나 실행 출력을 회색 상자에 줄 그대로 넣는다. 긴 줄은 상자 안에서 줄바꿈된다."""
    lines = [escape(ln).replace(" ", "&nbsp;") if ln.strip() else "&nbsp;" for ln in text.rstrip().splitlines()]
    t = Table([[Paragraph("<br/>".join(lines), CODE)]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f4f4")),
                           ("BOX", (0, 0), (-1, -1), 0.4, colors.grey)]))
    return t


def between(src, start, end):
    """src에서 start가 든 줄부터 end가 든 줄까지를 돌려준다."""
    lines = src.splitlines()
    i = next(n for n, ln in enumerate(lines) if start in ln)
    j = next(n for n, ln in enumerate(lines) if end in ln and n >= i)
    return "\n".join(lines[i:j + 1])


src = Path(check_data.__file__).read_text(encoding="utf-8")
origin_code = between(src, "AUG_SUFFIX = re.compile", "return AUG_SUFFIX.split")
overlap_code = inspect.cleandoc(between(src, "origin_splits = defaultdict(set)", "leaks.append"))
check_out = (COMP / "check_data_output.txt").read_text(encoding="utf-8").replace("✗", "x")

story = [P("Step 3 · 2주차 실습 보고서: 주석과 모델 학습", H0),
         P("이름: 신재윤 &nbsp;&nbsp; 학번: 20118701 &nbsp;&nbsp; 작성일: 2026-11-15"),
         Spacer(1, 6)]

# ---- ① 주석 결과 -----------------------------------------------------------------
story += [P("1. 주석 결과", H1),
          P("train 원본에서 고른 15장을 CVAT에서 폴리곤으로 직접 주석하고 Ultralytics YOLO Segmentation 포맷으로 내보냈다. "
            "과정을 익히는 연습이라 이 라벨은 학습에 쓰지 않았다.", SMALL),
          Spacer(1, 4),
          table([["", "crack", "efflorescence", "spall_detach", "합계"],
                 ["영상 수", "4", "6", "5", "15"],
                 ["인스턴스 수", "4", "6", "5", "15"]], [3 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm])]

# ---- ② 포맷 확인 -----------------------------------------------------------------
story += [P("2. 포맷 확인", H1),
          P("직접 주석해 내보낸 라벨의 첫 파일 첫 줄 (강의 10쪽 코드 실행 출력):", SMALL),
          block((COMP / "format_check.txt").read_text(encoding="utf-8"))]

# ---- ③ 무결성 점검 ---------------------------------------------------------------
story += [P("3. 무결성 점검", H1),
          P("scripts/check_data.py 실행 출력. 영상–라벨 대응, 빈 라벨, 클래스 ID, 좌표 범위, 영상 읽기, 원본 단위 분할, "
            "중복 영상을 점검한다.", SMALL),
          block(check_out),
          Spacer(1, 3),
          P("이상 항목 수정 여부: 1주차 점검에서 배포본 train 4,036장에 아래 세 가지 오류가 있는 것을 찾았고, 해당 146장(영상과 라벨)을 "
            "train에서 제외했다. 제외 후 위와 같이 다시 점검해 문제 0건이며, 이번 주 학습은 정리된 train 3,890장으로 했다. "
            "val·test 각 40장은 배포본 그대로다.", SMALL),
          Spacer(1, 3),
          table([["오류", "제외한 수", "내용", "그대로 학습하면 생기는 문제"],
                 ["train–test 누수", "55장",
                  "원본 1개(URT017_2020_02_08_001_24512)가 test에 1장, train에 원본과 증강본 55장으로 같이 들어 있었다.",
                  "학습 때 본 사진으로 평가하게 되어 테스트 성능이 부풀려진다."],
                 ["중복 영상", "28장",
                  "내용이 완전히 같은 영상 27묶음. 같은 회전·뒤집기 증강이 두 번 저장된 것으로, 묶음마다 1장만 남겼다.",
                  "같은 샘플이 학습에 두 번 세어진다."],
                 ["0바이트 영상", "63장",
                  "파일 이름만 있고 내용이 비어 있다. 다시 받아도 같아 배포본 자체의 문제로 보았다.",
                  "학습 중 읽지 못해 건너뛰거나 오류가 난다."]],
                [2.6 * cm, 1.8 * cm, W - 9.4 * cm, 5 * cm]),
          Spacer(1, 3),
          P("세 오류 모두 train의 증강본에서 났다. 영상–라벨 이름 대응, 클래스 ID, 좌표 범위만 보는 점검(강의 13쪽 코드)으로는 "
            "잡히지 않아 파일 크기, 파일 내용(md5), 원본 ID를 보는 검사를 더했다.", SMALL)]

# ---- ④ 분할 코드 -----------------------------------------------------------------
story += [P("4. 분할 코드 (원본 ID 기준)", H1),
          P("데이터가 이미 train/val/test로 나뉘어 배포되어 새로 나누지 않고, 배포된 분할이 원본 단위인지 확인했다. "
            "파일 이름에서 원본 ID를 뽑는 부분:", SMALL),
          block(origin_code),
          Spacer(1, 3),
          P("같은 원본 ID가 두 split 이상에 있는지 찾는 부분:", SMALL),
          block(overlap_code),
          Spacer(1, 3),
          P("결과: 원본 ID 수 train 119 · val 40 · test 40, 여러 split에 걸친 원본 ID 0건. val·test에 증강 영상 0장.", SMALL)]

# ---- ⑤ 학습 곡선 -----------------------------------------------------------------
story += [P("5. 학습 곡선", H1),
          Image(str(COMP / "curve.png"), width=W, height=W / 3),
          P("3 epoch 시험 실행(train 3,890장, val 40장)의 segmentation loss와 mask mAP. 학습 손실은 4.10 → 2.75로 줄었고 "
            "mask mAP50은 0.355 → 0.529로 올랐다. 학습 시간 20.3분(Apple M4, MPS).", SMALL)]

# ---- ⑥ 설정 근거 -----------------------------------------------------------------
story += [P("6. 설정 근거", H1)]
story += bullets([
    "imgsz 960: 균열은 폭이 몇 픽셀뿐이라 입력을 작게 줄이면 사라진다. 가는 균열의 세부를 보존하려고 큰 입력을 쓴다. "
    "종횡비를 유지하는 letterbox로 맞춰 형상 왜곡을 줄인다.",
    "Mosaic·MixUp 비활성화: Mosaic은 여러 영상을 이어 붙여 콘크리트 표면의 공간적 맥락을 왜곡하고, MixUp은 두 영상을 "
    "겹쳐 결함 경계를 물리적으로 의미 없게 만든다. 결함의 경계와 주변 맥락이 판단 근거라서 둘 다 껐다.",
    "모델: 장비 사양 때문에 강의의 YOLOv8s-Seg 대신 더 작은 YOLOv8n-Seg를 썼다. 학습 장비가 CUDA GPU가 아닌 "
    "Apple M4(MPS, 메모리 16 GB)라서 small은 60 epoch에 약 13~14시간이 걸리는 것으로 추정되었다. "
    "나머지(batch 4, AdamW, lr0 0.00015, patience 20, seed 42)는 강의 설정 그대로다."])

SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                  topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                  title="Step 3 2주차 실습 보고서", author="신재윤").build(story)
print("저장:", OUT)
