import time
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent

EPOCHS = 3
NAME = "step3_try"

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
    print(f"학습시간 : {minutes:.1f}분")
if __name__ == "__main__":
    main()