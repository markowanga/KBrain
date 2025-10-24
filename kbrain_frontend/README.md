# KBrain Frontend

Modern React frontend for KBrain document management system.

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite 7** - Build tool
- **Tailwind CSS 3** - Styling
- **Custom Hooks** - State management

## Project Structure

```
src/
├── api/                    # API client and types
│   ├── client.ts          # Base HTTP client
│   ├── scopes.ts          # Scopes API
│   ├── documents.ts       # Documents API
│   ├── statistics.ts      # Statistics API
│   ├── types.ts           # TypeScript types
│   └── index.ts           # Module exports
├── hooks/                 # React hooks
│   ├── useScopes.ts       # Scope management hook
│   ├── useDocuments.ts    # Document management hook
│   ├── useStatistics.ts   # Statistics hook
│   └── index.ts           # Module exports
├── utils/                 # Utility functions
│   └── format.ts          # Formatting helpers
├── App.tsx                # Main application component
└── main.tsx               # Application entry point
```

## Features

### API Integration

- **Type-safe API client** with TypeScript
- **Centralized error handling**
- **Request/response interceptors**
- **Environment-based configuration**

### React Hooks

Custom hooks for data management:

- `useScopes()` - Manage scopes (create, update, delete, list)
- `useDocuments()` - Manage documents (upload, download, delete, list)
- `useStatistics()` - Fetch global and scope statistics

### Components

- **Dashboard** - Global statistics and metrics
- **Scopes** - Scope management interface
- **Documents** - Document upload and management

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install
```

### Configuration

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## API Client Usage

### Using API Functions Directly

```typescript
import { scopesApi, documentsApi } from './api'

// Create a scope
const scope = await scopesApi.create({
  name: 'My Scope',
  description: 'Description',
  allowed_extensions: ['pdf', 'docx'],
  storage_backend: 'local'
})

// Upload a document
const document = await documentsApi.upload(scopeId, file)

// List documents
const { documents, pagination } = await documentsApi.list(scopeId, {
  page: 1,
  per_page: 20,
  status: 'processed'
})
```

### Using React Hooks

```typescript
import { useScopes, useDocuments } from './hooks'

function MyComponent() {
  const { scopes, loading, error, createScope, deleteScope } = useScopes()
  const { documents, uploadDocument } = useDocuments()

  // Create scope
  const handleCreate = async () => {
    const scope = await createScope({
      name: 'New Scope',
      allowed_extensions: ['pdf']
    })
  }

  // Upload document
  const handleUpload = async (file: File) => {
    const doc = await uploadDocument(scopeId, file)
  }

  return (
    // Your component JSX
  )
}
```

## Error Handling

The API client includes centralized error handling:

```typescript
try {
  const data = await scopesApi.list()
} catch (error) {
  if (error instanceof ApiClientError) {
    console.error(error.message)      // User-friendly message
    console.error(error.statusCode)   // HTTP status code
    console.error(error.code)         // API error code
    console.error(error.details)      // Validation details
  }
}
```

## TypeScript Types

All API responses are fully typed:

```typescript
import type {
  Scope,
  ScopeCreate,
  Document,
  DocumentListParams,
  GlobalStatistics
} from './api/types'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000` |

## Development Notes

- All API calls use the base client in `src/api/client.ts`
- Error responses follow the backend schema
- Pagination is handled automatically
- Loading states are managed by hooks

## License

MIT
