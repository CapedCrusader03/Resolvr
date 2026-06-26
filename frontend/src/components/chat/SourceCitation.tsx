import React from 'react';
import { Citation } from '../../types';
import { getFileTypeIcon } from '../../utils/fileTypeIcons';
import { Link2, Award } from 'lucide-react';

interface SourceCitationProps {
  citation: Citation;
}

const SourceCitation: React.FC<SourceCitationProps> = ({ citation }) => {
  const fileExtension = citation.filename.substring(citation.filename.lastIndexOf('.'));
  const FileIcon = getFileTypeIcon(fileExtension);
  
  return (
    <div className="citation-card glass glass-interactive">
      <div className="citation-header">
        <FileIcon size={14} className="citation-file-icon" />
        <span className="citation-filename" title={citation.filename}>
          {citation.filename}
        </span>
      </div>
      
      <div className="citation-meta">
        {citation.page_number !== null && citation.page_number !== undefined && (
          <span className="citation-badge">Page {citation.page_number}</span>
        )}
        {citation.row_number !== null && citation.row_number !== undefined && (
          <span className="citation-badge">Row {citation.row_number}</span>
        )}
        <span className="citation-badge confidence-badge flex-center">
          <Award size={10} className="badge-icon" />
          {Math.round(citation.confidence * 100)}%
        </span>
      </div>
      
      {/* clickable link trigger */}
      <a 
        href={`file://${citation.filename}`} 
        onClick={(e) => {
          e.preventDefault();
          alert(`Opening document: ${citation.filename}`);
        }}
        className="citation-link flex-center"
      >
        <Link2 size={12} className="link-icon" />
        View Source
      </a>
    </div>
  );
};

export default SourceCitation;
