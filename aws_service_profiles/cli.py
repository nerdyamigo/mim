"""CLI interface for AWS Service Profiles."""

import click
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .aws_client import AWSClient
from .formatters import OutputFormatter
from .service_helper import ServiceHelper, validate_service_name
import json
import yaml
import fnmatch


class ServiceAwareCommand(click.Command):
    """Custom Click command that provides service-specific help."""
    
    def get_help(self, ctx):
        """Get help text with optional service-specific information."""
        # Check if service name is provided as first argument
        service_name = None
        if ctx.params.get('service_name'):
            service_name = ctx.params['service_name']
        elif len(ctx.args) > 0:
            # If service name is in args but not yet parsed
            potential_service = ctx.args[0]
            if not potential_service.startswith('-'):
                service_name = potential_service
        
        # If service name is provided and we're not in a global flag context, show service help
        if (service_name and 
            not any(ctx.params.get(flag) for flag in [
                'list_services', 'list_all_context_keys', 
                'list_global_context_keys', 'list_service_context_keys'
            ])):
            
            try:
                client = AWSClient()
                helper = ServiceHelper(client)
                
                # Check if service is valid before showing detailed help
                if helper.is_valid_service(service_name):
                    # Show service-specific help
                    service_help = helper.format_service_help(service_name)
                    return service_help
            except Exception:
                # Fall back to default help if service help fails
                pass
        
        # Default help
        return super().get_help(ctx)


def print_all_actions_for_service(client: AWSClient, service_name: str) -> None:
    """Print all actions for a service in a readable format."""
    actions = client.get_all_actions_for_service(service_name)
    if actions:
        click.echo(f"Actions for {service_name}:")
        for action in actions:
            click.echo(f"  - {action}")
    else:
        click.echo(f"No actions found for service '{service_name}'", err=True)


def print_resources_for_service_action(client: AWSClient, service_name: str, action_name: str) -> None:
    """Print all resources for a specific service action in a readable format."""
    resources = client.get_resources_for_service_action(service_name, action_name)
    if resources:
        click.echo(f"Resources for {service_name}:{action_name}:")
        for resource in resources:
            click.echo(f"  - {resource}")
    else:
        click.echo(f"No resources found for action '{action_name}' in service '{service_name}'", err=True)


def expand_wildcard_actions(client: AWSClient, service: str, action_pattern: str) -> List[str]:
    """Expand a wildcard pattern to a list of matching actions for a service."""
    try:
        # Get all actions for the service
        all_actions = client.get_all_actions_for_service(service)
        # Filter actions that match the pattern
        matching_actions = [action for action in all_actions if fnmatch.fnmatch(action, action_pattern)]
        return matching_actions
    except Exception as e:
        click.echo(f"Error expanding wildcard for {service}:{action_pattern}: {str(e)}", err=True)
        return []


def parse_service_action_input(service_actions: List[str]) -> List[Tuple[str, str]]:
    """Parse service:action format input into service-action pairs."""
    pairs = []
    for input_str in service_actions:
        # Split by comma and strip whitespace
        service_action_list = [sa.strip() for sa in input_str.split(',')]
        
        for service_action in service_action_list:
            try:
                service, action = service_action.split(':', 1)
                pairs.append((service.strip(), action.strip()))
            except ValueError:
                raise click.UsageError(
                    f"Invalid format: '{service_action}'. Expected format is 'service:action'.\n"
                    "Example: s3:GetObject or sagemaker:CreateTrainingJob\n"
                    "Multiple pairs can be comma-separated: s3:GetObject,s3:PutObject,sagemaker:CreateTrainingJob\n"
                    "Wildcards are supported: sagemaker:Create*"
                )
    return pairs


def process_service_action(client: AWSClient, service: str, action: str) -> Dict[str, Any]:
    """Process a single service-action pair and return the results."""
    try:
        # Check if action contains wildcards
        if '*' in action or '?' in action:
            # Expand wildcard pattern
            matching_actions = expand_wildcard_actions(client, service, action)
            if not matching_actions:
                return {
                    'service': service,
                    'action': action,
                    'error': f"No actions found matching pattern '{action}'"
                }
            
            # Process each matching action
            results = []
            for matched_action in matching_actions:
                try:
                    # Get action metadata with enhanced condition keys
                    action_metadata = client.get_action_metadata_with_full_condition_keys(service, matched_action)
                    if not action_metadata:
                        results.append({
                            'service': service,
                            'action': matched_action,
                            'error': f"Action '{matched_action}' not found for service '{service}'"
                        })
                        continue
                    
                    results.append({
                        'service': service,
                        'action': matched_action,
                        'resources': action_metadata['resources'],
                        'condition_keys': action_metadata['condition_keys']
                    })
                except Exception as e:
                    results.append({
                        'service': service,
                        'action': matched_action,
                        'error': str(e)
                    })
            
            return {
                'service': service,
                'pattern': action,
                'matched_actions': results
            }
        else:
            # Process single action with enhanced condition keys
            action_metadata = client.get_action_metadata_with_full_condition_keys(service, action)
            if not action_metadata:
                return {
                    'service': service,
                    'action': action,
                    'error': f"Action '{action}' not found for service '{service}'"
                }
            
            return {
                'service': service,
                'action': action,
                'resources': action_metadata['resources'],
                'condition_keys': action_metadata['condition_keys']
            }
    except Exception as e:
        return {
            'service': service,
            'action': action,
            'error': str(e)
        }


@click.command(cls=ServiceAwareCommand)
@click.argument('service_name', required=False)
@click.argument('action_name', required=False)
@click.option('--format', '-f', type=click.Choice(['table', 'text', 'json', 'yaml']), default='table',
              help='Output format: table (default), text, json, or yaml')
@click.option('--count', is_flag=True, help='Show only count instead of full list')
@click.option('--no-color', is_flag=True, help='Disable colored output')
@click.option('--list-services', is_flag=True, help='List all available AWS services')
@click.option('--list-all-context-keys', is_flag=True, help='List all unique context keys across all AWS services')
@click.option('--list-global-context-keys', is_flag=True, help='List all AWS global context keys (aws:) across all services')
@click.option('--list-service-context-keys', is_flag=True, help='List all service-specific context keys across all services')
@click.option('--context-keys', is_flag=True, help='Show all unique context keys for the service')
@click.option('--global-context-keys', is_flag=True, help='Show only AWS global context keys (aws:) for the service')
@click.option('--service-context-keys', is_flag=True, help='Show only service-specific context keys for the service')
@click.option('--resources', is_flag=True, help='Show all unique resources for the service')
@click.option('--action', help='Get details for a specific action')
@click.option('--resource', help='Get details for a specific resource')
@click.option('--service-actions', '-sa', help='Specify comma-separated service:action pairs (e.g., s3:GetObject,s3:PutObject,sagemaker:Create*)')
@click.pass_context
def cli(ctx, service_name, action_name, format, count, no_color, list_services, list_all_context_keys, list_global_context_keys, list_service_context_keys, context_keys, global_context_keys, service_context_keys, resources, action, resource, service_actions):
    """
    AWS Service Profiles CLI - Get AWS service actions and resources
    
    Usage:
    - python main.py <service>                        → Get all actions for the service
    - python main.py <service> <action>               → Get all resources for the service/action
    - python main.py <service> --resources            → Get all unique resources for the service
    - python main.py <service> --context-keys         → Get all unique context keys for the service
    - python main.py <service> --global-context-keys  → Get AWS global context keys for the service
    - python main.py <service> --service-context-keys → Get service-specific context keys for the service
    - python main.py <service> --action <action>      → Get details for a specific action
    - python main.py <service> --resource <resource>  → Get details for a specific resource
    - python main.py --list-services                  → List all available services
    - python main.py --list-all-context-keys          → List all unique context keys across AWS
    - python main.py --list-global-context-keys       → List all AWS global context keys
    - python main.py --list-service-context-keys      → List all service-specific context keys
    - python main.py -sa s3:GetObject,s3:PutObject,sagemaker:Create*  → Get metadata for specific service/action pairs (wildcards supported)
    """
    
    client = AWSClient()
    formatter = OutputFormatter(use_color=not no_color)
    
    # Handle service-action pairs
    if service_actions:
        try:
            # Parse service-action pairs
            service_action_pairs = parse_service_action_input([service_actions])
            
            # Validate all services
            helper = ServiceHelper(client)
            invalid_services = [service for service, _ in service_action_pairs if not helper.is_valid_service(service)]
            if invalid_services:
                for service in invalid_services:
                    suggestions = helper.get_similar_services(service)
                    click.echo(f"Error: Invalid service name '{service}'", err=True)
                    if suggestions:
                        click.echo("\nDid you mean one of these?", err=True)
                        for suggestion in suggestions:
                            click.echo(f"  • {suggestion}", err=True)
                return
            
            # Process service-action pairs
            all_results = []
            with ThreadPoolExecutor() as executor:
                futures = []
                for service, action in service_action_pairs:
                    futures.append(executor.submit(process_service_action, client, service, action))
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        click.echo(f"Error processing service/action: {str(e)}", err=True)
            
            # Format results
            if format == "json":
                print(json.dumps(all_results, indent=2))
            elif format == "yaml":
                formatter.console.print(yaml.dump(all_results, default_flow_style=False))
            elif format == "table":
                for result in all_results:
                    if 'error' in result:
                        click.echo(f"Error for {result['service']}:{result['action']}: {result['error']}", err=True)
                        continue
                    
                    if 'matched_actions' in result:
                        # Handle wildcard expansion results
                        for matched_result in result['matched_actions']:
                            if 'error' in matched_result:
                                click.echo(f"Error for {matched_result['service']}:{matched_result['action']}: {matched_result['error']}", err=True)
                                continue
                            formatter.format_action_details_enhanced(
                                matched_result['service'],
                                matched_result['action'],
                                matched_result['resources'],
                                matched_result['condition_keys'],
                                format
                            )
                    else:
                        formatter.format_action_details_enhanced(
                            result['service'],
                            result['action'],
                            result['resources'],
                            result['condition_keys'],
                            format
                        )
            else:  # text
                for result in all_results:
                    if 'error' in result:
                        click.echo(f"Error for {result['service']}:{result['action']}: {result['error']}", err=True)
                        continue
                    
                    if 'matched_actions' in result:
                        # Handle wildcard expansion results
                        for matched_result in result['matched_actions']:
                            if 'error' in matched_result:
                                click.echo(f"Error for {matched_result['service']}:{matched_result['action']}: {matched_result['error']}", err=True)
                                continue
                            formatter.format_action_details_enhanced(
                                matched_result['service'],
                                matched_result['action'],
                                matched_result['resources'],
                                matched_result['condition_keys'],
                                format
                            )
                    else:
                        formatter.format_action_details_enhanced(
                            result['service'],
                            result['action'],
                            result['resources'],
                            result['condition_keys'],
                            format
                        )
            return
            
        except click.UsageError as e:
            click.echo(str(e), err=True)
            return
    
    if list_services:
        all_services = client.get_aws_services_urls()
        if all_services:
            formatter.format_services_list(all_services, format)
        else:
            click.echo("No services found", err=True)
        return
    
    if list_all_context_keys:
        if count:
            # Get flattened list for count
            all_keys = client.get_all_unique_context_keys_flattened()
            formatter.format_count("Total unique context keys across all AWS services", len(all_keys))
        else:
            # Get detailed breakdown by service with progress indicator
            context_keys_by_service = client.get_all_unique_context_keys_across_aws(show_progress=True)
            if context_keys_by_service:
                formatter.format_all_context_keys(context_keys_by_service, format)
            else:
                click.echo("No context keys found", err=True)
        return
    
    if list_global_context_keys:
        global_keys = client.get_all_global_context_keys_across_aws()
        if global_keys:
            if count:
                formatter.format_count("Total AWS global context keys across all services", len(global_keys))
            else:
                formatter.format_flattened_context_keys(global_keys, format)
        else:
            click.echo("No global context keys found", err=True)
        return
    
    if list_service_context_keys:
        if count:
            # Get flattened count of service-specific keys
            service_keys = client.get_all_service_specific_context_keys_flattened()
            formatter.format_count("Total service-specific context keys across all AWS services", len(service_keys))
        else:
            # Get detailed breakdown by service
            service_keys_by_service = client.get_all_service_specific_context_keys_across_aws()
            if service_keys_by_service:
                formatter.format_all_context_keys(service_keys_by_service, format)
            else:
                click.echo("No service-specific context keys found", err=True)
        return
    
    if not service_name:
        click.echo("Error: Service name is required", err=True)
        click.echo("Use --help for usage information")
        return
    
    
    # Validate service name and provide suggestions if invalid
    helper = ServiceHelper(client)
    if not helper.is_valid_service(service_name):
        suggestions = helper.get_similar_services(service_name)
        click.echo(f"Error: Invalid service name '{service_name}'", err=True)
        
        if suggestions:
            click.echo("\nDid you mean one of these?", err=True)
            for suggestion in suggestions:
                click.echo(f"  • {suggestion}", err=True)
        
        click.echo(f"\nUse 'mim --list-services' to see all available services.", err=True)
        return
    
    # Special handling for service info command (undocumented)
    if action_name == "info" or action_name == "help":
        helper = ServiceHelper(client)
        service_help = helper.format_service_help(service_name)
        click.echo(service_help)
        return
    
    # If --action flag is used, show details for a specific action
    if action:
        # Get enhanced action metadata with full condition key details
        action_metadata = client.get_action_metadata_with_full_condition_keys(service_name, action)
        
        if not action_metadata:
            click.echo(f"Action '{action}' not found for service '{service_name}'", err=True)
            return
        
        formatter.format_action_details_enhanced(service_name, action, action_metadata['resources'], action_metadata['condition_keys'], format)
        return
    
    # If --resource flag is used, show details for a specific resource
    if resource:
        # Get enhanced resource details with full condition key metadata
        resource_details = client.get_resource_details_with_full_condition_keys(service_name, resource)
        
        if not resource_details:
            click.echo(f"Resource '{resource}' not found for service '{service_name}'", err=True)
            return
        
        formatter.format_resource_details(service_name, resource, resource_details, format)
        return
    
    # If --context-keys flag is used, show all unique context keys for the service
    if context_keys:
        # Get enhanced context keys with metadata when possible
        if format == 'json' or format == 'yaml':
            service_context_keys_with_metadata = client.get_condition_keys_with_metadata_for_service(service_name)
            if service_context_keys_with_metadata:
                if count:
                    formatter.format_count(f"Total unique context keys for {service_name}", len(service_context_keys_with_metadata))
                else:
                    formatter.format_context_keys_with_metadata(service_name, service_context_keys_with_metadata, format)
                return
        
        # Fallback to string list for table/text formats
        service_context_keys = client.get_all_unique_context_keys_for_service(service_name)
        
        if not service_context_keys:
            click.echo(f"No context keys found for service '{service_name}'", err=True)
            return
        
        if count:
            formatter.format_count(f"Total unique context keys for {service_name}", len(service_context_keys))
        else:
            formatter.format_context_keys_list(service_name, service_context_keys, format)
        return
    
    # If --global-context-keys flag is used, show only AWS global context keys for the service
    if global_context_keys:
        global_keys = client.get_global_context_keys_for_service(service_name)
        
        if not global_keys:
            click.echo(f"No AWS global context keys found for service '{service_name}'", err=True)
            return
        
        if count:
            formatter.format_count(f"Total AWS global context keys for {service_name}", len(global_keys))
        else:
            formatter.format_context_keys_list(f"{service_name} (AWS Global)", global_keys, format)
        return
    
    # If --service-context-keys flag is used, show only service-specific context keys
    if service_context_keys:
        service_keys = client.get_service_specific_context_keys_for_service(service_name)
        
        if not service_keys:
            click.echo(f"No service-specific context keys found for service '{service_name}'", err=True)
            return
        
        if count:
            formatter.format_count(f"Total service-specific context keys for {service_name}", len(service_keys))
        else:
            formatter.format_context_keys_list(f"{service_name} (Service-Specific)", service_keys, format)
        return
    
    # If --resources flag is used, show all unique resources for the service
    if resources:
        unique_resources_list = client.get_all_unique_resources_for_service(service_name)
        
        if not unique_resources_list:
            click.echo(f"No unique resources found for service '{service_name}'", err=True)
            return
        
        if count:
            formatter.format_count(f"Total unique resources for {service_name}", len(unique_resources_list))
        else:
            formatter.format_resources_list(service_name, "all-resources", unique_resources_list, format)
        return
    
    # If only service is provided, return all actions
    if not action_name:
        actions_list = client.get_all_actions_for_service(service_name)
        
        if not actions_list:
            click.echo(f"No actions found for service '{service_name}'", err=True)
            return
        
        if count:
            formatter.format_count(f"Total actions for {service_name}", len(actions_list))
        else:
            formatter.format_actions_list(service_name, actions_list, format)
    
    # If both service and action are provided, return enhanced action metadata
    else:
        # Get enhanced action metadata with full condition key details
        action_metadata = client.get_action_metadata_with_full_condition_keys(service_name, action_name)
        
        if not action_metadata:
            click.echo(f"Action '{action_name}' not found for service '{service_name}'", err=True)
            return
        
        if count:
            formatter.format_count(f"Total resources for {service_name}:{action_name}", len(action_metadata['resources']))
        else:
            if format == 'json':
                # For JSON format, show full action metadata with condition keys
                data = {
                    'service': service_name,
                    'action': action_name,
                    'resources': action_metadata['resources'],
                    'condition_keys': action_metadata['condition_keys'],
                    'count': len(action_metadata['resources'])
                }
                print(json.dumps(data, indent=2))
            else:
                # For other formats, show resources list
                formatter.format_resources_list(service_name, action_name, action_metadata['resources'], format)