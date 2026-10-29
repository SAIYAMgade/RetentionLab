import { useState, useEffect } from "react";
import { api } from "./api";
import type {
  SystemSummary,
  Pipeline,
  PipelineRun,
  QualityRule,
  ValidationResult,
  SchemaVersion,
  SchemaDriftEvent,
  FailureScenario,
} from "./api";

type Tab =
  | "overview"
  | "pipelines"
  | "runs"
  | "quality"
  | "schema"
  | "failure-lab"
  | "observability"
  | "settings";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [summary, setSummary] = useState<SystemSummary | null>(null);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<PipelineRun | null>(null);
  const [qualityRules, setQualityRules] = useState<QualityRule[]>([]);
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
  const [schemas, setSchemas] = useState<SchemaVersion[]>([]);
  const [driftEvents, setDriftEvents] = useState<SchemaDriftEvent[]>([]);
  const [scenarios, setScenarios] = useState<FailureScenario[]>([]);

  // Action states
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [scenarioResult, setScenarioResult] = useState<any | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumData, pipeData, runData, rulesData, valData, schemaData, driftData, scenData] =
        await Promise.all([
          api.getSummary().catch(() => null),
          api.getPipelines().catch(() => []),
          api.getRuns(30).catch(() => []),
          api.getQualityRules().catch(() => []),
          api.getValidationResults(40).catch(() => []),
          api.getSchemas().catch(() => []),
          api.getDriftEvents().catch(() => []),
          api.getFailureScenarios().catch(() => []),
        ]);

      if (sumData) setSummary(sumData);
      setPipelines(pipeData);
      setRuns(runData);
      setQualityRules(rulesData);
      setValidationResults(valData);
      setSchemas(schemaData);
      setDriftEvents(driftData);
      setScenarios(scenData);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  const handleTriggerPipeline = async (pipeId: string) => {
    try {
      setActionLoading(`pipe_${pipeId}`);
      const newRun = await api.triggerPipeline(pipeId);
      await loadData();
      const detailed = await api.getRunDetails(newRun.id);
      setSelectedRun(detailed);
      setActiveTab("runs");
    } catch (err: any) {
      alert(`Pipeline execution error: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleTriggerScenario = async (scenId: string) => {
    try {
      setActionLoading(`scen_${scenId}`);
      setScenarioResult(null);
      const res = await api.triggerScenario(scenId);
      setScenarioResult(res);
      await loadData();
    } catch (err: any) {
      alert(`Scenario execution error: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewRun = async (runId: string) => {
    try {
      setLoading(true);
      const detailed = await api.getRunDetails(runId);
      setSelectedRun(detailed);
      setActiveTab("runs");
    } catch (err: any) {
      alert(`Failed to load run details: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: "260px",
          backgroundColor: "#111827",
          borderRight: "1px solid #1f2937",
          padding: "24px 16px",
          display: "flex",
          flexDirection: "column",
          gap: "24px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: "#2563eb",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: "bold",
                color: "#fff",
                fontSize: "18px",
              }}
            >
              SF
            </div>
            <div>
              <h1 style={{ fontSize: "18px", fontWeight: "bold", letterSpacing: "0.5px" }}>
                SignalForge
              </h1>
              <p style={{ fontSize: "11px", color: "#9ca3af" }}>Reliability Control Plane</p>
            </div>
          </div>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {[
            { id: "overview", label: "Overview", icon: "📊" },
            { id: "pipelines", label: "Pipelines", icon: "⚡" },
            { id: "runs", label: "Run Details", icon: "⏱️" },
            { id: "quality", label: "Data Quality", icon: "🛡️" },
            { id: "schema", label: "Schema Explorer", icon: "📐" },
            { id: "failure-lab", label: "Failure Lab", icon: "🧪" },
            { id: "observability", label: "Observability", icon: "📈" },
            { id: "settings", label: "Settings", icon: "⚙️" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as Tab)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "10px 14px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: activeTab === item.id ? "#1f2937" : "transparent",
                color: activeTab === item.id ? "#38bdf8" : "#9ca3af",
                fontWeight: activeTab === item.id ? "600" : "400",
                fontSize: "14px",
                textAlign: "left",
              }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div style={{ marginTop: "auto", borderTop: "1px solid #1f2937", paddingTop: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px" }}>
            <span
              style={{
                display: "inline-block",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: "#10b981",
              }}
            />
            <span style={{ color: "#d1d5db" }}>Engine Connected</span>
          </div>
          <p style={{ fontSize: "11px", color: "#6b7280", marginTop: "4px" }}>v0.1.0 (Production Core)</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflowY: "auto" }}>
        {/* Header */}
        <header
          style={{
            height: "64px",
            borderBottom: "1px solid #1f2937",
            padding: "0 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backgroundColor: "#0d131f",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "600", textTransform: "capitalize" }}>
              {activeTab.replace("-", " ")}
            </h2>
            <span
              style={{
                padding: "3px 8px",
                borderRadius: "12px",
                fontSize: "11px",
                fontWeight: "600",
                backgroundColor: "#064e3b",
                color: "#6ee7b7",
              }}
            >
              ACTIVE CLUSTER
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              onClick={loadData}
              disabled={loading}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "1px solid #374151",
                backgroundColor: "#1f2937",
                color: "#e5e7eb",
                fontSize: "13px",
                fontWeight: "500",
              }}
            >
              {loading ? "Refreshing..." : "↻ Refresh Data"}
            </button>
          </div>
        </header>

        {/* Tab Views */}
        <div style={{ padding: "32px", flex: 1 }}>
          {error && (
            <div
              style={{
                padding: "16px",
                backgroundColor: "#450a0a",
                border: "1px solid #991b1b",
                borderRadius: "8px",
                marginBottom: "24px",
                color: "#fca5a5",
                fontSize: "14px",
              }}
            >
              ⚠️ {error}
            </div>
          )}

          {/* 1. OVERVIEW VIEW */}
          {activeTab === "overview" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
              {/* Stat Cards */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: "20px",
                }}
              >
                {[
                  {
                    title: "Active Pipelines",
                    value: summary ? `${summary.active_pipelines} / ${summary.total_pipelines}` : "0 / 0",
                    sub: "Orchestrated ETL Workflows",
                    color: "#38bdf8",
                  },
                  {
                    title: "Total Executions",
                    value: summary ? summary.total_runs.toLocaleString() : "0",
                    sub: `${summary?.successful_runs || 0} Successful Runs`,
                    color: "#34d399",
                  },
                  {
                    title: "Failure Rate",
                    value: summary ? `${summary.failure_rate_percent}%` : "0%",
                    sub: `${summary?.failed_runs || 0} Incident Runs`,
                    color: (summary?.failure_rate_percent || 0) > 10 ? "#f87171" : "#fbbf24",
                  },
                  {
                    title: "Records Processed",
                    value: summary ? summary.total_records_ingested.toLocaleString() : "0",
                    sub: `${summary?.total_records_rejected || 0} Quarantined Records`,
                    color: "#a78bfa",
                  },
                ].map((card, i) => (
                  <div
                    key={i}
                    style={{
                      backgroundColor: "#111827",
                      border: "1px solid #1f2937",
                      borderRadius: "10px",
                      padding: "20px",
                    }}
                  >
                    <p style={{ color: "#9ca3af", fontSize: "13px", fontWeight: "500" }}>{card.title}</p>
                    <p style={{ fontSize: "28px", fontWeight: "bold", margin: "8px 0 4px", color: card.color }}>
                      {card.value}
                    </p>
                    <p style={{ color: "#6b7280", fontSize: "12px" }}>{card.sub}</p>
                  </div>
                ))}
              </div>

              {/* Recent Incident Feed */}
              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "10px",
                  padding: "24px",
                }}
              >
                <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px" }}>
                  Operational Reliability & Incident Feed
                </h3>
                {summary?.recent_incidents && summary.recent_incidents.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {summary.recent_incidents.map((inc, i) => (
                      <div
                        key={i}
                        style={{
                          backgroundColor: "#1c1917",
                          borderLeft: "4px solid #ef4444",
                          padding: "16px",
                          borderRadius: "4px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "8px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontWeight: "600", color: "#fca5a5" }}>
                            {inc.pipeline_name} — Stage: {inc.failing_stage}
                          </span>
                          <span
                            style={{
                              fontSize: "11px",
                              backgroundColor: "#7f1d1d",
                              color: "#fecaca",
                              padding: "2px 8px",
                              borderRadius: "4px",
                            }}
                          >
                            {inc.error_category}
                          </span>
                        </div>
                        <p style={{ fontSize: "13px", color: "#e5e7eb" }}>{inc.error_message}</p>
                        {inc.recommended_steps && inc.recommended_steps.length > 0 && (
                          <div style={{ marginTop: "4px" }}>
                            <p style={{ fontSize: "12px", color: "#a8a29e", fontWeight: "600" }}>
                              Remediation:
                            </p>
                            <p style={{ fontSize: "12px", color: "#d6d3d1" }}>
                              {inc.recommended_steps.join(" ")}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: "#9ca3af", fontSize: "14px" }}>
                    No recent failure incidents recorded. All pipelines operating within SLA.
                  </p>
                )}
              </div>

              {/* Recent Runs Table */}
              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "10px",
                  padding: "24px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                  <h3 style={{ fontSize: "16px", fontWeight: "600" }}>Recent Pipeline Executions</h3>
                  <button
                    onClick={() => setActiveTab("runs")}
                    style={{
                      background: "none",
                      border: "none",
                      color: "#38bdf8",
                      fontSize: "13px",
                      fontWeight: "500",
                    }}
                  >
                    View All Runs →
                  </button>
                </div>

                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #374151", color: "#9ca3af", textAlign: "left" }}>
                      <th style={{ padding: "10px" }}>Run ID</th>
                      <th style={{ padding: "10px" }}>Status</th>
                      <th style={{ padding: "10px" }}>Trigger</th>
                      <th style={{ padding: "10px" }}>Extracted</th>
                      <th style={{ padding: "10px" }}>Loaded</th>
                      <th style={{ padding: "10px" }}>Rejected</th>
                      <th style={{ padding: "10px" }}>Duration</th>
                      <th style={{ padding: "10px" }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.slice(0, 8).map((run) => (
                      <tr key={run.id} style={{ borderBottom: "1px solid #1f2937" }}>
                        <td style={{ padding: "12px 10px", fontFamily: "monospace", color: "#d1d5db" }}>
                          {run.id.slice(0, 8)}...
                        </td>
                        <td style={{ padding: "12px 10px" }}>
                          <span
                            style={{
                              padding: "2px 8px",
                              borderRadius: "10px",
                              fontSize: "11px",
                              fontWeight: "600",
                              backgroundColor:
                                run.status === "COMPLETED"
                                  ? "#064e3b"
                                  : run.status === "FAILED"
                                  ? "#7f1d1d"
                                  : "#1e3a8a",
                              color:
                                run.status === "COMPLETED"
                                  ? "#6ee7b7"
                                  : run.status === "FAILED"
                                  ? "#fca5a5"
                                  : "#93c5fd",
                            }}
                          >
                            {run.status}
                          </span>
                        </td>
                        <td style={{ padding: "12px 10px", color: "#9ca3af" }}>{run.trigger_type}</td>
                        <td style={{ padding: "12px 10px" }}>{run.records_extracted.toLocaleString()}</td>
                        <td style={{ padding: "12px 10px", color: "#34d399" }}>{run.records_loaded.toLocaleString()}</td>
                        <td style={{ padding: "12px 10px", color: run.records_rejected > 0 ? "#f87171" : "#9ca3af" }}>
                          {run.records_rejected}
                        </td>
                        <td style={{ padding: "12px 10px", color: "#9ca3af" }}>{run.duration_ms} ms</td>
                        <td style={{ padding: "12px 10px" }}>
                          <button
                            onClick={() => handleViewRun(run.id)}
                            style={{
                              padding: "4px 10px",
                              backgroundColor: "#374151",
                              border: "none",
                              borderRadius: "4px",
                              color: "#fff",
                              fontSize: "12px",
                            }}
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 2. PIPELINES VIEW */}
          {activeTab === "pipelines" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <input
                  type="text"
                  placeholder="Filter pipelines by name or target..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    padding: "10px 16px",
                    width: "360px",
                    borderRadius: "8px",
                    backgroundColor: "#111827",
                    border: "1px solid #374151",
                    color: "#fff",
                    fontSize: "14px",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
                {pipelines
                  .filter((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase()))
                  .map((pipe) => (
                    <div
                      key={pipe.id}
                      style={{
                        backgroundColor: "#111827",
                        border: "1px solid #1f2937",
                        borderRadius: "10px",
                        padding: "24px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "14px",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div>
                          <h4 style={{ fontSize: "16px", fontWeight: "600", color: "#f9fafb" }}>{pipe.name}</h4>
                          <p style={{ fontSize: "12px", color: "#9ca3af", marginTop: "2px" }}>
                            Target: <span style={{ color: "#38bdf8", fontFamily: "monospace" }}>{pipe.target_table}</span>
                          </p>
                        </div>
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "10px",
                            fontSize: "11px",
                            fontWeight: "600",
                            backgroundColor: pipe.is_active ? "#064e3b" : "#374151",
                            color: pipe.is_active ? "#6ee7b7" : "#9ca3af",
                          }}
                        >
                          {pipe.is_active ? "ACTIVE" : "INACTIVE"}
                        </span>
                      </div>

                      <p style={{ fontSize: "13px", color: "#d1d5db", minHeight: "38px" }}>
                        {pipe.description || "Production ETL pipeline."}
                      </p>

                      <div
                        style={{
                          fontSize: "12px",
                          color: "#9ca3af",
                          backgroundColor: "#0b0f19",
                          padding: "10px",
                          borderRadius: "6px",
                          display: "flex",
                          justifyContent: "space-between",
                        }}
                      >
                        <span>Schedule: <b>{pipe.schedule}</b></span>
                        <span>Policy: <b>{pipe.batch_fail_policy}</b></span>
                      </div>

                      <div style={{ marginTop: "auto", display: "flex", gap: "10px" }}>
                        <button
                          onClick={() => handleTriggerPipeline(pipe.id)}
                          disabled={actionLoading === `pipe_${pipe.id}`}
                          style={{
                            flex: 1,
                            padding: "8px",
                            borderRadius: "6px",
                            border: "none",
                            backgroundColor: "#2563eb",
                            color: "#fff",
                            fontSize: "13px",
                            fontWeight: "500",
                          }}
                        >
                          {actionLoading === `pipe_${pipe.id}` ? "Executing Run..." : "▶ Trigger Run Now"}
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* 3. RUN DETAILS VIEW */}
          {activeTab === "runs" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
              {selectedRun ? (
                <div
                  style={{
                    backgroundColor: "#111827",
                    border: "1px solid #1f2937",
                    borderRadius: "10px",
                    padding: "28px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "24px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <button
                        onClick={() => setSelectedRun(null)}
                        style={{
                          background: "none",
                          border: "none",
                          color: "#38bdf8",
                          fontSize: "13px",
                          marginBottom: "8px",
                        }}
                      >
                        ← Back to all runs
                      </button>
                      <h3 style={{ fontSize: "20px", fontWeight: "bold" }}>
                        Run Inspection: <span style={{ fontFamily: "monospace", color: "#93c5fd" }}>{selectedRun.id}</span>
                      </h3>
                      <p style={{ color: "#9ca3af", fontSize: "13px" }}>
                        Started: {new Date(selectedRun.started_at).toLocaleString()} | Trigger: {selectedRun.trigger_type}
                      </p>
                    </div>

                    <span
                      style={{
                        padding: "6px 14px",
                        borderRadius: "20px",
                        fontSize: "13px",
                        fontWeight: "bold",
                        backgroundColor:
                          selectedRun.status === "COMPLETED"
                            ? "#064e3b"
                            : selectedRun.status === "FAILED"
                            ? "#7f1d1d"
                            : "#1e3a8a",
                        color:
                          selectedRun.status === "COMPLETED"
                            ? "#6ee7b7"
                            : selectedRun.status === "FAILED"
                            ? "#fca5a5"
                            : "#93c5fd",
                      }}
                    >
                      {selectedRun.status}
                    </span>
                  </div>

                  {/* Stage Waterfall Progression */}
                  <div>
                    <h4 style={{ fontSize: "14px", fontWeight: "600", marginBottom: "12px", color: "#d1d5db" }}>
                      Pipeline Stage Execution Waterfall
                    </h4>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "10px" }}>
                      {["EXTRACT", "VALIDATE", "TRANSFORM", "LOAD", "VERIFY"].map((stName) => {
                        const stageData = selectedRun.stages?.find((s) => s.stage_name === stName);
                        const isDone = stageData?.status === "COMPLETED";
                        const isFailed = stageData?.status === "FAILED";

                        return (
                          <div
                            key={stName}
                            style={{
                              backgroundColor: "#0b0f19",
                              border: `1px solid ${isFailed ? "#ef4444" : isDone ? "#10b981" : "#374151"}`,
                              borderRadius: "8px",
                              padding: "14px",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <span style={{ fontSize: "12px", fontWeight: "bold" }}>{stName}</span>
                              <span style={{ fontSize: "11px", color: isFailed ? "#f87171" : isDone ? "#34d399" : "#9ca3af" }}>
                                {stageData?.status || "SKIPPED"}
                              </span>
                            </div>
                            <p style={{ fontSize: "18px", fontWeight: "bold", margin: "8px 0 2px" }}>
                              {stageData ? `${stageData.duration_ms} ms` : "—"}
                            </p>
                            <p style={{ fontSize: "11px", color: "#6b7280" }}>
                              In: {stageData?.records_in || 0} | Out: {stageData?.records_out || 0}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Diagnostic Report Panel if Failed */}
                  {selectedRun.diagnostics && (
                    <div
                      style={{
                        backgroundColor: "#1c1917",
                        border: "1px solid #78350f",
                        borderRadius: "8px",
                        padding: "20px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "14px",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span style={{ fontSize: "20px" }}>🔍</span>
                        <h4 style={{ fontSize: "16px", fontWeight: "bold", color: "#fef08a" }}>
                          Root-Cause Investigation Diagnostic Report
                        </h4>
                      </div>

                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                        <div>
                          <p style={{ fontSize: "12px", fontWeight: "bold", color: "#fbbf24", marginBottom: "6px" }}>
                            EMPIRICAL EVIDENCE (CONFIRMED FACTS)
                          </p>
                          <ul style={{ fontSize: "13px", color: "#e5e7eb", paddingLeft: "18px" }}>
                            {selectedRun.diagnostics.facts.map((fact, idx) => (
                              <li key={idx} style={{ marginBottom: "4px" }}>{fact}</li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <p style={{ fontSize: "12px", fontWeight: "bold", color: "#f87171", marginBottom: "6px" }}>
                            LIKELY ROOT CAUSES
                          </p>
                          <ul style={{ fontSize: "13px", color: "#e5e7eb", paddingLeft: "18px" }}>
                            {selectedRun.diagnostics.possible_causes.map((cause, idx) => (
                              <li key={idx} style={{ marginBottom: "4px" }}>{cause}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      <div style={{ borderTop: "1px solid #44403c", paddingTop: "12px" }}>
                        <p style={{ fontSize: "12px", fontWeight: "bold", color: "#34d399", marginBottom: "6px" }}>
                          RECOMMENDED REMEDIATION ACTIONS
                        </p>
                        <ul style={{ fontSize: "13px", color: "#e5e7eb", paddingLeft: "18px" }}>
                          {selectedRun.diagnostics.recommended_steps.map((step, idx) => (
                            <li key={idx} style={{ marginBottom: "4px" }}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div
                  style={{
                    backgroundColor: "#111827",
                    border: "1px solid #1f2937",
                    borderRadius: "10px",
                    padding: "24px",
                  }}
                >
                  <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px" }}>
                    Execution History (Audit Trail)
                  </h3>

                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid #374151", color: "#9ca3af", textAlign: "left" }}>
                        <th style={{ padding: "10px" }}>Run ID</th>
                        <th style={{ padding: "10px" }}>Status</th>
                        <th style={{ padding: "10px" }}>Trigger</th>
                        <th style={{ padding: "10px" }}>Extracted</th>
                        <th style={{ padding: "10px" }}>Loaded</th>
                        <th style={{ padding: "10px" }}>Rejected</th>
                        <th style={{ padding: "10px" }}>Error Category</th>
                        <th style={{ padding: "10px" }}>Duration</th>
                        <th style={{ padding: "10px" }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runs.map((r) => (
                        <tr key={r.id} style={{ borderBottom: "1px solid #1f2937" }}>
                          <td style={{ padding: "12px 10px", fontFamily: "monospace" }}>{r.id.slice(0, 8)}...</td>
                          <td style={{ padding: "12px 10px" }}>
                            <span
                              style={{
                                padding: "2px 8px",
                                borderRadius: "10px",
                                fontSize: "11px",
                                fontWeight: "600",
                                backgroundColor:
                                  r.status === "COMPLETED" ? "#064e3b" : "#7f1d1d",
                                color: r.status === "COMPLETED" ? "#6ee7b7" : "#fca5a5",
                              }}
                            >
                              {r.status}
                            </span>
                          </td>
                          <td style={{ padding: "12px 10px", color: "#9ca3af" }}>{r.trigger_type}</td>
                          <td style={{ padding: "12px 10px" }}>{r.records_extracted}</td>
                          <td style={{ padding: "12px 10px", color: "#34d399" }}>{r.records_loaded}</td>
                          <td style={{ padding: "12px 10px", color: r.records_rejected > 0 ? "#f87171" : "#9ca3af" }}>
                            {r.records_rejected}
                          </td>
                          <td style={{ padding: "12px 10px", color: "#fbbf24" }}>{r.error_category || "—"}</td>
                          <td style={{ padding: "12px 10px", color: "#9ca3af" }}>{r.duration_ms} ms</td>
                          <td style={{ padding: "12px 10px" }}>
                            <button
                              onClick={() => handleViewRun(r.id)}
                              style={{
                                padding: "4px 10px",
                                backgroundColor: "#374151",
                                border: "none",
                                borderRadius: "4px",
                                color: "#fff",
                                fontSize: "12px",
                              }}
                            >
                              Details
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* 4. DATA QUALITY VIEW */}
          {activeTab === "quality" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "10px",
                  padding: "24px",
                }}
              >
                <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px" }}>
                  Active Data Quality Rules
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
                  {qualityRules.map((rule) => (
                    <div
                      key={rule.id}
                      style={{
                        backgroundColor: "#0b0f19",
                        border: "1px solid #1f2937",
                        borderRadius: "8px",
                        padding: "16px",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontWeight: "600", fontSize: "14px", color: "#38bdf8" }}>
                          {rule.rule_name}
                        </span>
                        <span
                          style={{
                            fontSize: "11px",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor: rule.severity === "BATCH_FAIL" ? "#7f1d1d" : "#78350f",
                            color: rule.severity === "BATCH_FAIL" ? "#fca5a5" : "#fef08a",
                          }}
                        >
                          {rule.severity}
                        </span>
                      </div>
                      <p style={{ fontSize: "12px", color: "#9ca3af", marginTop: "6px" }}>
                        Dataset: <b>{rule.dataset_name}</b> | Type: <b>{rule.rule_type}</b>
                      </p>
                      <pre
                        style={{
                          backgroundColor: "#111827",
                          padding: "8px",
                          borderRadius: "4px",
                          fontSize: "11px",
                          marginTop: "8px",
                          overflowX: "auto",
                        }}
                      >
                        {JSON.stringify(rule.params_json, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>

              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "10px",
                  padding: "24px",
                }}
              >
                <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px" }}>
                  Historical Validation Outcomes
                </h3>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #374151", color: "#9ca3af", textAlign: "left" }}>
                      <th style={{ padding: "10px" }}>Dataset</th>
                      <th style={{ padding: "10px" }}>Rule Name</th>
                      <th style={{ padding: "10px" }}>Status</th>
                      <th style={{ padding: "10px" }}>Checked</th>
                      <th style={{ padding: "10px" }}>Violations</th>
                      <th style={{ padding: "10px" }}>Latency</th>
                      <th style={{ padding: "10px" }}>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {validationResults.slice(0, 15).map((vr) => (
                      <tr key={vr.id} style={{ borderBottom: "1px solid #1f2937" }}>
                        <td style={{ padding: "12px 10px", fontFamily: "monospace" }}>{vr.dataset_name}</td>
                        <td style={{ padding: "12px 10px", fontWeight: "500" }}>{vr.rule_name}</td>
                        <td style={{ padding: "12px 10px" }}>
                          <span
                            style={{
                              padding: "2px 8px",
                              borderRadius: "10px",
                              fontSize: "11px",
                              fontWeight: "600",
                              backgroundColor: vr.passed ? "#064e3b" : "#7f1d1d",
                              color: vr.passed ? "#6ee7b7" : "#fca5a5",
                            }}
                          >
                            {vr.passed ? "PASSED" : "FAILED"}
                          </span>
                        </td>
                        <td style={{ padding: "12px 10px" }}>{vr.total_checked}</td>
                        <td style={{ padding: "12px 10px", color: vr.failed_count > 0 ? "#f87171" : "#34d399" }}>
                          {vr.failed_count}
                        </td>
                        <td style={{ padding: "12px 10px", color: "#9ca3af" }}>{vr.execution_time_ms} ms</td>
                        <td style={{ padding: "12px 10px", color: "#6b7280" }}>
                          {new Date(vr.created_at).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 5. SCHEMA EXPLORER VIEW */}
          {activeTab === "schema" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "10px",
                  padding: "24px",
                }}
              >
                <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px" }}>
                  Active Schema Baseline Contracts
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
                  {schemas.map((s) => (
                    <div
                      key={s.id}
                      style={{
                        backgroundColor: "#0b0f19",
                        border: "1px solid #1f2937",
                        borderRadius: "8px",
                        padding: "18px",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontWeight: "bold", fontSize: "15px", color: "#38bdf8" }}>
                          {s.dataset_name}
                        </span>
                        <span style={{ fontSize: "12px", color: "#10b981", fontWeight: "600" }}>v{s.version}</span>
                      </div>
                      <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
                        {Object.entries(s.columns_json).map(([cName, cMeta]: any) => (
                          <div
                            key={cName}
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              fontSize: "12px",
                              padding: "4px 8px",
                              backgroundColor: "#111827",
                              borderRadius: "4px",
                            }}
                          >
                            <span style={{ fontFamily: "monospace" }}>{cName}</span>
                            <span style={{ color: "#9ca3af" }}>
                              {cMeta.data_type} {cMeta.required && "• Required"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "10px",
                  padding: "24px",
                }}
              >
                <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px" }}>
                  Detected Schema Drift Events
                </h3>
                {driftEvents.length > 0 ? (
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid #374151", color: "#9ca3af", textAlign: "left" }}>
                        <th style={{ padding: "10px" }}>Dataset</th>
                        <th style={{ padding: "10px" }}>Severity</th>
                        <th style={{ padding: "10px" }}>Drift Type</th>
                        <th style={{ padding: "10px" }}>Recommended Remediation</th>
                        <th style={{ padding: "10px" }}>Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {driftEvents.map((de) => (
                        <tr key={de.id} style={{ borderBottom: "1px solid #1f2937" }}>
                          <td style={{ padding: "12px 10px", fontFamily: "monospace" }}>{de.dataset_name}</td>
                          <td style={{ padding: "12px 10px" }}>
                            <span
                              style={{
                                padding: "2px 8px",
                                borderRadius: "10px",
                                fontSize: "11px",
                                fontWeight: "600",
                                backgroundColor:
                                  de.severity === "BREAKING"
                                    ? "#7f1d1d"
                                    : de.severity === "POTENTIALLY_BREAKING"
                                    ? "#78350f"
                                    : "#064e3b",
                                color:
                                  de.severity === "BREAKING"
                                    ? "#fca5a5"
                                    : de.severity === "POTENTIALLY_BREAKING"
                                    ? "#fef08a"
                                    : "#6ee7b7",
                              }}
                            >
                              {de.severity}
                            </span>
                          </td>
                          <td style={{ padding: "12px 10px", color: "#f87171" }}>{de.drift_type}</td>
                          <td style={{ padding: "12px 10px", color: "#d1d5db" }}>{de.recommended_action}</td>
                          <td style={{ padding: "12px 10px", color: "#6b7280" }}>
                            {new Date(de.created_at).toLocaleTimeString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p style={{ color: "#9ca3af", fontSize: "14px" }}>
                    No schema drift detected. All incoming sources match registered baseline versions.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* 6. FAILURE LABORATORY VIEW */}
          {activeTab === "failure-lab" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
              <div
                style={{
                  backgroundColor: "#1e1b4b",
                  border: "1px solid #4338ca",
                  borderRadius: "10px",
                  padding: "20px",
                }}
              >
                <h3 style={{ fontSize: "16px", fontWeight: "bold", color: "#c7d2fe", marginBottom: "4px" }}>
                  🧪 Controlled Failure Injection Laboratory
                </h3>
                <p style={{ fontSize: "13px", color: "#a5b4fc" }}>
                  Deliberately inject reproducible data anomalies, upstream outages, and breaking changes.
                  SignalForge detects the failure, isolates the evidence, records diagnostics, and exercises recovery policies.
                </p>
              </div>

              {/* Execution Feedback Panel */}
              {scenarioResult && (
                <div
                  style={{
                    backgroundColor: "#111827",
                    border: `1px solid ${scenarioResult.status === "FAILED" ? "#ef4444" : "#10b981"}`,
                    borderRadius: "10px",
                    padding: "20px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <h4 style={{ fontSize: "16px", fontWeight: "bold" }}>
                      Scenario Result: {scenarioResult.scenario?.name}
                    </h4>
                    <span
                      style={{
                        padding: "3px 10px",
                        borderRadius: "12px",
                        fontSize: "12px",
                        fontWeight: "bold",
                        backgroundColor: scenarioResult.status === "FAILED" ? "#7f1d1d" : "#064e3b",
                        color: scenarioResult.status === "FAILED" ? "#fca5a5" : "#6ee7b7",
                      }}
                    >
                      {scenarioResult.status} ({scenarioResult.error_category || "COMPLETED"})
                    </span>
                  </div>

                  <p style={{ fontSize: "13px", color: "#e5e7eb", margin: "10px 0" }}>
                    {scenarioResult.error_message || scenarioResult.message}
                  </p>

                  {scenarioResult.diagnostic && (
                    <div style={{ backgroundColor: "#0b0f19", padding: "12px", borderRadius: "6px", fontSize: "12px" }}>
                      <p style={{ color: "#38bdf8", fontWeight: "bold" }}>Remediation Recommendation:</p>
                      <p style={{ color: "#d1d5db" }}>
                        {scenarioResult.diagnostic.recommended_steps?.join(" ")}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Scenarios Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
                {scenarios.map((sc) => (
                  <div
                    key={sc.id}
                    style={{
                      backgroundColor: "#111827",
                      border: "1px solid #1f2937",
                      borderRadius: "10px",
                      padding: "20px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "12px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <h4 style={{ fontSize: "15px", fontWeight: "600", color: "#f9fafb" }}>{sc.name}</h4>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: "bold",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          backgroundColor: "#312e81",
                          color: "#a5b4fc",
                        }}
                      >
                        {sc.fault_type}
                      </span>
                    </div>

                    <p style={{ fontSize: "13px", color: "#9ca3af", minHeight: "42px" }}>{sc.description}</p>

                    <div
                      style={{
                        backgroundColor: "#0b0f19",
                        padding: "10px",
                        borderRadius: "6px",
                        fontSize: "11px",
                        color: "#6b7280",
                        display: "flex",
                        flexDirection: "column",
                        gap: "4px",
                      }}
                    >
                      <div>Expected Stage: <b style={{ color: "#e5e7eb" }}>{sc.expected_stage}</b></div>
                      <div>Expected Category: <b style={{ color: "#f59e0b" }}>{sc.expected_category}</b></div>
                    </div>

                    <button
                      onClick={() => handleTriggerScenario(sc.id)}
                      disabled={actionLoading === `scen_${sc.id}`}
                      style={{
                        marginTop: "auto",
                        padding: "8px",
                        borderRadius: "6px",
                        border: "none",
                        backgroundColor: sc.id.includes("retry") ? "#059669" : "#dc2626",
                        color: "#fff",
                        fontSize: "13px",
                        fontWeight: "600",
                      }}
                    >
                      {actionLoading === `scen_${sc.id}` ? "Executing Fault..." : "⚡ Trigger Scenario"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 7. OBSERVABILITY VIEW */}
          {activeTab === "observability" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "10px",
                  padding: "24px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: "bold" }}>Prometheus & Grafana Observability</h3>
                    <p style={{ fontSize: "13px", color: "#9ca3af", marginTop: "4px" }}>
                      SignalForge natively exposes Prometheus metrics on <code>/metrics</code>.
                    </p>
                  </div>
                  <a
                    href="http://localhost:3000"
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      padding: "8px 16px",
                      borderRadius: "6px",
                      backgroundColor: "#ea580c",
                      color: "#fff",
                      textDecoration: "none",
                      fontSize: "13px",
                      fontWeight: "600",
                    }}
                  >
                    Open Grafana Dashboard ↗
                  </a>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px" }}>
                {[
                  {
                    name: "signalforge_pipeline_runs_total",
                    desc: "Counter partitioned by pipeline name and status (COMPLETED, FAILED)",
                    type: "Counter",
                  },
                  {
                    name: "signalforge_pipeline_duration_seconds",
                    desc: "Histogram of end-to-end pipeline run durations in seconds",
                    type: "Histogram",
                  },
                  {
                    name: "signalforge_records_processed_total",
                    desc: "Throughput metrics partitioned by pipeline and stage (EXTRACT, TRANSFORM, LOAD)",
                    type: "Counter",
                  },
                  {
                    name: "signalforge_records_rejected_total",
                    desc: "Quarantined record count partitioned by pipeline and rejection rule",
                    type: "Counter",
                  },
                  {
                    name: "signalforge_validation_failures_total",
                    desc: "Data quality validation violations by dataset and rule",
                    type: "Counter",
                  },
                  {
                    name: "signalforge_data_freshness_seconds",
                    desc: "Real-time gauge tracking age of the latest record timestamp in dataset",
                    type: "Gauge",
                  },
                ].map((m) => (
                  <div
                    key={m.name}
                    style={{
                      backgroundColor: "#111827",
                      border: "1px solid #1f2937",
                      borderRadius: "8px",
                      padding: "16px",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "10px",
                        backgroundColor: "#1e3a8a",
                        color: "#93c5fd",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        fontWeight: "bold",
                      }}
                    >
                      {m.type}
                    </span>
                    <p style={{ fontFamily: "monospace", fontSize: "13px", fontWeight: "600", margin: "8px 0 4px" }}>
                      {m.name}
                    </p>
                    <p style={{ fontSize: "12px", color: "#9ca3af" }}>{m.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 8. SETTINGS VIEW */}
          {activeTab === "settings" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "700px" }}>
              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "10px",
                  padding: "24px",
                }}
              >
                <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px" }}>
                  Platform Configuration & Environment
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "13px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #1f2937", paddingBottom: "8px" }}>
                    <span style={{ color: "#9ca3af" }}>Application Name</span>
                    <b>SignalForge</b>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #1f2937", paddingBottom: "8px" }}>
                    <span style={{ color: "#9ca3af" }}>Database Dialect</span>
                    <b>PostgreSQL / SQLite Compatible Engine</b>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #1f2937", paddingBottom: "8px" }}>
                    <span style={{ color: "#9ca3af" }}>Prometheus Exporter</span>
                    <span style={{ color: "#10b981", fontWeight: "bold" }}>ENABLED (Port 8000/metrics)</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #1f2937", paddingBottom: "8px" }}>
                    <span style={{ color: "#9ca3af" }}>Airflow Orchestrator</span>
                    <b>DAG: signalforge_daily_etl</b>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #1f2937", paddingBottom: "8px" }}>
                    <span style={{ color: "#9ca3af" }}>Data Directory</span>
                    <code>./data</code>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#9ca3af" }}>Diagnostic Engine</span>
                    <span style={{ color: "#38bdf8", fontWeight: "bold" }}>Deterministic Rule-Based</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
