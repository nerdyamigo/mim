"""Service helper functions for providing detailed service information."""

import click
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from .aws_client import AWSClient


class ServiceHelper:
    """Helper class for providing service-specific information and help."""

    def __init__(self, client: AWSClient):
        self.client = client

    def is_valid_service(self, service_name: str) -> bool:
        """Check if a service name is valid (case-insensitive)."""
        return self.client.find_service_entry(service_name) is not None

    def get_service_summary(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get a summary of service information for help display."""
        entry = self.client.find_service_entry(service_name)
        if not entry:
            return None

        try:
            canonical_name = entry.get("service", service_name)
            metadata = self.client.find_all_service_metadata(canonical_name) or {}

            actions = self.client.get_all_actions_for_service(canonical_name)
            detailed_actions = self.client.get_all_actions_with_metadata_for_service(
                canonical_name
            )
            resources = self.client.get_all_unique_resources_for_service(canonical_name)
            context_keys = self.client.get_all_unique_context_keys_for_service(
                canonical_name
            )
            global_keys = self.client.get_global_context_keys_for_service(
                canonical_name
            )
            service_keys = self.client.get_service_specific_context_keys_for_service(
                canonical_name
            )
            operations = self.client.get_operations_for_service(canonical_name)

            access_breakdown: Dict[str, int] = {
                "Read": 0,
                "Write": 0,
                "List": 0,
                "Tagging": 0,
                "Permissions management": 0,
            }
            data_plane_count = 0
            control_plane_count = 0

            for act in detailed_actions:
                lvl = act.get("access_level", "Read")
                access_breakdown[lvl] = access_breakdown.get(lvl, 0) + 1
                if act.get("plane") == "Data Plane":
                    data_plane_count += 1
                else:
                    control_plane_count += 1

            modified_ts = entry.get("modified")
            modified_str = None
            if isinstance(modified_ts, (int, float)) and modified_ts > 0:
                modified_str = datetime.fromtimestamp(
                    modified_ts, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S UTC")

            return {
                "service_name": canonical_name,
                "display_name": metadata.get("ServiceName")
                or entry.get("serviceName")
                or canonical_name.upper(),
                "version": metadata.get("Version", "v1"),
                "modified": modified_str,
                "actions_count": len(actions),
                "operations_count": len(operations),
                "resources_count": len(resources),
                "total_context_keys": len(context_keys),
                "global_context_keys": len(global_keys),
                "service_context_keys": len(service_keys),
                "access_breakdown": access_breakdown,
                "data_plane_count": data_plane_count,
                "control_plane_count": control_plane_count,
                "sample_actions": actions[:5] if actions else [],
                "sample_operations": [op.get("Name") for op in operations[:5]]
                if operations
                else [],
                "sample_resources": [r["name"] for r in resources[:5]]
                if resources
                else [],
                "sample_context_keys": context_keys[:5] if context_keys else [],
            }
        except Exception:
            return None

    def format_service_help(self, service_name: str) -> str:
        """Format service-specific help text including new ServiceName, Version, Operations, and Access Levels."""
        summary = self.get_service_summary(service_name)
        if not summary:
            return f"Service '{service_name}' not found or unavailable."

        canonical = summary["service_name"]
        display_name = summary.get("display_name", canonical.upper())
        version = summary.get("version", "v1")
        modified = summary.get("modified")

        header_meta = f"Version: {version}"
        if modified:
            header_meta += f" | Last Modified: {modified}"

        ab = summary.get("access_breakdown", {})
        help_text = f"""
Service: {canonical.upper()} ({display_name})
{header_meta}

📊 Available Data:
  • Actions: {summary['actions_count']} (Read: {ab.get('Read', 0)}, Write: {ab.get('Write', 0)}, List: {ab.get('List', 0)}, Tagging: {ab.get('Tagging', 0)}, Permissions: {ab.get('Permissions management', 0)})
  • Planes: Control Plane: {summary.get('control_plane_count', 0)}, Data Plane: {summary.get('data_plane_count', 0)}
  • API Operations: {summary['operations_count']}
  • Resources: {summary['resources_count']}
  • Context Keys: {summary['total_context_keys']} (AWS Global: {summary['global_context_keys']}, Service-Specific: {summary['service_context_keys']})

🔍 Sample Actions:
"""

        for action in summary["sample_actions"]:
            help_text += f"  • {action}\n"

        if summary["actions_count"] > 5:
            help_text += f"  ... and {summary['actions_count'] - 5} more\n"

        if summary.get("sample_operations"):
            help_text += "\n⚙️  Sample API Operations:\n"
            for op in summary["sample_operations"]:
                help_text += f"  • {op}\n"
            if summary["operations_count"] > 5:
                help_text += f"  ... and {summary['operations_count'] - 5} more\n"

        if summary["sample_resources"]:
            help_text += "\n🏗️  Sample Resources:\n"
            for resource in summary["sample_resources"]:
                help_text += f"  • {resource}\n"

            if summary["resources_count"] > 5:
                help_text += f"  ... and {summary['resources_count'] - 5} more\n"

        if summary["sample_context_keys"]:
            help_text += "\n🔑 Sample Context Keys:\n"
            for key in summary["sample_context_keys"]:
                help_text += f"  • {key}\n"

            if summary["total_context_keys"] > 5:
                help_text += f"  ... and {summary['total_context_keys'] - 5} more\n"

        help_text += f"""
💡 Common Usage Examples:
  mim {canonical}                        # List all actions
  mim {canonical} --access-level Write   # Filter actions by access level
  mim {canonical} --plane data           # Filter Data Plane vs Control Plane actions
  mim {canonical} --operations           # Show API Operations & SDK mappings
  mim {canonical} --context-keys         # Show all context keys
  mim {canonical} --global-context-keys  # Show AWS global keys only
  mim {canonical} --service-context-keys # Show service-specific keys only
  mim {canonical} --resources            # Show all resources
  mim {canonical} --count                # Show counts only
"""

        if summary["sample_actions"]:
            sample_action = summary["sample_actions"][0]
            help_text += f"  mim {canonical} {sample_action}        # Get resources for specific action\n"
            help_text += f"  mim {canonical} --action {sample_action} # Get full action details\n"

        help_text += """
📋 Output Formats:
  --format table    # Structured table (default)
  --format json     # Machine-readable JSON
  --format yaml     # Human-readable YAML
  --format text     # Simple text list
"""

        return help_text

    def get_similar_services(
        self, invalid_service: str, max_suggestions: int = 5
    ) -> List[str]:
        """Get similar service names for typo suggestions (matches both service code and serviceName)."""
        try:
            services = self.client.get_aws_services_urls()
            suggestions = []
            invalid_lower = invalid_service.lower()

            for svc_obj in services:
                service = svc_obj.get("service", "")
                service_lower = service.lower()
                display_lower = svc_obj.get("serviceName", "").lower()
                if (
                    invalid_lower in service_lower
                    or invalid_lower in display_lower
                    or service_lower.startswith(invalid_lower[:3])
                    or any(
                        part in service_lower
                        for part in invalid_lower.split("-")
                        if len(part) > 2
                    )
                ):
                    suggestions.append(service)

            return suggestions[:max_suggestions]
        except Exception:
            return []


def validate_service_name(ctx, param, value):
    """Click callback to validate service names and provide helpful suggestions."""
    if value is None:
        return value

    if any(
        ctx.params.get(flag)
        for flag in [
            "list_services",
            "list_all_context_keys",
            "list_global_context_keys",
            "list_service_context_keys",
            "update",
            "clear_cache",
            "check_schema",
        ]
    ):
        return value

    try:
        client = AWSClient()
        helper = ServiceHelper(client)

        if not helper.is_valid_service(value):
            suggestions = helper.get_similar_services(value)
            error_msg = f"Invalid service name: '{value}'"

            if suggestions:
                error_msg += "\n\nDid you mean one of these?\n"
                for suggestion in suggestions:
                    error_msg += f"  • {suggestion}\n"
                error_msg += (
                    "\nUse 'mim --list-services' to see all available services."
                )
            else:
                error_msg += (
                    "\n\nUse 'mim --list-services' to see all available services."
                )

            raise click.BadParameter(error_msg)
    except click.BadParameter:
        raise
    except Exception:
        pass

    return value
