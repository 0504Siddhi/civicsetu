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
- Auto-classifies issues (pothole, garbage, leakage, streetlight, sewage, tree fall, electricity, etc.)  
- Confidence-based fallback to manual selection  

### 🏛️ Admin Dashboard
- Manage and update complaints  
- Live priority system based on real-time complaint volume  
- Status updates with audit logs and timestamps  
- CSV Export of complaint history  

### 🏆 Engagement System
- Civic Honor Score  
- Badges for active users (Civic Hero, Area Guardian, Top Contributor)  
- Encourages citizen participation  

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt)  
- **Database:** SQLite (local) / PostgreSQL (production)  
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5  
- **AI Vision Engine:** Google Gemini Vision API  
- **Image Storage:** Cloudinary (Production) / Local Disk (Development)  
- **Production Server:** Gunicorn WSGI  
- **Deployment:** Render  

---

## ♿ Accessibility

- Keyboard navigation support  
- High contrast mode  
- Voice input support  
- ARIA labels  
- WAVE & Lighthouse tested  

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in the values:

| Variable | Description | Required in Production | Default / Example |
|---|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key from AI Studio | **Yes** | `AIzaSy...` |
| `SECRET_KEY` | Secret key for Flask secure sessions | **Yes** | 32-byte hex string |
| `CLOUDINARY_URL` | Cloudinary connection string for persistent images | **Yes** (in Production) | `cloudinary://key:secret@cloud` |
| `DATABASE_URL` | PostgreSQL connection string | Optional (uses SQLite if omitted) | `postgresql://user:pass@host/db` |
| `FLASK_ENV` | Environment mode (`development` / `production`) | Optional | `development` |
| `ADMIN_EMAIL` | Initial super admin email | Optional | `admin@civicsetu.in` |
| `ADMIN_PASSWORD` | Initial super admin password | Optional (required for seeding in prod) | Custom secure password |

---

## 🚀 Local Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/civicsetu.git
   cd civicsetu
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_development_secret_key
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```
   Open your browser at `http://localhost:5000`.

---

## ☁️ Render Deployment

1. Create a new **Web Service** on [Render](https://render.com).
2. Connect your GitHub repository.
3. Configure the build & start commands:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app` (or uses the included `Procfile`)
4. Add Environment Variables in Render Dashboard:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `SECRET_KEY`: A secure random secret key
   - `CLOUDINARY_URL`: Your Cloudinary connection string (for persistent complaint photos)
   - `DATABASE_URL`: (Optional) Render PostgreSQL connection string
   - `ADMIN_PASSWORD`: (Optional) Password for initial admin seeding
