# KBrain

**Knowledge Management System with Flexible Document Processing**

KBrain is a comprehensive knowledge management system that allows you to organize and process documents within defined scopes. The system provides a flexible document upload mechanism with pluggable storage backends (S3, Azure Blob, SFTP) and an automated document processing pipeline.

## Features

- **Scope-based Organization**: Organize documents within customizable knowledge scopes
- **Flexible File Types**: Configure allowed file extensions per scope
- **Multiple Storage Backends**: Support for AWS S3, Azure Blob Storage, and SFTP
- **Processing Pipeline**: Automatic document processing with status tracking (Added → Processing → Processed)
- **RESTful API**: Clean and well-documented API for all operations
- **Modern Frontend**: Intuitive web interface for document and scope management
- **Extensible Architecture**: Easy to extend with custom processing logic

## Project Status

This project is currently in the **planning and design phase**. All architectural documentation has been completed and is ready for implementation.

## Documentation

Comprehensive documentation is available in the `/docs` directory:

### Core Documentation

- **[Architecture](./docs/ARCHITECTURE.md)** - System architecture, data flow, and design decisions
- **[Database Schema](./docs/DATABASE_SCHEMA.md)** - Complete database design with tables, relationships, and indexes
- **[Storage Interface](./docs/STORAGE_INTERFACE.md)** - Storage abstraction layer specification for S3, Azure Blob, and SFTP
- **[API Specification](./docs/API_SPECIFICATION.md)** - RESTful API endpoints with request/response examples
- **[Project Structure](./docs/PROJECT_STRUCTURE.md)** - Recommended codebase organization and file structure
- **[Technology Stack](./docs/TECH_STACK.md)** - Recommended technologies, libraries, and tools

### Quick Links

- [System Architecture Diagram](./docs/ARCHITECTURE.md#high-level-architecture)
- [Database ERD](./docs/DATABASE_SCHEMA.md#entity-relationship-diagram)
- [API Endpoints](./docs/API_SPECIFICATION.md#api-endpoints)
- [Storage Providers](./docs/STORAGE_INTERFACE.md#storage-provider-implementations)
- [Tech Stack Recommendations](./docs/TECH_STACK.md#recommended-stack-combinations)

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Web UI)                        │
│  - Scope Management                                          │
│  - Document Upload                                           │
│  - Status Monitoring                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Backend API Server                        │
│  - Scope CRUD Operations                                     │
│  - Document Upload Handler                                   │
│  - Storage Abstraction Layer                                 │
│  - Processing Queue Manager                                  │
└───────┬──────────────────────────┬──────────────────────────┘
        │                          │
        │                          │
┌───────▼─────────┐      ┌─────────▼────────────────────────┐
│   Database      │      │    Storage Layer (Interface)     │
│                 │      │                                   │
│ - Scopes        │      │  ┌─────────────────────────────┐ │
│ - Documents     │      │  │  S3 Implementation          │ │
│ - Status        │      │  └─────────────────────────────┘ │
│ - Metadata      │      │  ┌─────────────────────────────┐ │
└─────────────────┘      │  │  Azure Blob Implementation  │ │
                         │  └─────────────────────────────┘ │
                         │  ┌─────────────────────────────┐ │
                         │  │  SFTP Implementation        │ │
                         │  └─────────────────────────────┘ │
                         └──────────────────────────────────┘
```

## Key Concepts

### Scopes

Scopes are organizational units for grouping related documents. Each scope has:
- Name and description
- Allowed file extensions (e.g., pdf, docx, txt)
- Storage backend configuration
- Independent storage and processing settings

### Documents

Documents are files uploaded to a scope. Each document:
- Belongs to a single scope
- Has a processing status (Added, Processing, Processed, Failed)
- Stores metadata (size, type, checksums, custom fields)
- Is stored in the configured backend (S3, Azure Blob, or SFTP)

### Processing Pipeline

Documents go through an automated processing pipeline:
1. **Added**: Document uploaded and stored
2. **Processing**: Document being processed by workers
3. **Processed**: Processing completed successfully
4. **Failed**: Processing failed (with error details)

## Technology Recommendations

The recommended technology stack for implementation:

**Backend:**
- Node.js 20+ with TypeScript
- Express.js or Fastify
- Prisma ORM
- PostgreSQL 15+

**Frontend:**
- React 18 with TypeScript
- Vite build tool
- Redux Toolkit for state management
- Material-UI or similar component library

**Storage:**
- AWS SDK for S3
- Azure SDK for Blob Storage
- SSH2 for SFTP

See [TECH_STACK.md](./docs/TECH_STACK.md) for detailed recommendations and alternatives.

## Next Steps

1. **Review Documentation**: Read through all documentation to understand the system design
2. **Choose Tech Stack**: Select technologies based on your team's expertise (see [TECH_STACK.md](./docs/TECH_STACK.md))
3. **Setup Project Structure**: Follow [PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md) to organize the codebase
4. **Implement Backend**: Start with database setup, then API, then storage layer
5. **Implement Frontend**: Build UI components following the API specification
6. **Testing**: Implement comprehensive tests (unit, integration, e2e)
7. **Deployment**: Deploy using Docker and recommended infrastructure

## Development Workflow (Future)

Once implemented, local development will be:

```bash
# Clone repository
git clone https://github.com/your-org/kbrain.git
cd kbrain

# Start all services with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:3000
# API Docs: http://localhost:3000/docs
```

## Contributing

This project is currently in planning phase. Once implementation begins:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add your license here]

## Contact

[Add contact information here]

---

**Note**: This project is currently in the design phase. All documentation is complete and ready for implementation. Review the docs and start building!
