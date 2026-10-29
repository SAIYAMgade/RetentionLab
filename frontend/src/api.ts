const API_BASE = "http://localhost:8000";

export interface SystemSummary {
  total_pipelines: number;
  active_pipelines: number;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  failure_rate_percent: number;
  total_records_ingested: number;
  total_records_rejected: number;
  recent_incidents: Array<{
    run_id: string;
    pipeline_name: string;
    error_category: string;
    error_message: string;
    failed_at: string;
    failing_stage: string;
    recommended_steps: string[];
  }>;
}

export interface DataSource {
  id: string;
  name: string;
  source_type: string;
  config_json: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

export interface Pipeline {
  id: string;
  name: string;
  description?: string;
  source_id: string;
  target_table: string;
  schedule: string;
  batch_fail_policy: string;
  is_active: boolean;
  created_at: string;
}

export interface RunStage {
  id: string;
  stage_name: string;
  status: string;
  records_in: number;
  records_out: number;
  duration_ms: number;
  details_json: Record<string, any>;
  started_at: string;
  completed_at?: string;
}

export interface FailureDiagnostic {
  id: string;
  failing_stage: string;
  error_category: string;
  facts: string[];
  possible_causes: string[];
  recommended_steps: string[];
  created_at: string;
}

export interface PipelineRun {
  id: string;
  pipeline_id: string;
  trigger_type: string;
  status: string;
  records_extracted: number;
  records_transformed: number;
  records_rejected: number;
  records_loaded: number;
  error_message?: string;
  error_category?: string;
  duration_ms: number;
  started_at: string;
  completed_at?: string;
  stages?: RunStage[];
  diagnostics?: FailureDiagnostic;
}

export interface QualityRule {
  id: string;
  dataset_name: string;
  rule_name: string;
  rule_type: string;
  params_json: Record<string, any>;
  severity: string;
  is_active: boolean;
  created_at: string;
}

export interface ValidationResult {
  id: string;
  run_id: string;
  dataset_name: string;
  rule_name: string;
  passed: boolean;
  total_checked: number;
  failed_count: number;
  sample_failures_json: any[];
  execution_time_ms: number;
  created_at: string;
}

export interface SchemaVersion {
  id: string;
  dataset_name: string;
  version: number;
  columns_json: Record<string, { name: string; data_type: string; nullable: boolean; required: boolean }>;
  is_active: boolean;
  created_at: string;
}

export interface SchemaDriftEvent {
  id: string;
  pipeline_id?: string;
  run_id?: string;
  dataset_name: string;
  baseline_version: number;
  drift_type: string;
  severity: string;
  diff_json: Record<string, any>;
  recommended_action: string;
  created_at: string;
}

export interface FailureScenario {
  id: string;
  name: string;
  description: string;
  fault_type: string;
  expected_stage: string;
  expected_category: string;
  recovery_strategy: string;
}

export const api = {
  async getSummary(): Promise<SystemSummary> {
    const res = await fetch(`${API_BASE}/api/metrics/summary`);
    if (!res.ok) throw new Error("Failed to load summary");
    return res.json();
  },

  async getSources(): Promise<DataSource[]> {
    const res = await fetch(`${API_BASE}/api/sources`);
    if (!res.ok) throw new Error("Failed to load sources");
    return res.json();
  },

  async getPipelines(): Promise<Pipeline[]> {
    const res = await fetch(`${API_BASE}/api/pipelines`);
    if (!res.ok) throw new Error("Failed to load pipelines");
    return res.json();
  },

  async triggerPipeline(id: string): Promise<PipelineRun> {
    const res = await fetch(`${API_BASE}/api/pipelines/${id}/run`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to trigger pipeline run");
    return res.json();
  },

  async getRuns(limit = 25): Promise<PipelineRun[]> {
    const res = await fetch(`${API_BASE}/api/runs?limit=${limit}`);
    if (!res.ok) throw new Error("Failed to load runs");
    return res.json();
  },

  async getRunDetails(id: string): Promise<PipelineRun> {
    const res = await fetch(`${API_BASE}/api/runs/${id}`);
    if (!res.ok) throw new Error("Failed to load run details");
    return res.json();
  },

  async getQualityRules(): Promise<QualityRule[]> {
    const res = await fetch(`${API_BASE}/api/quality/rules`);
    if (!res.ok) throw new Error("Failed to load quality rules");
    return res.json();
  },

  async getValidationResults(limit = 30): Promise<ValidationResult[]> {
    const res = await fetch(`${API_BASE}/api/quality/results?limit=${limit}`);
    if (!res.ok) throw new Error("Failed to load validation results");
    return res.json();
  },

  async getSchemas(): Promise<SchemaVersion[]> {
    const res = await fetch(`${API_BASE}/api/schemas`);
    if (!res.ok) throw new Error("Failed to load schemas");
    return res.json();
  },

  async getDriftEvents(): Promise<SchemaDriftEvent[]> {
    const res = await fetch(`${API_BASE}/api/schemas/drift`);
    if (!res.ok) throw new Error("Failed to load schema drift events");
    return res.json();
  },

  async getFailureScenarios(): Promise<FailureScenario[]> {
    const res = await fetch(`${API_BASE}/api/failure-lab/scenarios`);
    if (!res.ok) throw new Error("Failed to load failure scenarios");
    return res.json();
  },

  async triggerScenario(scenarioId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/failure-lab/trigger`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId }),
    });
    if (!res.ok) throw new Error("Failed to execute failure lab scenario");
    return res.json();
  },
};
