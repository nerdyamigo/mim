"""CLI interface for AWS Service Profiles (`mim`)."""

import click
from typing import List, Dict, Any, Tuple, Optional
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
        service_name = None
        if ctx.params.get("service_name"):
            service_name = ctx.params["service_name"]
        elif len(ctx.args) > 0:
            potential_service = ctx.args[0]
            if not potential_service.startswith("-"):
                service_name = potential_service

        if service_name and not any(
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
            try:
                client = AWSClient()
                helper = ServiceHelper(client)
                if helper.is_valid_service(service_name):
                    return helper.format_service_help(service_name)
            except Exception:
                pass

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


def print_resources_for_service_action(
    client: AWSClient, service_name: str, action_name: str
) -> None:
    """Print all resources for a specific service action in a readable format."""
    resources = client.get_resources_for_service_action(service_name, action_name)
    if resources:
        click.echo(f"Resources for {service_name}:{action_name}:")
        for resource in resources:
            click.echo(f"  - {resource}")
    else:
        click.echo(
            f"No resources found for action '{action_name}' in service '{service_name}'",
            err=True,
        )


def expand_wildcard_actions(
    client: AWSClient, service: str, action_pattern: str
) -> List[str]:
    """Expand a wildcard pattern (case-insensitively) to a list of matching actions for a service."""
    try:
        all_actions = client.get_all_actions_for_service(service)
        pattern_lower = action_pattern.lower()
        matching_actions = [
            action
            for action in all_actions
            if fnmatch.fnmatch(action.lower(), pattern_lower)
        ]
        return matching_actions
    except Exception as e:
        click.echo(
            f"Error expanding wildcard for {service}:{action_pattern}: {str(e)}",
            err=True,
        )
        return []


def parse_service_action_input(
    service_actions: List[str],
) -> List[Tuple[str, str]]:
    """Parse service:action format input into service-action pairs."""
    pairs = []
    for input_str in service_actions:
        service_action_list = [
            sa.strip() for sa in input_str.split(",") if sa.strip()
        ]

        for service_action in service_action_list:
            try:
                service, action = service_action.split(":", 1)
                pairs.append((service.strip(), action.strip()))
            except ValueError:
                raise click.UsageError(
                    f"Invalid format: '{service_action}'. Expected format is 'service:action'.\n"
                    "Example: s3:GetObject or sagemaker:CreateTrainingJob\n"
                    "Multiple pairs can be comma-separated: s3:GetObject,s3:PutObject,sagemaker:CreateTrainingJob\n"
                    "Wildcards are supported: sagemaker:Create*"
                )
    return pairs


def process_service_action(
    client: AWSClient, service: str, action: str
) -> Dict[str, Any]:
    """Process a single service-action pair and return the results."""
    try:
        if "*" in action or "?" in action:
            matching_actions = expand_wildcard_actions(client, service, action)
            if not matching_actions:
                return {
                    "service": service,
                    "action": action,
                    "error": f"No actions found matching pattern '{action}'",
                }

            results = []
            for matched_action in matching_actions:
                try:
                    action_metadata = (
                        client.get_action_metadata_with_full_condition_keys(
                            service, matched_action
                        )
                    )
                    if not action_metadata:
                        results.append(
                            {
                                "service": service,
                                "action": matched_action,
                                "error": f"Action '{matched_action}' not found for service '{service}'",
                            }
                        )
                        continue

                    results.append(
                        {
                            "service": service,
                            "action": action_metadata["name"],
                            "access_level": action_metadata.get("access_level"),
                            "plane": action_metadata.get("plane"),
                            "annotations": action_metadata.get("annotations"),
                            "supported_by": action_metadata.get("supported_by"),
                            "operations": action_metadata.get("operations"),
                            "resources": action_metadata["resources"],
                            "condition_keys": action_metadata["condition_keys"],
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "service": service,
                            "action": matched_action,
                            "error": str(e),
                        }
                    )

            return {
                "service": service,
                "pattern": action,
                "matched_actions": results,
            }
        else:
            action_metadata = client.get_action_metadata_with_full_condition_keys(
                service, action
            )
            if not action_metadata:
                return {
                    "service": service,
                    "action": action,
                    "error": f"Action '{action}' not found for service '{service}'",
                }

            return {
                "service": service,
                "action": action_metadata["name"],
                "access_level": action_metadata.get("access_level"),
                "plane": action_metadata.get("plane"),
                "annotations": action_metadata.get("annotations"),
                "supported_by": action_metadata.get("supported_by"),
                "operations": action_metadata.get("operations"),
                "resources": action_metadata["resources"],
                "condition_keys": action_metadata["condition_keys"],
            }
    except Exception as e:
        return {"service": service, "action": action, "error": str(e)}


@click.command(cls=ServiceAwareCommand)
@click.argument("service_name", required=False)
@click.argument("action_name", required=False)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "text", "json", "yaml"]),
    default="table",
    help="Output format: table (default), text, json, or yaml",
)
@click.option(
    "--count", is_flag=True, help="Show only count instead of full list"
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option(
    "--search",
    "-s",
    help="Filter services, actions, resources, operations, or context keys by substring or wildcard",
)
@click.option(
    "--access-level",
    type=click.Choice(
        ["Read", "Write", "List", "Tagging", "Permissions", "read", "write", "list", "tagging", "permissions"],
        case_sensitive=False,
    ),
    help="Filter service actions by IAM access level (Read, Write, List, Tagging, Permissions)",
)
@click.option(
    "--plane",
    type=click.Choice(["data", "control"], case_sensitive=False),
    help="Filter service actions by plane (data or control)",
)
@click.option(
    "--list-services", is_flag=True, help="List all available AWS services"
)
@click.option(
    "--list-all-context-keys",
    is_flag=True,
    help="List all unique context keys across all AWS services",
)
@click.option(
    "--list-global-context-keys",
    is_flag=True,
    help="List all AWS global context keys (aws:) across all services",
)
@click.option(
    "--list-service-context-keys",
    is_flag=True,
    help="List all service-specific context keys across all services",
)
@click.option(
    "--context-keys",
    is_flag=True,
    help="Show all unique context keys for the service",
)
@click.option(
    "--global-context-keys",
    is_flag=True,
    help="Show only AWS global context keys (aws:) for the service",
)
@click.option(
    "--service-context-keys",
    is_flag=True,
    help="Show only service-specific context keys for the service",
)
@click.option(
    "--resources",
    is_flag=True,
    help="Show all unique resources for the service",
)
@click.option(
    "--operations",
    is_flag=True,
    help="Show all API Operations (with AuthorizedActions and SDK mappings) for the service",
)
@click.option("--action", help="Get details for a specific action")
@click.option("--operation", help="Get details for a specific API Operation")
@click.option("--resource", help="Get details for a specific resource")
@click.option(
    "--service-actions",
    "-sa",
    help="Specify comma-separated service:action pairs (e.g., s3:GetObject,s3:PutObject,sagemaker:Create*)",
)
@click.option(
    "--update",
    is_flag=True,
    help="Fetch latest AWS Service Reference metadata index and refresh local cache",
)
@click.option(
    "--clear-cache",
    is_flag=True,
    help="Clear local AWS metadata cache (~/.cache/mim)",
)
@click.option(
    "--check-schema",
    is_flag=True,
    help="Check live AWS Service Reference API metadata against baseline schema",
)
@click.pass_context
def cli(
    ctx,
    service_name: Optional[str],
    action_name: Optional[str],
    format: str,
    count: bool,
    no_color: bool,
    search: Optional[str],
    access_level: Optional[str],
    plane: Optional[str],
    list_services: bool,
    list_all_context_keys: bool,
    list_global_context_keys: bool,
    list_service_context_keys: bool,
    context_keys: bool,
    global_context_keys: bool,
    service_context_keys: bool,
    resources: bool,
    operations: bool,
    action: Optional[str],
    operation: Optional[str],
    resource: Optional[str],
    service_actions: Optional[str],
    update: bool,
    clear_cache: bool,
    check_schema: bool,
):
    """
    AWS Service Profiles CLI (`mim`) - Explore AWS service actions, operations, resources, and IAM condition keys.

    Examples:
      mim --list-services                         List all AWS services (with ServiceName & modified date)
      mim --list-services --search bedrock        Search AWS services by keyword
      mim --update                                Update local AWS service metadata cache
      mim s3 info                                 Show S3 overview, access levels & planes
      mim s3                                      List all S3 actions with access level & plane
      mim s3 --access-level Write --plane data    Filter S3 actions by access level and plane
      mim s3 GetObject                            Show full details for s3:GetObject (or s3:Get* wildcard)
      mim s3 --operations                         List S3 API Operations and Boto3 SDK methods
      mim s3 --resources                          List all S3 resource types and ARN formats
      mim s3 --context-keys                       List all S3 IAM condition keys with types
      mim -sa "s3:Get*,ec2:RunInstances"          Query multiple service:action pairs
    """
    client = AWSClient()
    formatter = OutputFormatter(use_color=not no_color)

    # 1. Handle cache clearing
    if clear_cache:
        removed = client.clear_cache()
        click.echo(f"Cleared local metadata cache ({removed} cached file(s) removed).")
        return

    # 2. Handle metadata update experience (`mim --update` or `mim update` or `mim <service> --update`)
    if update or (service_name and service_name.lower() == "update" and not action_name):
        target_services = None
        if service_name and service_name.lower() != "update":
            target_services = [service_name]
        elif action_name:
            target_services = [action_name]
        summary = client.update_metadata_cache(service_names=target_services)
        formatter.format_update_summary(summary, format)
        return

    # 3. Handle live schema check (`mim --check-schema`)
    if check_schema:
        from scripts.schema_monitor import SchemaMonitor, format_changes_report

        monitor = SchemaMonitor()
        result = monitor.monitor_changes(sample_size=10, save_updates=False)
        if format == "json":
            click.echo(json.dumps(result, indent=2))
        elif format == "yaml":
            formatter.console.print(yaml.dump(result, default_flow_style=False))
        else:
            click.echo(format_changes_report(result.get("changes", {})))
        return

    # Helper for filtering strings or dicts by `--search`
    def matches_search(text_val: str) -> bool:
        if not search:
            return True
        s_lower = search.lower()
        t_lower = text_val.lower()
        if "*" in s_lower or "?" in s_lower:
            return fnmatch.fnmatch(t_lower, s_lower)
        return s_lower in t_lower

    # 4. Support shorthand `mim s3:GetObject` passed as the first positional argument
    if (
        service_name
        and ":" in service_name
        and not action_name
        and not service_actions
    ):
        service_actions = service_name
        service_name = None

    # 5. Handle `-sa` / `--service-actions`
    if service_actions:
        try:
            service_action_pairs = parse_service_action_input([service_actions])

            helper = ServiceHelper(client)
            invalid_services = [
                service
                for service, _ in service_action_pairs
                if not helper.is_valid_service(service)
            ]
            if invalid_services:
                for service in invalid_services:
                    suggestions = helper.get_similar_services(service)
                    click.echo(f"Error: Invalid service name '{service}'", err=True)
                    if suggestions:
                        click.echo("\nDid you mean one of these?", err=True)
                        for suggestion in suggestions:
                            click.echo(f"  • {suggestion}", err=True)
                return

            # Preserve input order using indexed futures
            ordered_results: List[Optional[Dict[str, Any]]] = [None] * len(
                service_action_pairs
            )
            with ThreadPoolExecutor() as executor:
                future_to_idx = {
                    executor.submit(
                        process_service_action, client, service, act_name
                    ): idx
                    for idx, (service, act_name) in enumerate(service_action_pairs)
                }
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        ordered_results[idx] = future.result()
                    except Exception as e:
                        svc, act = service_action_pairs[idx]
                        ordered_results[idx] = {
                            "service": svc,
                            "action": act,
                            "error": str(e),
                        }

            all_results = [r for r in ordered_results if r is not None]

            if format == "json":
                print(json.dumps(all_results, indent=2))
            elif format == "yaml":
                formatter.console.print(
                    yaml.dump(all_results, default_flow_style=False)
                )
            else:
                for result in all_results:
                    if "error" in result:
                        click.echo(
                            f"Error for {result['service']}:{result['action']}: {result['error']}",
                            err=True,
                        )
                        continue

                    if "matched_actions" in result:
                        for matched_result in result["matched_actions"]:
                            if "error" in matched_result:
                                click.echo(
                                    f"Error for {matched_result['service']}:{matched_result['action']}: {matched_result['error']}",
                                    err=True,
                                )
                                continue
                            formatter.format_action_details_enhanced(
                                matched_result["service"],
                                matched_result["action"],
                                matched_result["resources"],
                                matched_result["condition_keys"],
                                format,
                                action_metadata=matched_result,
                            )
                    else:
                        formatter.format_action_details_enhanced(
                            result["service"],
                            result["action"],
                            result["resources"],
                            result["condition_keys"],
                            format,
                            action_metadata=result,
                        )
            return

        except click.UsageError as e:
            click.echo(str(e), err=True)
            return

    # 6. Handle `--list-services`
    if list_services:
        all_services = client.get_aws_services_urls()
        if search:
            all_services = [
                s
                for s in all_services
                if matches_search(s.get("service", ""))
                or matches_search(s.get("serviceName", ""))
            ]
        if all_services:
            if count:
                formatter.format_count("Total AWS services", len(all_services))
            else:
                formatter.format_services_list(all_services, format)
        else:
            click.echo("No services found", err=True)
        return

    # 7. Handle AWS-wide context key flags
    if list_all_context_keys:
        if count:
            all_keys = client.get_all_unique_context_keys_flattened()
            if search:
                all_keys = [k for k in all_keys if matches_search(k)]
            formatter.format_count(
                "Total unique context keys across all AWS services", len(all_keys)
            )
        else:
            context_keys_by_service = client.get_all_unique_context_keys_across_aws(
                show_progress=True
            )
            if search:
                context_keys_by_service = {
                    svc: [k for k in keys if matches_search(k)]
                    for svc, keys in context_keys_by_service.items()
                }
                context_keys_by_service = {
                    svc: keys for svc, keys in context_keys_by_service.items() if keys
                }
            if context_keys_by_service:
                formatter.format_all_context_keys(context_keys_by_service, format)
            else:
                click.echo("No context keys found", err=True)
        return

    if list_global_context_keys:
        global_keys = client.get_all_global_context_keys_across_aws()
        if search:
            global_keys = [k for k in global_keys if matches_search(k)]
        if global_keys:
            if count:
                formatter.format_count(
                    "Total AWS global context keys across all services",
                    len(global_keys),
                )
            else:
                formatter.format_flattened_context_keys(global_keys, format)
        else:
            click.echo("No global context keys found", err=True)
        return

    if list_service_context_keys:
        if count:
            service_keys = client.get_all_service_specific_context_keys_flattened()
            if search:
                service_keys = [k for k in service_keys if matches_search(k)]
            formatter.format_count(
                "Total service-specific context keys across all AWS services",
                len(service_keys),
            )
        else:
            service_keys_by_service = (
                client.get_all_service_specific_context_keys_across_aws()
            )
            if search:
                service_keys_by_service = {
                    svc: [k for k in keys if matches_search(k)]
                    for svc, keys in service_keys_by_service.items()
                }
                service_keys_by_service = {
                    svc: keys for svc, keys in service_keys_by_service.items() if keys
                }
            if service_keys_by_service:
                formatter.format_all_context_keys(service_keys_by_service, format)
            else:
                click.echo("No service-specific context keys found", err=True)
        return

    if not service_name:
        click.echo("Error: Service name is required", err=True)
        click.echo("Use --help for usage information")
        return

    # Validate service name (case-insensitive) and resolve canonical service code
    helper = ServiceHelper(client)
    entry = client.find_service_entry(service_name)
    if not entry:
        suggestions = helper.get_similar_services(service_name)
        click.echo(f"Error: Invalid service name '{service_name}'", err=True)

        if suggestions:
            click.echo("\nDid you mean one of these?", err=True)
            for suggestion in suggestions:
                click.echo(f"  • {suggestion}", err=True)

        click.echo(
            "\nUse 'mim --list-services' to see all available services.", err=True
        )
        return

    canonical_service = entry.get("service", service_name)

    # 8. Service overview (`mim s3 info` or `mim s3 help`)
    if action_name and action_name.lower() in ("info", "help"):
        service_help = helper.format_service_help(canonical_service)
        click.echo(service_help)
        return

    # 9. Specific API Operation (`--operation`)
    if operation:
        op_details = client.get_operation_details(canonical_service, operation)
        if not op_details:
            click.echo(
                f"Operation '{operation}' not found for service '{canonical_service}'",
                err=True,
            )
            return
        formatter.format_operation_details(
            canonical_service, op_details["name"], op_details, format
        )
        return

    # 10. All API Operations for a service (`--operations`)
    if operations:
        ops_list = client.get_operations_for_service(canonical_service)
        if search:
            ops_list = [
                op for op in ops_list if matches_search(op.get("Name", ""))
            ]
        if not ops_list:
            click.echo(
                f"No operations found for service '{canonical_service}'", err=True
            )
            return
        if count:
            formatter.format_count(
                f"Total operations for {canonical_service}", len(ops_list)
            )
        else:
            formatter.format_operations_list(canonical_service, ops_list, format)
        return

    # 11. Specific action (`--action`)
    if action:
        action_metadata = client.get_action_metadata_with_full_condition_keys(
            canonical_service, action
        )
        if not action_metadata:
            click.echo(
                f"Action '{action}' not found for service '{canonical_service}'",
                err=True,
            )
            return

        formatter.format_action_details_enhanced(
            canonical_service,
            action_metadata["name"],
            action_metadata["resources"],
            action_metadata["condition_keys"],
            format,
            action_metadata=action_metadata,
        )
        return

    # 12. Specific resource (`--resource`)
    if resource:
        resource_details = client.get_resource_details_with_full_condition_keys(
            canonical_service, resource
        )
        if not resource_details:
            click.echo(
                f"Resource '{resource}' not found for service '{canonical_service}'",
                err=True,
            )
            return

        formatter.format_resource_details(
            canonical_service, resource_details["name"], resource_details, format
        )
        return

    # 13. Service context keys (`--context-keys`)
    if context_keys:
        service_context_keys_with_metadata = (
            client.get_condition_keys_with_metadata_for_service(canonical_service)
        )
        if search:
            service_context_keys_with_metadata = [
                k
                for k in service_context_keys_with_metadata
                if matches_search(k.get("Name", ""))
            ]
        if service_context_keys_with_metadata:
            if count:
                formatter.format_count(
                    f"Total unique context keys for {canonical_service}",
                    len(service_context_keys_with_metadata),
                )
            elif format in ("json", "yaml", "table"):
                formatter.format_context_keys_with_metadata(
                    canonical_service, service_context_keys_with_metadata, format
                )
            else:
                names_only = [
                    k.get("Name", "") for k in service_context_keys_with_metadata
                ]
                formatter.format_context_keys_list(
                    canonical_service, names_only, format
                )
            return

        service_context_keys = client.get_all_unique_context_keys_for_service(
            canonical_service
        )
        if search:
            service_context_keys = [
                k for k in service_context_keys if matches_search(k)
            ]
        if not service_context_keys:
            click.echo(
                f"No context keys found for service '{canonical_service}'", err=True
            )
            return
        if count:
            formatter.format_count(
                f"Total unique context keys for {canonical_service}",
                len(service_context_keys),
            )
        else:
            formatter.format_context_keys_list(
                canonical_service, service_context_keys, format
            )
        return

    # 14. Global context keys for service (`--global-context-keys`)
    if global_context_keys:
        global_keys = client.get_global_context_keys_for_service(canonical_service)
        if search:
            global_keys = [k for k in global_keys if matches_search(k)]
        if not global_keys:
            click.echo(
                f"No AWS global context keys found for service '{canonical_service}'",
                err=True,
            )
            return
        if count:
            formatter.format_count(
                f"Total AWS global context keys for {canonical_service}",
                len(global_keys),
            )
        else:
            formatter.format_context_keys_list(
                f"{canonical_service} (AWS Global)", global_keys, format
            )
        return

    # 15. Service-specific context keys (`--service-context-keys`)
    if service_context_keys:
        service_keys = client.get_service_specific_context_keys_for_service(
            canonical_service
        )
        if search:
            service_keys = [k for k in service_keys if matches_search(k)]
        if not service_keys:
            click.echo(
                f"No service-specific context keys found for service '{canonical_service}'",
                err=True,
            )
            return
        if count:
            formatter.format_count(
                f"Total service-specific context keys for {canonical_service}",
                len(service_keys),
            )
        else:
            formatter.format_context_keys_list(
                f"{canonical_service} (Service-Specific)", service_keys, format
            )
        return

    # 16. All unique resources for service (`--resources`)
    if resources:
        unique_resources_list = client.get_all_unique_resources_for_service(
            canonical_service
        )
        if search:
            unique_resources_list = [
                r
                for r in unique_resources_list
                if matches_search(r.get("name", ""))
            ]
        if not unique_resources_list:
            click.echo(
                f"No unique resources found for service '{canonical_service}'",
                err=True,
            )
            return
        if count:
            formatter.format_count(
                f"Total unique resources for {canonical_service}",
                len(unique_resources_list),
            )
        else:
            formatter.format_resources_list(
                canonical_service, "all-resources", unique_resources_list, format
            )
        return

    # 17. Service only (`mim s3` with optional `--access-level`, `--plane`, `--search`)
    if not action_name:
        actions_list = client.get_all_actions_for_service(
            canonical_service, access_level=access_level, plane=plane
        )
        detailed_actions = client.get_all_actions_with_metadata_for_service(
            canonical_service, access_level=access_level, plane=plane
        )
        if search:
            actions_list = [a for a in actions_list if matches_search(a)]
            detailed_actions = [
                a for a in detailed_actions if matches_search(a.get("name", ""))
            ]

        if not actions_list:
            click.echo(
                f"No actions found for service '{canonical_service}'", err=True
            )
            return

        if count:
            formatter.format_count(
                f"Total actions for {canonical_service}", len(actions_list)
            )
        else:
            # Pass detailed_actions for table/text display so Access Level & Plane are visible,
            # while keeping actions_list as string list for backward-compatible JSON/YAML unless filtered
            formatter.format_actions_list(
                canonical_service,
                actions_list,
                format,
                detailed_actions=detailed_actions if format in ("table", "text") else None,
            )
        return

    # 18. Service + Action (`mim s3 GetObject` or wildcard `mim s3 "Get*"`)
    if "*" in action_name or "?" in action_name:
        matched = expand_wildcard_actions(
            client, canonical_service, action_name
        )
        if not matched:
            click.echo(
                f"No actions found matching '{action_name}' for service '{canonical_service}'",
                err=True,
            )
            return
        if count:
            formatter.format_count(
                f"Total actions matching {canonical_service}:{action_name}",
                len(matched),
            )
        else:
            detailed = [
                a
                for a in client.get_all_actions_with_metadata_for_service(
                    canonical_service
                )
                if a.get("name") in matched
            ]
            formatter.format_actions_list(
                canonical_service,
                matched,
                format,
                detailed_actions=detailed if format in ("table", "text") else None,
            )
        return

    action_metadata = client.get_action_metadata_with_full_condition_keys(
        canonical_service, action_name
    )

    if not action_metadata:
        click.echo(
            f"Action '{action_name}' not found for service '{canonical_service}'",
            err=True,
        )
        return

    canonical_action = action_metadata["name"]
    if count:
        formatter.format_count(
            f"Total resources for {canonical_service}:{canonical_action}",
            len(action_metadata["resources"]),
        )
    else:
        if format == "json":
            data = {
                "service": canonical_service,
                "action": canonical_action,
                "access_level": action_metadata.get("access_level"),
                "plane": action_metadata.get("plane"),
                "annotations": action_metadata.get("annotations"),
                "supported_by": action_metadata.get("supported_by"),
                "operations": action_metadata.get("operations"),
                "resources": action_metadata["resources"],
                "condition_keys": action_metadata["condition_keys"],
                "count": len(action_metadata["resources"]),
            }
            print(json.dumps(data, indent=2))
        else:
            formatter.format_action_details_enhanced(
                canonical_service,
                canonical_action,
                action_metadata["resources"],
                action_metadata["condition_keys"],
                format,
                action_metadata=action_metadata,
            )
