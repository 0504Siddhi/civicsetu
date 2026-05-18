# CivicSetu — Smart Civic Issue Reporting & Resolution System

CivicSetu (सेतु = Bridge) is an AI-powered civic issue reporting platform that connects citizens and municipalities through structured, transparent, and trackable complaint management.

It enables citizens to report civic issues using images, while AI automatically detects and categorizes problems for faster resolution.

---

## 🌍 Problem

Many civic issues in India (potholes, garbage, water leakage, etc.) are still reported through informal channels like calls or WhatsApp messages, leading to:

- No tracking system  
- No accountability  
- No structured complaint records  

CivicSetu solves this by creating a transparent digital workflow.

---

## 🎯 Features

### 👤 Citizen Module
- Report civic issues using images  
- AI-based automatic issue detection  
- GPS-based location tagging  
- Unique complaint ID generation  
- Real-time status tracking (Pending → In Progress → Resolved)  

### 🤖 AI System
- Google Gemini Vision API integration  
- Auto-classifies issues (pothole, garbage, leakage, etc.)  
- Confidence-based fallback to manual selection  

### 🏛️ Admin Dashboard
- Manage and update complaints  
- Priority system based on issue volume  
- Status updates with timestamps  
- Audit logs (admin actions tracked)  

### 🏆 Engagement System
- Civic Honor Score  
- Badges for active users (Civic Hero, Area Guardian, etc.)  
- Encourages citizen participation  

---

## 🛠️ Tech Stack

- Python (Flask)  
- SQLite  
- HTML, CSS, JavaScript  
- Google Gemini Vision API  
- Render (Deployment)  

---

## ♿ Accessibility

- Keyboard navigation support  
- High contrast mode  
- Voice input support  
- ARIA labels  
- WAVE & Lighthouse tested  

---

## ⚙️ Setup Instructions

1. Install dependencies  
```bash
pip install -r requirements.txt
```
2. Set API key
```bash
GEMINI_API_KEY=your_api_key_here
```
3. Run the project
```bash
python run.py
```
