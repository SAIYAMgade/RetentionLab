# RetentionLab Technical Architecture & Data Flow

## System Architecture Diagram

```mermaid
flowchart TD
    subgraph S1["1. Data Layer"]
        A["Deterministic Data Generator (Seed: 42)"] --> B["104,990 Transactions (>97k)"]
        A --> C["5,000 Customers & Accounts"]
        A --> D["115k Activities, 7k Tickets, 32k Campaigns"]
        B & C & D --> E["SQLite Relational Database & Indexes"]
    end

    subgraph S2["2. Analytics & Features"]
        E --> F["12 SQL Relational Analytics Queries"]
        E --> G["Automated SQL Data Quality Checks"]
        E --> H["44-Feature Behavioral Engineering Engine"]
        E --> I["Leakage-Free 60d Target Labeler"]
    end

    subgraph S3["3. Predictive ML & Prioritization"]
        H & I --> J["Temporal Split: Train (70%) / Val (15%) / Test (15%)"]
        J --> K["Benchmark Models: Logistic Regression, RF, HistGB"]
        K --> L["Validation-Optimized Operating Threshold (0.74)"]
        L --> M["Customer Scoring Pipeline & Probabilities"]
        M --> N["Revenue Prioritization Engine: Risk * Value Proxy"]
        N --> O["Explainable Behavioral Signals & Action Dispatcher"]
    end

    subgraph S4["4. Enterprise Delivery"]
        M & N --> P["Interactive Streamlit Workspace (9 Pages)"]
        N --> Q["Power BI Star Schema Package & DAX Measures"]
        N --> R["Excel Retention-Action Workbook (5 Sheets)"]
    end
```

## Architectural Principles

1. **Separation of Concerns**: Data generation, feature engineering, predictive inference, and user presentation operate in independent modules with zero cyclic dependencies.
2. **Strict Leakage Isolation**: The scoring observation point ($T = \text{2026-04-01}$) strictly bounds historical feature calculations ($t \le T$). Target labels examine strictly future behavior ($T < t \le T + 60\text{d}$).
3. **Decoupled BI & Reporting**: Star-schema export tables conform to Kimball dimensional standards (`CUSTOMER_DIMENSION`, `DATE_DIMENSION`, `TRANSACTION_FACT`, `CUSTOMER_RISK_FACT`).
4. **Reproducible Pipeline**: A single command `python scripts/run_pipeline.py` executes all stages deterministically in ~15-20 seconds.
