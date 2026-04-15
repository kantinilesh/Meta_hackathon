'use client'

import { useState, useRef } from 'react'
import { api } from '@/lib/api'
import { CompanyDocument, DocumentType } from '@/types'
import { Upload, FileText, Trash2, Loader2 } from 'lucide-react'

interface DocumentUploaderProps {
  sessionId: string
  documents: CompanyDocument[]
  onDocumentsChange: (docs: CompanyDocument[]) => void
}

const DOC_TYPES: { value: DocumentType; label: string; desc: string }[] = [
  { value: 'financials', label: 'Financials', desc: 'Revenue, profits, liabilities, valuation' },
  { value: 'bylaws', label: 'Bylaws', desc: 'Governance, voting rights, board structure' },
  { value: 'due_diligence', label: 'Due Diligence', desc: 'DD report, findings, risks' },
  { value: 'cap_table', label: 'Cap Table', desc: 'Equity holders, ownership percentages' },
  { value: 'employment', label: 'Employment', desc: 'Key contracts, retention terms' },
  { value: 'ip_assignment', label: 'IP Assignment', desc: 'Intellectual property ownership' },
  { value: 'other', label: 'Other', desc: 'Other prerequisite documents' },
]

export function DocumentUploader({ sessionId, documents, onDocumentsChange }: DocumentUploaderProps) {
  const [uploading, setUploading] = useState(false)
  const [selectedType, setSelectedType] = useState<DocumentType>('financials')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !sessionId) return

    setUploading(true)
    try {
      const { data } = await api.document.upload(file, sessionId, selectedType, true)
      onDocumentsChange([...documents, {
        document_id: data.document_id,
        file_name: data.file_name,
        file_type: data.file_type,
        document_type: data.document_type,
        summary: data.summary,
        key_terms: data.key_terms,
        upload_date: data.upload_date
      }])
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleRemove = (docId: string) => {
    onDocumentsChange(documents.filter(d => d.document_id !== docId))
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-semibold text-slate mb-2">Document Type</label>
        <select 
          value={selectedType} 
          onChange={e => setSelectedType(e.target.value as DocumentType)}
          className="w-full bg-pink-50 border border-pink-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-400 text-charcoal"
        >
          {DOC_TYPES.map(t => (
            <option key={t.value} value={t.value}>{t.label} - {t.desc}</option>
          ))}
        </select>
      </div>

      <div className="border-2 border-dashed border-pink-200 rounded-xl p-6 text-center hover:border-pink-300 transition-colors cursor-pointer" onClick={() => fileInputRef.current?.click()}>
        <input 
          ref={fileInputRef}
          type="file" 
          accept=".pdf,.docx,.txt,.xlsx" 
          onChange={handleUpload}
          className="hidden"
        />
        {uploading ? (
          <Loader2 className="w-8 h-8 animate-spin text-pink-400 mx-auto" />
        ) : (
          <>
            <Upload className="w-8 h-8 text-pink-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate">Click to upload document</p>
            <p className="text-xs text-pink-400 mt-1">PDF, DOCX, TXT, XLSX supported</p>
          </>
        )}
      </div>

      {documents.length > 0 && (
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate">Uploaded Documents</label>
          {documents.map(doc => (
            <div key={doc.document_id} className="flex items-center gap-3 bg-pink-50 border border-pink-100 rounded-lg p-3">
              <FileText className="w-5 h-5 text-pink-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-charcoal truncate">{doc.file_name}</p>
                <p className="text-xs text-pink-500">{doc.document_type}</p>
                {doc.key_terms.length > 0 && (
                  <p className="text-xs text-slate mt-1 truncate">
                    Terms: {doc.key_terms.slice(0, 3).join(', ')}...
                  </p>
                )}
              </div>
              <button onClick={() => handleRemove(doc.document_id)} className="text-slate hover:text-red-500">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}