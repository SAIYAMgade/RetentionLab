from signalforge.schema.drift import DriftSeverity, DriftType, SchemaDriftDetector

def test_detect_no_drift():
    baseline = {
        "id": {"name": "id", "data_type": "string", "nullable": False, "required": True},
        "amount": {"name": "amount", "data_type": "float", "nullable": False, "required": True}
    }
    observed = {
        "id": {"name": "id", "data_type": "string", "nullable": False, "required": True},
        "amount": {"name": "amount", "data_type": "float", "nullable": False, "required": True}
    }
    report = SchemaDriftDetector.detect_drift(baseline, observed)

    assert report.has_drift is False
    assert report.severity == DriftSeverity.COMPATIBLE
    assert report.drift_types == [DriftType.NONE]

def test_detect_compatible_column_added():
    baseline = {
        "id": {"name": "id", "data_type": "string", "nullable": False, "required": True}
    }
    observed = {
        "id": {"name": "id", "data_type": "string", "nullable": False, "required": True},
        "notes": {"name": "notes", "data_type": "string", "nullable": True, "required": False}
    }
    report = SchemaDriftDetector.detect_drift(baseline, observed)

    assert report.has_drift is True
    assert report.severity == DriftSeverity.COMPATIBLE
    assert DriftType.COLUMN_ADDED in report.drift_types
    assert "notes" in report.added_columns

def test_detect_breaking_missing_required():
    baseline = {
        "id": {"name": "id", "data_type": "string", "nullable": False, "required": True},
        "amount": {"name": "amount", "data_type": "float", "nullable": False, "required": True}
    }
    observed = {
        "id": {"name": "id", "data_type": "string", "nullable": False, "required": True}
    }
    report = SchemaDriftDetector.detect_drift(baseline, observed)

    assert report.has_drift is True
    assert report.severity == DriftSeverity.BREAKING
    assert DriftType.REQUIRED_MISSING in report.drift_types
    assert "amount" in report.missing_required

def test_detect_breaking_incompatible_type_change():
    baseline = {
        "amount": {"name": "amount", "data_type": "float", "nullable": False, "required": False}
    }
    observed = {
        "amount": {"name": "amount", "data_type": "datetime", "nullable": False, "required": False}
    }
    report = SchemaDriftDetector.detect_drift(baseline, observed)

    assert report.has_drift is True
    assert report.severity == DriftSeverity.BREAKING
    assert DriftType.TYPE_CHANGED in report.drift_types
    assert report.type_changes["amount"]["from"] == "float"
    assert report.type_changes["amount"]["to"] == "datetime"
