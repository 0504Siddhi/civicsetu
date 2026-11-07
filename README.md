# CivicSetu

CivicSetu is a web-based civic issue reporting and resolution platform that bridges citizens and municipal administrations through structured, transparent complaint workflows. Citizens can report civic issues with photo uploads, automatic geolocation tagging, and AI-assisted issue classification, while municipal administrators manage resolution lifecycles using dynamic priority queues, audit logs, and status tracking. The application is built with Python Flask and provides persistent cloud asset storage, role-based access control, and mobile-responsive interfaces.

---

## Key Features

### Citizen Portal
- **Complaint Submission**: Citizens can file civic complaints with photos (PNG/JPG, up to 5 MB), geolocation tagging, and descriptions.
- **AI-Assisted Issue Classification**: Integrates Google Gemini Vision API (`POST /api/ai-classify`) to automatically categorize issues (potholes, garbage, water leakage, streetlights, sewage, tree falls, electrical hazards) with confidence scores and manual override options.
- **Geolocation Integration**: Auto-populates coordinates or addresses using the browser Geolocation API and OpenStreetMap Nominatim reverse geocoding.
- **Complaint Tracking**: Real-time status monitoring (`Pending`, `In Progress`, `Resolved`, `Rejected`) with unique complaint IDs.
- **Community Interaction**: Citizen engagement through like/dislike reactions and public comments on complaint records.
- **Citizen Profile & Gamification**: Profile management with activity metrics, a Civic Honor Score, and milestone badges (Civic Hero, Area Guardian, Top Contributor).
- **Accessibility Tools**: Integrated accessibility controls including client-side font resizing (A+/A-/A), high contrast mode toggle, and Web Speech API voice input for complaint descriptions.

### Administrative Management
- **Role-Based Access Control**: Strict segregation between Citizen and Admin roles via Flask-Login and session authentication (`@admin_required`).
- **Real-Time Operational Dashboard**: Metrics for total, pending, in-progress, resolved, and rejected complaints.
- **Dynamic Priority Engine**: Automatically calculates complaint urgency levels (`Critical`, `High`, `Medium`, `Low`) based on live complaint volume per category across the municipality.
- **Status Workflow & Audit Logging**: Admins update complaint statuses with audit remarks; all transitions are tracked in a dedicated `StatusLog` table with timestamps.
- **Data Export**: Built-in CSV export (`/admin/complaints/export`) for external reporting and analysis.

### Resilience & Storage
- **Dual-Mode Image Storage**: Production uses Cloudinary CDN for persistent asset storage; local development falls back to local disk storage (`static/uploads/`).
- **Compensating Cleanup**: Automatic asset cleanup on Cloudinary if an associated database transaction fails, preventing orphaned cloud assets.
- **CSRF Protection**: Cryptographic HMAC-based CSRF protection on state-changing requests.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3, Flask 3.0+ |
| **ORM & Database** | Flask-SQLAlchemy 3.1+, SQLite (development), PostgreSQL (production via psycopg2-binary) |
| **Authentication & Security** | Flask-Login, Flask-Bcrypt, HMAC CSRF verification |
| **AI Vision Engine** | Google Gemini API (urllib client invoking Gemini 2.5 and 3.x series models with retry handling) |
| **Cloud Storage** | Cloudinary Python SDK (`cloudinary>=1.36.0`) |
| **Production WSGI** | Gunicorn 21.2+ |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons |
| **External APIs** | OpenStreetMap Nominatim API, Web Speech API (browser-native) |

---

## Project Architecture

CivicSetu follows a modular Flask application structure using Blueprints and an MVC-oriented design pattern:

```text
[ Browser / Client ]
       │
       ├─ HTTP Requests (Jinja2 Templates & Bootstrap 5 UI)
       ├─ Asynchronous Calls (POST /api/ai-classify with base64 image data)
       └─ External APIs (OpenStreetMap Nominatim reverse geocoding)
       │
[ Flask Application Server (run.py / app.py) ]
       │
       ├── Blueprints:
       │     ├── auth_bp     (/login, /register, /logout)
       │     ├── citizen_bp  (/citizen/dashboard, /citizen/submit, /citizen/profile)
       │     ├── admin_bp    (/admin/dashboard, /admin/complaints, /admin/complaints/export)
       │     └── api_bp      (/api/complaints, /api/issue-types, /api/stats, /api/ai-classify)
       │
       ├── Utilities & Services:
       │     ├── utils/storage.py  ──> Cloudinary CDN (production) / Local Disk (dev)
       │     └── routes/api.py     ──> Google Gemini Vision API (AI categorization)
       │
[ Database Layer (SQLAlchemy ORM) ]
       │
       └── SQLite (Local development: instance/civicsetu.db)
           OR
           PostgreSQL (Production: DATABASE_URL on Render)
```

1. **Client Interaction**: Citizens and administrators interact with server-rendered Jinja2 templates. Frontend JavaScript captures images, handles accessibility controls, and communicates with the REST API.
2. **AI Classification**: When an image is uploaded in the submission form, client-side JavaScript sends the image payload to `/api/ai-classify`. The server queries Google Gemini Vision API to detect the civic issue category and returns confidence scores and explanations.
3. **Storage Handling**: Image files submitted with complaints are handled by `utils/storage.py`. In production, the file is uploaded to Cloudinary, and a reference string (`cloudinary:<public_id>`) is persisted in the database. In local development without credentials, files are stored under `static/uploads/`.
4. **Data Persistence**: SQLAlchemy manages relational data models (`User`, `Admin`, `Complaint`, `IssueType`, `StatusLog`, `ComplaintReaction`, `ComplaintComment`). Database connections switch between SQLite and PostgreSQL based on configuration.

---

## Project Structure

```text
civicsetu/
├── app.py                  # Flask application factory, configuration, CSRF & seeders
├── run.py                  # Application entry point with dotenv configuration
├── Procfile                # Render deployment process definition (gunicorn run:app)
├── requirements.txt        # Python package dependencies
├── schema.sql              # Relational database schema reference
├── .env.example            # Environment configuration template
├── .gitignore              # Git ignore rules for secrets, DBs, and virtual environments
├── models/
│   ├── __init__.py
│   └── models.py           # SQLAlchemy ORM models and relationships
├── routes/
│   ├── __init__.py
│   ├── auth.py             # User authentication routes (login, register, logout)
│   ├── citizen.py          # Citizen dashboard, complaint submission, reactions, comments
│   ├── admin.py            # Admin dashboard, dynamic priority queues, CSV export
│   └── api.py              # REST API endpoints & Gemini Vision integration
├── utils/
│   ├── __init__.py
│   └── storage.py          # Cloudinary & local disk storage manager
├── templates/
│   ├── base.html           # Base layout with accessibility tools & navbar
│   ├── admin/              # Admin dashboard, complaint queue, and detail templates
│   ├── auth/               # Login and registration templates
│   └── citizen/            # Citizen dashboard, submission form, and profile templates
└── static/
    ├── css/
    │   └── style.css       # Custom styles & design tokens
    ├── js/
    │   └── main.js         # Alert handling and UI helpers
    ├── images/             # Static logos and assets
    └── uploads/            # Local image storage directory (.gitkeep tracked)
```

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- `pip` package manager
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/0504Siddhi/civicsetu_new_final.git
   cd civicsetu_new_final
   ```

2. **Create and activate a virtual environment:**
   - **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in the required variables (see [Environment Variables](#environment-variables)).

---

## Environment Variables

CivicSetu reads configuration from environment variables (or a local `.env` file via `python-dotenv`). Copy `.env.example` to create your `.env` file.

| Variable | Description | Required in Production | Default / Example |
|---|---|---|---|
| `SECRET_KEY` | Secret key for Flask secure session cookies and CSRF validation. | **Yes** | 32-byte hex string (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `GEMINI_API_KEY` | Google Gemini API key from Google AI Studio for image classification. | **Yes** (for AI features) | `AIzaSy...` |
| `CLOUDINARY_URL` | Cloudinary connection URI for persistent complaint images. | **Yes** (in Production) | `cloudinary://<api_key>:<api_secret>@<cloud_name>` |
| `DATABASE_URL` | Relational database connection string. | Optional (uses SQLite if omitted) | `postgresql://user:password@host:5432/dbname` |
| `FLASK_ENV` | Application environment mode (`development` or `production`). | Optional | `development` |
| `ADMIN_EMAIL` | Email address for default admin account seeding. | Optional | `admin@civicsetu.in` |
| `ADMIN_PASSWORD` | Password for default admin account seeding. | Optional (required for prod seeding) | Custom secure password |

---

## Running Locally

Because CivicSetu is a monolithic Flask application with server-rendered Jinja2 templates, frontend and backend execute together in a single command.

1. **Start the local server:**
   ```bash
   python run.py
   ```

2. **Access the application:**
   Open your browser and navigate to:
   ```text
   http://localhost:5000
   ```

3. **Default Test Accounts:**
   - **Administrator:**
     - Email: `admin@civicsetu.in`
     - Password: `admin123` (seeded automatically in development)
     - Role: Admin
   - **Citizen:**
     - Register a new account via the `/register` page, or log in with created credentials.

---

## Deployment

CivicSetu is deployed as a cloud-hosted Flask application using Render, with PostgreSQL for persistent relational data and Cloudinary for image storage.

The production deployment supports:
- Persistent PostgreSQL database storage.
- Cloudinary CDN integration for complaint image uploads.
- Environment-based configuration and secret management.
- Gunicorn WSGI server for production execution.

**Live Demo:** [Add your Render deployment URL here]




