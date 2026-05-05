# CivicSetu — Smart Civic Issue Reporting and Resolution System

## Quick Start (3 steps)

### 1. Install dependencies
pip install flask flask-sqlalchemy flask-login flask-bcrypt

### 2. Get FREE Gemini API key (no card needed)
- Go to https://aistudio.google.com/
- Sign in with Google → Click "Get API Key" → "Create API Key"
- Copy the key (starts with AIzaSy...)

### 3. Run
# Windows CMD:
set GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxxxxxxxx
python run.py

# Mac/Linux:
export GEMINI_API_KEY=AIzaSy-xxxxxxxxxxxxxxxxxx
python run.py

Open http://localhost:5000

## Admin Login
Email: admin@civicsetu.in
Password: admin123

## AI Detection
- Uses Google Gemini 1.5 Flash Vision (FREE - 1500 calls/day)
- Auto-detects: pothole, garbage, water_leakage, streetlight, sewage, tree_fall, electricity, other
- If GEMINI_API_KEY not set → user selects manually, everything else still works
