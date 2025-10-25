import { useState, useEffect } from 'react'
import { useScopes, useDocuments, useStatistics, useTags } from './hooks'
import { documentsApi } from './api'
import type { GlobalStatistics, Tag, TagCreate } from './api/types'
import { formatBytes, getStatusColor } from './utils/format'

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'scopes' | 'documents' | 'tags'>('dashboard')
  const [selectedScopeId, setSelectedScopeId] = useState<string | null>(null)

  // Custom hooks
  const scopesHook = useScopes()
  const documentsHook = useDocuments()
  const statisticsHook = useStatistics()
  const tagsHook = useTags()

  // Fetch data when tab changes
  useEffect(() => {
    if (activeTab === 'dashboard') {
      statisticsHook.fetchGlobalStatistics()
    } else if (activeTab === 'scopes') {
      scopesHook.fetchScopes()
    } else if (activeTab === 'documents') {
      scopesHook.fetchScopes()
    } else if (activeTab === 'tags') {
      scopesHook.fetchScopes()
    }
  }, [activeTab])

  // Fetch documents and tags when scope is selected
  useEffect(() => {
    if (selectedScopeId) {
      documentsHook.fetchDocuments(selectedScopeId)
      tagsHook.fetchTags(selectedScopeId)
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

  const handleCreateTag = async (scopeId: string, data: TagCreate) => {
    const tag = await tagsHook.createTag(scopeId, data)
    return tag !== null
  }

  const handleUpdateTag = async (scopeId: string, tagId: string, data: TagCreate) => {
    const tag = await tagsHook.updateTag(scopeId, tagId, data)
    return tag !== null
  }

  const handleDeleteTag = async (scopeId: string, tagId: string) => {
    return await tagsHook.deleteTag(scopeId, tagId)
  }

  // Combined loading and error states
  const loading = scopesHook.loading || documentsHook.loading || statisticsHook.loading || tagsHook.loading
  const error = scopesHook.error || documentsHook.error || statisticsHook.error || tagsHook.error

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
            <button
              onClick={() => setActiveTab('tags')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
                activeTab === 'tags'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Tagi
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
                tagsHook.clearError()
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
            tags={tagsHook.tags || []}
            selectedScope={selectedScopeId}
            onSelectScope={handleSelectScope}
            onUploadDocument={handleUploadDocument}
            onDeleteDocument={handleDeleteDocument}
            onUpdateDocumentTags={async (documentId: string, tagIds: string[]) => {
              try {
                await documentsApi.updateTags(documentId, tagIds)
                // Refresh documents after updating tags
                if (selectedScopeId) {
                  await documentsHook.fetchDocuments(selectedScopeId)
                }
                return true
              } catch (error) {
                console.error('Failed to update document tags:', error)
                return false
              }
            }}
          />
        )}
        {!loading && activeTab === 'tags' && (
          <Tags
            scopes={scopesHook.scopes?.scopes || []}
            tags={tagsHook.tags || []}
            selectedScope={selectedScopeId}
            onSelectScope={handleSelectScope}
            onCreateTag={handleCreateTag}
            onUpdateTag={handleUpdateTag}
            onDeleteTag={handleDeleteTag}
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
            <div className="flex justify-end">
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
    tags?: Tag[]
  }>
  tags: Tag[]
  selectedScope: string | null
  onSelectScope: (scopeId: string) => void
  onUploadDocument: (scopeId: string, file: File) => Promise<boolean>
  onDeleteDocument: (documentId: string) => Promise<boolean>
  onUpdateDocumentTags: (documentId: string, tagIds: string[]) => Promise<boolean>
}

function Documents({
  scopes,
  documents,
  tags,
  selectedScope,
  onSelectScope,
  onUploadDocument,
  onDeleteDocument,
  onUpdateDocumentTags,
}: DocumentsProps) {
  const [file, setFile] = useState<File | null>(null)
  const [editingDocumentId, setEditingDocumentId] = useState<string | null>(null)
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([])

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

  const handleEditTags = (documentId: string, currentTags: Tag[] = []) => {
    setEditingDocumentId(documentId)
    setSelectedTagIds(currentTags.map(t => t.id))
  }

  const handleSaveTags = async (documentId: string) => {
    const success = await onUpdateDocumentTags(documentId, selectedTagIds)
    if (success) {
      setEditingDocumentId(null)
      setSelectedTagIds([])
    }
  }

  const handleCancelEditTags = () => {
    setEditingDocumentId(null)
    setSelectedTagIds([])
  }

  const toggleTagSelection = (tagId: string) => {
    setSelectedTagIds(prev =>
      prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    )
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
        <div className="space-y-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200"
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                {/* Document Info */}
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-800 mb-2">{doc.original_name}</h3>
                  <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                    <span>Rozmiar: {formatBytes(doc.file_size)}</span>
                    <span>Data: {new Date(doc.upload_date).toLocaleDateString()}</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(doc.status)}`}>
                      {doc.status}
                    </span>
                  </div>

                  {/* Tags Display */}
                  <div className="mt-3">
                    {editingDocumentId === doc.id ? (
                      <div className="space-y-3">
                        <div className="flex flex-wrap gap-2">
                          {tags.length > 0 ? (
                            tags.map((tag) => (
                              <button
                                key={tag.id}
                                onClick={() => toggleTagSelection(tag.id)}
                                className={`px-3 py-1 rounded-full text-sm font-semibold border-2 transition-all ${
                                  selectedTagIds.includes(tag.id)
                                    ? 'text-white'
                                    : 'bg-white text-gray-700'
                                }`}
                                style={{
                                  backgroundColor: selectedTagIds.includes(tag.id) ? tag.color || '#3B82F6' : 'white',
                                  borderColor: tag.color || '#3B82F6',
                                }}
                              >
                                {selectedTagIds.includes(tag.id) ? '✓ ' : ''}{tag.name}
                              </button>
                            ))
                          ) : (
                            <p className="text-sm text-gray-500">Brak tagów w tym scope. Utwórz tagi w zakładce Tagi.</p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleSaveTags(doc.id)}
                            className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg text-sm font-semibold hover:shadow-md transition-all"
                          >
                            Zapisz
                          </button>
                          <button
                            onClick={handleCancelEditTags}
                            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg text-sm font-semibold hover:shadow-md transition-all"
                          >
                            Anuluj
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-2 items-center">
                        <span className="text-sm text-gray-600 font-semibold">Tagi:</span>
                        {doc.tags && doc.tags.length > 0 ? (
                          doc.tags.map((tag) => (
                            <span
                              key={tag.id}
                              className="px-3 py-1 rounded-full text-sm font-semibold text-white"
                              style={{ backgroundColor: tag.color || '#3B82F6' }}
                            >
                              {tag.name}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-gray-400 italic">Brak tagów</span>
                        )}
                        <button
                          onClick={() => handleEditTags(doc.id, doc.tags)}
                          className="ml-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-semibold hover:bg-blue-200 transition-all"
                        >
                          Edytuj tagi
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => onDeleteDocument(doc.id)}
                    className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    Usuń
                  </button>
                </div>
              </div>
            </div>
          ))}
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

// Tags Component
interface TagsProps {
  scopes: Array<{
    id: string
    name: string
  }>
  tags: Tag[]
  selectedScope: string | null
  onSelectScope: (scopeId: string) => void
  onCreateTag: (scopeId: string, data: TagCreate) => Promise<boolean>
  onUpdateTag: (scopeId: string, tagId: string, data: TagCreate) => Promise<boolean>
  onDeleteTag: (scopeId: string, tagId: string) => Promise<boolean>
}

function Tags({
  scopes,
  tags,
  selectedScope,
  onSelectScope,
  onCreateTag,
  onUpdateTag,
  onDeleteTag,
}: TagsProps) {
  const [showForm, setShowForm] = useState(false)
  const [editingTag, setEditingTag] = useState<Tag | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [color, setColor] = useState('#3B82F6')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedScope) return

    const tagData: TagCreate = {
      name,
      description: description || null,
      color,
    }

    const success = editingTag
      ? await onUpdateTag(selectedScope, editingTag.id, tagData)
      : await onCreateTag(selectedScope, tagData)

    if (success) {
      setName('')
      setDescription('')
      setColor('#3B82F6')
      setShowForm(false)
      setEditingTag(null)
    }
  }

  const handleEdit = (tag: Tag) => {
    setEditingTag(tag)
    setName(tag.name)
    setDescription(tag.description || '')
    setColor(tag.color || '#3B82F6')
    setShowForm(true)
  }

  const handleCancelEdit = () => {
    setEditingTag(null)
    setName('')
    setDescription('')
    setColor('#3B82F6')
    setShowForm(false)
  }

  const handleDelete = async (tagId: string) => {
    if (!selectedScope) return
    if (!confirm('Czy na pewno chcesz usunąć ten tag?')) return
    await onDeleteTag(selectedScope, tagId)
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Zarządzanie Tagami</h2>

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

      {/* Create/Edit Form */}
      {selectedScope && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-800">
              {tags.length} {tags.length === 1 ? 'Tag' : 'Tagów'}
            </h3>
            <button
              onClick={() => showForm ? handleCancelEdit() : setShowForm(true)}
              className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
            >
              {showForm ? 'Anuluj' : '+ Nowy Tag'}
            </button>
          </div>

          {showForm && (
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                {editingTag ? 'Edytuj Tag' : 'Utwórz Nowy Tag'}
              </h3>
              <form onSubmit={handleSubmit}>
                <div className="mb-4">
                  <label className="block text-gray-700 font-semibold mb-2">Nazwa</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="np. pilne, do przeczytania"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-gray-700 font-semibold mb-2">Opis</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Opis tagu"
                    rows={2}
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-gray-700 font-semibold mb-2">Kolor</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      value={color}
                      onChange={(e) => setColor(e.target.value)}
                      className="h-12 w-20 border border-gray-300 rounded-lg cursor-pointer"
                    />
                    <input
                      type="text"
                      value={color}
                      onChange={(e) => setColor(e.target.value)}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                      placeholder="#3B82F6"
                      pattern="^#[0-9A-Fa-f]{6}$"
                    />
                  </div>
                </div>
                <div className="flex gap-3">
                  <button
                    type="submit"
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200"
                  >
                    {editingTag ? 'Zaktualizuj Tag' : 'Utwórz Tag'}
                  </button>
                  {editingTag && (
                    <button
                      type="button"
                      onClick={handleCancelEdit}
                      className="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200"
                    >
                      Anuluj
                    </button>
                  )}
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Tags List */}
      {selectedScope && tags.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tags.map((tag) => (
            <div
              key={tag.id}
              className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200 border-l-4"
              style={{ borderLeftColor: tag.color || '#3B82F6' }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: tag.color || '#3B82F6' }}
                  />
                  <h3 className="text-xl font-bold text-gray-800">{tag.name}</h3>
                </div>
              </div>

              {tag.description && (
                <p className="text-gray-600 mb-4 text-sm">{tag.description}</p>
              )}

              <div className="text-xs text-gray-400 mb-4">
                Utworzono: {new Date(tag.created_at).toLocaleDateString()}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(tag)}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
                >
                  Edytuj
                </button>
                <button
                  onClick={() => handleDelete(tag.id)}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
                >
                  Usuń
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedScope && tags.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <p className="text-gray-500 text-lg">Brak tagów w tym scope. Utwórz pierwszy!</p>
        </div>
      )}

      {!selectedScope && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <p className="text-gray-500 text-lg">Wybierz scope aby zobaczyć i zarządzać tagami</p>
        </div>
      )}
    </div>
  )
}

export default App
