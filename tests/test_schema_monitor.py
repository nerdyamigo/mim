"""Unit tests for scripts/schema_monitor.py."""

from scripts.schema_monitor import SchemaMonitor, format_changes_report
from tests.conftest import MOCK_S3_METADATA, MOCK_SERVICES_INDEX


def test_extract_schema_structure_tracks_new_fields(tmp_path):
    """Verify SchemaMonitor extracts top-level, action, annotation, operation, and condition key fields."""
    monitor = SchemaMonitor(schema_dir=tmp_path)
    s3_schema = monitor.extract_schema_structure(
        MOCK_S3_METADATA, MOCK_SERVICES_INDEX[0]
    )

    assert "modified" in s3_schema["service_index_fields"]
    assert "serviceName" in s3_schema["service_index_fields"]
    assert "Operations" in s3_schema["top_level_fields"]
    assert "ServiceName" in s3_schema["top_level_fields"]
    assert "SupportedBy" in s3_schema["action_fields"]
    assert "IsDataPlane" in s3_schema["annotation_property_fields"]
    assert "IAM Access Analyzer Policy Generation" in s3_schema["supported_by_fields"]
    assert "AuthorizedActions" in s3_schema["operation_fields"]
    assert "SDK" in s3_schema["operation_fields"]
    assert "ARN" in s3_schema["data_types"]
    assert "ArrayOfString" in s3_schema["data_types"]
    assert any(c["context"] == "operation" for c in s3_schema["field_combinations"])


def test_compare_schemas_detects_new_fields(tmp_path):
    """Verify compare_schemas detects newly introduced fields across all schema categories."""
    monitor = SchemaMonitor(schema_dir=tmp_path)

    baseline = {
        "top_level_fields": ["Actions", "ConditionKeys", "Name", "Resources", "Version"],
        "service_index_fields": ["service", "url"],
        "action_fields": ["ActionConditionKeys", "Annotations", "Name", "Resources"],
        "annotation_property_fields": [
            "IsList",
            "IsPermissionManagement",
            "IsTaggingOnly",
            "IsWrite",
        ],
        "supported_by_fields": [],
        "resource_fields": ["ARNFormats", "ConditionKeys", "Name"],
        "condition_key_fields": ["Name", "Types"],
        "operation_fields": [],
        "data_types": ["String"],
        "field_combinations": [],
    }

    current = {
        "top_level_fields": [
            "Actions",
            "ConditionKeys",
            "Name",
            "Operations",
            "Resources",
            "ServiceName",
            "Version",
        ],
        "service_index_fields": ["modified", "service", "serviceName", "url"],
        "action_fields": [
            "ActionConditionKeys",
            "Annotations",
            "Name",
            "Resources",
            "SupportedBy",
        ],
        "annotation_property_fields": [
            "IsDataPlane",
            "IsList",
            "IsPermissionManagement",
            "IsTaggingOnly",
            "IsWrite",
        ],
        "supported_by_fields": [
            "IAM Access Analyzer Policy Generation",
            "IAM Action Last Accessed",
        ],
        "resource_fields": ["ARNFormats", "ConditionKeys", "Name"],
        "condition_key_fields": ["Name", "Types"],
        "operation_fields": ["AuthorizedActions", "Name", "SDK"],
        "data_types": ["ARN", "ArrayOfString", "String"],
        "field_combinations": [],
    }

    changes = monitor.compare_schemas(baseline, current)
    assert changes["has_changes"] is True
    assert set(changes["new_fields"]["top_level_fields"]) == {"Operations", "ServiceName"}
    assert set(changes["new_fields"]["service_index_fields"]) == {"modified", "serviceName"}
    assert changes["new_fields"]["action_fields"] == ["SupportedBy"]
    assert changes["new_fields"]["annotation_property_fields"] == ["IsDataPlane"]
    assert set(changes["new_fields"]["operation_fields"]) == {
        "AuthorizedActions",
        "Name",
        "SDK",
    }
    assert set(changes["new_data_types"]) == {"ARN", "ArrayOfString"}

    report = format_changes_report(changes)
    assert "Schema Changes Detected" in report
    assert "Operations" in report
