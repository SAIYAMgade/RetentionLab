# SignalForge Threat Model & Security Policy

## 1. Trust Boundaries
- **External Data Sources**: CSV files, JSON payloads, and third-party REST APIs are treated as untrusted inputs. All incoming payloads pass through schema validation and type parsing before database interaction.
- **REST API Endpoints**: All state-changing endpoints (`POST /api/pipelines/{id}/run`, `POST /api/failure-lab/trigger`) accept strictly validated Pydantic schemas. Unrestricted shell or arbitrary SQL queries are prohibited.

## 2. Mitigation Strategies
- **SQL Injection**: All database interactions use SQLAlchemy Core and ORM with parameterized queries (`:param`), preventing SQL injection.
- **Credential Masking**: Sensitive tokens (API keys, authorization bearer headers) are masked in structured logs and API responses.
- **Path Traversal**: Extractor file paths are validated against allowed root directories (`./data`) to prevent directory traversal attacks (`../../etc/passwd`).
- **Resource Exhaustion**: REST API client applies explicit timeouts (`timeout_seconds=5.0`) and bounded retries (`max_retries=3`) with exponential backoff to avoid hanging threads or cascading socket exhaustion.
- **Least-Privilege Database User**: Production Docker configurations run PostgreSQL with application-specific users and passwords rather than root superuser privileges.
