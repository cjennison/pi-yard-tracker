# Active Learning / Human-in-the-Loop Training

## Overview

The **Active Learning** feature enables continuous model improvement by allowing users to mark photos where the model missed detections. This implements a **Human-in-the-Loop (HITL)** workflow where field deployment reveals edge cases that can be used to retrain and improve the model.

## Industry Context

This is a **best practice** in production ML systems, known as:

- **Active Learning**: Strategically selecting data for annotation
- **Hard Negative Mining**: Focusing on missed detections
- **Continuous Learning**: Iterative model improvement with real-world data
- **Domain Adaptation**: Adapting synthetic training data to real backyard conditions

## User Workflow

1. **Deploy Camera** - Camera captures photos in the field (e.g., overnight)
2. **Review Photos** - User reviews captured photos via web interface
3. **Mark Misses** - When model missed a detection, click "Mark for Retraining"
   - Photo is flagged in database (`marked_for_retraining = true`)
   - Photo is copied to `data/to_annotate/` directory
4. **Annotate** - User runs annotation tool to draw bounding boxes on marked photos
5. **Retrain** - Add annotated photos to training dataset and retrain model
6. **Deploy** - Test new model, compare metrics, deploy if better
7. **Repeat** - Continuous improvement cycle

## Database Schema

New columns added to `photos` table:

```sql
marked_for_retraining BOOLEAN NOT NULL DEFAULT 0
marked_at TIMESTAMP
```

## API Endpoints

### Mark Photo for Retraining

```http
POST /photos/{photo_id}/mark-for-retraining
```

- Marks photo in database
- Copies photo to `data/to_annotate/`
- Returns updated photo with `marked_for_retraining: true`

### Unmark Photo

```http
DELETE /photos/{photo_id}/mark-for-retraining
```

- Removes flag from database
- Does NOT delete photo from `data/to_annotate/` (preserves annotations)

### List Marked Photos

```http
GET /photos/marked/list?limit=100&offset=0
```

- Returns all photos marked for retraining
- Supports pagination

### Count Marked Photos

```http
GET /photos/marked/count
```

- Returns `{"count": N}` for display in dashboard

## Frontend Integration

### Photos Page

- Modal for each photo now includes "Mark for Retraining" button
- Button shows different states:
  - **Not Marked**: Blue "Mark for Retraining" button with brain icon
  - **Already Marked**: Orange "Marked for Retraining" button with checkmark
- Click toggles state (mark/unmark)
- Uses React Query mutations for optimistic updates

### TypeScript Types

```typescript
interface Photo {
  // ... existing fields
  marked_for_retraining: boolean;
  marked_at: string | null;
}
```

### API Hooks

```typescript
useMarkPhotoForRetraining(); // Mutation to mark photo
useUnmarkPhotoForRetraining(); // Mutation to unmark photo
useMarkedPhotosCount(); // Query for count (dashboard)
```

## File Organization

### Backend

- `backend/database/migrations/001_add_marked_for_retraining.sql` - Schema migration
- `backend/database/migrate.py` - Migration runner
- `backend/database/queries/active_learning.py` - Query functions
- `backend/api/routes/photos.py` - API endpoints

### Directory Structure

```
data/
├── photos/              # Original captured photos
├── to_annotate/         # Photos marked for retraining (copied here)
├── training_data/       # Organized dataset (train/val/test)
└── synthetic_training/  # Generated synthetic images
```

## Best Practices

### ✅ DO:

- Mark both false negatives (missed detections) AND false positives (wrong detections)
- Annotate marked photos carefully using annotation tool
- Keep a balanced dataset (don't only add hard examples)
- Track model version that generated each detection
- Compare baseline metrics before deploying retrained model
- Keep validation set separate from field data

### ⚠️ DON'T:

- Put field photos directly into validation set (data leakage)
- Delete original training data when adding new photos
- Deploy retrained model without testing on validation set
- Over-fit to edge cases (maintain dataset balance)

## Retraining Process

1. **Collect Marked Photos**

   ```bash
   # Photos are already in data/to_annotate/
   ls data/to_annotate/*.jpg
   ```

2. **Annotate Images**

   ```bash
   python backend/training/annotation_tool.py \
       --input data/to_annotate \
       --output data/to_annotate
   ```

3. **Add to Training Dataset**

   ```bash
   # Copy annotated images and labels to training data
   cp data/to_annotate/*.jpg data/training_data/images/train/
   cp data/to_annotate/*.txt data/training_data/labels/train/
   ```

4. **Retrain Model**

   ```bash
   # On powerful machine (not Raspberry Pi!)
   python backend/training/train_custom_model.py \
       --dataset data/deer_dataset.yaml \
       --epochs 50 \
       --batch 16
   ```

5. **Test New Model**

   ```bash
   python backend/training/test_custom_model.py \
       --model models/custom_model/weights/best.pt \
       --images data/training_data/images/val
   ```

6. **Compare Metrics**

   - Check validation accuracy
   - Compare to baseline model
   - Test on real photos from `data/to_annotate/`

7. **Deploy if Better**

   ```bash
   # Backup old model
   cp models/custom_model/weights/best.pt models/custom_model/weights/best_backup.pt

   # Copy new model
   cp runs/detect/train/weights/best.pt models/custom_model/weights/best.pt

   # Commit to git
   git add models/custom_model/weights/best.pt
   git commit -m "Retrained model with active learning data"
   ```

## Performance Tracking

### Recommended Metrics to Track:

- **Precision**: What % of detections are correct?
- **Recall**: What % of actual objects are detected?
- **mAP (mean Average Precision)**: Overall detection quality
- **False Positive Rate**: How often does it see things that aren't there?
- **False Negative Rate**: How often does it miss objects?

### Create Retraining Log:

```
data/retraining_log.csv:
date,model_version,photos_added,precision,recall,mAP50,notes
2025-10-30,v1.0,0,0.85,0.78,0.82,Initial model
2025-11-15,v1.1,50,0.89,0.83,0.86,Added nighttime deer photos
2025-12-01,v1.2,30,0.91,0.87,0.89,Added rainy day photos
```

## Future Enhancements

- [ ] Dashboard widget showing marked photos count
- [ ] Batch annotation interface in web UI
- [ ] Automatic quality checks on annotations
- [ ] Model performance comparison dashboard
- [ ] Export marked photos as YOLO dataset
- [ ] Integration with auto-labeling (use current model to pre-label)
- [ ] A/B testing different model versions
- [ ] Confidence threshold optimization based on field data

## Benefits Realized

1. **Real-world Adaptation**: Model learns actual backyard conditions
2. **Edge Case Discovery**: Find scenarios not in synthetic data
3. **Continuous Improvement**: Incremental gains with each deployment
4. **Cost-Effective**: Reuse photos already being captured
5. **Targeted Learning**: Focus on what the model struggles with
6. **Production-Ready**: Industry-standard ML workflow
