"""Unit tests for OutputFormatter across table, text, json, and yaml formats."""

import json
import yaml
from io import StringIO
from rich.console import Console
from aws_service_profiles.formatters import OutputFormatter


def _make_formatter():
    """Return an OutputFormatter writing to an in-memory StringIO buffer."""
    fmt = OutputFormatter(use_color=False)
    buf = StringIO()
    fmt.console = Console(file=buf, force_terminal=False, color_system=None, width=120)
    return fmt, buf


def test_format_action_details_enhanced_all_formats(mock_aws_client):
    """Ensure enhanced action details format cleanly without raw dict strings."""
    details = mock_aws_client.get_action_metadata_with_full_condition_keys("s3", "GetObject")
    assert details is not None

    fmt, buf = _make_formatter()
    fmt.format_action_details_enhanced(
        "s3",
        details["name"],
        details["resources"],
        details["condition_keys"],
        "table",
        action_metadata=details,
    )
    table_out = buf.getvalue()
    assert "GetObject" in table_out
    assert "Read" in table_out
    assert "Data Plane" in table_out
    assert "IAM Access Analyzer Policy Generation" in table_out
    assert "s3:ExistingObjectTag/<key> (String)" in table_out
    assert "{'Name':" not in table_out
    assert "CopyObject" in table_out

    fmt_text, buf_text = _make_formatter()
    fmt_text.format_action_details_enhanced(
        "s3",
        details["name"],
        details["resources"],
        details["condition_keys"],
        "text",
        action_metadata=details,
    )
    text_out = buf_text.getvalue()
    assert "s3:RequestObjectTagKeys (ArrayOfString)" in text_out
    assert "{'Name':" not in text_out

    fmt_json, buf_json = _make_formatter()
    fmt_json.format_action_details_enhanced(
        "s3",
        details["name"],
        details["resources"],
        details["condition_keys"],
        "json",
        action_metadata=details,
    )
    json_out = json.loads(buf_json.getvalue())
    assert json_out["action"] == "GetObject"
    assert json_out["access_level"] == "Read"

    fmt_yaml, buf_yaml = _make_formatter()
    fmt_yaml.format_action_details_enhanced(
        "s3",
        details["name"],
        details["resources"],
        details["condition_keys"],
        "yaml",
        action_metadata=details,
    )
    yaml_out = yaml.safe_load(buf_yaml.getvalue())
    assert yaml_out["plane"] == "Data Plane"


def test_format_resource_details_does_not_crash_on_dict_condition_keys(mock_aws_client):
    """Regression test: format_resource_details must handle dict context_keys."""
    res_details = mock_aws_client.get_resource_details_with_full_condition_keys("s3", "bucket")
    assert res_details is not None

    fmt, buf = _make_formatter()
    fmt.format_resource_details("s3", "bucket", res_details, "table")
    table_out = buf.getvalue()
    assert "s3:ResourceAccount (String)" in table_out
    assert "arn:${Partition}:s3:::${BucketName}" in table_out

    fmt_text, buf_text = _make_formatter()
    fmt_text.format_resource_details("s3", "bucket", res_details, "text")
    text_out = buf_text.getvalue()
    assert "s3:ResourceAccount (String)" in text_out


def test_format_operations_list_and_details(mock_aws_client):
    """Verify formatting for service API operations list and single operation details."""
    ops = mock_aws_client.get_operations_for_service("s3")
    fmt, buf = _make_formatter()
    fmt.format_operations_list("s3", ops, "table")
    table_out = buf.getvalue()
    assert "AbortMultipartUpload" in table_out
    assert "CopyObject" in table_out
    assert "Boto3: S3.abort_multipart_upload" in table_out

    op_detail = mock_aws_client.get_operation_details("ec2", "RunInstances")
    fmt_op, buf_op = _make_formatter()
    fmt_op.format_operation_details("ec2", "RunInstances", op_detail, "table")
    detail_out = buf_op.getvalue()
    assert "RunInstances" in detail_out
    assert "ec2:CreateTags" in detail_out


def test_format_update_summary():
    """Verify update summary output formatting."""
    summary = {
        "last_updated": "2026-11-09T06:00:00+00:00",
        "total_services": 457,
        "new_services_count": 1,
        "new_services": ["bedrock"],
        "modified_services_count": 2,
        "modified_services": ["s3", "ec2"],
        "refreshed_services": ["s3"],
    }
    fmt, buf = _make_formatter()
    fmt.format_update_summary(summary, "table")
    text = buf.getvalue()
    assert "AWS Service Reference Metadata Update Summary" in text
    assert "457" in text
    assert "s3" in text
