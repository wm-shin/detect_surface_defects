# train.py

사전학습된 YOLOv8n-Seg를 이 데이터셋으로 미세조정한다. 모델만 nano이고 나머지 설정은 강의 2주차 13쪽 그대로다. 에폭 수와 결과 폴더 이름은 파일 위쪽의 `EPOCHS`, `NAME`에서 바꾼다.

실행: `python scripts/train.py` (오래 돌릴 때는 `caffeinate -i python scripts/train.py`)

## 하는 일

| 단계 | 하는 일 |
|---|---|
| ① | 사전학습 가중치 `yolov8n-seg.pt`를 불러온다 (없으면 자동 다운로드) |
| ② | 강의 설정으로 학습한다: imgsz 960, batch 4, AdamW, lr0 0.00015, Mosaic·MixUp 끔, patience 20, seed 42, 장치는 맥의 MPS |
| ③ | 걸린 시간을 분 단위로 출력한다 (3주차 리포트용) |

같은 이름의 결과 폴더가 이미 있으면 덮어쓰지 않고 `이름-2`, `이름-3`으로 새로 만든다.

## 흐름

```mermaid
flowchart TD
    Y["data/data.yaml"] --> B
    W["yolov8n-seg.pt<br/>(사전학습 가중치)"] --> A
    subgraph M["main()"]
        A["① YOLO() 모델 불러오기"]
        B["② model.train()<br/>강의 2주차 13쪽 설정 + MPS"]
        C["③ 학습 시간 출력"]
        A --> B --> C
    end
    B --> R["runs/&lt;NAME&gt;/<br/>weights/best.pt · last.pt<br/>results.csv · results.png · args.yaml<br/>labels.jpg · train_batch*.jpg · val_batch*.jpg"]
```

## 출력 예

3 epoch 시험 실행(`EPOCHS = 3`, `NAME = "step3_try"`)의 끝부분.

```
      Epoch    GPU_mem   box_loss   seg_loss   cls_loss   dfl_loss  Instances       Size
        3/3       ...      1.398      2.746      1.547      1.554        ...        960
...
학습시간 : 20.3분
```
