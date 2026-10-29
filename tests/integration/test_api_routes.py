from fastapi.testclient import TestClient

def test_health_and_readiness(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"

def test_sources_and_pipeline_crud(client: TestClient):
    # 1. Create source
    src_payload = {
        "name": "api_test_source",
        "source_type": "CSV",
        "config_json": {"path": "data/test.csv"}
    }
    src_resp = client.post("/api/sources", json=src_payload)
    assert src_resp.status_code == 201
    source_id = src_resp.json()["id"]

    # 2. List sources
    list_resp = client.get("/api/sources")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 3. Create pipeline
    pipe_payload = {
        "name": "api_test_pipeline",
        "source_id": source_id,
        "target_table": "dim_customers",
        "schedule": "manual",
        "batch_fail_policy": "REJECT_AND_CONTINUE"
    }
    pipe_resp = client.post("/api/pipelines", json=pipe_payload)
    assert pipe_resp.status_code == 201
    pipeline_id = pipe_resp.json()["id"]

    # 4. Get pipeline
    get_pipe = client.get(f"/api/pipelines/{pipeline_id}")
    assert get_pipe.status_code == 200
    assert get_pipe.json()["name"] == "api_test_pipeline"

def test_quality_rules_api(client: TestClient):
    rule_payload = {
        "dataset_name": "dim_customers",
        "rule_name": "api_rule_not_null",
        "rule_type": "NOT_NULL",
        "params_json": {"column": "email"},
        "severity": "RECORD_REJECT"
    }
    resp = client.post("/api/quality/rules", json=rule_payload)
    assert resp.status_code == 201
    assert resp.json()["rule_name"] == "api_rule_not_null"

    list_resp = client.get("/api/quality/rules?dataset_name=dim_customers")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

def test_failure_lab_api(client: TestClient):
    scenarios_resp = client.get("/api/failure-lab/scenarios")
    assert scenarios_resp.status_code == 200
    scenarios = scenarios_resp.json()
    assert len(scenarios) == 8

    # Trigger duplicate records scenario
    trigger_resp = client.post("/api/failure-lab/trigger", json={"scenario_id": "duplicate_records"})
    assert trigger_resp.status_code == 200
    res_data = trigger_resp.json()
    assert res_data["status"] == "FAILED"
    assert res_data["error_category"] == "DATA_QUALITY_VIOLATION"

def test_metrics_and_summary_api(client: TestClient):
    # Summary
    summary_resp = client.get("/api/metrics/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert "total_pipelines" in summary
    assert "failure_rate_percent" in summary

    # Prometheus metrics
    prom_resp = client.get("/metrics")
    assert prom_resp.status_code == 200
    assert "signalforge_pipeline_runs_total" in prom_resp.text
