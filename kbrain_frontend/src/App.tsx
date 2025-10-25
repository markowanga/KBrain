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

  const handleCreateScope = async (name: string, description: string, allowedExtensions: string[]) => {
    const scope = await scopesHook.createScope({
      name,
      description,
      allowed_extensions: allowedExtensions,
      storage_backend: 'local',
    })
    return scope !== null
  }

  const handleUpdateScope = async (scopeId: string, name: string, description: string, allowedExtensions: string[]) => {
    const scope = await scopesHook.updateScope(scopeId, {
      name,
      description,
      allowed_extensions: allowedExtensions,
    })
    return scope !== null
  }

  const handleDeleteScope = async (scopeId: string) => {
    const success = await scopesHook.deleteScope(scopeId)
    if (success && selectedScopeId === scopeId) {
      setSelectedScopeId(null)
    }
  }

  const handleUploadDocument = async (scopeId: string, file: File, tagIds?: string[]) => {
    const doc = await documentsHook.uploadDocument(scopeId, file, tagIds)
    if (doc) {
      // Refresh scopes and statistics after upload
      scopesHook.fetchScopes()
      statisticsHook.fetchGlobalStatistics()
    }
    return doc !== null
  }

  const handleDeleteDocument = async (documentId: string) => {
    const success = await documentsHook.deleteDocument(documentId)
    if (success) {
      // Refresh scopes and statistics after delete
      scopesHook.fetchScopes()
      statisticsHook.fetchGlobalStatistics()
    }
    return success
  }

  const handleDownloadDocument = async (documentId: string, filename: string) => {
    await documentsHook.downloadDocument(documentId, filename)
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            {/* Logo */}
            <svg className="w-10 h-10" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#2563eb" />
                  <stop offset="100%" stopColor="#4f46e5" />
                </linearGradient>
              </defs>
              {/* Brain shape */}
              <path d="M50 15 C35 15 25 25 25 35 C20 35 15 40 15 45 C15 50 18 54 22 56 C22 62 25 68 30 72 C35 76 42 78 50 78 C58 78 65 76 70 72 C75 68 78 62 78 56 C82 54 85 50 85 45 C85 40 80 35 75 35 C75 25 65 15 50 15 Z" fill="url(#brainGradient)" stroke="url(#brainGradient)" strokeWidth="2"/>
              {/* Brain folds */}
              <path d="M35 30 Q40 35 35 40" stroke="white" strokeWidth="2" fill="none" opacity="0.6"/>
              <path d="M50 25 Q55 30 50 35" stroke="white" strokeWidth="2" fill="none" opacity="0.6"/>
              <path d="M65 30 Q60 35 65 40" stroke="white" strokeWidth="2" fill="none" opacity="0.6"/>
              <path d="M40 50 Q45 55 40 60" stroke="white" strokeWidth="2" fill="none" opacity="0.6"/>
              <path d="M60 50 Q55 55 60 60" stroke="white" strokeWidth="2" fill="none" opacity="0.6"/>
              {/* Knowledge dots */}
              <circle cx="45" cy="45" r="2" fill="white" opacity="0.8"/>
              <circle cx="55" cy="45" r="2" fill="white" opacity="0.8"/>
              <circle cx="50" cy="55" r="2" fill="white" opacity="0.8"/>
            </svg>
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
              KBrain
            </h1>
          </div>
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
              Scopes
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
                activeTab === 'documents'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Documents
            </button>
            <button
              onClick={() => setActiveTab('tags')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
                activeTab === 'tags'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Tags
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
              Close
            </button>
          </div>
        )}

        {/* Global Scope Selector for Documents and Tags */}
        {(activeTab === 'documents' || activeTab === 'tags') && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="flex items-center gap-4">
              <label className="block text-gray-700 font-semibold whitespace-nowrap">Active Scope:</label>
              <select
                value={selectedScopeId || ''}
                onChange={(e) => handleSelectScope(e.target.value)}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">-- No scope selected --</option>
                {scopesHook.scopes?.scopes.map((scope) => (
                  <option key={scope.id} value={scope.id}>
                    {scope.name}
                  </option>
                ))}
              </select>
              {selectedScopeId && (
                <button
                  onClick={() => setSelectedScopeId(null)}
                  className="px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-all"
                >
                  Clear
                </button>
              )}
            </div>
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
            onUpdateScope={handleUpdateScope}
            onDeleteScope={handleDeleteScope}
          />
        )}
        {!loading && activeTab === 'documents' && (
          <Documents
            documents={documentsHook.documents?.documents || []}
            tags={tagsHook.tags || []}
            selectedScope={selectedScopeId}
            onUploadDocument={handleUploadDocument}
            onDeleteDocument={handleDeleteDocument}
            onDownloadDocument={handleDownloadDocument}
          />
        )}
        {!loading && activeTab === 'tags' && (
          <Tags
            tags={tagsHook.tags || []}
            selectedScope={selectedScopeId}
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
        <p className="text-gray-500 text-lg">Loading statistics...</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="All Scopes"
          value={statistics.total_scopes || 0}
          color="blue"
        />
        <StatCard
          title="All Documents"
          value={statistics.total_documents || 0}
          color="indigo"
        />
        <StatCard
          title="Total Size"
          value={formatBytes(statistics.total_size || 0)}
          color="purple"
        />
      </div>

      {statistics.documents_by_status && (
        <div className="mt-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Document Status</h3>
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
          <h3 className="text-xl font-bold text-gray-800 mb-4">Documents by Extension</h3>
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
    allowed_extensions: string[]
    document_count: number
    total_size: number
  }>
  onCreateScope: (name: string, description: string, allowedExtensions: string[]) => Promise<boolean>
  onUpdateScope: (scopeId: string, name: string, description: string, allowedExtensions: string[]) => Promise<boolean>
  onDeleteScope: (scopeId: string) => Promise<void>
}

function Scopes({ scopes, onCreateScope, onUpdateScope, onDeleteScope }: ScopesProps) {
  const [showForm, setShowForm] = useState(false)
  const [editingScope, setEditingScope] = useState<{ id: string; name: string; description: string | null; allowed_extensions: string[] } | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedExtensions, setSelectedExtensions] = useState<string[]>(['pdf', 'docx', 'txt'])
  const [customExtension, setCustomExtension] = useState('')

  // Common file extensions
  const commonExtensions = [
    'pdf', 'doc', 'docx', 'txt', 'rtf',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
    'xlsx', 'xls', 'csv',
    'pptx', 'ppt',
    'zip', 'rar', '7z',
    'mp4', 'avi', 'mov',
    'mp3', 'wav',
  ]

  const toggleExtension = (ext: string) => {
    setSelectedExtensions(prev =>
      prev.includes(ext)
        ? prev.filter(e => e !== ext)
        : [...prev, ext]
    )
  }

  const addCustomExtension = () => {
    const ext = customExtension.trim().toLowerCase().replace(/^\./, '')
    if (ext && !selectedExtensions.includes(ext)) {
      setSelectedExtensions(prev => [...prev, ext])
      setCustomExtension('')
    }
  }

  const removeExtension = (ext: string) => {
    setSelectedExtensions(prev => prev.filter(e => e !== ext))
  }

  const handleEditScope = (scope: typeof scopes[0]) => {
    setEditingScope({
      id: scope.id,
      name: scope.name,
      description: scope.description,
      allowed_extensions: scope.allowed_extensions
    })
    setName(scope.name)
    setDescription(scope.description || '')
    setSelectedExtensions([...scope.allowed_extensions])
    setShowForm(true)
  }

  const handleCancelEdit = () => {
    setEditingScope(null)
    setName('')
    setDescription('')
    setSelectedExtensions(['pdf', 'docx', 'txt'])
    setCustomExtension('')
    setShowForm(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedExtensions.length === 0) {
      alert('Please select at least one file extension')
      return
    }

    const success = editingScope
      ? await onUpdateScope(editingScope.id, name, description, selectedExtensions)
      : await onCreateScope(name, description, selectedExtensions)

    if (success) {
      setEditingScope(null)
      setName('')
      setDescription('')
      setSelectedExtensions(['pdf', 'docx', 'txt'])
      setCustomExtension('')
      setShowForm(false)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-gray-800">Scope Management</h2>
        <button
          onClick={() => showForm ? handleCancelEdit() : setShowForm(true)}
          className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
        >
          {showForm ? 'Cancel' : '+ New Scope'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">
            {editingScope ? 'Edit Scope' : 'Create New Scope'}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 font-semibold mb-2">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g. Project Documents"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 font-semibold mb-2">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Scope description"
                rows={3}
              />
            </div>

            {/* File Extensions Selection */}
            <div className="mb-4">
              <label className="block text-gray-700 font-semibold mb-2">Allowed File Extensions *</label>

              {/* Selected Extensions */}
              <div className="mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-sm text-gray-600 mb-2 font-semibold">Selected Extensions:</div>
                <div className="flex flex-wrap gap-2">
                  {selectedExtensions.length > 0 ? (
                    selectedExtensions.map((ext) => (
                      <span
                        key={ext}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold flex items-center gap-2"
                      >
                        .{ext}
                        <button
                          type="button"
                          onClick={() => removeExtension(ext)}
                          className="text-blue-900 hover:text-red-600 font-bold"
                        >
                          ×
                        </button>
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-400 italic">No extensions selected</span>
                  )}
                </div>
              </div>

              {/* Common Extensions */}
              <div className="mb-3">
                <div className="text-sm text-gray-600 mb-2">Common Extensions:</div>
                <div className="flex flex-wrap gap-2">
                  {commonExtensions.map((ext) => (
                    <button
                      key={ext}
                      type="button"
                      onClick={() => toggleExtension(ext)}
                      className={`px-3 py-1 rounded-full text-sm font-semibold border-2 transition-all ${
                        selectedExtensions.includes(ext)
                          ? 'bg-blue-500 text-white border-blue-500'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                      }`}
                    >
                      .{ext}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Extension Input */}
              <div>
                <div className="text-sm text-gray-600 mb-2">Add Custom Extension:</div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customExtension}
                    onChange={(e) => setCustomExtension(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addCustomExtension()
                      }
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g. xml, json, md"
                  />
                  <button
                    type="button"
                    onClick={addCustomExtension}
                    className="px-4 py-2 bg-gray-500 text-white rounded-lg font-semibold hover:bg-gray-600 transition-all"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200"
            >
              {editingScope ? 'Update Scope' : 'Create Scope'}
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
            <p className="text-gray-600 mb-4">{scope.description || 'No description'}</p>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-500">
                Documents: {scope.document_count || 0}
              </span>
              <span className="text-sm text-gray-500">
                {formatBytes(scope.total_size || 0)}
              </span>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => handleEditScope(scope)}
                className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
              >
                Edit
              </button>
              <button
                onClick={() => onDeleteScope(scope.id)}
                className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {scopes.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <p className="text-gray-500 text-lg">No scopes. Create your first one!</p>
        </div>
      )}
    </div>
  )
}

// Documents Component
interface DocumentsProps {
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
  onUploadDocument: (scopeId: string, file: File, tagIds?: string[]) => Promise<boolean>
  onDeleteDocument: (documentId: string) => Promise<boolean>
  onDownloadDocument: (documentId: string, filename: string) => Promise<void>
}

function Documents({
  documents,
  tags,
  selectedScope,
  onUploadDocument,
  onDeleteDocument,
  onDownloadDocument,
}: DocumentsProps) {
  const [file, setFile] = useState<File | null>(null)
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (file && selectedScope) {
      const success = await onUploadDocument(selectedScope, file, selectedTagIds)
      if (success) {
        setFile(null)
        setSelectedTagIds([])
        ;(e.target as HTMLFormElement).reset()
      }
    }
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
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Document Management</h2>

      {/* Upload Form */}
      {selectedScope && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Upload Document</h3>
          <form onSubmit={handleUpload}>
            <div className="mb-4">
              <input
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Tag Selection */}
            {tags.length > 0 && (
              <div className="mb-4">
                <label className="block text-gray-700 font-semibold mb-2">Select Tags (optional)</label>
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => toggleTagSelection(tag.id)}
                      className={`px-3 py-1 rounded-full text-sm font-semibold border-2 transition-all ${
                        selectedTagIds.includes(tag.id)
                          ? 'bg-blue-500 text-white border-blue-500'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                      }`}
                      style={{
                        backgroundColor: selectedTagIds.includes(tag.id) ? tag.color : undefined,
                        borderColor: selectedTagIds.includes(tag.id) ? tag.color : undefined
                      }}
                    >
                      {tag.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={!file}
              className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Upload Document
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
                    <span>Size: {formatBytes(doc.file_size)}</span>
                    <span>Date: {new Date(doc.upload_date).toLocaleDateString()}</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(doc.status)}`}>
                      {doc.status}
                    </span>
                  </div>

                  {/* Tags Display (Read-Only) */}
                  <div className="mt-3">
                    <div className="flex flex-wrap gap-2 items-center">
                      <span className="text-sm text-gray-600 font-semibold">Tags:</span>
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
                        <span className="text-sm text-gray-400 italic">No tags</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => onDownloadDocument(doc.id, doc.original_name)}
                    className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    Download
                  </button>
                  <button
                    onClick={() => onDeleteDocument(doc.id)}
                    className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedScope && documents.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <p className="text-gray-500 text-lg">No documents in this scope. Upload your first one!</p>
        </div>
      )}

      {!selectedScope && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <div className="max-w-md mx-auto">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-gray-500 text-lg font-semibold mb-2">No Scope Selected</p>
            <p className="text-gray-400 text-sm">Please select a scope from the dropdown above to manage documents</p>
          </div>
        </div>
      )}
    </div>
  )
}

// Tags Component
interface TagsProps {
  tags: Tag[]
  selectedScope: string | null
  onCreateTag: (scopeId: string, data: TagCreate) => Promise<boolean>
  onUpdateTag: (scopeId: string, tagId: string, data: TagCreate) => Promise<boolean>
  onDeleteTag: (scopeId: string, tagId: string) => Promise<boolean>
}

function Tags({
  tags,
  selectedScope,
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
    if (!confirm('Are you sure you want to delete this tag?')) return
    await onDeleteTag(selectedScope, tagId)
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Tag Management</h2>

      {/* Create/Edit Form */}
      {selectedScope && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-800">
              {tags.length} {tags.length === 1 ? 'Tag' : 'Tags'}
            </h3>
            <button
              onClick={() => showForm ? handleCancelEdit() : setShowForm(true)}
              className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
            >
              {showForm ? 'Cancel' : '+ New Tag'}
            </button>
          </div>

          {showForm && (
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                {editingTag ? 'Edit Tag' : 'Create New Tag'}
              </h3>
              <form onSubmit={handleSubmit}>
                <div className="mb-4">
                  <label className="block text-gray-700 font-semibold mb-2">Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g. urgent, to read"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-gray-700 font-semibold mb-2">Description</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Tag description"
                    rows={2}
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-gray-700 font-semibold mb-2">Color</label>
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
                    {editingTag ? 'Update Tag' : 'Create Tag'}
                  </button>
                  {editingTag && (
                    <button
                      type="button"
                      onClick={handleCancelEdit}
                      className="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg font-semibold shadow-md hover:shadow-lg transition-all duration-200"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Tags List */}
      {tags.length > 0 && (
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
                Created: {new Date(tag.created_at).toLocaleDateString()}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(tag)}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(tag.id)}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-semibold hover:shadow-md transition-all duration-200 hover:scale-105"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {tags.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <p className="text-gray-500 text-lg">No tags in this scope. Create your first one!</p>
        </div>
      )}

      {!selectedScope && (
        <div className="text-center py-12 bg-white rounded-xl shadow-lg">
          <div className="max-w-md mx-auto">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <p className="text-gray-500 text-lg font-semibold mb-2">No Scope Selected</p>
            <p className="text-gray-400 text-sm">Please select a scope from the dropdown above to manage tags</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
