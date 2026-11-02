export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  organization?: {
    id: string;
    name: string;
    slug: string;
  };
  role: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface DocumentSummary {
  id: string;
  organization_id: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  file_hash_sha256?: string;
  status: "UPLOADED" | "PROCESSING" | "COMPLETED" | "FAILED" | "NEEDS_REVIEW" | "APPROVED" | "REJECTED";
  document_type: string;
  confidence: number;
  created_at: string;
  updated_at: string;
  error_message?: string;
  supplier_name?: string;
  invoice_number?: string;
  grand_total?: number;
}

export interface InvoiceLineItem {
  id?: string;
  line_number: number;
  description: string;
  hsn_sac?: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount: number;
  tax_rate: number;
  tax_amount: number;
  line_total: number;
}

export interface Invoice {
  id: string;
  document_id: string;
  organization_id: string;
  invoice_number: string;
  invoice_date: string;
  due_date?: string;
  supplier_id?: string;
  supplier_name_raw?: string;
  supplier_gstin_raw?: string;
  supplier_address_raw?: string;
  customer_name_raw?: string;
  customer_gstin_raw?: string;
  customer_address_raw?: string;
  currency: string;
  subtotal: number;
  taxable_amount: number;
  cgst: number;
  sgst: number;
  igst: number;
  total_tax: number;
  discount: number;
  other_charges: number;
  grand_total: number;
  payment_terms?: string;
  purchase_order_number?: string;
  status: string;
  line_items: InvoiceLineItem[];
}

export interface ExtractedField {
  id: string;
  field_name: string;
  field_value?: string;
  confidence: number;
  source_page: number;
  evidence_text?: string;
  is_corrected: boolean;
}

export interface DocumentPage {
  id: string;
  page_number: number;
  extracted_text: string;
  ocr_engine: string;
  confidence: number;
  page_metadata?: Record<string, any>;
}

export interface ValidationErrorItem {
  field: string;
  message: string;
  code: string;
  expected?: string;
  actual?: string;
}

export interface ValidationWarningItem {
  field: string;
  message: string;
  code: string;
}

export interface ValidationResult {
  id: string;
  document_id: string;
  invoice_id?: string;
  status: "PASSED" | "WARNING" | "FAILED";
  is_valid: boolean;
  errors: ValidationErrorItem[];
  warnings: ValidationWarningItem[];
  field_explanations: Record<string, any>;
}

export interface DuplicateMatch {
  id: string;
  matched_document_id: string;
  match_type: string;
  match_score: number;
  match_details: Record<string, any>;
  is_confirmed: boolean;
}

export interface AnomalyFinding {
  id: string;
  anomaly_type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  description: string;
  details: Record<string, any>;
}

export interface AgentExecution {
  id: string;
  document_id: string;
  agent_name: string;
  status: string;
  latency_ms: number;
  tokens_used: number;
  cost_usd: number;
  created_at: string;
  error_message?: string;
  input_payload?: Record<string, any>;
  output_payload?: Record<string, any>;
}

export interface ExportRecord {
  id: string;
  export_type: string;
  format: string;
  record_count: number;
  file_path: string;
  created_at: string;
}

export interface DocumentDetail extends DocumentSummary {
  file_path: string;
  pages: DocumentPage[];
  extracted_fields: ExtractedField[];
  invoice?: Invoice;
  validations: ValidationResult[];
  duplicates: DuplicateMatch[];
  anomalies: AnomalyFinding[];
  agent_executions: AgentExecution[];
}

export interface DocumentListResponse {
  items: DocumentSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApprovalRequest {
  id: string;
  document_id: string;
  invoice_id?: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "REPROCESSING_REQUESTED";
  priority: "LOW" | "NORMAL" | "HIGH" | "URGENT";
  created_at: string;
  updated_at: string;
  document?: DocumentSummary;
  invoice?: Invoice;
  history?: Array<{
    id: string;
    reviewer_name?: string;
    action: string;
    comments?: string;
    created_at: string;
  }>;
}

export interface Supplier {
  id: string;
  name: string;
  gstin?: string;
  pan?: string;
  address?: string;
  city?: string;
  state?: string;
  country: string;
  email?: string;
  phone?: string;
  total_spend: number;
  invoice_count: number;
  created_at: string;
}

export interface AgentStatusSummary {
  agent_id: string;
  name: string;
  purpose: string;
  status: "ACTIVE" | "IDLE" | "ERROR";
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  avg_latency_ms: number;
  last_execution_at?: string;
  last_error?: string;
}

export interface DashboardMetrics {
  total_documents: number;
  total_invoices: number;
  processed_documents: number;
  pending_approvals: number;
  failed_documents: number;
  duplicate_warnings: number;
  total_invoice_value: number;
  currency: string;
  monthly_expense_trend: Array<{ month: string; total: number; tax: number; count: number }>;
  processing_status_distribution: Array<{ name: string; value: number }>;
  document_type_distribution: Array<{ name: string; value: number }>;
  recent_activity: Array<{ id: string; action: string; entity: string; timestamp: string; details: any }>;
}
