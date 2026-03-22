# Eventora Backend

Django + MySQL REST API for the Eventora event coordination platform.

---

## Tech Stack

| Layer          | Technology                        |
|----------------|-----------------------------------|
| Framework      | Django 4.2 + Django REST Framework |
| Database       | MySQL 8+                          |
| Authentication | JWT via SimpleJWT                 |
| CORS           | django-cors-headers               |

---

## Project Structure

```
eventora_backend/
├── manage.py
├── requirements.txt
├── setup_db.sql              ← Run this first in MySQL
├── .env.example              ← Copy to .env and fill in values
│
├── eventora/                 ← Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── apps/
    ├── accounts/             ← Users, Auth (Student & Admin)
    ├── events/               ← Event CRUD + Categories
    ├── registrations/        ← Student event registrations
    └── payments/             ← Payment initiation & confirmation
```

---

## Setup Guide

### 1. Clone and create virtual environment

```bash
cd eventora_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up MySQL

```bash
mysql -u root -p < setup_db.sql
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your MySQL credentials and secret key
```

### 5. Run migrations

```bash
python manage.py makemigrations accounts events registrations payments
python manage.py migrate
```

### 6. Seed initial data

```bash
python manage.py seed_data
# Creates 6 categories + superadmin: admin@eventora.com / Admin@1234
```

### 7. Start the development server

```bash
python manage.py runserver
# API available at http://127.0.0.1:8000/api/v1/
```

---

## API Reference

### Auth  `/api/v1/auth/`

| Method | Endpoint                  | Auth     | Description                     |
|--------|---------------------------|----------|---------------------------------|
| POST   | `login/`                  | Public   | Login → returns JWT tokens      |
| POST   | `logout/`                 | Required | Blacklists refresh token        |
| POST   | `token/refresh/`          | Public   | Get new access token            |
| POST   | `register/student/`       | Public   | Register a student account      |
| POST   | `register/admin/`         | Admin    | Create admin account            |
| GET    | `profile/`                | Required | Get logged-in user's profile    |
| PUT    | `profile/`                | Required | Update profile                  |
| POST   | `change-password/`        | Required | Change password                 |
| GET    | `users/`                  | Admin    | List all users                  |

#### Login — Example Request
```json
POST /api/v1/auth/login/
{
  "email": "student@university.edu",
  "password": "password123"
}
```
#### Login — Example Response
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>",
  "user": {
    "id": 1,
    "email": "student@university.edu",
    "full_name": "Rahul Sharma",
    "role": "student",
    "student_id": "CS2021001",
    "department": "cs"
  }
}
```

---

### Events  `/api/v1/events/`

| Method | Endpoint                  | Auth     | Description                         |
|--------|---------------------------|----------|-------------------------------------|
| GET    | `/`                       | Public   | List open events (filterable)       |
| GET    | `categories/`             | Public   | List all categories                 |
| GET    | `<slug>/`                 | Public   | Event detail                        |
| GET    | `admin/`                  | Admin    | List ALL events (any status)        |
| POST   | `admin/`                  | Admin    | Create new event                    |
| GET    | `admin/<id>/`             | Admin    | Get event detail                    |
| PUT    | `admin/<id>/`             | Admin    | Update event                        |
| DELETE | `admin/<id>/`             | Admin    | Delete event                        |
| PATCH  | `admin/<id>/status/`      | Admin    | Update event status only            |
| GET    | `admin/stats/`            | Admin    | Dashboard summary stats             |

#### Query params for GET `/api/v1/events/`
- `?category=workshop` — filter by category slug
- `?search=AI` — search title/description
- `?department=cs` — filter by department
- `?ordering=event_date` — sort (prefix `-` for descending)

#### Create Event — Example Request
```json
POST /api/v1/events/admin/
Authorization: Bearer <admin_access_token>
{
  "title": "AI in Healthcare",
  "description": "A seminar on AI applications in modern healthcare.",
  "category_id": 2,
  "emoji": "🎤",
  "event_date": "2025-03-12",
  "start_time": "10:00:00",
  "end_time": "13:00:00",
  "venue": "Hall A",
  "department": "Computer Science",
  "capacity": 150,
  "registration_fee": "0.00",
  "registration_deadline": "2025-03-10T23:59:00",
  "status": "open"
}
```

---

### Registrations  `/api/v1/registrations/`

| Method | Endpoint                     | Auth     | Description                          |
|--------|------------------------------|----------|--------------------------------------|
| POST   | `/`                          | Student  | Register for an event                |
| GET    | `my/`                        | Student  | List student's own registrations     |
| GET    | `<id>/`                      | Required | Get registration detail              |
| PATCH  | `<id>/cancel/`               | Student  | Cancel a registration                |
| GET    | `admin/`                     | Admin    | List all registrations               |
| PATCH  | `admin/<id>/status/`         | Admin    | Update registration status           |
| POST   | `admin/attendance/`          | Admin    | Bulk mark as attended                |

#### Register — Example Request
```json
POST /api/v1/registrations/
Authorization: Bearer <student_access_token>
{
  "event": 3
}
```
- Free events → status immediately `confirmed`
- Paid events → status `pending`, awaiting payment

---

### Payments  `/api/v1/payments/`

| Method | Endpoint                          | Auth     | Description                     |
|--------|-----------------------------------|----------|---------------------------------|
| POST   | `initiate/`                       | Student  | Create pending payment record   |
| POST   | `confirm/`                        | Student  | Confirm/fail after gateway      |
| GET    | `my/`                             | Student  | List student's payments         |
| GET    | `<transaction_id>/`               | Required | Get payment detail              |
| GET    | `admin/`                          | Admin    | List all payments               |
| POST   | `admin/<transaction_id>/refund/`  | Admin    | Refund a payment                |

#### Payment Flow

```
1. POST /registrations/          → creates Registration (status: pending)
2. POST /payments/initiate/      → creates Payment (status: pending), returns transaction_id
3. [Frontend processes payment with Razorpay / Stripe / etc.]
4. POST /payments/confirm/       → marks Payment success, Registration confirmed
```

#### Initiate — Example Request
```json
POST /api/v1/payments/initiate/
Authorization: Bearer <student_access_token>
{
  "registration_id": 5,
  "method": "card"
}
```

#### Confirm — Example Request
```json
POST /api/v1/payments/confirm/
Authorization: Bearer <student_access_token>
{
  "transaction_id": "TXN-A1B2C3D4E5F6",
  "gateway_reference": "pay_razorpay_abc123",
  "success": true
}
```

---

## Authentication

All protected endpoints require a Bearer token in the header:

```
Authorization: Bearer <access_token>
```

Access tokens expire after 60 minutes. Use the refresh endpoint to get a new one:

```json
POST /api/v1/auth/token/refresh/
{
  "refresh": "<refresh_token>"
}
```

---

## Connecting the Frontend

In your Eventora HTML files, replace hardcoded data with fetch calls:

```javascript
const API = 'http://127.0.0.1:8000/api/v1';

// Get all open events
const res   = await fetch(`${API}/events/`);
const data  = await res.json();

// Login
const login = await fetch(`${API}/auth/login/`, {
  method:  'POST',
  headers: { 'Content-Type': 'application/json' },
  body:    JSON.stringify({ email, password }),
});
const { access, refresh, user } = await login.json();
localStorage.setItem('access', access);

// Authenticated request
const myRegs = await fetch(`${API}/registrations/my/`, {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access')}` }
});
```

---

## Django Admin Panel

Access the built-in admin UI at `http://127.0.0.1:8000/admin/`

Login with the superadmin credentials created by `seed_data`:
- **Email:** admin@eventora.com
- **Password:** Admin@1234 *(change immediately!)*
