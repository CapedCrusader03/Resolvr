import { FileText, FileSpreadsheet, Eye } from 'lucide-react';
import React from 'react';

export const getFileTypeIcon = (fileType: string): React.ComponentType<any> => {
  const ext = fileType.toLowerCase();
  if (ext === '.pdf') {
    return FileText;
  }
  if (ext === '.xlsx' || ext === '.xls' || ext === '.csv') {
    return FileSpreadsheet;
  }
  if (ext === '.txt' || ext === '.md') {
    return FileText;
  }
  return FileSpreadsheet;
};

export const getIngestMethodIcon = (method: string): React.ComponentType<any> => {
  const lower = method.toLowerCase();
  if (lower === 'vision' || lower === 'ocr') {
    return Eye;
  }
  return FileText;
};
