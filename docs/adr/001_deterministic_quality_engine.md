# ADR 001: Declarative In-Engine Data Quality vs Heavy Validation Frameworks

## Context
Data engineering platforms require robust validation checks (not null, uniqueness, type compatibility, referential integrity, category whitelist, range boundaries, freshness). Heavyweight tools like Great Expectations or Soda Core introduce complex dependency trees, custom JSON DSLs, and significant overhead for single-node / containerized workloads.

## Decision
Implement a pure, vectorized Python/Pandas declarative validation engine (`QualityValidator`) with 10 explicit rule types. Validation results and row-level rejections are persisted directly into PostgreSQL tables (`validation_results`, `rejected_records`).

## Consequences
- **Positive**: Zero external framework bloat, sub-50ms validation latency over 5,000+ records, transparent debugging, full unit test coverage.
- **Negative**: Rule definitions are stored in database models rather than Great Expectations JSON suites.
