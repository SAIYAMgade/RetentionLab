# RetentionLab Data Directory

This directory manages the transaction data lifecycle across raw, sample, and processed stages.

## Directory Structure
- `data/raw/`:
  - `transactions.csv`: Complete transactional log containing 109,308 records for 8,500 customers spanning Jan 2022 to Mar 2024.
- `data/sample/`:
  - `transactions_sample.csv`: Lightweight 5,000-row representative slice for rapid local prototyping and test suites.
- `data/processed/`:
  - `retentionlab.db`: SQLite database populated with raw transactions, cleaned records, features, predictions, and prioritization tables.
  - `customer_features.parquet`: 44 behavioral features extracted per customer strictly as of cutoff date.
  - `customer_predictions.parquet`: Model probabilities and predicted binary labels.
  - `customer_prioritization.csv`: Prioritized customer action matrix.
