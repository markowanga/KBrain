import { useState, useEffect } from 'react'
import { useScopes, useDocuments, useStatistics } from './hooks'
import type { GlobalStatistics } from './api/types'
import { formatBytes, getStatusColor } from './utils/format'

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'scopes' | 'documents'>('dashboard')
  const [selectedScopeId, setSelectedScopeId] = useState<string | null>(null)

  // Custom hooks
  const scopesHook = useScopes()
  const documentsHook = useDocuments()
  const statisticsHook = useStatistics()

  // Fetch data when tab changes
  useEffect(() => {
    if (activeTab === 'dashboard') {
      statisticsHook.fetchGlobalStatistics()
    } else if (activeTab === 'scopes') {
      scopesHook.fetchScopes()
    } else if (activeTab === 'documents') {
      scopesHook.fetchScopes()
    }
  }, [activeTab])

  // Fetch documents when scope is selected
  useEffect(() => {
    if (selectedScopeId) {
      documentsHook.fetchDocuments(selectedScopeId)
    }
  }, [selectedScopeId])

  const handleCreateScope = async (name: string, description: string) => {
    const scope = await scopesHook.createScope({
      name,
      description,
      allowed_extensions: ['pdf', 'docx', 'txt', 'jpg', 'png', 'doc', 'xlsx', 'pptx'],
      storage_backend: 'local',
    })
    return scope !== null
  }

  const handleDeleteScope = async (scopeId: string) => {
    const success = await scopesHook.deleteScope(scopeId)
    if (success && selectedScopeId === scopeId) {
      setSelectedScopeId(null)
    }
  }

  const handleUploadDocument = async (scopeId: string, file: File) => {
    const doc = await documentsHook.uploadDocument(scopeId, file)
    return doc !== null
  }

  const handleDeleteDocument = async (documentId: string) => {
    return await documentsHook.deleteDocument(documentId)
  }

  const handleSelectScope = (scopeId: string) => {
    setSelectedScopeId(scopeId)
  }

  // Combined loading and error states
  const loading = scopesHook.loading || documentsHook.loading || statisticsHook.loading
  const error = scopesHook.error || documentsHook.error || statisticsHook.error

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
            KBrain
          </h1>
          <p className="text-gray-600 mt-1">System zarządzania dokumentami</p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-2 py-4">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
                activeTab === 'dashboard'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('scopes')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
                activeTab === 'scopes'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Scope'y
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
                activeTab === 'documents'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Dokumenty
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
            <p className="text-red-700 font-semibold">{error}</p>
            <button
              onClick={() => {
                scopesHook.clearError()
                documentsHook.clearError()
                statisticsHook.clearError()
              }}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              Zamknij
            </button>
          </div>
        )}

        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {!loading && activeTab === 'dashboard' && (
          <Dashboard statistics={statisticsHook.globalStats} />
        )}
        {!loading && activeTab === 'scopes' && (
          <Scopes
            scopes={scopesHook.scopes?.scopes || []}
            onCreateScope={handleCreateScope}
            onDeleteScope={handleDeleteScope}
          />
        )}
        {!loading && activeTab === 'documents' && (
          <Documents
            scopes={scopesHook.scopes?.scopes || []}
            documents={documentsHook.documents?.documents || []}
            selectedScope={selectedScopeId}
            onSelectScope={handleSelectScope}
            onUploadDocument={handleUploadDocument}
            onDeleteDocument={handleDeleteDocument}
          />
        )}
      </main>
    </div>
  )
}

// Dashboard Component
function Dashboard({ statistics }: { statistics: GlobalStatistics | null }) {
  if (!statistics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">Ładowanie statystyk...</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Wszystkie Scope'y"
          value={statistics.total_scopes || 0}
          color="blue"
        />
        <StatCard
          title="Wszystkie Dokumenty"
          value={statistics.total_documents || 0}
          color="indigo"
        />
        <StatCard
          title="Łączny Rozmiar"
          value={formatBytes(statistics.total_size || 0)}
          color="purple"
        />
      </div>

      {statistics.documents_by_status && (
        <div className="mt-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Status Dokumentów</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(statistics.documents_by_status).map(([status, count]) => (
              <div key={status} className="bg-white rounded-lg shadow-md p-4">
                <p className="text-gray-600 text-sm uppercase">{status}</p>
                <p className="text-2xl font-bold text-blue-600">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {statistics.documents_by_extension && Object.keys(statistics.documents_by_extension).length > 0 && (
        <div className="mt-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Dokumenty według rozszerzenia</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(statistics.documents_by_extension).map(([ext, count]) => (
              <div key={ext} className="bg-white rounded-lg shadow-md p-4">
                <p className="text-gray-600 text-sm uppercase">.{ext}</p>
                <p className="text-2xl font-bold text-indigo-600">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// StatCard Component
function StatCard({ title, value, color }: { title: string; value: string | number; color: 'blue' | 'indigo' | 'purple' }) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    indigo: 'from-indigo-500 to-indigo-600',
    purple: 'from-purple-500 to-purple-600',
  }

  return (
    <div className={`bg-gradient-to-br ${colors[color]} rounded-xl shadow-lg p-6 text-white`}>
      <h3 className="text-sm font-semibold uppercase opacity-90">{title}</h3>
      <p className="text-4xl font-bold mt-2">{value}</p>
    </div>
  )
}

// Scopes Component
interface ScopesProps {
  scopes: Array<{
    id: string
    name: string
    description: string | null
    is_active: boolean
    document_count: number
    total_size: number
  }>
  onCreateScope: (name: string, description: string) => Promise<boolean>
  onDeleteScope: (scopeId: string) => Promise<void>
}

function Scopes({ scopes, onCreateScope, onDeleteScope }: ScopesProps) {
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const success = await onCreateScope(name, description)
    if (success) {
      setName('')
      setDescription('')
      setShowForm(false)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-gray-800">Zarządzanie Scope'ami</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
        >
          {showForm ? 'Anuluj' : '+ Nowy Scope'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Utwórz Nowy Scope</h3>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 font-semibold mb-2">Nazwa</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="np. Dokumenty Projektowe"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 font-semibold mb-2">Opis</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Opis scope'a"
                rows={3}
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200"
            >
              Utwórz Scope
            </button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {scopes.map((scope) => (
          <div
            key={scope.id}
            className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200"
          >
            <h3 className="text-xl font-bold text-gray-800 mb-2">{scope.name}</h3>
            <p className="text-gray-600 mb-4">{scope.description || 'Brak opisu'}</p>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-500">
                Dokumenty: {scope.document_count || 0}
              </span>
              <span className="text-sm text-gray-500">
                {formatBytes(scope.total_size || 0)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">
                {scope.is_active ? '✓ Aktywny' : '✗ Nieaktywny'}
              </span>
              <button
                onClick={() => onDeleteScope(scope.id)}
                className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
              >
                Usuń
              </button>
            </div>
          </div>
        ))}
      </div>

      {scopes.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <p className="text-gray-500 text-lg">Brak scope'ów. Utwórz pierwszy!</p>
        </div>
      )}
    </div>
  )
}

// Documents Component
interface DocumentsProps {
  scopes: Array<{
    id: string
    name: string
  }>
  documents: Array<{
    id: string
    original_name: string
    file_size: number
    status: string
    upload_date: string
  }>
  selectedScope: string | null
  onSelectScope: (scopeId: string) => void
  onUploadDocument: (scopeId: string, file: File) => Promise<boolean>
  onDeleteDocument: (documentId: string) => Promise<boolean>
}

function Documents({
  scopes,
  documents,
  selectedScope,
  onSelectScope,
  onUploadDocument,
  onDeleteDocument,
}: DocumentsProps) {
  const [file, setFile] = useState<File | null>(null)

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (file && selectedScope) {
      const success = await onUploadDocument(selectedScope, file)
      if (success) {
        setFile(null)
        ;(e.target as HTMLFormElement).reset()
      }
    }
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Zarządzanie Dokumentami</h2>

      {/* Scope Selection */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <label className="block text-gray-700 font-semibold mb-2">Wybierz Scope</label>
        <select
          value={selectedScope || ''}
          onChange={(e) => onSelectScope(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">-- Wybierz scope --</option>
          {scopes.map((scope) => (
            <option key={scope.id} value={scope.id}>
              {scope.name}
            </option>
          ))}
        </select>
      </div>

      {/* Upload Form */}
      {selectedScope && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Upload Dokumentu</h3>
          <form onSubmit={handleUpload}>
            <div className="mb-4">
              <input
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <button
              type="submit"
              disabled={!file}
              className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Wyślij Dokument
            </button>
          </form>
        </div>
      )}

      {/* Documents List */}
      {selectedScope && documents.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white">
              <tr>
                <th className="px-6 py-4 text-left font-semibold">Nazwa</th>
                <th className="px-6 py-4 text-left font-semibold">Rozmiar</th>
                <th className="px-6 py-4 text-left font-semibold">Status</th>
                <th className="px-6 py-4 text-left font-semibold">Data</th>
                <th className="px-6 py-4 text-left font-semibold">Akcje</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc, idx) => (
                <tr key={doc.id} className={idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                  <td className="px-6 py-4">{doc.original_name}</td>
                  <td className="px-6 py-4">{formatBytes(doc.file_size)}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(doc.status)}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">{new Date(doc.upload_date).toLocaleDateString()}</td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => onDeleteDocument(doc.id)}
                      className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
                    >
                      Usuń
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedScope && documents.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <p className="text-gray-500 text-lg">Brak dokumentów w tym scope. Wyślij pierwszy!</p>
        </div>
      )}

      {!selectedScope && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <p className="text-gray-500 text-lg">Wybierz scope aby zobaczyć dokumenty</p>
        </div>
      )}
    </div>
  )
}

export default App
