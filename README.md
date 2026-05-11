<div align="center">

# Knowledge Zakat

### An Educational Platform Connecting Teachers and Students

[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Svelte 5](https://img.shields.io/badge/Svelte-5.43-FF3E00?style=flat-square&logo=svelte&logoColor=white)](https://svelte.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](#license)

**A full-stack platform with three roles (Student, Teacher, Admin), JWT Authentication, RTL Arabic UI, and a real-time rating system.**

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Security](#security)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Knowledge Zakat** is an Arabic educational platform that allows teachers to publish lectures and students to enroll in them, complemented by a comprehensive rating and administration system. The project follows a clean **Backend / Frontend** separation:

- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Frontend:** Svelte 5 + TypeScript + Tailwind CSS

The name "Knowledge Zakat" is inspired by the Islamic concept of *zakat* (a form of giving) — the idea that knowledge is purified through sharing.

---

## Features

### Student Role
- Browse lectures filtered by academic category
- Submit enrollment requests to join lectures
- Rate both the lecture and the teacher (5-star system)
- Edit personal profile with avatar upload
- Dashboard for tracking approved sessions
- Guest mode for browsing the platform before signing up

### Teacher Role
- Create lectures with cover image upload
- Edit and delete own lectures
- Accept or reject student enrollment requests
- Interactive statistics dashboard (Chart.js):
  - Student growth curve over the last 7 days
  - Rating distribution (1 to 5 stars)
  - Overall average rating
- View list of approved students per lecture
- Set lecture capacity limits (`student_limit`)

### Admin Role
- Manage users (suspend, activate, delete)
- Process teacher promotion requests
- Manage academic categories
- Full activity log (audit trail)
- Live statistics (students, teachers, sessions, pending requests)
- **Admin Immunity**: an admin cannot delete another admin's account

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.121 | High-performance async web framework |
| **SQLModel** | 0.0.27 | ORM built on SQLAlchemy and Pydantic |
| **PostgreSQL** | 15+ | Primary relational database |
| **Pydantic v2** | 2.12 | Request and response validation |
| **python-jose** | 3.5 | JWT signing and verification |
| **passlib + bcrypt** | 1.7 / 3.2 | Password hashing |
| **SlowAPI** | latest | Rate limiting against brute-force attacks |
| **python-multipart** | 0.0.20 | File upload handling |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **Svelte 5** | 5.43 | UI framework (Runes mode) |
| **TypeScript** | 5.x | End-to-end type safety |
| **Vite** | 7.2 | Build tool and dev server |
| **Tailwind CSS** | 3.4 | Utility-first styling |
| **Axios** | 1.13 | HTTP client with interceptors |
| **Chart.js** | 4.5 | Interactive data visualization |
| **Lucide Svelte** | 1.0 | Icon library |

---

## Project Structure

```
knowledge-zakat/
│
├── backend/                       FastAPI server
│   ├── main.py                    Entry point, CORS, router registration
│   ├── database.py                SQLModel engine and session factory
│   ├── models.py                  Database tables (SQLModel)
│   ├── schemas.py                 Pydantic request/response schemas
│   ├── oauth2.py                  JWT issuance and dependencies
│   ├── utils.py                   Bcrypt hashing and activity logging
│   ├── requirements.txt           Python dependencies
│   ├── .env                       Secrets (gitignored)
│   │
│   ├── core/
│   │   └── config.py              Settings loader from .env
│   │
│   ├── routers/                   HTTP layer
│   │   ├── auth.py                /login, /token, /logout
│   │   ├── users.py               /users, /me, /teachers
│   │   ├── sessions.py            /sessions, /enrollments
│   │   └── admin.py               /admin/*
│   │
│   └── crud/                      Database access layer
│       ├── users.py
│       └── sessions.py
│
└── frontend/                      Svelte 5 + Vite
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.js
    ├── tailwind.config.js
    │
    └── src/
        ├── App.svelte             Root component and route guards
        ├── main.js
        ├── app.css                Tailwind directives and global styles
        ├── app.d.ts               TypeScript ambient declarations
        │
        ├── lib/                   Shared services
        │   ├── api.ts             Axios instance and interceptors
        │   ├── router.ts          Hash-based client-side router
        │   ├── stores.ts          Auth state (token, user)
        │   ├── notifications.ts   Toast notification system
        │   ├── types.ts           Shared TypeScript types
        │   └── authPrompt.ts      Guest auth prompt store
        │
        ├── components/            Reusable UI components
        │   ├── Button.svelte
        │   ├── Input.svelte
        │   ├── Card.svelte
        │   ├── Badge.svelte
        │   ├── Notification.svelte
        │   ├── StudentLayout.svelte
        │   ├── TeacherLayout.svelte
        │   ├── AdminLayout.svelte
        │   ├── auth/              Authentication page components
        │   │   ├── AuthFlipCard.svelte
        │   │   ├── LoginForm.svelte
        │   │   ├── RegisterForm.svelte
        │   │   └── ...
        │   └── admin/
        │       ├── UserManager.svelte
        │       ├── LogViewer.svelte
        │       └── ...
        │
        └── pages/                 Application pages
            ├── Home.svelte
            ├── Auth.svelte
            ├── TeacherHome.svelte
            ├── AdminPanel.svelte
            ├── MyLearning.svelte
            ├── MyLectures.svelte
            ├── SessionView.svelte
            ├── SessionDetails.svelte
            ├── CreateSession.svelte
            ├── ViewTeacher.svelte
            └── Profile.svelte
```

---

## Installation and Setup

### Prerequisites

- Python **3.11+**
- Node.js **20+**
- PostgreSQL **15+**

### 1. Database Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE knowledgeZakat;
\q
```

### 2. Backend Setup

```bash
# Navigate to the backend directory
cd backend/

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate
# Or (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the env template
cp _env .env

# Edit .env with your real values:
#   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/knowledgeZakat
#   JWT_SECRET_KEY=<generate with the command below>
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Run the server
uvicorn main:app --reload --port 8000
```

The API is now running at: **http://127.0.0.1:8000**
Auto-generated Swagger documentation: **http://127.0.0.1:8000/docs**

### 3. Frontend Setup

```bash
# In a separate terminal
cd frontend/

# Install dependencies
npm install

# Create .env (optional, defaults work for local dev)
echo "VITE_API_URL=http://127.0.0.1:8000" > .env

# Start the dev server
npm run dev
```

The frontend is now running at: **http://localhost:5173**

---

## Security

This project applies several professional-grade security practices that exceed typical undergraduate work:

### Authentication
- **JWT** with explicit `algorithm pinning` to defeat `alg: none` confusion attacks
- Passwords hashed with **bcrypt (12 rounds)** — the OWASP-recommended minimum
- **Timing-attack defense**: identical response time for "user not found" and "wrong password" branches, preventing user enumeration
- `is_active` checked on every request — admin-driven deactivation revokes sessions immediately, not after token expiry

### Abuse Prevention
- **Rate limiting** on `/login` (5 attempts per minute per IP)
- `current_password` verification required before any password change
- **CORS** restricted to explicit origins from `.env` (no wildcard with credentials)
- File uploads validated for size (5 MB max) and MIME type (JPEG/PNG/WEBP only)

### Data Confidentiality
- All secrets loaded from `.env` (with `.gitignore` enforced)
- `JWT_SECRET_KEY` must be defined — the application refuses to start without it
- **SQL injection** fully prevented through SQLModel's parameterized queries
- Every security-sensitive action logged to `ActivityLog` (full audit trail)

### Authorization
- Flexible role-based access control (Student / Teacher / Admin) via `user_roles` table
- **Admin Immunity**: admins cannot delete other admin accounts
- Every route verifies resource ownership (you cannot modify another user's lecture)

---

## API Reference

### Authentication
| Method | Path | Description |
|---|---|---|
| `POST` | `/login` | Authenticate and receive a JWT |
| `POST` | `/token` | Alias for `/login` (OAuth2-compatible) |
| `POST` | `/logout` | Invalidate session (audit log entry) |

### Users
| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/users/` | Public | Register a new account |
| `GET` | `/users/me` | Authenticated | Current user profile |
| `GET` | `/users/` | Admin | Paginated user list |
| `PUT` | `/users/{id}` | Owner/Admin | Update profile |
| `DELETE` | `/users/{id}` | Owner/Admin | Delete account |
| `POST` | `/me/upload-image` | Authenticated | Upload avatar |

### Sessions
| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/sessions/` | Public | List all lectures |
| `POST` | `/sessions/` | Teacher | Create a new lecture |
| `GET` | `/sessions/{id}` | Public | Lecture details |
| `PUT` | `/sessions/{id}` | Owner | Update lecture |
| `DELETE` | `/sessions/{id}` | Owner | Delete lecture |
| `POST` | `/sessions/upload-cover` | Teacher | Upload cover image |

### Enrollments
| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/enrollments/request` | Student | Request to join a lecture |
| `GET` | `/enrollments/my-sessions/` | Student | Approved sessions |
| `GET` | `/teacher/enrollments/pending` | Teacher | Pending requests |
| `PATCH` | `/enrollments/update` | Teacher | Approve or reject a request |

### Teachers
| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/teachers/` | Public | Public teacher directory |
| `GET` | `/teachers/{id}/profile` | Public | Public teacher profile and lectures |
| `GET` | `/teacher/dashboard-stats` | Teacher | Dashboard statistics |

### Admin
| Method | Path | Description |
|---|---|---|
| `GET` | `/admin/stats` | Platform-wide statistics |
| `PATCH` | `/admin/users/{id}/status` | Suspend or activate a user |
| `DELETE` | `/admin/users/{id}/delete` | Delete a user |
| `GET` | `/admin/teacher-requests` | Pending teacher promotions |
| `GET` | `/admin/logs` | Activity log |

> Full interactive documentation is automatically generated at `/docs` (Swagger UI) and `/redoc`.

---

## Database Schema

### Simplified ERD

```
┌────────────┐       ┌──────────────┐       ┌─────────────┐
│   User     │◄──────│   UserRole   │──────►│    Role     │
│            │  N:M  │              │  N:M  │             │
│ id (PK)    │       │ user_id (FK) │       │ id (PK)     │
│ email      │       │ role_id (FK) │       │ role_name   │
│ password   │       └──────────────┘       └─────────────┘
│ is_active  │
└─────┬──────┘
      │ 1:N
      │
      ▼
┌─────────────────┐       ┌─────────────┐       ┌──────────────┐
│  SessionModel   │◄──────│ Enrollment  │       │  Category    │
│                 │  N:M  │             │       │              │
│ id (PK)         │       │ user_id     │       │ id (PK)      │
│ user_id (FK)    │       │ session_id  │       │ category_name│
│ title           │       │ status      │       └──────┬───────┘
│ description     │       └─────────────┘              │
│ date_time       │                                    │
│ student_limit   │              ┌───────────────────┐ │
└─────┬───────────┘              │  SessionCategory  │ │
      │ 1:N                      │                   │◄┘
      │                          │ session_id (FK)   │
      ▼                          │ category_id (FK)  │
┌─────────────┐                  └───────────────────┘
│   Rating    │
│             │       ┌────────────────┐
│ session_id  │       │ ActivityLog    │
│ teacher_id  │       │                │
│ user_id     │       │ user_id (FK)   │
│ session_rate│       │ details        │
│ teacher_rate│       │ timestamp      │
└─────────────┘       └────────────────┘
```

### Core Tables

| Table | Purpose |
|---|---|
| `users` | All user accounts (student/teacher/admin) |
| `roles` | Available roles |
| `user_roles` | N:M link between users and roles |
| `sessions` | Lectures (named `SessionModel` in code to avoid SQLAlchemy clash) |
| `categories` | Academic categories |
| `session_categories` | N:M link between lectures and categories |
| `enrollments` | Enrollment requests (status: pending / approved / rejected) |
| `ratings` | Student ratings for sessions and teachers |
| `comments` | Threaded comments (self-referencing via `parent_id`) |
| `activity_logs` | Append-only audit trail |
| `teacher_approvals` | Pending teacher promotion requests |
| `uploaded_files` | CVs and other binary uploads (BLOB) |

---

## Testing

### Manual Testing Scenarios

The following scenarios have been verified manually:

- Login with correct credentials succeeds
- Login with wrong credentials returns 401
- Login on a suspended account returns 403
- Rate limiting kicks in after 5 failed attempts within a minute
- Page refresh preserves the current route (hash-based routing)
- Expired JWT automatically redirects to the login page
- A student attempting to access an admin route is redirected
- A teacher cannot delete a lecture owned by another teacher (403)
- An admin cannot delete another admin account (Admin Immunity)
- Uploading a file larger than 5 MB is rejected
- Uploading an unsupported MIME type is rejected
- Changing password without supplying `old_password` is rejected

### Running in Development Mode

```bash
# Backend (with auto-reload)
uvicorn main:app --reload --log-level debug

# Frontend (with HMR)
npm run dev

# TypeScript type-checking
npx svelte-check
```

---

## Contributing

This project was developed as a graduation requirement. Contributions, bug reports, and suggestions are welcome via GitHub Issues and Pull Requests.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes following conventional commits (`feat:`, `fix:`, `docs:`, etc.)
4. Push to your fork (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Knowledge Zakat — Built to spread knowledge.**

Copyright © 2026

</div>
