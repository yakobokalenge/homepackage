# 📚 HomePackage — Tanzania National EdTech Platform

<div align="center">

![HomePackage](https://img.shields.io/badge/HomePackage-v1.0.0-blue?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-5.x-green?style=for-the-badge&logo=django)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-brightgreen?style=for-the-badge&logo=vue.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**A comprehensive online learning, assessment, and proctored examination platform built for Tanzanian schools, students, and teachers.**

[Features](#features) • [Tech Stack](#tech-stack) • [Getting Started](#getting-started) • [API Documentation](#api-documentation) • [Payment Integration](#payment-integration) • [Proctoring System](#proctoring-system) • [Deployment](#deployment)

</div>

---

## 🌍 Overview

**HomePackage** is a national online learning and assessment platform where teachers from any school or region in Tanzania can create, share, and manage educational content, and students can access quizzes, tests, assignments, and full online examinations with robust proctoring.

### Key Highlights
- 🏫 **Multi-School**: Teachers and students from any school can participate
- 📝 **Rich Assessments**: 8 question types with LaTeX, images, and rich text
- 🔒 **AI Proctoring**: Browser lockdown, face detection, audio monitoring
- 💰 **Tanzania Payments**: M-Pesa, Tigo Pesa, Airtel Money, HaloPesa
- 🌐 **Bilingual**: English + Kiswahili
- 📱 **Mobile-First**: Optimized for low-end devices and variable internet
- 🏗️ **Scalable**: Built for national-level usage

---

## ✨ Features

### 👤 User Roles & Authentication
- **Student**: Take assessments, view results, track progress
- **Teacher**: Create content, manage assessments, review proctoring
- **School Admin**: Manage school, teachers, classrooms
- **Super Admin**: Platform-wide management
- JWT authentication (email/phone + Google OAuth)
- Role-based access control (RBAC)

### 📖 Content & Assessment System
- **Question Bank** with 8 question types:
  - Multiple Choice (MCQ)
  - Multiple Select
  - True/False
  - Fill in the Blank
  - Short Answer
  - Essay
  - Matching
  - Ordering
- Rich text, images, diagrams, and LaTeX support
- Bilingual questions (English + Kiswahili)
- Weekly/Monthly "Home Packages"
- Quizzes, Tests, Assignments, and Full Examinations

### 🔒 Proctoring System
- **Browser Lockdown**: Full-screen enforcement, copy/paste blocking, tab switch detection
- **Identity Verification**: Photo capture + facial recognition matching
- **AI Live Monitoring**: Face detection (multiple faces), head pose (looking away), audio detection
- **Teacher-Configurable Rules**: Webcam on/off, allowed tab switches, open/closed book
- **Post-Exam Review**: Flagged recordings, AI suspicion reports, teacher review
- **Privacy**: Secure encrypted storage, auto-deletion after review, student consent

### 💳 Payment System (Tanzania-Optimized)
- **Mobile Money**: M-Pesa (Vodacom), Tigo Pesa, Airtel Money, HaloPesa
- **Cards**: Visa, Mastercard
- **Bank Transfers**
- **Gateways**: Flutterwave (primary), ClickPesa, AzamPay
- **Subscriptions**: Weekly, Monthly, Yearly billing cycles
- **Plans**: Basic, Premium, Institutional
- **Currency**: Tanzania Shillings (TZS)
- Webhook handling, receipts, refunds, failed payment recovery

### 📊 Analytics & Dashboards
- **Student Dashboard**: Upcoming tasks, performance charts, weak topic analysis
- **Teacher Dashboard**: Class performance, grading, detailed reports
- **Admin Dashboard**: Platform-wide statistics

### 🔔 Notifications
- In-app notifications
- Email (via Resend)
- SMS (via Africa's Talking — full Tanzania coverage)

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **Python 3.12+** | Core language |
| **Django 5.x** | Web framework |
| **Django REST Framework** | REST API |
| **PostgreSQL 16** | Primary database |
| **Redis 7** | Cache + Celery broker |
| **Celery** | Background task processing |
| **SimpleJWT** | JWT authentication |
| **django-storages + boto3** | S3 file storage |
| **Cloudinary** | Image optimization |
| **Africa's Talking** | SMS notifications |
| **Resend** | Email delivery |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Vue.js 3** | UI framework (Composition API) |
| **Vite** | Build tool |
| **TypeScript** | Type safety |
| **Tailwind CSS v3** | Styling |
| **shadcn-vue** | UI components |
| **Pinia** | State management |
| **Vue Router 4** | Routing |
| **vue-i18n** | Internationalization |
| **MediaPipe** | Face detection/tracking |
| **Chart.js** | Analytics charts |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| **Docker + Docker Compose** | Containerization |
| **Nginx** | Reverse proxy + static files |
| **Gunicorn** | WSGI server |
| **Let's Encrypt** | SSL certificates |

---

## 🚀 Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)
- (For local development without Docker) Python 3.12+, Node.js 20+, PostgreSQL 16, Redis 7

### Quick Start with Docker

```bash
# 1. Clone the repository
git clone https://github.com/your-org/homepackage.git
cd homepackage

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section below)

# 3. Start all services
docker-compose up --build

# 4. Create a superadmin user
docker-compose exec backend python manage.py createsuperuser

# 5. Load initial data (subjects, subscription plans)
docker-compose exec backend python manage.py loaddata initial_data
```

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin/

### Local Development (Without Docker)

#### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements/dev.txt

# Set up database
# Make sure PostgreSQL is running, then:
createdb homepackage

# Set environment variables
export DJANGO_SETTINGS_MODULE=homepackage.settings.development
export DATABASE_URL=postgres://your_user:your_pass@localhost:5432/homepackage
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key-here

# Run migrations
python manage.py migrate

# Create superadmin
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

#### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local

# Start development server
npm run dev
```

#### Start Celery (for background tasks)

```bash
# In a new terminal, from the backend directory:
celery -A homepackage worker -l info

# In another terminal (for scheduled tasks):
celery -A homepackage beat -l info
```

---

## 🔑 Environment Variables

### Required for Development

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `random-50-char-string` |
| `DATABASE_URL` | PostgreSQL connection | `postgres://user:pass@db:5432/homepackage` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |

### Payment Gateways (Tanzania)

| Variable | Description | Get from |
|----------|-------------|----------|
| `FLUTTERWAVE_PUBLIC_KEY` | Flutterwave public key | [Flutterwave Dashboard](https://dashboard.flutterwave.com) |
| `FLUTTERWAVE_SECRET_KEY` | Flutterwave secret key | Same |
| `FLUTTERWAVE_WEBHOOK_HASH` | Webhook verification hash | Same → Settings → Webhooks |
| `CLICKPESA_CLIENT_ID` | ClickPesa client ID | [ClickPesa Dashboard](https://dashboard.clickpesa.com) |
| `CLICKPESA_API_KEY` | ClickPesa API key | Same |
| `AZAMPAY_APP_NAME` | AzamPay app name | [AzamPay Developers](https://developers.azampay.co.tz) |
| `AZAMPAY_CLIENT_ID` | AzamPay client ID | Same |
| `AZAMPAY_CLIENT_SECRET` | AzamPay client secret | Same |

### File Storage

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key (for S3 video storage) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name |
| `CLOUDINARY_URL` | Cloudinary URL (for image storage) |

### SMS & Email

| Variable | Description |
|----------|-------------|
| `AFRICASTALKING_USERNAME` | Africa's Talking username (`sandbox` for testing) |
| `AFRICASTALKING_API_KEY` | Africa's Talking API key |
| `RESEND_API_KEY` | Resend email API key |

See `.env.example` for the complete list of all variables.

---

## 📡 API Documentation

### Base URL
```
Development: http://localhost:8000/api/v1/
Production:  https://homepackage.co.tz/api/v1/
```

### Authentication
All authenticated endpoints require the JWT token:
```
Authorization: Bearer <access_token>
```

### Key Endpoints

#### Authentication
```
POST   /api/v1/auth/register/              Register new user
POST   /api/v1/auth/login/                 Login (returns JWT)
POST   /api/v1/auth/token/refresh/         Refresh JWT token
POST   /api/v1/auth/google/                Google OAuth login
GET    /api/v1/auth/me/                    Current user profile
```

#### Assessments
```
GET    /api/v1/assessments/                List assessments
POST   /api/v1/assessments/                Create assessment
POST   /api/v1/assessments/{id}/start/     Start attempt
POST   /api/v1/assessments/{id}/submit/    Submit attempt
GET    /api/v1/assessments/{id}/results/   View results
```

#### Payments
```
GET    /api/v1/plans/                      List subscription plans
POST   /api/v1/subscriptions/              Create subscription
POST   /api/v1/payments/initiate/          Initiate payment
GET    /api/v1/payments/verify/{id}/       Verify payment status
POST   /api/v1/webhooks/flutterwave/       Flutterwave webhook
POST   /api/v1/webhooks/clickpesa/         ClickPesa webhook
```

#### Proctoring
```
POST   /api/v1/proctoring/sessions/                    Start session
POST   /api/v1/proctoring/sessions/{id}/verify-identity/   Verify identity
POST   /api/v1/proctoring/sessions/{id}/upload-chunk/      Upload video chunk
POST   /api/v1/proctoring/sessions/{id}/flags/             Report flag
GET    /api/v1/proctoring/sessions/{id}/report/            Get AI report
```

---

## 💳 Payment Integration

### Payment Flow

```mermaid
sequenceDiagram
    participant S as Student
    participant F as Frontend
    participant B as Backend
    participant G as Gateway (Flutterwave/ClickPesa)
    participant M as Mobile Money (M-Pesa/Tigo)

    S->>F: Select plan & payment method
    F->>B: POST /payments/initiate/
    B->>G: Create charge (mobile_money_tanzania)
    G->>M: Send STK Push / USSD prompt
    M->>S: Enter PIN on phone
    M->>G: Payment confirmed
    G->>B: Webhook notification
    B->>B: Verify & activate subscription
    B->>F: Payment confirmed (via polling/websocket)
    F->>S: Show success + receipt
```

### Supported Payment Methods

| Method | Provider | Gateway |
|--------|----------|---------|
| M-Pesa | Vodacom Tanzania | Flutterwave / ClickPesa |
| Tigo Pesa | Tigo Tanzania | Flutterwave / ClickPesa |
| Airtel Money | Airtel Tanzania | Flutterwave / ClickPesa |
| HaloPesa | TTCL | Flutterwave / ClickPesa |
| Visa / Mastercard | International | Flutterwave |
| Bank Transfer | Local banks | AzamPay |

### Gateway Abstraction

The payment system uses a **Strategy Pattern** for easy gateway switching:

```python
from apps.payments.gateways.factory import PaymentGatewayFactory

# Get the appropriate gateway
gateway = PaymentGatewayFactory.get_gateway('flutterwave')

# Initiate a mobile money payment
response = gateway.initiate_payment(PaymentRequest(
    amount=Decimal('15000.00'),
    currency='TZS',
    phone_number='255712345678',
    payment_method='mpesa',
    description='Premium Monthly Subscription',
    callback_url='https://homepackage.co.tz/api/v1/webhooks/flutterwave/',
    idempotency_key='unique-key-123',
))
```

Adding a new gateway requires only:
1. Create a new class implementing `PaymentGateway` interface
2. Register it in the factory

---

## 🔒 Proctoring System

### Architecture

```
┌─────────────────────────────────────────────┐
│             Browser (Client-Side)            │
├─────────────────────────────────────────────┤
│  Browser Lockdown    │  AI Engine            │
│  ├─ Fullscreen API   │  ├─ MediaPipe Face    │
│  ├─ Visibility API   │  │  Detection         │
│  ├─ Clipboard block  │  ├─ Face Landmarks    │
│  ├─ DevTools detect  │  │  (Head Pose)       │
│  └─ Keyboard block   │  ├─ Audio Monitor     │
│                      │  └─ Object Detection  │
├──────────────────────┼──────────────────────┤
│  Video Recorder                              │
│  ├─ MediaRecorder (WebM/VP8)                 │
│  ├─ 10-second chunks                         │
│  ├─ Retry queue + IndexedDB backup           │
│  └─ Direct S3 upload (presigned URLs)        │
├─────────────────────────────────────────────┤
│  Violation Reporter                          │
│  └─ POST /proctoring/sessions/{id}/flags/    │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│             Server (Django)                  │
├─────────────────────────────────────────────┤
│  ├─ ProctoringSession model                  │
│  ├─ ProctoringFlag model                     │
│  ├─ VideoChunk management                    │
│  ├─ Presigned S3 URL generation              │
│  ├─ Teacher review API                       │
│  └─ Celery: auto-cleanup after retention     │
└─────────────────────────────────────────────┘
```

### Security Considerations
- All browser lockdown is **deterrent-level** (client-side JS can be bypassed)
- Critical validation happens **server-side** (answer timestamps, IP tracking)
- Video evidence provides **accountability** for disputes
- Teacher **review required** before any action taken on flags
- Students must give **explicit consent** before proctoring begins
- Recordings are **auto-deleted** after the configured retention period

---

## 🚢 Deployment (Production)

### Prerequisites
- A Linux server (Ubuntu 22.04+ recommended)
- Domain name pointed to your server (e.g., homepackage.co.tz)
- SSL certificate (Let's Encrypt)

### Steps

```bash
# 1. Clone to server
git clone https://github.com/your-org/homepackage.git
cd homepackage

# 2. Set up production environment
cp .env.example .env
nano .env  # Fill in ALL production values
# IMPORTANT: Set DEBUG=False, generate a new SECRET_KEY,
# use real payment gateway keys (not sandbox)

# 3. Build frontend for production
cd frontend
npm install
npm run build
cd ..

# 4. Start with production Docker Compose
docker-compose -f docker-compose.prod.yml up -d --build

# 5. Create superadmin
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 6. Load initial data
docker-compose -f docker-compose.prod.yml exec backend python manage.py loaddata initial_data

# 7. Set up SSL with Certbot (if not using pre-existing certs)
sudo certbot certonly --webroot -w /var/www/certbot -d homepackage.co.tz -d www.homepackage.co.tz
```

### Monitoring
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f celery-worker

# Check status
docker-compose -f docker-compose.prod.yml ps

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

---

## 🏗️ Project Structure

```
homepackage/
├── backend/                    # Django Backend
│   ├── homepackage/            # Project configuration
│   │   ├── settings/           # Split settings (base/dev/prod)
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py / asgi.py
│   ├── apps/
│   │   ├── accounts/           # User auth & profiles
│   │   ├── schools/            # School management
│   │   ├── content/            # Questions & question banks
│   │   ├── assessments/        # Exams, quizzes, attempts
│   │   ├── proctoring/         # Proctoring sessions & flags
│   │   ├── subscriptions/      # Plans & subscriptions
│   │   ├── payments/           # Transactions & gateways
│   │   │   └── gateways/       # Payment abstraction layer
│   │   ├── analytics/          # Dashboards & reports
│   │   └── notifications/      # Email, SMS, in-app
│   ├── requirements/
│   └── Dockerfile
├── frontend/                   # Vue.js 3 Frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── composables/        # Vue composables (proctoring engine)
│   │   ├── layouts/            # Page layouts
│   │   ├── pages/              # Route-level pages
│   │   ├── router/             # Vue Router config
│   │   ├── services/           # API layer (Axios)
│   │   ├── stores/             # Pinia state management
│   │   ├── types/              # TypeScript interfaces
│   │   ├── i18n/               # English + Kiswahili
│   │   └── assets/             # CSS, fonts, images
│   └── Dockerfile
├── nginx/                      # Nginx configuration
├── docker-compose.yml          # Development
├── docker-compose.prod.yml     # Production
├── .env.example                # Environment template
└── README.md                   # This file
```

---

## 🌐 Multi-Language Support

HomePackage supports **English** and **Kiswahili** (Swahili). All UI text is served through `vue-i18n`.

### Adding a Language
1. Create a new JSON file in `frontend/src/i18n/` (e.g., `fr.json`)
2. Add translations for all keys
3. Register in `frontend/src/i18n/index.ts`

### Question Translation
Questions support bilingual content with `text` (English) and `text_sw` (Kiswahili) fields.

---

## 🔐 Security Best Practices

- **Authentication**: JWT tokens with short-lived access (30 min) + long-lived refresh (7 days)
- **CORS**: Strict origin whitelisting
- **CSRF**: Django CSRF protection on all non-API forms
- **Rate Limiting**: Nginx rate limits on auth (5/min), API (30/s), webhooks (50/s)
- **Input Validation**: DRF serializer validation on all inputs
- **SQL Injection**: Protected by Django ORM
- **XSS**: Content Security Policy headers via Nginx
- **Payment Security**: Webhook signature verification, idempotency keys
- **Data Privacy**: Compliant with Tanzanian data regulations; auto-deletion of proctoring data

---

## 🧪 Testing

```bash
# Backend tests
cd backend
python manage.py test

# Test specific app
python manage.py test apps.payments

# Frontend tests
cd frontend
npm run test

# Lint
npm run lint
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

- **Email**: support@homepackage.co.tz
- **Phone**: +255 XXX XXX XXX
- **Documentation**: https://docs.homepackage.co.tz

---

<div align="center">

**Built with ❤️ for Tanzanian students and teachers**

*Empowering education across every region of Tanzania* 🇹🇿

</div>
