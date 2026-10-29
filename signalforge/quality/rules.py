from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class RuleSeverity(str, Enum):
    RECORD_REJECT = "RECORD_REJECT"
    BATCH_FAIL = "BATCH_FAIL"

class RuleType(str, Enum):
    NOT_NULL = "NOT_NULL"
    UNIQUE = "UNIQUE"
    TYPE_CHECK = "TYPE_CHECK"
    NON_NEGATIVE = "NON_NEGATIVE"
    VALID_TIMESTAMP = "VALID_TIMESTAMP"
    REFERENTIAL_INTEGRITY = "REFERENTIAL_INTEGRITY"
    CATEGORY_WHITELIST = "CATEGORY_WHITELIST"
    RECORD_COUNT_DEVIATION = "RECORD_COUNT_DEVIATION"
    DATA_FRESHNESS = "DATA_FRESHNESS"
    SCHEMA_COMPATIBILITY = "SCHEMA_COMPATIBILITY"

@dataclass
class QualityRule:
    rule_name: str
    rule_type: RuleType
    dataset_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    severity: RuleSeverity = RuleSeverity.RECORD_REJECT
    id: Optional[str] = None
    is_active: bool = True

@dataclass
class RuleEvaluationResult:
    rule_name: str
    rule_type: RuleType
    dataset_name: str
    passed: bool
    total_checked: int
    failed_count: int
    severity: RuleSeverity
    sample_failures: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    failed_indices: List[int] = field(default_factory=list)
    rejection_reasons_by_index: Dict[int, List[str]] = field(default_factory=dict)
