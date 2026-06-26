import React from 'react';
import { Document } from '../../types';
import { getFileTypeIcon, getIngestMethodIcon } from '../../utils/fileTypeIcons';
import { Calendar } from 'lucide-react';

interface DocumentListProps {
  documents: Document[];
}

const DocumentList: React.FC<DocumentListProps> = ({ documents }) => {
  if (documents.length === 0) {
    return (
      <div className="empty-state-container">
        <p className="empty-text">No audit documents ingested yet.</p>
        <span className="empty-subtext">Upload files above to begin auditing.</span>
      </div>
    );
  }

  return (
    <div className="document-list">
      {documents.map((doc) => {
        const FileIcon = getFileTypeIcon(doc.file_type);
        const MethodIcon = getIngestMethodIcon(doc.ingestion_method);
        const dateStr = new Date(doc.created_at).toLocaleDateString();

        return (
          <div key={doc.id} className="document-card glass glass-interactive">
            <div className="document-icon-wrapper">
              <FileIcon size={18} className="doc-type-icon" />
            </div>
            
            <div className="document-details">
              <span className="document-filename" title={doc.filename}>{doc.filename}</span>
              <div className="document-meta">
                <span className="meta-item flex-center">
                  <MethodIcon size={12} className="meta-icon" />
                  {doc.ingestion_method}
                </span>
                <span className="meta-item flex-center">
                  <Calendar size={12} className="meta-icon" />
                  {dateStr}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DocumentList;
