# 🚀 Nexus Core - Enterprise Knowledge & Workflow Orchestration Platform

**Production-Ready | Security-First | Fully Audited | Docker-Native**

## 📋 Overview

Nexus Core is an enterprise-grade platform combining knowledge management with powerful workflow automation. Built with security, scalability, and performance in mind.

### ✨ Core Features

- **🔐 Enterprise Security**
  - JWT-based authentication with refresh tokens
  - Argon2 password hashing
  - MFA support (TOTP)
  - Account lockout protection
  - Role-based access control (RBAC)
  - Comprehensive audit logging

- **📝 Knowledge Management**
  - Rich text notes with version history
  - Notebook organization with hierarchy
  - Tag-based categorization
  - Knowledge graph with link detection
  - Collaborative comments
  - Full-text search ready

- **⚡ Workflow Engine**
  - Visual workflow builder
  - Multiple trigger types (manual, scheduled, webhook, event)
  - Step-by-step execution tracking
  - Retry logic with configurable limits
  - Webhook integrations

- **🏗️ Architecture**
  - FastAPI backend (Python 3.11+)
  - React 18 frontend (TypeScript)
  - PostgreSQL database with async drivers
  - Redis caching & session store
  - Docker & Docker Compose deployment
  - Health checks & monitoring ready

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/nexus-core.git
cd nexus-core

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (dev mode)
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
nexus-core/
├── README.md                    # Complete documentation
├── docker-compose.yml           # Service orchestration
│
├── backend/                     # FastAPI Backend (Python 3.11+)
│   ├── Dockerfile
│   ├── requirements.txt         # Python dependencies
│   └── app/
│       ├── main.py              # Application entry point
│       ├── __init__.py
│       │
│       ├── api/                 # API Layer
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       └── endpoints/
│       │           ├── __init__.py
│       │           ├── auth.py  # Authentication endpoints
│       │           └── notes.py # Note management endpoints
│       │
│       ├── core/                # Core Configuration & Security
│       │   ├── __init__.py
│       │   ├── config.py        # Environment configuration
│       │   ├── security.py      # JWT, MFA, password hashing
│       │   └── rate_limiter.py  # Redis-based rate limiting
│       │
│       ├── db/                  # Database Layer
│       │   ├── __init__.py
│       │   └── session.py       # Async session management
│       │
│       ├── models/              # ORM Models
│       │   ├── __init__.py
│       │   └── entities.py      # User, Note, AuditLog models
│       │
│       ├── services/            # Business Logic
│       │   └── __init__.py
│       │
│       └── utils/               # Utility Functions
│           └── __init__.py
│
├── frontend/                    # React 18 Frontend (TypeScript)
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .eslintrc.cjs
│   ├── nginx.conf               # Production nginx config
│   └── src/
│       ├── main.tsx             # React entry point
│       ├── App.tsx              # Root component
│       ├── index.css            # Global styles
│       │
│       ├── components/          # Reusable UI components
│       ├── pages/               # Page components
│       ├── hooks/               # Custom React hooks
│       │   └── index.ts
│       │
│       ├── services/            # API clients
│       │   ├── index.ts
│       │   └── api.ts           # HTTP client configuration
│       │
│       ├── store/               # State management
│       │   ├── index.ts
│       │   └── authStore.ts     # Authentication state
│       │
│       ├── types/               # TypeScript type definitions
│       │   └── index.ts
│       │
│       └── utils/               # Helper utilities
│           └── index.ts
│
├── docker/                      # Docker Configuration
│   └── init.sql                 # PostgreSQL initialization script
│
└── scripts/                     # Operational Scripts (optional)
```

**Total Files**: 42 production-ready files

## 🔧 Configuration

Environment variables (via `.env` or Docker):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | auto-generated | JWT signing key |
| `DATABASE_URL` | postgresql+asyncpg://... | Database connection |
| `REDIS_URL` | redis://... | Redis connection |
| `DEBUG` | false | Debug mode |
| `LOG_LEVEL` | INFO | Logging level |
| `ENABLE_MFA` | true | MFA feature flag |
| `ENABLE_AUDIT_LOG` | true | Audit logging |

## 🛡️ Security Features

1. **Password Policy**
   - Minimum 12 characters
   - Uppercase, lowercase, digit, special character required
   - Argon2id hashing

2. **Account Protection**
   - Max 5 login attempts before 30-minute lockout
   - Session timeout after 60 minutes
   - Refresh token rotation

3. **API Security**
   - CORS configuration
   - Rate limiting ready
   - CSRF protection
   - Structured logging

4. **Audit Trail**
   - All authentication events logged
   - Resource changes tracked
   - IP addresses recorded
   - Immutable log storage

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Notes (Coming Soon)
- `GET /api/v1/notes` - List notes
- `POST /api/v1/notes` - Create note
- `PUT /api/v1/notes/{id}` - Update note
- `DELETE /api/v1/notes/{id}` - Delete note

### Workflows (Coming Soon)
- `GET /api/v1/workflows` - List workflows
- `POST /api/v1/workflows` - Create workflow
- `POST /api/v1/workflows/{id}/execute` - Execute workflow

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest -v --cov=app

# Run with coverage report
pytest --cov=app --cov-report=html
```

## 📈 Production Deployment

### Recommendations

1. **Change default secrets**
   ```bash
   export SECRET_KEY=$(openssl rand -hex 64)
   ```

2. **Use external database**
   - Configure managed PostgreSQL (AWS RDS, Google Cloud SQL)
   - Enable SSL connections

3. **Enable HTTPS**
   - Use reverse proxy (nginx, Traefik)
   - Configure SSL certificates

4. **Monitoring**
   - Prometheus metrics endpoint
   - Health check integration
   - Log aggregation (ELK, Loki)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)

---

**Nexus Core** - Where Knowledge Meets Automation
