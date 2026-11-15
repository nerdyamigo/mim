#!/usr/bin/env python3
"""CLI wrapper for AWS Service Reference API Schema Monitor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aws_service_profiles.schema_monitor import (  # noqa: E402
    SchemaMonitor,
    format_changes_report,
    main,
)

__all__ = ["SchemaMonitor", "format_changes_report", "main"]

if __name__ == "__main__":
    main()
