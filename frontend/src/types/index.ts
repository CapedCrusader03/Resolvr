export interface Transaction {
  id: string;
  source_doc_id: string;
  merchant: string | null;
  transaction_date: string | null;
  total_amount: number | null;
  line_items: string[] | null;
  category: string | null;
  confidence_score: number;
  is_duplicate: boolean;
  reconciliation_status: 'matched' | 'unmatched' | 'flagged';
  ingestion_method: string;
  page_number: number | null;
  row_number: number | null;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  ingestion_method: string;
  created_at: string;
}

export interface Anomaly {
  id: string;
  transaction_id: string;
  anomaly_type: 'math_mismatch' | 'potential_duplicate' | 'low_confidence';
  description: string;
  severity: 'low' | 'medium' | 'high';
  is_resolved: boolean;
  resolution_details: string | null;
}

export interface Citation {
  source_doc_id: string;
  filename: string;
  page_number: number | null;
  row_number: number | null;
  confidence: number;
}

export interface Thought {
  node: string;
  type: 'thought' | 'action' | 'observation';
  content: string;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: Citation[];
  thoughtLog?: Thought[];
  calculationResult?: number;
}

export interface IngestProgress {
  status: 'processing' | 'done' | 'error';
  file: string;
  doc_id?: string;
  transactions_found?: number;
  message?: string;
}
