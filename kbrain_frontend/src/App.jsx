import { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [scopes, setScopes] = useState([])
  const [documents, setDocuments] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedScope, setSelectedScope] = useState(null)

  // Fetch statistics
  const fetchStatistics = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/v1/statistics`)
      const data = await response.json()
      setStatistics(data)
      setError(null)
    } catch (err) {
      setError('Nie można pobrać statystyk')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Fetch scopes
  const fetchScopes = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/v1/scopes`)
      const data = await response.json()
      setScopes(data.items || [])
      setError(null)
    } catch (err) {
      setError('Nie można pobrać scope\'ów')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Fetch documents
  const fetchDocuments = async (scopeId) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/v1/scopes/${scopeId}/documents`)
      const data = await response.json()
      setDocuments(data.items || [])
      setError(null)
    } catch (err) {
      setError('Nie można pobrać dokumentów')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Create scope
  const createScope = async (name, description) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/v1/scopes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description,
          allowed_extensions: ['pdf', 'docx', 'txt', 'jpg', 'png'],
          storage_backend: 'local'
        })
      })
      if (!response.ok) throw new Error('Błąd tworzenia scope')
      await fetchScopes()
      setError(null)
    } catch (err) {
      setError('Nie można utworzyć scope')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Delete scope
  const deleteScope = async (scopeId) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/v1/scopes/${scopeId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Błąd usuwania scope')
      await fetchScopes()
      setError(null)
    } catch (err) {
      setError('Nie można usunąć scope')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Upload document
  const uploadDocument = async (scopeId, file) => {
    try {
      setLoading(true)
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_URL}/v1/scopes/${scopeId}/documents`, {
        method: 'POST',
        body: formData
      })
      if (!response.ok) throw new Error('Błąd uploadu')
      await fetchDocuments(scopeId)
      setError(null)
    } catch (err) {
      setError('Nie można wysłać dokumentu')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Delete document
  const deleteDocument = async (documentId) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/v1/documents/${documentId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Błąd usuwania dokumentu')
      if (selectedScope) {
        await fetchDocuments(selectedScope)
      }
      setError(null)
    } catch (err) {
      setError('Nie można usunąć dokumentu')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchStatistics()
    } else if (activeTab === 'scopes') {
      fetchScopes()
    }
  }, [activeTab])

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
          </div>
        )}

        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {!loading && activeTab === 'dashboard' && <Dashboard statistics={statistics} />}
        {!loading && activeTab === 'scopes' && (
          <Scopes
            scopes={scopes}
            onCreateScope={createScope}
            onDeleteScope={deleteScope}
          />
        )}
        {!loading && activeTab === 'documents' && (
          <Documents
            scopes={scopes}
            documents={documents}
            selectedScope={selectedScope}
            onSelectScope={(scopeId) => {
              setSelectedScope(scopeId)
              fetchDocuments(scopeId)
            }}
            onUploadDocument={uploadDocument}
            onDeleteDocument={deleteDocument}
          />
        )}
      </main>
    </div>
  )
}

// Dashboard Component
function Dashboard({ statistics }) {
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
          value={formatBytes(statistics.total_storage_used || 0)}
          color="purple"
        />
      </div>

      {statistics.by_status && (
        <div className="mt-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Status Dokumentów</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(statistics.by_status).map(([status, count]) => (
              <div key={status} className="bg-white rounded-lg shadow-md p-4">
                <p className="text-gray-600 text-sm uppercase">{status}</p>
                <p className="text-2xl font-bold text-blue-600">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// StatCard Component
function StatCard({ title, value, color }) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    indigo: 'from-indigo-500 to-indigo-600',
    purple: 'from-purple-500 to-purple-600'
  }

  return (
    <div className={`bg-gradient-to-br ${colors[color]} rounded-xl shadow-lg p-6 text-white`}>
      <h3 className="text-sm font-semibold uppercase opacity-90">{title}</h3>
      <p className="text-4xl font-bold mt-2">{value}</p>
    </div>
  )
}

// Scopes Component
function Scopes({ scopes, onCreateScope, onDeleteScope }) {
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    await onCreateScope(name, description)
    setName('')
    setDescription('')
    setShowForm(false)
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
                rows="3"
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
          <div key={scope.id} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200">
            <h3 className="text-xl font-bold text-gray-800 mb-2">{scope.name}</h3>
            <p className="text-gray-600 mb-4">{scope.description || 'Brak opisu'}</p>
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
function Documents({ scopes, documents, selectedScope, onSelectScope, onUploadDocument, onDeleteDocument }) {
  const [file, setFile] = useState(null)

  const handleUpload = async (e) => {
    e.preventDefault()
    if (file && selectedScope) {
      await onUploadDocument(selectedScope, file)
      setFile(null)
      e.target.reset()
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
                onChange={(e) => setFile(e.target.files[0])}
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

// Helper functions
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

function getStatusColor(status) {
  const colors = {
    added: 'bg-blue-100 text-blue-800',
    processing: 'bg-yellow-100 text-yellow-800',
    processed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800'
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

export default App
