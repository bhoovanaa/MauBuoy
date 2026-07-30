# Model artifacts

Place these local checkpoints in this directory:

- `reefguardian_yolo11n_best.pt` - YOLO11n coral detector and
  Healthy/Bleached/Dead classifier.
- `vit_b_coralscop.pth` - Segment Anything ViT-B checkpoint used only for
  optional box-prompted coral-mask refinement.

Expected SHA-256 checksums for the artifacts integrated on 29 July 2026:

```text
8E6D3545F7A1B2F0165864741CB9B94297B2B6D457C2BC37C4BEFD30444B46A0  reefguardian_yolo11n_best.pt
CC589B67A4430173A35A61C6EFDB68E31D15D985096E17ABF27F92D6B9842D06  vit_b_coralscop.pth
```

The binary checkpoints are intentionally ignored by Git. Override their paths
with `REEFGUARDIAN_YOLO_MODEL` and `REEFGUARDIAN_SAM_MODEL`.
