/** TypeScript interfaces matching Django models across specs + sources apps. */

// ---------------------------------------------------------------------------
// Form Specification Models (specs app)
// ---------------------------------------------------------------------------

export interface TaxForm {
  id: string;
  jurisdiction: string;
  form_number: string;
  form_title: string;
  entity_types: string[];
  tax_year: number;
  version: number;
  status: "draft" | "review" | "approved" | "archived";
  notes: string;
  created_at: string;
  updated_at: string;
  // List extras
  fact_count?: number;
  rule_count?: number;
  // Detail nested data
  facts?: FormFact[];
  rules?: FormRule[];
  lines?: FormLine[];
  diagnostics?: FormDiagnostic[];
  test_scenarios?: TestScenario[];
}

export interface FormFact {
  id: string;
  tax_form: string;
  fact_key: string;
  label: string;
  data_type: "string" | "integer" | "decimal" | "boolean" | "date" | "choice";
  required: boolean;
  default_value: string | null;
  validation_rule: string | null;
  choices: unknown[] | null;
  sort_order: number;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface FormRule {
  id: string;
  tax_form: string;
  rule_id: string;
  title: string;
  description: string;
  rule_type: "calculation" | "classification" | "routing" | "validation" | "conditional";
  conditions: Record<string, unknown>;
  formula: string;
  inputs: string[];
  outputs: string[];
  precedence: number;
  exceptions: string;
  notes: string;
  sort_order: number;
  authority_link_count?: number;
  created_at: string;
  updated_at: string;
}

export interface FormLine {
  id: string;
  tax_form: string;
  line_number: string;
  description: string;
  calculation: string;
  source_facts: string[];
  source_rules: string[];
  destination_form: string | null;
  line_type: "input" | "calculated" | "subtotal" | "total" | "informational";
  notes: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface FormDiagnostic {
  id: string;
  tax_form: string;
  diagnostic_id: string;
  title: string;
  severity: "error" | "warning" | "info";
  condition: string;
  message: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface TestScenario {
  id: string;
  tax_form: string;
  scenario_name: string;
  scenario_type: "normal" | "edge" | "failure";
  inputs: Record<string, unknown>;
  expected_outputs: Record<string, unknown>;
  notes: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Authority Source Models (sources app)
// ---------------------------------------------------------------------------

export type SourceType =
  | "code_section" | "regulation" | "official_form" | "official_instruction"
  | "official_publication" | "official_notice" | "official_revenue_ruling"
  | "official_revenue_procedure" | "mef_schema" | "mef_business_rule"
  | "mef_release_memo" | "state_statute" | "state_regulation" | "state_form"
  | "state_instruction" | "state_efile_spec" | "state_vendor_guide"
  | "state_conformity_notice" | "internal_memo" | "internal_example"
  | "internal_test_case";

export type SourceRank =
  | "controlling" | "primary_official" | "implementation_official"
  | "internal_interpretation" | "reference_only";

export type SourceStatus = "active" | "superseded" | "draft" | "archived";

export interface AuthoritySource {
  id: string;
  source_code: string;
  source_type: SourceType;
  source_rank: SourceRank;
  jurisdiction_code: string;
  tax_year_start: number | null;
  tax_year_end: number | null;
  entity_type_code: string | null;
  title: string;
  citation: string | null;
  issuer: string;
  official_url: string | null;
  publication_date: string | null;
  effective_date_start: string | null;
  effective_date_end: string | null;
  superseded_by: string | null;
  current_status: SourceStatus;
  checksum_sha256: string | null;
  is_substantive_authority: boolean;
  is_filing_authority: boolean;
  is_internal_only: boolean;
  requires_human_review: boolean;
  trust_score: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  // List extras
  excerpt_count?: number;
  topics?: string[];
  // Detail nested
  excerpts?: AuthorityExcerpt[];
  versions?: AuthorityVersion[];
}

export interface AuthorityExcerpt {
  id: string;
  authority_source: string;
  excerpt_label: string | null;
  location_reference: string | null;
  excerpt_text: string;
  summary_text: string | null;
  topic_tags: string[];
  line_or_page_start: string | null;
  line_or_page_end: string | null;
  effective_year_start: number | null;
  effective_year_end: number | null;
  is_key_excerpt: boolean;
  created_at: string;
  // Search extras
  source_code?: string;
  source_title?: string;
  source_rank?: string;
}

export interface AuthorityTopic {
  id: string;
  topic_code: string;
  topic_name: string;
  parent_topic: string | null;
  description: string | null;
}

export interface AuthorityVersion {
  id: string;
  authority_source: string;
  version_label: string;
  version_date: string | null;
  retrieval_url: string | null;
  retrieval_timestamp: string | null;
  file_type: string;
  file_path: string | null;
  checksum_sha256: string | null;
  is_current: boolean;
  created_at: string;
}

export interface RuleAuthorityLink {
  id: string;
  form_rule: string;
  authority_source: string;
  authority_excerpt: string | null;
  support_level: "primary" | "secondary" | "interpretive" | "implementation";
  relevance_note: string | null;
  sort_order: number;
  created_at: string;
  // Read extras
  source_code?: string;
  source_title?: string;
  excerpt_label?: string | null;
}

export interface JurisdictionConformitySource {
  id: string;
  jurisdiction_code: string;
  tax_year: number;
  federal_reference_note: string | null;
  conformity_type: "rolling" | "static" | "partial" | "decoupled";
  authority_source: string | null;
  summary: string | null;
  decoupled_items: unknown[];
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceFeedDefinition {
  id: string;
  feed_code: string;
  feed_name: string;
  jurisdiction_code: string;
  source_family: string;
  base_url: string | null;
  feed_type: "html_index" | "pdf_list" | "xml_repo" | "manual_upload";
  refresh_frequency: string;
  parser_strategy: string;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// DRF paginated response wrapper
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
