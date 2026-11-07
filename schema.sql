-- =============================================================
--  CivicSetu — Database Schema (MySQL / SQLite compatible)
--  DBMS Mini Project, SPPU · 2026
-- =============================================================

-- ─── Issue Types ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS issue_types (
    type_id        INTEGER     PRIMARY KEY AUTOINCREMENT,
    type_name      VARCHAR(50) UNIQUE NOT NULL,
    description    VARCHAR(255),
    priority_level VARCHAR(20) DEFAULT 'Medium'
        CHECK (priority_level IN ('Low','Medium','High','Critical'))
);

-- Seed data
INSERT OR IGNORE INTO issue_types (type_name, description, priority_level) VALUES
    ('pothole',       'Road potholes and surface damage',        'High'),
    ('garbage',       'Garbage dumping or uncollected waste',    'Medium'),
    ('water_leakage', 'Water pipeline leaks or flooding',        'Critical'),
    ('streetlight',   'Broken or non-functional streetlights',   'Medium'),
    ('sewage',        'Sewage overflow or blocked drains',       'High'),
    ('tree_fall',     'Fallen trees blocking roads/paths',       'High'),
    ('electricity',   'Electrical hazards or power outages',     'Critical'),
    ('other',         'Other civic issues',                      'Low');

-- ─── Citizens ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER      PRIMARY KEY AUTOINCREMENT,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone         VARCHAR(15),
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- ─── Administrators ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admins (
    admin_id      INTEGER      PRIMARY KEY AUTOINCREMENT,
    username      VARCHAR(80)  UNIQUE NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  DEFAULT 'moderator'
        CHECK (role IN ('moderator','super_admin'))
);

-- ─── Complaints ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id  INTEGER      PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER      NOT NULL,
    type_id       INTEGER      NOT NULL,
    image_path    VARCHAR(300),
    location      VARCHAR(255) NOT NULL,
    description   TEXT,
    status        VARCHAR(20)  NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending','In Progress','Resolved','Rejected')),
    ai_confidence REAL,
    submitted_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    resolved_at   DATETIME,

    FOREIGN KEY (user_id)  REFERENCES users(user_id)       ON DELETE CASCADE,
    FOREIGN KEY (type_id)  REFERENCES issue_types(type_id) ON DELETE RESTRICT
);

-- ─── Status Change Log ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS status_log (
    log_id       INTEGER     PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER     NOT NULL,
    admin_id     INTEGER     NOT NULL,
    old_status   VARCHAR(20),
    new_status   VARCHAR(20) NOT NULL,
    changed_at   DATETIME    DEFAULT CURRENT_TIMESTAMP,
    remarks      TEXT,

    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id)     REFERENCES admins(admin_id)         ON DELETE SET NULL
);

-- ─── Complaint Reactions (Likes / Dislikes) ───────────────────
CREATE TABLE IF NOT EXISTS complaint_reactions (
    reaction_id  INTEGER     PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER     NOT NULL,
    user_id      INTEGER     NOT NULL,
    reaction     VARCHAR(10) NOT NULL CHECK (reaction IN ('like', 'dislike')),
    created_at   DATETIME    DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)      REFERENCES users(user_id)           ON DELETE CASCADE,
    CONSTRAINT uq_reaction_user_complaint UNIQUE (complaint_id, user_id)
);

-- ─── Complaint Comments ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaint_comments (
    comment_id   INTEGER  PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER  NOT NULL,
    user_id      INTEGER  NOT NULL,
    body         TEXT     NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)      REFERENCES users(user_id)           ON DELETE CASCADE
);

-- ─── Indexes for performance ──────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_complaints_user       ON complaints(user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status     ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_type       ON complaints(type_id);
CREATE INDEX IF NOT EXISTS idx_statuslog_complaint   ON status_log(complaint_id);
CREATE INDEX IF NOT EXISTS idx_reactions_complaint   ON complaint_reactions(complaint_id);
CREATE INDEX IF NOT EXISTS idx_comments_complaint    ON complaint_comments(complaint_id);

-- ─── Useful views ─────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS complaint_summary AS
    SELECT
        c.complaint_id,
        u.name         AS citizen_name,
        u.email        AS citizen_email,
        it.type_name   AS issue_type,
        it.priority_level,
        c.location,
        c.status,
        c.submitted_at,
        c.resolved_at,
        CASE
            WHEN c.resolved_at IS NOT NULL
            THEN ROUND((JULIANDAY(c.resolved_at) - JULIANDAY(c.submitted_at)) * 24, 1)
            ELSE NULL
        END AS hours_to_resolve
    FROM complaints c
    JOIN users       u  ON c.user_id = u.user_id
    JOIN issue_types it ON c.type_id = it.type_id;
