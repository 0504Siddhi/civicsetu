# How to Train Your CivicSetu AI Model (10 minutes, free)

## Step 1 — Go to Teachable Machine
Open: https://teachablemachine.withgoogle.com/train/image

## Step 2 — Create Classes
Click "Add a class" and create these 8 classes (names must match exactly):
- pothole
- garbage
- water_leakage
- streetlight
- sewage
- tree_fall
- electricity
- other

## Step 3 — Add Training Images
For each class, upload 15–30 images:
- Search Google Images or use your own photos
- Drag and drop directly into each class panel
- More varied images = better accuracy

## Step 4 — Train
Click **"Train Model"** — takes ~2 minutes

## Step 5 — Export
1. Click **"Export Model"**
2. Select **"TensorFlow.js"** tab
3. Click **"Upload my model"** (saves to Google cloud, free)
4. Copy the shareable link — looks like:
   `https://teachablemachine.withgoogle.com/models/ABC123XYZ/`

## Step 6 — Plug into CivicSetu
Open `templates/citizen/submit.html` and find this line near the top of the `<script>`:

```js
const TM_MODEL_URL = "https://teachablemachine.withgoogle.com/models/KuKVAk1hA/";
```

Replace the URL with your own model URL and save.

That's it! The AI will now auto-detect issue types when citizens upload photos.

## Tips for Better Accuracy
- Include images taken on phones in various lighting conditions
- Include images at different angles and distances
- Include partial/blurry images (real-world conditions)
- For `other`, use random street/nature photos that don't fit any category
- Target 30+ images per class for best results
