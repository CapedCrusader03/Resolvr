import React, { useRef, useState } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, Loader } from 'lucide-react';
import { useIngest } from '../../hooks/useIngest';

interface FileUploaderProps {
  activeSession: string | null;
  onIngestSuccess: () => void;
}

const FileUploader: React.FC<FileUploaderProps> = ({
  activeSession,
  onIngestSuccess,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const { uploadFiles, isUploading, progress, error } = useIngest(activeSession, onIngestSuccess);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const filesArray = Array.from(e.dataTransfer.files);
      uploadFiles(filesArray);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const filesArray = Array.from(e.target.files);
      uploadFiles(filesArray);
    }
  };

  const triggerInputClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="uploader-container">
      <div 
        className={`dropzone ${isDragActive ? 'active' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={isUploading ? undefined : triggerInputClick}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange}
          multiple 
          accept=".pdf,.xlsx,.xls,.csv,.txt,.md"
          className="hidden-file-input"
          disabled={isUploading}
        />
        
        {isUploading ? (
          <div className="dropzone-status">
            <Loader className="animate-spin text-accent" size={32} />
            <p className="status-text">Ingesting files...</p>
          </div>
        ) : (
          <div className="dropzone-status">
            <UploadCloud className="upload-icon" size={32} />
            <p className="status-text">Drag & drop files or click to browse</p>
            <span className="file-types-hint">PDF, Excel, CSV, TXT, MD</span>
          </div>
        )}
      </div>

      {/* Uploading progress list */}
      {Object.keys(progress).length > 0 && (
        <div className="progress-list">
          {Object.entries(progress).map(([filename, prog]) => (
            <div key={filename} className="progress-item">
              <div className="progress-info">
                <span className="progress-filename" title={filename}>{filename}</span>
                {prog.status === 'processing' && (
                  <span className="progress-badge processing">Processing</span>
                )}
                {prog.status === 'done' && (
                  <span className="progress-badge done flex-center">
                    <CheckCircle2 size={12} className="mr-1" /> Found {prog.transactions_found} tx
                  </span>
                )}
                {prog.status === 'error' && (
                  <span className="progress-badge error flex-center" title={prog.message}>
                    <AlertCircle size={12} className="mr-1" /> Error
                  </span>
                )}
              </div>
              <div className="progress-bar-bg">
                <div 
                  className={`progress-bar-fill ${prog.status}`} 
                  style={{ width: prog.status === 'done' ? '100%' : '50%' }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {error && <div className="uploader-error">{error}</div>}
    </div>
  );
};

export default FileUploader;
