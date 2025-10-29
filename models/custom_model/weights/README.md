# Custom Model Weights

This directory will contain the trained custom deer detection model.

## Expected File: `best.pt`

After training on a powerful machine, place the trained model here:

```
models/custom_model/weights/best.pt
```

## Training Instructions

See [`models/README.md`](../../README.md) or [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md) for complete training workflow.

**Quick Start:**

1. Train on GPU machine: `python backend/train_custom_model.py --dataset data/deer_dataset.yaml --epochs 100`
2. Copy `best.pt` to this directory
3. Commit to git: `git add best.pt && git commit -m "Add trained deer model"`
4. Push to GitHub so Pi can pull it

## Status

⚠️ **No custom model yet** - Use `models/yolov8n.pt` for general detection until custom model is trained.
