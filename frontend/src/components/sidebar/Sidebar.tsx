import React from 'react';
import FileUploader from './FileUploader';
import DocumentList from './DocumentList';
import { Document } from '../../types';

interface SidebarProps {
  activeSession: string | null;
  documents: Document[];
  refreshDocuments: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  activeSession,
  documents,
  refreshDocuments,
}) => {
  return (
    <aside className="app-sidebar">
      {/* File Ingestion Dropzone */}
      <div className="sidebar-section">
        <h3 className="section-title">Upload Audit Docs</h3>
        <FileUploader 
          activeSession={activeSession} 
          onIngestSuccess={refreshDocuments}
        />
      </div>
      
      {/* Ingested Documents List */}
      <div className="sidebar-section flex-1 overflow-y-auto">
        <div className="section-header">
          <h3 className="section-title">Parsed Documents ({documents.length})</h3>
        </div>
        <DocumentList documents={documents} />
      </div>
    </aside>
  );
};

export default Sidebar;
