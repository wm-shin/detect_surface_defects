import time
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent

EPOCHS = 60
NAME = "full"

def main():
    model = YOLO("yolov8n-seg.pt")

    start = time.time()
    model.train(
        data = str(ROOT / "data" / "data.yaml"),
        epochs = EPOCHS,
        imgsz=960,
        batch=4,
        optimizer="AdamW",
        lr0=0.00015,
        mosaic=0.0,
        mixup=0.0,
        patience = 20,
        seed = 42,
        device = "mps",
        project=str(ROOT / "runs"),
        name = NAME
    )

    minutes = (time.time() - start) / 60
    msg = f"학습시간 : {minutes:.1f}분 (설정 {EPOCHS} epochs)"
    print(msg)

    # 학습 시간을 결과 폴더에 따로 저장한다. 같은 이름 폴더가 있으면 ultralytics가 "full-2"처럼
    # 번호를 붙이므로, NAME이 아니라 실제로 저장된 폴더(save_dir)를 쓴다.
    out = Path(model.trainer.save_dir) / "train_time.txt"
    out.write_text(msg + "\n", encoding="utf-8")
    print("저장:", out)


if __name__ == "__main__":
    main()