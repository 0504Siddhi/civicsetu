"""
ai_service/config.py
--------------------
Drop your Teachable Machine model URL here after training.

HOW TO TRAIN YOUR OWN MODEL (free, 10 minutes):
1. Go to https://teachablemachine.withgoogle.com/train/image
2. Create classes: pothole, garbage, water_leakage, streetlight, sewage, tree_fall, electricity, other
3. Upload 10-20 sample images per class (search Google Images)
4. Click Train Model → Export Model → Upload (TensorFlow.js)
5. Copy the shareable link and paste it as TM_MODEL_URL below

The demo uses a public pre-trained civic issues model.
"""

# Your Teachable Machine model URL (replace with your own after training)
TM_MODEL_URL = "https://teachablemachine.withgoogle.com/models/civic-issues-demo/"

# Confidence threshold — below this, AI won't auto-select (user picks manually)
CONFIDENCE_THRESHOLD = 0.65
