"""Synthetic transaction dataset generator for RetentionLab.

Generates realistic customer transaction histories across diverse behavioral
archetypes (frequent repeat, occasional, declining, irregular, lapsed, recently acquired).
Produces deterministic output using a fixed random seed.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

from retentionlab.config.settings import DEFAULT_CONFIG, PipelineConfig


def generate_synthetic_transactions(config: PipelineConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """Generate a realistic transaction dataset.

    Returns:
        pd.DataFrame containing synthetic transactions matching Section 4.1 specification.
    """
    rng = np.random.default_rng(config.random_seed)

    start_dt = datetime.strptime(config.start_date, "%Y-%m-%d")
    cutoff_dt = datetime.strptime(config.cutoff_date, "%Y-%m-%d")
    future_end_dt = datetime.strptime(config.future_end_date, "%Y-%m-%d")
    total_days = (future_end_dt - start_dt).days
    obs_days = (cutoff_dt - start_dt).days

    categories = [
        "Electronics", "Apparel", "Home & Kitchen",
        "Books", "Health & Beauty", "Sports & Outdoors"
    ]
    category_mean_spend = {
        "Electronics": 185.0,
        "Apparel": 62.0,
        "Home & Kitchen": 78.0,
        "Books": 28.0,
        "Health & Beauty": 45.0,
        "Sports & Outdoors": 88.0
    }

    channels = ["Web", "Mobile App", "In-Store"]
    channel_weights = [0.45, 0.35, 0.20]

    source_systems = {
        "Web": "WEB_CHECKOUT",
        "Mobile App": "APP_GATEWAY",
        "In-Store": "POS_TERMINAL"
    }

    archetype_weights = [0.22, 0.25, 0.20, 0.15, 0.10, 0.08]
    archetypes = [
        "frequent_loyal",
        "steady_occasional",
        "declining_engagement",
        "irregular_sporadic",
        "lapsed_churner",
        "recently_acquired"
    ]

    records: List[Dict[str, Any]] = []
    tx_counter = 10000001

    for cust_idx in range(1, config.n_customers + 1):
        cust_id = f"CUST_{cust_idx:05d}"
        archetype = rng.choice(archetypes, p=archetype_weights)

        # Determine customer acquisition date (first purchase)
        if archetype == "recently_acquired":
            # Acquired between 35 and 90 days before cutoff date
            join_offset = obs_days - int(rng.integers(35, 91))
        elif archetype == "lapsed_churner":
            # Acquired early in the observation window
            join_offset = int(rng.integers(10, 200))
        else:
            # Acquired randomly across the first 18 months
            join_offset = int(rng.integers(0, max(1, obs_days - 120)))

        join_date = start_dt + timedelta(days=join_offset)

        # Baseline category and channel affinities for this customer
        pref_category = rng.choice(categories)
        pref_channel = rng.choice(channels, p=channel_weights)

        curr_date = join_date

        while curr_date <= future_end_dt:
            # Determine gap to next transaction based on archetype and time relative to cutoff
            is_post_cutoff = curr_date > cutoff_dt

            if archetype == "frequent_loyal":
                mean_gap = rng.uniform(14, 28)
                gap = int(rng.exponential(mean_gap)) + 2

            elif archetype == "steady_occasional":
                mean_gap = rng.uniform(45, 75)
                gap = int(rng.exponential(mean_gap)) + 10

            elif archetype == "declining_engagement":
                # Accelerating gap over time
                days_since_join = (curr_date - join_date).days
                decay_factor = 1.0 + (days_since_join / 250.0)
                mean_gap = rng.uniform(20, 35) * decay_factor
                gap = int(rng.exponential(mean_gap)) + 5

            elif archetype == "irregular_sporadic":
                # Log-normal heavy-tailed intervals
                gap = int(rng.lognormal(mean=3.2, sigma=0.85)) + 4

            elif archetype == "lapsed_churner":
                # Drops off early; rare chance of revival
                days_since_join = (curr_date - join_date).days
                if days_since_join > 280:
                    gap = int(rng.integers(150, 450))
                else:
                    gap = int(rng.exponential(40)) + 7

            elif archetype == "recently_acquired":
                mean_gap = rng.uniform(25, 45)
                gap = int(rng.exponential(mean_gap)) + 5
            else:
                gap = int(rng.exponential(35)) + 5

            # Advance timestamp
            hour_noise = int(rng.integers(8, 22))
            minute_noise = int(rng.integers(0, 60))
            second_noise = int(rng.integers(0, 60))
            tx_dt = curr_date.replace(hour=hour_noise, minute=minute_noise, second=second_noise)

            if tx_dt > future_end_dt:
                break

            # Product Category selection (70% affinity, 30% exploration)
            if rng.random() < 0.70:
                cat = pref_category
            else:
                cat = rng.choice(categories)

            # Monetary amount: Log-normal distribution centered around category mean
            cat_mean = category_mean_spend[cat]
            # sigma=0.45 creates realistic variation with occasional large orders
            amount = float(np.round(rng.lognormal(mean=np.log(cat_mean) - 0.1, sigma=0.42), 2))
            amount = max(5.0, min(amount, 2500.0))

            # Channel selection (75% preferred, 25% other)
            if rng.random() < 0.75:
                ch = pref_channel
            else:
                ch = rng.choice(channels)

            # Transaction status and type (96.5% completed purchase, 2.5% refund, 1.0% failed)
            r_type_status = rng.random()
            if r_type_status < 0.025:
                tx_type = "refund"
                tx_status = "completed"
                # Refund amount matches realistic transaction amount
                amount = -1.0 * float(np.round(min(amount, rng.uniform(15.0, 150.0)), 2))
            elif r_type_status < 0.035:
                tx_type = "purchase"
                tx_status = "failed"
            else:
                tx_type = "purchase"
                tx_status = "completed"

            records.append({
                "transaction_id": f"TXN_{tx_counter}",
                "customer_id": cust_id,
                "transaction_date": tx_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "transaction_amount": amount,
                "transaction_type": tx_type,
                "transaction_status": tx_status,
                "product_category": cat,
                "channel": ch,
                "currency": "USD",
                "source_system": source_systems[ch]
            })

            tx_counter += 1
            curr_date += timedelta(days=gap)

    df = pd.DataFrame(records)
    # Sort chronologically
    df["dt_sort"] = pd.to_datetime(df["transaction_date"])
    df = df.sort_values("dt_sort").reset_index(drop=True).drop(columns=["dt_sort"])

    return df
