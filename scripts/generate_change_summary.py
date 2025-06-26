#!/usr/bin/env python3
"""Generate a markdown summary of schema changes for GitHub notifications."""

import json
import sys
from pathlib import Path

def generate_summary(results_file: str) -> str:
    """Generate a markdown summary from monitoring results."""
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return f"❌ Error reading results: {e}"
    
    changes = data.get('changes', {})
    
    if not changes.get('has_changes', False):
        return "✅ No schema changes detected."
    
    summary = ["## 🔍 AWS API Schema Changes Detected", ""]
    
    # New fields
    if changes.get('new_fields'):
        summary.append("### 🆕 New Fields:")
        for field_type, fields in changes['new_fields'].items():
            summary.append(f"- **{field_type}**: {', '.join(fields)}")
        summary.append("")
    
    # Removed fields
    if changes.get('removed_fields'):
        summary.append("### 🗑️ Removed Fields:")
        for field_type, fields in changes['removed_fields'].items():
            summary.append(f"- **{field_type}**: {', '.join(fields)}")
        summary.append("")
    
    # New data types
    if changes.get('new_data_types'):
        summary.append(f"### 📊 New Data Types: {', '.join(changes['new_data_types'])}")
        summary.append("")
    
    # Removed data types
    if changes.get('removed_data_types'):
        summary.append(f"### 📉 Removed Data Types: {', '.join(changes['removed_data_types'])}")
        summary.append("")
    
    # Footer
    summary.extend([
        "---",
        "💡 **Action Required**: Review these changes and update the AWS Service Profiles CLI accordingly.",
        "",
        f"🕐 **Analysis Time**: {data.get('current_timestamp', 'Unknown')}",
        f"📊 **Services Analyzed**: {len(data.get('current_schema', {}).get('analyzed_services', []))}"
    ])
    
    return "\n".join(summary)

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_change_summary.py <results_file>", file=sys.stderr)
        sys.exit(1)
    
    results_file = sys.argv[1]
    if not Path(results_file).exists():
        print(f"Error: {results_file} not found", file=sys.stderr)
        sys.exit(1)
    
    summary = generate_summary(results_file)
    print(summary)

if __name__ == '__main__':
    main()