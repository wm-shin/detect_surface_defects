"""1주차 리포트 PDF를 만든다.

입력: component/ 아래 그림·CSV, annotation_guideline.md의 내용(아래에 요약해 옮김)
출력: scripts/report/week_1/week1_report.pdf
실행: python scripts/report/week_1/build_week1_report.py
"""
import csv
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
COMP = HERE / "component"
OUT = HERE / "week1_report.pdf"

pdfmetrics.registerFont(TTFont("KR", "/System/Library/Fonts/Supplemental/AppleGothic.ttf"))
BASE = ParagraphStyle("base", fontName="KR", fontSize=9.5, leading=14, alignment=TA_LEFT)
SMALL = ParagraphStyle("small", parent=BASE, fontSize=8.5, leading=12)
H0 = ParagraphStyle("h0", parent=BASE, fontSize=16, leading=22, spaceAfter=4)
H1 = ParagraphStyle("h1", parent=BASE, fontSize=12.5, leading=18, spaceBefore=10, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=BASE, fontSize=10.5, leading=15, spaceBefore=6, spaceAfter=2)
CODE = ParagraphStyle("code", fontName="Courier", fontSize=8.5, leading=11)
W = A4[0] - 4 * cm  # 본문 폭


def P(text, style=BASE):
    return Paragraph(text, style)


def bullets(items, style=BASE):
    return [Paragraph(f"• {t}", ParagraphStyle("b", parent=style, leftIndent=10, firstLineIndent=-8)) for t in items]


def table(rows, widths, header=True, style=SMALL):
    data = [[P(str(c), style) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    ts = [("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        ts.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")))
    t.setStyle(TableStyle(ts))
    return t


TMP = HERE / ".pdf_images"  # PDF에 넣을 축소본 (git에 안 올림)
TMP.mkdir(exist_ok=True)


def img(path, max_w, max_h, max_px=1400):
    """그림을 표시 크기에 맞춰 PDF에 넣는다. 원본 PNG를 그대로 넣으면 PDF가 수십 MB가 되므로
    긴 변 max_px 이하의 JPEG로 줄여 넣는다."""
    im = PILImage.open(path).convert("RGB")
    w, h = im.size
    if max(w, h) > max_px:
        r = max_px / max(w, h)
        im = im.resize((round(w * r), round(h * r)), PILImage.LANCZOS)
    small = TMP / (Path(path).stem + ".jpg")
    im.save(small, "JPEG", quality=85)
    s = min(max_w / w, max_h / h)
    return Image(str(small), width=w * s, height=h * s)


story = []

# ---- 표지 정보 -------------------------------------------------------------------
story += [P("Step 3 · 1주차 실습 보고서: 결함의 이해와 주석 기준", H0),
          P("이름: 신재윤 &nbsp;&nbsp; 학번: 20118701 &nbsp;&nbsp; 작성일: 2026-11-07"),
          Spacer(1, 6)]

# ---- ① 환경 확인 -----------------------------------------------------------------
story += [P("1. 환경 확인", H1),
          table([["항목", "값"],
                 ["기기", "Mac (Apple M4, 메모리 16 GB), macOS 26.6.2"],
                 ["Python / 패키지", "Python 3.12.13, torch 2.15.0, ultralytics 8.4.203, opencv-python 5.0.0"],
                 ["GPU", "CUDA 없음. Apple GPU(MPS) 사용 가능"]], [3.5 * cm, W - 3.5 * cm]),
          Spacer(1, 4),
          P("YOLOv8s-Seg 모델 로드 결과 (노트북 실행 출력):"),
          Preformatted("torch: 2.15.0\nmps: True\nmodel loaded", CODE),
          P("yolov8s-seg.pt 사전학습 가중치가 자동으로 내려받아져 정상 로드되었다. 강의 자료의 CUDA 확인 대신 "
            "torch.backends.mps.is_available()로 Apple GPU 사용 가능 여부를 확인했다.", SMALL)]

# ---- ② 데이터 요약 ---------------------------------------------------------------
story += [P("2. 데이터 요약", H1),
          P("논문 최종 데이터셋(AI Hub 지하 콘크리트 구조물 영상 기반, YOLO segmentation 폴리곤, train/val/test 분할 완료)을 "
            "받아 사용했다. 클래스 ID는 0 crack, 1 efflorescence, 2 spall_detach."),
          Spacer(1, 4),
          table([["split", "영상 수", "원본 / 증강", "클래스별 영상 수<br/>crack / efflo / spall", "클래스별 인스턴스 수<br/>crack / efflo / spall", "해상도"],
                 ["train", "3,890", "118 / 3,772", "713 / 879 / 2,298", "1,044 / 1,768 / 2,592", "1920×1080 3,579장<br/>1080×1920 311장"],
                 ["val", "40", "40 / 0", "10 / 17 / 13", "10 / 27 / 16", "1920×1080"],
                 ["test", "40", "40 / 0", "13 / 13 / 14", "14 / 19 / 14", "1920×1080"]],
                [1.3 * cm, 1.6 * cm, 2.2 * cm, 3.6 * cm, 3.8 * cm, W - 12.5 * cm]),
          Spacer(1, 4),
          P("train은 배포본 4,036장에서 데이터 점검으로 146장을 제외한 수다. val·test는 배포본 그대로다.", SMALL)]
story += bullets([
    "train–test 누수 55장: 원본 1개(URT017_2020_02_08_001_24512)가 test에 1장, train에 원본+증강 55장으로 같이 들어 있어 "
    "train 쪽을 제외했다(같은 원본은 같은 split 원칙).",
    "중복 28장: 내용이 바이트까지 같은 영상 27묶음(같은 회전·뒤집기 증강을 두 번 저장)에서 묶음당 1장만 남겼다.",
    "빈 파일 63장: 0바이트 영상. 다시 받아도 같아 배포본 문제로 보고 제외했다.",
    "모든 영상에 라벨이 하나 이상 있고, 한 영상에는 한 클래스만 라벨되어 있다(두 클래스 이상 라벨된 영상 0장).",
    "밝기 예시: 첫 영상의 흑백 밝기 평균 144.5, 표준편차 17.1. 영상마다 조도 차이가 크고 어두운 영상도 많다."], SMALL)

# ---- ③ 샘플 그림 -----------------------------------------------------------------
story += [KeepTogether([P("3. 샘플 영상 (samples9.png)", H1),
          img(COMP / "samples9.png", W, 15 * cm),
          P("전체 영상에서 무작위로 고른 9장. 조도, 촬영 방향(세로 영상 포함), 케이블·배관·이음부 같은 배경 요소가 다양하다.", SMALL)])]

# ---- ④ 하드 네거티브 -------------------------------------------------------------
story += [PageBreak(), P("4. 하드 네거티브: 결함이 아닌데 결함처럼 보이는 것", H1),
          P("증강본을 뺀 원본 198장(train 118, val 40, test 40)을 라벨과 겹쳐 모두 보고, 라벨이 없는 영역에서 결함과 혼동될 만한 것을 "
            "7종류 10개 골랐다. 출처 영상과 자른 좌표는 component/hard_negatives.csv에 있다.", SMALL),
          Spacer(1, 4)]
rows = [["", "종류", "혼동되는 결함", "설명 (출처)"]]
with (COMP / "hard_negatives.csv").open(encoding="utf-8") as f:
    for i, r in enumerate(csv.DictReader(f), 1):
        rows.append([img(COMP / r["file"], 4.2 * cm, 2.1 * cm), f"{i}. {r['kind']}", r["confused_with"],
                     f"{r['description']}<br/><font size=7>({r['split']}/{r['image']})</font>"])
data = [[c if not isinstance(c, str) else P(c, SMALL) for c in r] for r in rows]
t = Table(data, colWidths=[4.5 * cm, 2.6 * cm, 2.5 * cm, W - 9.6 * cm], repeatRows=1)
t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                       ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                       ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
story.append(t)

# ---- ⑤ 주석 기준서 ---------------------------------------------------------------
story += [PageBreak(), P("5. 주석 기준서", H1),
          P("데이터가 이미 폴리곤으로 주석되어 있어, 원본 198장의 라벨을 보고 주석자가 실제로 따른 규칙을 거꾸로 정리했다. "
            "형식은 YOLO segmentation 폴리곤이고, 결함 하나(인스턴스)마다 폴리곤 하나다.", SMALL),
          P("① 클래스 정의", H2),
          table([["클래스", "정의"],
                 ["crack", "콘크리트 표면의 선형·분기형·망상형 불연속. 보수재로 덮였어도 균열을 따라 이어진 것은 균열로 본다."],
                 ["efflorescence", "수분 이동으로 표면에 생긴 흰색·담색 침착물. 흘러내린 줄기 모양도 포함한다."],
                 ["spall_detach", "표면층이 들뜬 것(박리)과 재료가 떨어져 나간 것(박락)을 합친 클래스. 영상에서 두 상태의 경계가 모호해 하나로 묶는다."]],
                [2.6 * cm, W - 2.6 * cm]),
          P("② 포함 기준", H2)]
story += bullets([
    "crack: 육안으로 경로를 따라갈 수 있는 균열. 흰 실런트 등 보수재로 덮여 있어도 균열 경로를 따라 이어지면 포함. "
    "균열이 잠시 안 보이다 다시 나타나면 끊긴 구간마다 따로 인스턴스.",
    "efflorescence: 흰 침착물이 실제로 보이는 영역. 그림자나 케이블이 위를 지나가도 그 아래가 침착물이면 포함.",
    "spall_detach: 재료가 떨어져 패인 곳과 금이 가서 들뜬 주변 조각. 시공 이음부를 따라 떨어진 부분이 가장 흔하다. "
    "넓게 들뜬 판은 판 전체를 포함."], SMALL)
story += [P("③ 제외 대상", H2),
          table([["제외 대상", "혼동되는 클래스"],
                 ["시공 이음부·줄눈 (곧고 폭이 일정한 선, 어두운 홈)", "crack"],
                 ["케이블·전선·강선·배관", "crack"],
                 ["그림자 (케이블·지지대가 만든 어두운 띠)", "crack"],
                 ["조명 빛 번짐·정반사", "efflorescence"],
                 ["보수재 띠 자체 (균열 경로가 아닌 곳)", "crack"],
                 ["검은 누수·곰팡이 얼룩, 먼지", "spall_detach, efflorescence"],
                 ["점검자가 그린 분필 선·글씨·표시", "crack, efflorescence"]], [W - 4.5 * cm, 4.5 * cm]),
          P("④ 경계 규칙", H2)]
story += bullets([
    "crack: 균열선을 가운데 두고 양옆에 여유를 둔 띠 모양으로 감싼다(폴리곤 평균 폭 중앙값 약 40 px, 1920×1080 기준).",
    "efflorescence: 침착물의 바깥 경계를 들쭉날쭉한 그대로 촘촘히 따라간다. 흘러내린 줄기는 끝까지 포함.",
    "spall_detach: 패인 부분과 들뜬 조각을 함께 감싸고 구멍 테두리에 약간 여유를 둔다. 구멍이 여러 개면 하나씩 따로.",
    "결함이 영상 밖으로 이어지면 영상 가장자리까지 그린다."], SMALL)
story += [P("⑤ 판단 보류", H2)]
story += bullets([
    "판단이 어려운 영상은 임의로 라벨하지 않고 보류 목록에 모아 재검토한다.",
    "보류 유형: 이음부를 따라 이어진 균열(이음부까지 crack으로 칠할지), 젖은 표면의 흰 반사(백태인지 정반사인지), 대비가 낮은 얼룩형 백태."], SMALL)
story += [P("⑥ 예시 영상", H2),
          P("클래스별 라벨 예시는 다음 쪽의 표, 제외 대상 예시는 4절의 하드 네거티브 표.", SMALL),
          P("라벨에서 확인한 특징", H2)]
story += bullets([
    "한 영상에는 한 클래스만 라벨되어 있다. 그래서 다른 클래스의 결함이 보여도 라벨이 없다(예: spall_detach 영상 속 균열). "
    "모델이 이런 균열을 찾으면 평가에서는 오탐으로 세어진다.",
    "이음부를 따라 이어진 균열은 처리가 일관되지 않다. 대부분 이음부 자체는 칠하지 않지만 일부는 이음부 구간까지 crack에 포함했다.",
    "오래된 표면의 잔 그물 균열은 대체로 라벨하지 않았다."], SMALL)
story += [PageBreak(), P("⑥ 예시 영상: 클래스별 라벨 예시", H2),
          P("배포 라벨을 원본 영상에 겹쳐 그린 것. 빨강 crack, 하늘 efflorescence, 초록 spall_detach. 출처와 자른 좌표는 "
            "component/annotation_examples.csv에 있다.", SMALL), Spacer(1, 4)]
rows = [["", "클래스", "라벨이 그려진 방식 (출처)"]]
with (COMP / "annotation_examples.csv").open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append([img(COMP / r["file"], 5.0 * cm, 2.4 * cm), r["cls"],
                     f"{r['description']}<br/><font size=7>({r['split']}/{r['image']})</font>"])
data = [[c if not isinstance(c, str) else P(c, SMALL) for c in r] for r in rows]
t = Table(data, colWidths=[5.3 * cm, 2.6 * cm, W - 7.9 * cm], repeatRows=1)
t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                       ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                       ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
story.append(t)


def footer(canvas, doc):
    canvas.setFont("KR", 8)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"신재윤 20118701 · {doc.page}")


SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                  topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                  title="Step 3 1주차 실습 보고서", author="신재윤").build(story, onFirstPage=footer, onLaterPages=footer)
print("저장:", OUT)
