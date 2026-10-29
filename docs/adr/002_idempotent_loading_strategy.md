# ADR 002: Idempotent UPSERT & Atomic Checkpoint Persistence

## Context
Network retries, interrupted runs, and scheduled re-executions frequently introduce duplicate records when pipelines lack safe loading strategies. Relying strictly on in-memory deduplication fails if a run halts midway through database persistence.

## Decision
1. Apply unique constraints on stable business identifiers (`customer_id`, `transaction_id`).
2. Utilize database-level UPSERT semantics (`SafeLoader.load_customers`, `SafeLoader.load_transactions`).
3. Persist pipeline cursors/checkpoints (`pipeline_checkpoints`) inside the exact same database transaction block as the record insertions.

## Consequences
- **Positive**: Complete idempotency guaranteed. Re-running identical batches creates 0 duplicate rows. Interrupted runs roll back atomically, leaving no orphaned data or corrupt checkpoints.
- **Negative**: Target tables must have stable unique identifiers defined.
