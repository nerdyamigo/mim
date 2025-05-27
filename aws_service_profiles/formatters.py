"""Output formatters for AWS service data."""

import json
import yaml
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from tabulate import tabulate


class OutputFormatter:
    """Base class for output formatters."""
    
    def __init__(self, use_color: bool = True):
        self.console = Console(color_system="auto" if use_color else None)
    
    def format_services_list(self, services: List[Dict[str, str]], format_type: str = "table") -> None:
        """Format and display list of AWS services."""
        if format_type == "json":
            self.console.print(json.dumps(services, indent=2))
        elif format_type == "yaml":
            self.console.print(yaml.dump(services, default_flow_style=False))
        elif format_type == "table":
            self._format_services_table(services)
        else:  # text
            self._format_services_text(services)
    
    def format_actions_list(self, service_name: str, actions: List[str], format_type: str = "table") -> None:
        """Format and display list of actions for a service."""
        if format_type == "json":
            data = {"service": service_name, "actions": actions, "count": len(actions)}
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {"service": service_name, "actions": actions, "count": len(actions)}
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_actions_table(service_name, actions)
        else:  # text
            self._format_actions_text(service_name, actions)
    
    def format_resources_list(self, service_name: str, action_name: str, resources: List[Dict[str, Any]], format_type: str = "table") -> None:
        """Format and display list of resources for a service action."""
        if format_type == "json":
            data = {"service": service_name, "action": action_name, "resources": resources, "count": len(resources)}
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {"service": service_name, "action": action_name, "resources": resources, "count": len(resources)}
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_resources_table(service_name, action_name, resources)
        else:  # text
            self._format_resources_text(service_name, action_name, resources)
    
    def format_action_details(self, service_name: str, action_name: str, resources: List[str], condition_keys: List[str], format_type: str = "table") -> None:
        """Format and display details for a specific action."""
        if format_type == "json":
            data = {
                "service": service_name,
                "action": action_name,
                "resources": resources,
                "condition_keys": condition_keys
            }
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {
                "service": service_name,
                "action": action_name,
                "resources": resources,
                "condition_keys": condition_keys
            }
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_action_details_table(service_name, action_name, resources, condition_keys)
        else:  # text
            self._format_action_details_text(service_name, action_name, resources, condition_keys)
    
    def format_resource_details(self, service_name: str, resource_name: str, resource_details: Dict[str, Any], format_type: str = "table") -> None:
        """Format and display details for a specific resource."""
        if format_type == "json":
            data = {"service": service_name, "resource": resource_name, **resource_details}
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {"service": service_name, "resource": resource_name, **resource_details}
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_resource_details_table(service_name, resource_name, resource_details)
        else:  # text
            self._format_resource_details_text(service_name, resource_name, resource_details)
    
    def format_count(self, label: str, count: int) -> None:
        """Format and display a simple count."""
        panel = Panel(
            Text(str(count), style="bold blue", justify="center"),
            title=f"[bold]{label}[/bold]",
            title_align="left"
        )
        self.console.print(panel)
    
    def _format_services_table(self, services: List[Dict[str, str]]) -> None:
        """Format services as a table."""
        table = Table(title="Available AWS Services", show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("URL", style="green")
        
        for service in sorted(services, key=lambda x: x['service']):
            table.add_row(service['service'], service['url'])
        
        self.console.print(table)
    
    def _format_services_text(self, services: List[Dict[str, str]]) -> None:
        """Format services as plain text."""
        self.console.print("[bold]Available AWS services:[/bold]")
        for service in sorted(services, key=lambda x: x['service']):
            self.console.print(f"  • [cyan]{service['service']}[/cyan]")
    
    def _format_actions_table(self, service_name: str, actions: List[str]) -> None:
        """Format actions as a table."""
        table = Table(title=f"Actions for {service_name} ({len(actions)} total)", show_header=True, header_style="bold magenta")
        table.add_column("Action", style="cyan")
        
        for action in actions:
            table.add_row(action)
        
        self.console.print(table)
    
    def _format_actions_text(self, service_name: str, actions: List[str]) -> None:
        """Format actions as plain text."""
        self.console.print(f"[bold]Actions for {service_name}:[/bold]")
        for action in actions:
            self.console.print(f"  • [cyan]{action}[/cyan]")
    
    def _format_resources_table(self, service_name: str, action_name: str, resources: List[Dict[str, Any]]) -> None:
        """Format resources as a table."""
        table = Table(
            title=f"Resources for {service_name}:{action_name} ({len(resources)} total)",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Resource", style="cyan", no_wrap=True)
        table.add_column("ARN Format(s)", style="green")
        table.add_column("Context Keys", style="yellow")
        
        for resource in resources:
            arn_formats = "\n".join(resource['arn_formats']) if len(resource['arn_formats']) > 1 else resource['arn_formats'][0]
            context_keys = "\n".join(resource['context_keys']) if resource['context_keys'] else "None"
            table.add_row(resource['name'], arn_formats, context_keys)
        
        self.console.print(table)
    
    def _format_resources_text(self, service_name: str, action_name: str, resources: List[Dict[str, Any]]) -> None:
        """Format resources as plain text."""
        self.console.print(f"[bold]Resources for {service_name}:{action_name}:[/bold]")
        for resource in resources:
            self.console.print(f"\n  [cyan]Resource:[/cyan] {resource['name']}")
            if len(resource['arn_formats']) == 1:
                self.console.print(f"    [green]ARN Format:[/green] {resource['arn_formats'][0]}")
            else:
                self.console.print(f"    [green]ARN Formats:[/green]")
                for arn_format in resource['arn_formats']:
                    self.console.print(f"      • {arn_format}")
            if resource['context_keys']:
                self.console.print(f"    [yellow]Context Keys:[/yellow] {', '.join(resource['context_keys'])}")
            else:
                self.console.print(f"    [yellow]Context Keys:[/yellow] None")
    
    def _format_action_details_table(self, service_name: str, action_name: str, resources: List[str], condition_keys: List[str]) -> None:
        """Format action details as a table."""
        table = Table(title=f"Action Details: {service_name}:{action_name}", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Resources", ", ".join(resources) if resources else "None")
        table.add_row("Condition Keys", ", ".join(condition_keys) if condition_keys else "None")
        
        self.console.print(table)
    
    def _format_action_details_text(self, service_name: str, action_name: str, resources: List[str], condition_keys: List[str]) -> None:
        """Format action details as plain text."""
        self.console.print(f"[bold]Action details for {service_name}:{action_name}[/bold]")
        self.console.print(f"  [cyan]Resources:[/cyan] {', '.join(resources) if resources else 'None'}")
        self.console.print(f"  [yellow]Action Condition Keys:[/yellow] {', '.join(condition_keys) if condition_keys else 'None'}")
    
    def _format_resource_details_table(self, service_name: str, resource_name: str, resource_details: Dict[str, Any]) -> None:
        """Format resource details as a table."""
        table = Table(title=f"Resource Details: {service_name}:{resource_name}", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        if len(resource_details['arn_formats']) == 1:
            table.add_row("ARN Format", resource_details['arn_formats'][0])
        else:
            table.add_row("ARN Formats", "\n".join(resource_details['arn_formats']))
        
        table.add_row("Context Keys", ", ".join(resource_details['context_keys']) if resource_details['context_keys'] else "None")
        
        self.console.print(table)
    
    def _format_resource_details_text(self, service_name: str, resource_name: str, resource_details: Dict[str, Any]) -> None:
        """Format resource details as plain text."""
        self.console.print(f"[bold]Resource details for {service_name}:{resource_name}[/bold]")
        if len(resource_details['arn_formats']) == 1:
            self.console.print(f"  [green]ARN Format:[/green] {resource_details['arn_formats'][0]}")
        else:
            self.console.print(f"  [green]ARN Formats:[/green]")
            for arn_format in resource_details['arn_formats']:
                self.console.print(f"    • {arn_format}")
        if resource_details['context_keys']:
            self.console.print(f"  [yellow]Resource Condition Keys:[/yellow] {', '.join(resource_details['context_keys'])}")
        else:
            self.console.print(f"  [yellow]Resource Condition Keys:[/yellow] None")
    
    def format_context_keys_list(self, service_name: str, context_keys: List[str], format_type: str = "table") -> None:
        """Format and display list of context keys for a service."""
        if format_type == "json":
            data = {"service": service_name, "context_keys": context_keys, "count": len(context_keys)}
            self.console.print(json.dumps(data, indent=2))
        elif format_type == "yaml":
            data = {"service": service_name, "context_keys": context_keys, "count": len(context_keys)}
            self.console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            self._format_context_keys_table(service_name, context_keys)
        else:  # text
            self._format_context_keys_text(service_name, context_keys)
    
    def format_all_context_keys(self, context_keys_by_service: Dict[str, List[str]], format_type: str = "table") -> None:
        """Format and display all context keys across AWS services."""
        if format_type == "json":
            self.console.print(json.dumps(context_keys_by_service, indent=2))
        elif format_type == "yaml":
            self.console.print(yaml.dump(context_keys_by_service, default_flow_style=False))
        elif format_type == "table":
            self._format_all_context_keys_table(context_keys_by_service)
        else:  # text
            self._format_all_context_keys_text(context_keys_by_service)
    
    def format_flattened_context_keys(self, context_keys: List[str], format_type: str = "table") -> None:
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
    
    def _format_context_keys_table(self, service_name: str, context_keys: List[str]) -> None:
        """Format context keys for a service as a table."""
        table = Table(
            title=f"Context Keys for {service_name} ({len(context_keys)} total)",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Context Key", style="yellow")
        
        for key in context_keys:
            table.add_row(key)
        
        self.console.print(table)
    
    def _format_context_keys_text(self, service_name: str, context_keys: List[str]) -> None:
        """Format context keys for a service as plain text."""
        self.console.print(f"[bold]Context Keys for {service_name}:[/bold]")
        for key in context_keys:
            self.console.print(f"  • [yellow]{key}[/yellow]")
    
    def _format_all_context_keys_table(self, context_keys_by_service: Dict[str, List[str]]) -> None:
        """Format all context keys across services as a table."""
        table = Table(
            title=f"Context Keys by Service ({len(context_keys_by_service)} services)",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Count", style="blue", justify="right")
        table.add_column("Context Keys", style="yellow")
        
        for service_name in sorted(context_keys_by_service.keys()):
            keys = context_keys_by_service[service_name]
            keys_display = ", ".join(keys[:5])  # Show first 5 keys
            if len(keys) > 5:
                keys_display += f"... (+{len(keys) - 5} more)"
            
            table.add_row(service_name, str(len(keys)), keys_display)
        
        self.console.print(table)
    
    def _format_all_context_keys_text(self, context_keys_by_service: Dict[str, List[str]]) -> None:
        """Format all context keys across services as plain text."""
        self.console.print(f"[bold]Context Keys by Service ({len(context_keys_by_service)} services):[/bold]")
        for service_name in sorted(context_keys_by_service.keys()):
            keys = context_keys_by_service[service_name]
            self.console.print(f"\n  [cyan]{service_name}[/cyan] ([blue]{len(keys)}[/blue] keys):")
            for key in keys[:10]:  # Show first 10 keys
                self.console.print(f"    • [yellow]{key}[/yellow]")
            if len(keys) > 10:
                self.console.print(f"    ... and {len(keys) - 10} more")
    
    def _format_flattened_context_keys_table(self, context_keys: List[str]) -> None:
        """Format flattened context keys as a table."""
        table = Table(
            title=f"All Unique Context Keys Across AWS ({len(context_keys)} total)",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Context Key", style="yellow")
        
        for key in context_keys:
            table.add_row(key)
        
        self.console.print(table)
    
    def _format_flattened_context_keys_text(self, context_keys: List[str]) -> None:
        """Format flattened context keys as plain text."""
        self.console.print(f"[bold]All Unique Context Keys Across AWS ({len(context_keys)} total):[/bold]")
        for key in context_keys:
            self.console.print(f"  • [yellow]{key}[/yellow]")