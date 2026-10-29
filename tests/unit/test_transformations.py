import pandas as pd
from signalforge.engine.transformers import Transformer

def test_field_mapping_and_trimming():
    df = pd.DataFrame([
        {"old_name": "  Alice  ", "age_str": " 30 "},
        {"old_name": "Bob", "age_str": "25"}
    ])
    transformer = Transformer(
        field_mapping={"old_name": "name", "age_str": "age"},
        type_conversions={"age": "int"}
    )
    result_df = transformer.transform(df)

    assert "name" in result_df.columns
    assert "old_name" not in result_df.columns
    assert result_df.iloc[0]["name"] == "Alice"
    assert result_df.iloc[0]["age"] == 30
    assert result_df.iloc[1]["name"] == "Bob"
    assert result_df.iloc[1]["age"] == 25

def test_fill_defaults_and_deduplication():
    df = pd.DataFrame([
        {"id": "1", "amount": 100.0, "currency": None},
        {"id": "2", "amount": None, "currency": "EUR"},
        {"id": "1", "amount": 100.0, "currency": "USD"},  # Duplicate ID
    ])
    transformer = Transformer(
        fill_defaults={"currency": "USD", "amount": 0.0},
        drop_duplicates_subset=["id"]
    )
    result_df = transformer.transform(df)

    assert len(result_df) == 2
    # Last duplicate is kept
    first_row = result_df[result_df["id"] == "1"].iloc[0]
    assert first_row["currency"] == "USD"
    second_row = result_df[result_df["id"] == "2"].iloc[0]
    assert second_row["amount"] == 0.0
