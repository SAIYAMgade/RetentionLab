# Data Directory

Datasets in this directory are generated deterministically by the SignalForge synthetic data generator:

```bash
python scripts/generate_synthetic_data.py --customers 500 --transactions 2500 --seed 42
```

Outputs:
- `customers.csv`: Customer dimension master dataset.
- `transactions.json`: Financial ledger transactions.
- `events_stream.jsonl`: Simulated streaming event logs.
- `api_mock_data.json`: Mock partner REST API response payload.
