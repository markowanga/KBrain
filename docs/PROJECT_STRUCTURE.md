# Project Structure

## Overview

This document outlines the recommended project structure for KBrain, including both backend and frontend codebases. The structure follows industry best practices for scalability, maintainability, and testability.

## Repository Layout

### Monorepo Approach (Recommended)

```
KBrain/
├── backend/              # Backend API server
├── frontend/             # Frontend web application
├── shared/               # Shared types/utilities
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── infrastructure/       # Infrastructure as Code (IaC)
├── .github/              # GitHub workflows
├── docker-compose.yml    # Local development setup
├── README.md
└── LICENSE
```

### Separate Repositories (Alternative)

```
KBrain-Backend/           # Backend repository
KBrain-Frontend/          # Frontend repository
KBrain-Docs/              # Documentation repository
```

---

## Backend Structure

### Technology-Agnostic Structure

```
backend/
├── src/
│   ├── api/                      # API layer
│   │   ├── routes/               # Route definitions
│   │   │   ├── scopes.routes.*
│   │   │   ├── documents.routes.*
│   │   │   └── statistics.routes.*
│   │   ├── controllers/          # Request handlers
│   │   │   ├── scopes.controller.*
│   │   │   ├── documents.controller.*
│   │   │   └── statistics.controller.*
│   │   ├── middleware/           # Middleware functions
│   │   │   ├── error-handler.*
│   │   │   ├── validation.*
│   │   │   ├── rate-limiter.*
│   │   │   └── request-logger.*
│   │   └── validators/           # Request validation schemas
│   │       ├── scope.validator.*
│   │       └── document.validator.*
│   │
│   ├── core/                     # Core business logic
│   │   ├── services/             # Business services
│   │   │   ├── scope.service.*
│   │   │   ├── document.service.*
│   │   │   └── processing.service.*
│   │   ├── repositories/         # Data access layer
│   │   │   ├── scope.repository.*
│   │   │   ├── document.repository.*
│   │   │   └── queue.repository.*
│   │   └── models/               # Domain models
│   │       ├── scope.model.*
│   │       ├── document.model.*
│   │       └── processing-queue.model.*
│   │
│   ├── storage/                  # Storage abstraction
│   │   ├── interfaces/
│   │   │   └── storage-provider.interface.*
│   │   ├── providers/
│   │   │   ├── s3.provider.*
│   │   │   ├── azure-blob.provider.*
│   │   │   ├── sftp.provider.*
│   │   │   └── local.provider.*
│   │   ├── factory/
│   │   │   └── storage-factory.*
│   │   └── utils/
│   │       ├── checksum.*
│   │       └── file-utils.*
│   │
│   ├── database/                 # Database layer
│   │   ├── migrations/           # Database migrations
│   │   │   ├── 001_create_scopes_table.sql
│   │   │   ├── 002_create_documents_table.sql
│   │   │   └── 003_create_processing_queue_table.sql
│   │   ├── seeds/                # Seed data
│   │   │   └── development-seeds.sql
│   │   ├── connection.*          # Database connection
│   │   └── client.*              # Database client wrapper
│   │
│   ├── workers/                  # Background workers
│   │   ├── document-processor.worker.*
│   │   └── cleanup.worker.*
│   │
│   ├── queue/                    # Queue management
│   │   ├── interfaces/
│   │   │   └── queue.interface.*
│   │   ├── providers/
│   │   │   ├── database-queue.provider.*
│   │   │   ├── redis-queue.provider.*
│   │   │   └── rabbitmq-queue.provider.*
│   │   └── factory/
│   │       └── queue-factory.*
│   │
│   ├── config/                   # Configuration
│   │   ├── database.config.*
│   │   ├── storage.config.*
│   │   ├── server.config.*
│   │   └── app.config.*
│   │
│   ├── utils/                    # Utility functions
│   │   ├── logger.*
│   │   ├── errors.*
│   │   ├── validators.*
│   │   └── helpers.*
│   │
│   ├── types/                    # Type definitions
│   │   ├── api.types.*
│   │   ├── storage.types.*
│   │   └── database.types.*
│   │
│   ├── app.*                     # Application setup
│   └── server.*                  # Server entry point
│
├── tests/                        # Tests
│   ├── unit/                     # Unit tests
│   │   ├── services/
│   │   ├── repositories/
│   │   └── storage/
│   ├── integration/              # Integration tests
│   │   ├── api/
│   │   ├── database/
│   │   └── storage/
│   ├── e2e/                      # End-to-end tests
│   │   └── scenarios/
│   ├── fixtures/                 # Test fixtures
│   │   └── sample-files/
│   └── helpers/                  # Test utilities
│
├── config/                       # Environment configs
│   ├── development.env
│   ├── production.env
│   └── test.env
│
├── scripts/                      # Utility scripts
│   ├── migrate.sh
│   ├── seed.sh
│   └── start-worker.sh
│
├── docs/                         # Backend-specific docs
│   └── api-examples/
│
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Local dev environment
├── package.json / requirements.txt / go.mod
├── tsconfig.json / pyproject.toml / go.sum
└── README.md
```

---

## Frontend Structure

### React/Vue/Angular Structure

```
frontend/
├── public/                       # Static files
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
│       └── images/
│
├── src/
│   ├── app/                      # Application setup
│   │   ├── App.*
│   │   ├── Router.*
│   │   └── main.*
│   │
│   ├── pages/                    # Page components
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.*
│   │   │   ├── Dashboard.test.*
│   │   │   └── Dashboard.styles.*
│   │   ├── Scopes/
│   │   │   ├── ScopeList.*
│   │   │   ├── ScopeDetail.*
│   │   │   ├── CreateScope.*
│   │   │   └── EditScope.*
│   │   ├── Documents/
│   │   │   ├── DocumentList.*
│   │   │   ├── DocumentDetail.*
│   │   │   ├── UploadDocument.*
│   │   │   └── BulkUpload.*
│   │   └── NotFound/
│   │
│   ├── components/               # Reusable components
│   │   ├── common/               # Common UI components
│   │   │   ├── Button/
│   │   │   ├── Input/
│   │   │   ├── Modal/
│   │   │   ├── Table/
│   │   │   ├── Pagination/
│   │   │   ├── FileUpload/
│   │   │   └── StatusBadge/
│   │   ├── layout/               # Layout components
│   │   │   ├── Header/
│   │   │   ├── Sidebar/
│   │   │   ├── Footer/
│   │   │   └── MainLayout/
│   │   ├── scopes/               # Scope-specific components
│   │   │   ├── ScopeCard/
│   │   │   ├── ScopeForm/
│   │   │   └── ScopeStats/
│   │   └── documents/            # Document-specific components
│   │       ├── DocumentCard/
│   │       ├── DocumentTable/
│   │       ├── DocumentUploader/
│   │       ├── UploadProgress/
│   │       └── StatusIndicator/
│   │
│   ├── services/                 # API services
│   │   ├── api/
│   │   │   ├── client.*          # HTTP client setup
│   │   │   ├── scopes.api.*
│   │   │   ├── documents.api.*
│   │   │   └── statistics.api.*
│   │   └── websocket/
│   │       └── ws.client.*
│   │
│   ├── store/                    # State management
│   │   ├── index.*
│   │   ├── slices/               # State slices (Redux)
│   │   │   ├── scopes.slice.*
│   │   │   ├── documents.slice.*
│   │   │   └── ui.slice.*
│   │   └── hooks/                # Custom hooks
│   │       ├── useScopes.*
│   │       ├── useDocuments.*
│   │       └── useUpload.*
│   │
│   ├── hooks/                    # React hooks
│   │   ├── useFileUpload.*
│   │   ├── usePagination.*
│   │   ├── useDebounce.*
│   │   └── useWebSocket.*
│   │
│   ├── utils/                    # Utility functions
│   │   ├── formatters.*          # Data formatters
│   │   ├── validators.*          # Client-side validation
│   │   ├── constants.*           # Constants
│   │   └── helpers.*
│   │
│   ├── types/                    # TypeScript types
│   │   ├── scope.types.*
│   │   ├── document.types.*
│   │   └── api.types.*
│   │
│   ├── styles/                   # Global styles
│   │   ├── global.*
│   │   ├── variables.*
│   │   ├── theme.*
│   │   └── mixins.*
│   │
│   ├── assets/                   # Assets
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   └── config/                   # Configuration
│       ├── routes.*
│       └── api.config.*
│
├── tests/                        # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env.example                  # Environment variables example
├── .env.development
├── .env.production
├── package.json
├── tsconfig.json
├── vite.config.* / webpack.config.*
├── Dockerfile
└── README.md
```

---

## Shared Module Structure

For monorepo setups, shared types and utilities:

```
shared/
├── src/
│   ├── types/                    # Shared TypeScript types
│   │   ├── scope.types.*
│   │   ├── document.types.*
│   │   ├── api.types.*
│   │   └── index.*
│   ├── constants/                # Shared constants
│   │   ├── status.constants.*
│   │   ├── mime-types.constants.*
│   │   └── index.*
│   ├── validators/               # Shared validation schemas
│   │   ├── scope.validator.*
│   │   └── document.validator.*
│   └── utils/                    # Shared utilities
│       ├── file-utils.*
│       └── date-utils.*
│
├── package.json
└── tsconfig.json
```

---

## Infrastructure Structure

Infrastructure as Code for deployment:

```
infrastructure/
├── docker/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── worker.Dockerfile
│   └── nginx.Dockerfile
│
├── kubernetes/                   # Kubernetes manifests
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── worker-deployment.yaml
│   │   └── services.yaml
│   ├── overlays/
│   │   ├── development/
│   │   ├── staging/
│   │   └── production/
│   └── kustomization.yaml
│
├── terraform/                    # Terraform IaC
│   ├── modules/
│   │   ├── vpc/
│   │   ├── database/
│   │   ├── storage/
│   │   └── compute/
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   └── variables.tf
│
├── helm/                         # Helm charts
│   └── kbrain/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── templates/
│       └── values/
│           ├── dev.yaml
│           └── prod.yaml
│
└── scripts/
    ├── deploy.sh
    └── rollback.sh
```

---

## Scripts Directory

Common utility scripts:

```
scripts/
├── setup/
│   ├── install-dependencies.sh
│   ├── setup-database.sh
│   └── generate-secrets.sh
│
├── database/
│   ├── migrate.sh
│   ├── rollback.sh
│   ├── seed.sh
│   └── backup.sh
│
├── development/
│   ├── start-dev.sh
│   ├── start-worker.sh
│   └── reset-db.sh
│
├── testing/
│   ├── run-unit-tests.sh
│   ├── run-integration-tests.sh
│   └── run-e2e-tests.sh
│
├── deployment/
│   ├── build.sh
│   ├── deploy.sh
│   └── health-check.sh
│
└── utilities/
    ├── generate-types.sh
    ├── lint.sh
    └── format.sh
```

---

## Configuration Files

### Backend Configuration Files

**Node.js/TypeScript:**
```
backend/
├── package.json
├── tsconfig.json
├── .eslintrc.json
├── .prettierrc
├── jest.config.js
└── nodemon.json
```

**Python:**
```
backend/
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── setup.py
├── pytest.ini
└── .flake8
```

**Go:**
```
backend/
├── go.mod
├── go.sum
├── Makefile
└── .golangci.yml
```

### Frontend Configuration Files

**React/TypeScript:**
```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .eslintrc.json
├── .prettierrc
└── vitest.config.ts
```

---

## Environment Variables

### Backend (.env)

```bash
# Server
NODE_ENV=development
PORT=3000
API_VERSION=v1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/kbrain
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10

# Storage (Default)
DEFAULT_STORAGE_BACKEND=s3

# AWS S3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET=kbrain-documents

# Azure Blob
AZURE_STORAGE_ACCOUNT=kbrainstorage
AZURE_STORAGE_KEY=your-storage-key
AZURE_STORAGE_CONTAINER=documents

# SFTP
SFTP_HOST=sftp.example.com
SFTP_PORT=22
SFTP_USERNAME=kbrain
SFTP_PRIVATE_KEY_PATH=/keys/sftp_rsa
SFTP_BASE_PATH=/data/kbrain/

# Queue
QUEUE_BACKEND=database  # or 'redis', 'rabbitmq'
REDIS_URL=redis://localhost:6379

# Processing
MAX_FILE_SIZE=104857600  # 100MB in bytes
PROCESSING_WORKER_COUNT=4

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Security
CORS_ORIGIN=http://localhost:5173
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=1000
```

### Frontend (.env)

```bash
# API
VITE_API_BASE_URL=http://localhost:3000/v1
VITE_WS_URL=ws://localhost:3000/v1/ws

# Upload
VITE_MAX_FILE_SIZE=104857600
VITE_CHUNK_SIZE=5242880

# Features
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_ANALYTICS=false
```

---

## File Naming Conventions

### Backend

**TypeScript/JavaScript:**
- Files: `kebab-case.ts` or `camelCase.ts`
- Classes: `PascalCase`
- Interfaces: `IPascalCase` or `PascalCase`
- Functions: `camelCase`

**Python:**
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`

**Go:**
- Files: `snake_case.go`
- Exported: `PascalCase`
- Unexported: `camelCase`

### Frontend

**React Components:**
```
ComponentName/
├── ComponentName.tsx         # Component logic
├── ComponentName.styles.ts   # Styled components / CSS-in-JS
├── ComponentName.test.tsx    # Tests
└── index.ts                  # Re-export
```

---

## Module Dependencies

### Backend Dependencies Flow

```
Routes → Controllers → Services → Repositories → Database
                    ↓
                Storage Providers
```

### Dependency Rules

1. **API layer** depends on **Core layer**
2. **Core layer** depends on **Storage** and **Database** layers
3. **Storage** and **Database** are independent
4. **Utils** can be used by any layer
5. No circular dependencies

---

## Development Workflow

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/kbrain.git
cd kbrain

# 2. Setup backend
cd backend
npm install  # or pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configurations

# 3. Setup database
npm run db:migrate
npm run db:seed

# 4. Start backend
npm run dev

# 5. Setup frontend (in new terminal)
cd ../frontend
npm install
cp .env.example .env
# Edit .env with your configurations

# 6. Start frontend
npm run dev
```

### Docker Development Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec backend npm run db:migrate

# Stop all services
docker-compose down
```

---

## Testing Structure

### Test Organization

```
tests/
├── unit/                     # Fast, isolated tests
│   ├── services/
│   ├── repositories/
│   └── utils/
├── integration/              # Test multiple components
│   ├── api/
│   ├── database/
│   └── storage/
└── e2e/                      # Full user workflows
    └── scenarios/
        ├── upload-document.test.*
        ├── create-scope.test.*
        └── process-document.test.*
```

### Test Commands

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests
npm run test:integration

# Run e2e tests
npm run test:e2e

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

---

## Build and Deployment

### Build Commands

```bash
# Backend build
cd backend
npm run build
# Output: dist/ or build/

# Frontend build
cd frontend
npm run build
# Output: dist/ or build/
```

### Deployment Structure

```
production/
├── backend/
│   ├── dist/               # Compiled backend code
│   ├── node_modules/       # Production dependencies only
│   └── .env.production
├── frontend/
│   └── dist/               # Static files for CDN/nginx
└── workers/
    └── dist/               # Compiled worker code
```

---

## Documentation Structure

```
docs/
├── ARCHITECTURE.md           # System architecture
├── DATABASE_SCHEMA.md        # Database design
├── STORAGE_INTERFACE.md      # Storage abstraction
├── API_SPECIFICATION.md      # API documentation
├── PROJECT_STRUCTURE.md      # This file
├── TECH_STACK.md             # Technology choices
├── DEPLOYMENT.md             # Deployment guide
├── DEVELOPMENT.md            # Development guide
├── TESTING.md                # Testing guide
├── CONTRIBUTING.md           # Contribution guidelines
└── CHANGELOG.md              # Version history
```

---

## Best Practices

### Code Organization

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Use DI for better testability
3. **Interface Segregation**: Define clear interfaces
4. **DRY Principle**: Don't repeat yourself
5. **SOLID Principles**: Follow SOLID design principles

### File Size

- Keep files under 300 lines
- Split large components/services into smaller modules
- Use barrel exports (index files) for cleaner imports

### Import Organization

```typescript
// 1. External dependencies
import express from 'express';
import { v4 as uuidv4 } from 'uuid';

// 2. Internal modules
import { ScopeService } from '@/core/services/scope.service';
import { IStorageProvider } from '@/storage/interfaces/storage-provider.interface';

// 3. Types
import type { Scope, CreateScopeDto } from '@/types/scope.types';

// 4. Utils
import { logger } from '@/utils/logger';
```

### Comments and Documentation

- Use JSDoc/docstrings for public APIs
- Comment "why", not "what"
- Keep comments up to date
- Use TODO/FIXME markers when appropriate

---

## Scalability Considerations

### Horizontal Scaling

```
Load Balancer
     ↓
Backend Instance 1 ─┐
Backend Instance 2 ─┼→ Shared Database
Backend Instance N ─┘   Shared Storage
     ↓
Worker Pool
```

### Microservices Evolution (Future)

```
KBrain/
├── api-gateway/              # API Gateway
├── scope-service/            # Scope management
├── document-service/         # Document management
├── processing-service/       # Document processing
├── storage-service/          # Storage abstraction
└── notification-service/     # Notifications
```
