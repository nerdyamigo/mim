"""Output formatters for AWS service data."""

import json
import yaml
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


def _format_condition_key_item(ck: Any) -> str:
    """Format a condition key entry (either a string or a dict with 'Name'/'name' and 'Types')."""
    if isinstance(ck, dict):
        key_name = ck.get("Name") or ck.get("name") or str(ck)
        key_types = ck.get("Types") or ck.get("types")
        if key_types and isinstance(key_types, list):
            return f"{key_name} ({', '.join(str(t) for t in key_types)})"
        return str(key_name)
    return str(ck)


def _format_modified_timestamp(modified_val: Any) -> str:
    """Convert Unix epoch seconds into YYYY-MM-DD UTC string if present."""
    if isinstance(modified_val, (int, float)) and modified_val > 0:
        try:
            dt = datetime.fromtimestamp(modified_val, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return str(modified_val)
    return "N/A"


class OutputFormatter:
    """Formatter for displaying AWS service metadata across table, text, json, and yaml formats."""

    def __init__(self, use_color: bool = True):
        self.console = Console(color_system="auto" if use_color else None)

    def format_services_list(
        self, services: List[Dict[str, Any]], format_type: str = "table"
    ) -> None:
        """Format and display list of AWS services (`service`, `serviceName`, `modified`, `url`)."""
        if format_type == "json":
            self.console.print(json.dumps(services, indent=2))
        elif format_type == "yaml":
            self.console.print(yaml.dump(services, default_flow_style=False))
        elif format_type == "table":
            self._format_services_table(services)
        else:  # text
            self._format_services_text(services)

    def format_actions_list(
        self,
        service_name: str,
        actions: List[Any],
        format_type: str = "table",
        detailed_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Format and display list of actions for a service."""
        if format_type == "json":
            payload_actions = detailed_actions if detailed_actions is not None else actions
            data = {
                "service": service_name,
                "actions": payload_actions,
                "count": len(payload_actions),
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            payload_actions = detailed_actions if detailed_actions is not None else actions
            data = {
                "service": service_name,
                "actions": payload_actions,
                "count": len(payload_actions),
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_actions_table(service_name, actions, detailed_actions)
        else:  # text
            self._format_actions_text(service_name, actions, detailed_actions)

    def format_operations_list(
        self,
        service_name: str,
        operations: List[Dict[str, Any]],
        format_type: str = "table",
    ) -> None:
        """Format and display API Operations (`Name`, `AuthorizedActions`, `SDK`) for a service."""
        if format_type == "json":
            data = {
                "service": service_name,
                "operations": operations,
                "count": len(operations),
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {
                "service": service_name,
                "operations": operations,
                "count": len(operations),
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            table = Table(
                title=f"API Operations for {service_name} ({len(operations)} total)",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Operation", style="cyan", no_wrap=True)
            table.add_column("Authorized IAM Actions", style="green")
            table.add_column("SDK Methods", style="yellow")

            for op in operations:
                op_name = op.get("Name", "Unknown")
                auth_actions = op.get("AuthorizedActions", [])
                auth_strs = [
                    f"{a.get('Service', service_name)}:{a.get('Name', '')}"
                    for a in auth_actions
                    if isinstance(a, dict)
                ]
                sdk_list = op.get("SDK", [])
                sdk_strs = [
                    f"{s.get('Package', 'SDK')}: {s.get('Name', '')}.{s.get('Method', '')}"
                    for s in sdk_list
                    if isinstance(s, dict)
                ]
                table.add_row(
                    op_name,
                    "\n".join(auth_strs) if auth_strs else "None",
                    "\n".join(sdk_strs) if sdk_strs else "None",
                )
            self.console.print(table)
        else:  # text
            self.console.print(
                f"[bold]API Operations for {service_name} ({len(operations)} total):[/bold]"
            )
            for op in operations:
                op_name = op.get("Name", "Unknown")
                auth_actions = op.get("AuthorizedActions", [])
                auth_strs = [
                    f"{a.get('Service', service_name)}:{a.get('Name', '')}"
                    for a in auth_actions
                    if isinstance(a, dict)
                ]
                sdk_list = op.get("SDK", [])
                sdk_strs = [
                    f"{s.get('Package', 'SDK')}: {s.get('Name', '')}.{s.get('Method', '')}"
                    for s in sdk_list
                    if isinstance(s, dict)
                ]
                self.console.print(f"  • [cyan]{op_name}[/cyan]")
                if auth_strs:
                    self.console.print(
                        f"    [green]Authorized Actions:[/green] {', '.join(auth_strs)}"
                    )
                if sdk_strs:
                    self.console.print(
                        f"    [yellow]SDK Methods:[/yellow] {', '.join(sdk_strs)}"
                    )

    def format_operation_details(
        self,
        service_name: str,
        operation_name: str,
        operation_details: Dict[str, Any],
        format_type: str = "table",
    ) -> None:
        """Format and display details for a single API Operation."""
        if format_type == "json":
            data = {"service": service_name, **operation_details}
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {"service": service_name, **operation_details}
            self.console.print(yaml.dump(data, default_flow_style=False))
        else:
            op_dict = {
                "Name": operation_details.get("name", operation_name),
                "AuthorizedActions": operation_details.get("authorized_actions", []),
                "SDK": operation_details.get("sdk", []),
            }
            self.format_operations_list(service_name, [op_dict], format_type)

    def format_update_summary(
        self, summary: Dict[str, Any], format_type: str = "table"
    ) -> None:
        """Format and display the metadata update / sync summary."""
        if format_type == "json":
            self.console.print(json.dumps(summary, indent=2))
            return
        if format_type == "yaml":
            self.console.print(yaml.dump(summary, default_flow_style=False))
            return

        table = Table(
            title="AWS Service Reference Metadata Update Summary",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", style="green")

        table.add_row("Last Updated (UTC)", str(summary.get("last_updated", "N/A")))
        table.add_row("Total AWS Services", str(summary.get("total_services", 0)))
        table.add_row(
            "New Services Added", str(summary.get("new_services_count", 0))
        )
        table.add_row(
            "Modified Services Upstream", str(summary.get("modified_services_count", 0))
        )
        refreshed = summary.get("refreshed_services", [])
        table.add_row(
            "Services Cached/Refreshed Locally",
            ", ".join(refreshed) if refreshed else "Index Only",
        )
        self.console.print(table)

    def format_resources_list(
        self,
        service_name: str,
        action_name: str,
        resources: List[Dict[str, Any]],
        format_type: str = "table",
    ) -> None:
        """Format and display list of resources for a service action."""
        if format_type == "json":
            data = {
                "service": service_name,
                "action": action_name,
                "resources": resources,
                "count": len(resources),
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {
                "service": service_name,
                "action": action_name,
                "resources": resources,
                "count": len(resources),
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_resources_table(service_name, action_name, resources)
        else:  # text
            self._format_resources_text(service_name, action_name, resources)

    def format_action_details(
        self,
        service_name: str,
        action_name: str,
        resources: List[str],
        condition_keys: List[str],
        format_type: str = "table",
    ) -> None:
        """Format and display details for a specific action."""
        if format_type == "json":
            data = {
                "service": service_name,
                "action": action_name,
                "resources": resources,
                "condition_keys": condition_keys,
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {
                "service": service_name,
                "action": action_name,
                "resources": resources,
                "condition_keys": condition_keys,
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_action_details_table(
                service_name, action_name, resources, condition_keys
            )
        else:  # text
            self._format_action_details_text(
                service_name, action_name, resources, condition_keys
            )

    def format_action_details_enhanced(
        self,
        service_name: str,
        action_name: str,
        detailed_resources: List[Dict[str, Any]],
        action_condition_keys: List[Any],
        format_type: str = "table",
        action_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Format and display enhanced details for a specific action including annotations, SupportedBy, and Operations."""
        extra_meta = {}
        if action_metadata:
            for k in ("access_level", "plane", "annotations", "supported_by", "operations"):
                if k in action_metadata:
                    extra_meta[k] = action_metadata[k]

        if format_type == "json":
            data = {
                "service": service_name,
                "action": action_name,
                **extra_meta,
                "action_condition_keys": action_condition_keys,
                "resources": detailed_resources,
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {
                "service": service_name,
                "action": action_name,
                **extra_meta,
                "action_condition_keys": action_condition_keys,
                "resources": detailed_resources,
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_action_details_enhanced_table(
                service_name,
                action_name,
                detailed_resources,
                action_condition_keys,
                action_metadata=action_metadata,
            )
        else:  # text
            self._format_action_details_enhanced_text(
                service_name,
                action_name,
                detailed_resources,
                action_condition_keys,
                action_metadata=action_metadata,
            )

    def format_resource_details(
        self,
        service_name: str,
        resource_name: str,
        resource_details: Dict[str, Any],
        format_type: str = "table",
    ) -> None:
        """Format and display details for a specific resource."""
        if format_type == "json":
            data = {
                "service": service_name,
                "resource": resource_name,
                **resource_details,
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {
                "service": service_name,
                "resource": resource_name,
                **resource_details,
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_resource_details_table(
                service_name, resource_name, resource_details
            )
        else:  # text
            self._format_resource_details_text(
                service_name, resource_name, resource_details
            )

    def format_count(self, label: str, count: int) -> None:
        """Format and display a simple count."""
        panel = Panel(
            Text(str(count), style="bold blue", justify="center"),
            title=f"[bold]{label}[/bold]",
            title_align="left",
        )
        self.console.print(panel)

    def _format_services_table(self, services: List[Dict[str, Any]]) -> None:
        """Format services as a table including ServiceName and Modified date when present."""
        table = Table(
            title=f"Available AWS Services ({len(services)} total)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Service Code", style="cyan", no_wrap=True)
        table.add_column("Service Name", style="bright_white")
        table.add_column("Last Modified", style="yellow", no_wrap=True)
        table.add_column("URL", style="green")

        for service in sorted(services, key=lambda x: x.get("service", "")):
            svc_code = service.get("service", "")
            svc_display = service.get("serviceName", svc_code)
            mod_date = _format_modified_timestamp(service.get("modified"))
            table.add_row(svc_code, svc_display, mod_date, service.get("url", ""))

        self.console.print(table)

    def _format_services_text(self, services: List[Dict[str, Any]]) -> None:
        """Format services as plain text."""
        self.console.print("[bold]Available AWS services:[/bold]")
        for service in sorted(services, key=lambda x: x.get("service", "")):
            svc_code = service.get("service", "")
            svc_display = service.get("serviceName")
            if svc_display and svc_display.lower() != svc_code.lower():
                self.console.print(f"  • [cyan]{svc_code}[/cyan] ({svc_display})")
            else:
                self.console.print(f"  • [cyan]{svc_code}[/cyan]")

    def _format_actions_table(
        self,
        service_name: str,
        actions: List[Any],
        detailed_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Format actions as a table, including Access Level and Plane when detailed metadata is available."""
        table = Table(
            title=f"Actions for {service_name} ({len(actions)} total)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Action", style="cyan", no_wrap=True)

        if detailed_actions:
            table.add_column("Access Level", style="green")
            table.add_column("Plane", style="blue")
            table.add_column("Resources", style="yellow", justify="right")
            table.add_column("Condition Keys", style="magenta", justify="right")
            for act in detailed_actions:
                table.add_row(
                    str(act.get("name", "")),
                    str(act.get("access_level", "Read")),
                    str(act.get("plane", "Control Plane")),
                    str(act.get("resources_count", 0)),
                    str(act.get("condition_keys_count", 0)),
                )
        else:
            for action in actions:
                table.add_row(str(action))

        self.console.print(table)

    def _format_actions_text(
        self,
        service_name: str,
        actions: List[Any],
        detailed_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Format actions as plain text."""
        self.console.print(f"[bold]Actions for {service_name}:[/bold]")
        if detailed_actions:
            for act in detailed_actions:
                self.console.print(
                    f"  • [cyan]{act['name']}[/cyan] [{act.get('access_level', 'Read')} | {act.get('plane', 'Control Plane')}]"
                )
        else:
            for action in actions:
                self.console.print(f"  • [cyan]{action}[/cyan]")

    def _format_resources_table(
        self,
        service_name: str,
        action_name: str,
        resources: List[Dict[str, Any]],
    ) -> None:
        """Format resources as a table."""
        table = Table(
            title=f"Resources for {service_name}:{action_name} ({len(resources)} total)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Resource", style="cyan", no_wrap=True)
        table.add_column("ARN Format(s)", style="green")
        table.add_column("Context Keys", style="yellow")

        for resource in resources:
            arn_list = resource.get("arn_formats", ["N/A"])
            arn_formats = "\n".join(arn_list) if len(arn_list) > 1 else (arn_list[0] if arn_list else "N/A")
            raw_keys = resource.get("context_keys") or resource.get("condition_keys") or []
            formatted_keys = [_format_condition_key_item(k) for k in raw_keys]
            context_keys = "\n".join(formatted_keys) if formatted_keys else "None"
            table.add_row(resource["name"], arn_formats, context_keys)

        self.console.print(table)

    def _format_resources_text(
        self,
        service_name: str,
        action_name: str,
        resources: List[Dict[str, Any]],
    ) -> None:
        """Format resources as plain text."""
        self.console.print(
            f"[bold]Resources for {service_name}:{action_name}:[/bold]"
        )
        for resource in resources:
            self.console.print(f"\n  [cyan]Resource:[/cyan] {resource['name']}")
            arn_list = resource.get("arn_formats", ["N/A"])
            if len(arn_list) == 1:
                self.console.print(f"    [green]ARN Format:[/green] {arn_list[0]}")
            else:
                self.console.print("    [green]ARN Formats:[/green]")
                for arn_format in arn_list:
                    self.console.print(f"      • {arn_format}")
            raw_keys = resource.get("context_keys") or resource.get("condition_keys") or []
            formatted_keys = [_format_condition_key_item(k) for k in raw_keys]
            if formatted_keys:
                self.console.print(
                    f"    [yellow]Context Keys:[/yellow] {', '.join(formatted_keys)}"
                )
            else:
                self.console.print("    [yellow]Context Keys:[/yellow] None")

    def _format_action_details_table(
        self,
        service_name: str,
        action_name: str,
        resources: List[str],
        condition_keys: List[str],
    ) -> None:
        """Format action details as a table."""
        table = Table(
            title=f"Action Details: {service_name}:{action_name}",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Property", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("Resources", ", ".join(resources) if resources else "None")
        table.add_row(
            "Condition Keys", ", ".join(condition_keys) if condition_keys else "None"
        )

        self.console.print(table)

    def _format_action_details_text(
        self,
        service_name: str,
        action_name: str,
        resources: List[str],
        condition_keys: List[str],
    ) -> None:
        """Format action details as plain text."""
        self.console.print(f"[bold]Action details for {service_name}:{action_name}[/bold]")
        self.console.print(
            f"  [cyan]Resources:[/cyan] {', '.join(resources) if resources else 'None'}"
        )
        self.console.print(
            f"  [yellow]Action Condition Keys:[/yellow] {', '.join(condition_keys) if condition_keys else 'None'}"
        )

    def _format_action_details_enhanced_table(
        self,
        service_name: str,
        action_name: str,
        resources: List[Dict[str, Any]],
        condition_keys: List[Any],
        action_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Format action details in an enhanced table format with fixed condition key rendering and new metadata."""
        title_str = f"{service_name}:{action_name}"
        if action_metadata:
            acc = action_metadata.get("access_level")
            plane = action_metadata.get("plane")
            if acc and plane:
                title_str = f"{service_name}:{action_name} [{acc} | {plane}]"

        table = Table(title=title_str, show_header=True, header_style="bold magenta")
        table.add_column("Resource", style="cyan", no_wrap=True)
        table.add_column("ARN Format", style="green")
        table.add_column("Resource Condition Keys", style="yellow")

        for resource in resources:
            arn_formats = (
                "\n".join(resource["arn_formats"])
                if resource.get("arn_formats")
                else "N/A"
            )
            resource_condition_keys = resource.get("condition_keys", [])
            if resource_condition_keys:
                resource_condition_keys_str = "\n".join(
                    [_format_condition_key_item(ck) for ck in resource_condition_keys]
                )
            else:
                resource_condition_keys_str = "None"
            table.add_row(
                resource["name"], arn_formats, resource_condition_keys_str
            )

        self.console.print(table)

        if condition_keys:
            cond_keys_str = "\n".join(
                [_format_condition_key_item(ck) for ck in condition_keys]
            )
            panel = Panel(
                Text(cond_keys_str, style="yellow"),
                title="[bold]Action Condition Keys[/bold]",
                title_align="left",
            )
            self.console.print(panel)
        else:
            self.console.print(
                Panel(
                    Text("None", style="yellow"),
                    title="[bold]Action Condition Keys[/bold]",
                    title_align="left",
                )
            )

        if action_metadata:
            meta_lines: List[str] = []
            supported_by = action_metadata.get("supported_by", {})
            if isinstance(supported_by, dict) and supported_by:
                sb_parts = [
                    f"{k}: {'Yes' if v else 'No'}" for k, v in supported_by.items()
                ]
                meta_lines.append("Supported By: " + " | ".join(sb_parts))

            ops = action_metadata.get("operations", [])
            if isinstance(ops, list) and ops:
                op_names = [op.get("Name", "") for op in ops if isinstance(op, dict)]
                sdk_methods = []
                for op in ops:
                    if isinstance(op, dict):
                        for s in op.get("SDK", []):
                            if isinstance(s, dict):
                                sdk_methods.append(
                                    f"{s.get('Package', 'SDK')}:{s.get('Name', '')}.{s.get('Method', '')}"
                                )
                if op_names:
                    meta_lines.append("API Operations: " + ", ".join(op_names))
                if sdk_methods:
                    meta_lines.append("SDK Methods: " + ", ".join(sdk_methods))

            if meta_lines:
                self.console.print(
                    Panel(
                        Text("\n".join(meta_lines), style="cyan"),
                        title="[bold]Action Metadata & SDK Mapping[/bold]",
                        title_align="left",
                    )
                )

    def _format_action_details_enhanced_text(
        self,
        service_name: str,
        action_name: str,
        detailed_resources: List[Dict[str, Any]],
        action_condition_keys: List[Any],
        action_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Format enhanced action details as plain text."""
        self.console.print(
            f"[bold]Enhanced Action details for {service_name}:{action_name}[/bold]"
        )
        if action_metadata:
            acc = action_metadata.get("access_level")
            plane = action_metadata.get("plane")
            if acc:
                self.console.print(f"  [green]Access Level:[/green] {acc}")
            if plane:
                self.console.print(f"  [blue]Plane:[/blue] {plane}")

        self.console.print("\n[bold cyan]Resources:[/bold cyan]")
        for resource in detailed_resources:
            self.console.print(f"  [cyan]• {resource['name']}[/cyan]")
            if len(resource["arn_formats"]) == 1:
                self.console.print(
                    f"    [green]ARN Format:[/green] {resource['arn_formats'][0]}"
                )
            else:
                self.console.print("    [green]ARN Formats:[/green]")
                for arn_format in resource["arn_formats"]:
                    self.console.print(f"      • {arn_format}")
            resource_condition_keys = resource.get("condition_keys", [])
            if resource_condition_keys:
                cond_keys_str = ", ".join(
                    [_format_condition_key_item(ck) for ck in resource_condition_keys]
                )
            else:
                cond_keys_str = "None"
            self.console.print(
                f"    [yellow]Resource Context Keys:[/yellow] {cond_keys_str}"
            )

        if action_condition_keys:
            cond_keys_str = ", ".join(
                [_format_condition_key_item(ck) for ck in action_condition_keys]
            )
            self.console.print(
                f"\n[bold yellow]Action-Level Condition Keys:[/bold yellow] {cond_keys_str}"
            )
        else:
            self.console.print(
                "\n[bold yellow]Action-Level Condition Keys:[/bold yellow] None"
            )

    def _format_resource_details_table(
        self,
        service_name: str,
        resource_name: str,
        resource_details: Dict[str, Any],
    ) -> None:
        """Format resource details as a table (fixing crash when context_keys is a list of dicts)."""
        table = Table(
            title=f"Resource Details: {service_name}:{resource_name}",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Property", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="green")

        if len(resource_details["arn_formats"]) == 1:
            table.add_row("ARN Format", resource_details["arn_formats"][0])
        else:
            table.add_row(
                "ARN Formats", "\n".join(resource_details["arn_formats"])
            )

        raw_keys = resource_details.get("context_keys", [])
        formatted_keys = [_format_condition_key_item(ck) for ck in raw_keys]
        table.add_row(
            "Context Keys",
            "\n".join(formatted_keys) if formatted_keys else "None",
        )

        self.console.print(table)

    def _format_resource_details_text(
        self,
        service_name: str,
        resource_name: str,
        resource_details: Dict[str, Any],
    ) -> None:
        """Format resource details as plain text (fixing crash when context_keys is a list of dicts)."""
        self.console.print(
            f"[bold]Resource details for {service_name}:{resource_name}[/bold]"
        )
        if len(resource_details["arn_formats"]) == 1:
            self.console.print(
                f"  [green]ARN Format:[/green] {resource_details['arn_formats'][0]}"
            )
        else:
            self.console.print("  [green]ARN Formats:[/green]")
            for arn_format in resource_details["arn_formats"]:
                self.console.print(f"    • {arn_format}")
        raw_keys = resource_details.get("context_keys", [])
        formatted_keys = [_format_condition_key_item(ck) for ck in raw_keys]
        if formatted_keys:
            self.console.print(
                f"  [yellow]Resource Condition Keys:[/yellow] {', '.join(formatted_keys)}"
            )
        else:
            self.console.print("  [yellow]Resource Condition Keys:[/yellow] None")

    def format_context_keys_list(
        self,
        service_name: str,
        context_keys: List[str],
        format_type: str = "table",
    ) -> None:
        """Format and display list of context keys for a service."""
        if format_type == "json":
            data = {
                "service": service_name,
                "context_keys": context_keys,
                "count": len(context_keys),
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {
                "service": service_name,
                "context_keys": context_keys,
                "count": len(context_keys),
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_context_keys_table(service_name, context_keys)
        else:  # text
            self._format_context_keys_text(service_name, context_keys)

    def format_context_keys_with_metadata(
        self,
        service_name: str,
        context_keys_with_metadata: List[Dict[str, Any]],
        format_type: str = "json",
    ) -> None:
        """Format and display context keys with full metadata for a service."""
        if format_type == "json":
            data = {
                "service": service_name,
                "context_keys": context_keys_with_metadata,
                "count": len(context_keys_with_metadata),
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {
                "service": service_name,
                "context_keys": context_keys_with_metadata,
                "count": len(context_keys_with_metadata),
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "text":
            self.console.print(f"[bold]Context Keys for {service_name}:[/bold]")
            for key_data in context_keys_with_metadata:
                self.console.print(
                    f"  • [yellow]{_format_condition_key_item(key_data)}[/yellow]"
                )
        else:
            self._format_context_keys_with_metadata_table(
                service_name, context_keys_with_metadata
            )

    def format_all_context_keys(
        self,
        context_keys_by_service: Dict[str, List[str]],
        format_type: str = "table",
    ) -> None:
        """Format and display all context keys across AWS services."""
        if format_type == "json":
            self.console.print(json.dumps(context_keys_by_service, indent=2))
        elif format_type == "yaml":
            self.console.print(
                yaml.dump(context_keys_by_service, default_flow_style=False)
            )
        elif format_type == "table":
            self._format_all_context_keys_table(context_keys_by_service)
        else:  # text
            self._format_all_context_keys_text(context_keys_by_service)

    def format_flattened_context_keys(
        self, context_keys: List[str], format_type: str = "table"
    ) -> None:
        """Format and display a flattened list of all unique context keys."""
        if format_type == "json":
            data = {"all_context_keys": context_keys, "count": len(context_keys)}
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {"all_context_keys": context_keys, "count": len(context_keys)}
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_flattened_context_keys_table(context_keys)
        else:  # text
            self._format_flattened_context_keys_text(context_keys)

    def _format_context_keys_table(
        self, service_name: str, context_keys: List[str]
    ) -> None:
        """Format context keys for a service as a table."""
        table = Table(
            title=f"Context Keys for {service_name} ({len(context_keys)} total)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Context Key", style="yellow")

        for key in context_keys:
            table.add_row(_format_condition_key_item(key))

        self.console.print(table)

    def _format_context_keys_text(
        self, service_name: str, context_keys: List[str]
    ) -> None:
        """Format context keys for a service as plain text."""
        self.console.print(f"[bold]Context Keys for {service_name}:[/bold]")
        for key in context_keys:
            self.console.print(f"  • [yellow]{_format_condition_key_item(key)}[/yellow]")

    def _format_context_keys_with_metadata_table(
        self,
        service_name: str,
        context_keys_with_metadata: List[Dict[str, Any]],
    ) -> None:
        """Format context keys with metadata for a service as a table."""
        table = Table(
            title=f"Context Keys for {service_name} ({len(context_keys_with_metadata)} total)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Context Key", style="yellow")
        table.add_column("Types", style="blue")

        for key_data in context_keys_with_metadata:
            key_name = key_data.get("Name") or key_data.get("name") or "Unknown"
            key_types = ", ".join(key_data.get("Types", ["Unknown"]))
            table.add_row(key_name, key_types)

        self.console.print(table)

    def _format_all_context_keys_table(
        self, context_keys_by_service: Dict[str, List[str]]
    ) -> None:
        """Format all context keys across services as a table."""
        table = Table(
            title=f"Context Keys by Service ({len(context_keys_by_service)} services)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Count", style="blue", justify="right")
        table.add_column("Context Keys", style="yellow")

        for service_name in sorted(context_keys_by_service.keys()):
            keys = context_keys_by_service[service_name]
            keys_display = ", ".join(keys[:5])
            if len(keys) > 5:
                keys_display += f"... (+{len(keys) - 5} more)"

            table.add_row(service_name, str(len(keys)), keys_display)

        self.console.print(table)

    def _format_all_context_keys_text(
        self, context_keys_by_service: Dict[str, List[str]]
    ) -> None:
        """Format all context keys across services as plain text."""
        self.console.print(
            f"[bold]Context Keys by Service ({len(context_keys_by_service)} services):[/bold]"
        )
        for service_name in sorted(context_keys_by_service.keys()):
            keys = context_keys_by_service[service_name]
            self.console.print(
                f"\n  [cyan]{service_name}[/cyan] ([blue]{len(keys)}[/blue] keys):"
            )
            for key in keys[:10]:
                self.console.print(f"    • [yellow]{key}[/yellow]")
            if len(keys) > 10:
                self.console.print(f"    ... and {len(keys) - 10} more")

    def _format_flattened_context_keys_table(
        self, context_keys: List[str]
    ) -> None:
        """Format flattened context keys as a table."""
        table = Table(
            title=f"All Unique Context Keys Across AWS ({len(context_keys)} total)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Context Key", style="yellow")

        for key in context_keys:
            table.add_row(key)

        self.console.print(table)

    def _format_flattened_context_keys_text(
        self, context_keys: List[str]
    ) -> None:
        """Format flattened context keys as plain text."""
        self.console.print(
            f"[bold]All Unique Context Keys Across AWS ({len(context_keys)} total):[/bold]"
        )
        for key in context_keys:
            self.console.print(f"  • [yellow]{key}[/yellow]")
