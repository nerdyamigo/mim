# AWS Service Profiles CLI (`mim`)

> A powerful CLI tool for exploring AWS service IAM actions, API operations, SDK mappings, resources, and condition keys

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AWS Service Profiles CLI** (`mim`) is a command-line tool that helps AWS developers, DevOps engineers, and security professionals explore and understand AWS services in detail. It provides comprehensive information about AWS service IAM actions, access levels, control/data plane classifications, API operations & SDK mappings, resources, ARN formats, and IAM condition keys.

---

## 🚀 Features

- **📋 Complete Service Catalog**: Browse all 450+ AWS services with display names (`serviceName`) and upstream modification dates (`modified`)
- **🔍 Action Discovery & Filtering**: List actions with `Access Level` (`Read`, `Write`, `List`, `Tagging`, `Permissions management`) and `Plane` (`Control Plane`, `Data Plane`) filtering
- **⚙️ API Operations & SDK Mappings**: Inspect service API `Operations`, their `AuthorizedActions` (including conditional authorization contexts), and `SDK` client methods (`Boto3`, `AWS SDK for Java v2`, etc.)
- **🛡️ IAM Feature Support (`SupportedBy`)**: View whether actions support `IAM Access Analyzer Policy Generation` and `IAM Action Last Accessed`
- **🏗️ Resource Information**: View resources, ARN formats, and both resource-level and action-scoped condition keys
- **🔑 Context Key Analysis**: Separate AWS global (`aws:`) from service-specific condition keys with data types (`ARN`, `ArrayOfARN`, `ArrayOfString`, `Bool`, `Date`, `Numeric`, `String`)
- **🔄 Metadata Update & Local Disk Cache**: Persistent disk cache (`~/.cache/mim`) with `mim --update` (`mim update`), `--clear-cache`, and `--check-schema`
- **📊 Multiple Output Formats & Search**: `table` (default), `json`, `yaml`, and `text` formats, `--count`, `--no-color`, case-insensitive lookups, wildcard matching, and substring search (`-s` / `--search`)

---

## 📦 Installation

### Install Standalone CLI (`pipx` or `uv`)

```bash
# Using pipx
pipx install git+https://github.com/nerdyamigo/mim.git

# Or using uv
uv tool install git+https://github.com/nerdyamigo/mim.git
```

### Install from Source (Development)

```bash
git clone https://github.com/nerdyamigo/mim.git
cd mim

# Install in editable mode with test dependencies
pip install -e ".[dev]"

# Verify installation
mim --help
```

---

## 🎯 Quick Start

```bash
# 1. Sync / update local AWS metadata cache and see newly added or modified services
mim --update

# 2. List all AWS services (or filter by keyword)
mim --list-services
mim --list-services --search bedrock

# 3. Get detailed overview of a service (actions breakdown, planes, operations, resources, keys)
mim s3 info

# 4. List all actions for a service (with Access Level and Plane columns)
mim s3

# 5. Filter actions by Access Level and Plane
mim s3 --access-level Write --plane data

# 6. Inspect a specific action (case-insensitive or shorthand syntax)
mim s3 --action GetObject
mim s3:GetObject

# 7. Explore API Operations and SDK method mappings
mim s3 --operations
mim s3 --operation AbortMultipartUpload
```

---

## 📖 Complete CLI Reference

### Command Syntax

```bash
mim [SERVICE_NAME] [ACTION_NAME] [OPTIONS]
```

### CLI Options

| Flag / Option | Short | Description |
| :--- | :--- | :--- |
| `--list-services` | | List all available AWS services (`service`, `serviceName`, `modified`, `url`) |
| `--update` | | Fetch latest AWS Service Reference index and refresh modified cached services (`mim --update`, `mim update`, or `mim <service> --update`) |
| `--clear-cache` | | Clear local disk metadata cache (`~/.cache/mim`) |
| `--check-schema` | | Compare live/cached AWS Service Reference API schema against bundled baseline schema |
| `--search <pattern>` | `-s` | Filter services, actions, operations, resources, or context keys by case-insensitive substring or wildcard |
| `--access-level <level>` | | Filter service actions by IAM access level: `Read`, `Write`, `List`, `Tagging`, or `Permissions` |
| `--plane <plane>` | | Filter service actions by plane: `control` (`Control Plane`) or `data` (`Data Plane`) |
| `--action <name>` | | Show enhanced details for a specific IAM action |
| `--operations` | | List all API Operations (`Name`, `AuthorizedActions`, `SDK`) for a service |
| `--operation <name>` | | Show details for a specific API Operation |
| `--resources` | | Show all unique resource types and ARN formats for a service |
| `--resource <name>` | | Show details (ARN formats & condition keys) for a specific resource |
| `--context-keys` | | Show all condition keys (with data types) for a service |
| `--global-context-keys` | | Show only AWS global condition keys (`aws:`) for a service |
| `--service-context-keys` | | Show only service-specific condition keys for a service |
| `--list-all-context-keys` | | List all unique condition keys across all AWS services |
| `--list-global-context-keys` | | List all AWS global condition keys (`aws:`) across all AWS services |
| `--list-service-context-keys` | | List all service-specific condition keys across all AWS services |
| `--service-actions <pairs>` | `-sa` | Query comma-separated `service:action` pairs in parallel (supports wildcards, e.g., `-sa "s3:Get*,ec2:RunInstances"`) |
| `--format <fmt>` | `-f` | Output format: `table` (default), `text`, `json`, or `yaml` |
| `--count` | | Display only the count of matching items |
| `--no-color` | | Disable ANSI color output |

---

## 💡 Usage Examples

### 1. Service Overview (`mim <service> info`)

```bash
mim s3 info
```

```text
Service: S3 (S3)
Version: v1.5 | Last Modified: 2026-10-21 17:45:14 UTC

📊 Available Data:
  • Actions: 180 (Read: 66, Write: 57, List: 18, Tagging: 12, Permissions: 27)
  • Planes: Control Plane: 155, Data Plane: 25
  • API Operations: 195
  • Resources: 13
  • Context Keys: 64 (AWS Global: 3, Service-Specific: 61)
```

### 2. Enhanced Action Details (`mim <service> --action <action>` or `mim <service>:<action>`)

```bash
mim s3 --action GetObject
# Or shorthand:
mim s3:GetObject
```

Displays:
- **Access Level & Plane**: `s3:GetObject [Read | Data Plane]`
- **Resources & ARN Formats**: `accesspointobject`, `object`, and their resource-level condition keys with types (`s3:DataAccessPointArn (ARN)`, `aws:ResourceTag/${TagKey} (String)`)
- **Action Condition Keys**: `s3:ExistingObjectTag/<key> (String)`, `s3:TlsVersion (Numeric)`, etc.
- **Action Metadata & SDK Mapping**:
  - `Supported By`: `IAM Access Analyzer Policy Generation` & `IAM Action Last Accessed`
  - `API Operations`: `CopyObject`, `GetObject`, `GetObjectAttributes`, `HeadObject`, etc.
  - `SDK Methods`: `Boto3:s3.get_object`, `Boto3:s3.copy_object`, etc.

### 3. Filtering Actions by Access Level, Plane, Search, or Wildcards

```bash
# Data plane write actions in S3
mim s3 --access-level Write --plane data

# Permission management actions in S3
mim s3 --access-level Permissions

# Search actions by substring
mim s3 -s Multipart

# Wildcard matching on a single service
mim s3 "Put*"
mim s3 "Get*" --format json
```

### 4. Exploring API Operations & SDK Methods

```bash
# List all API operations for S3
mim s3 --operations

# Filter operations by keyword
mim s3 --operations -s Multipart

# Inspect a specific API operation
mim s3 --operation AbortMultipartUpload
```

### 5. Batch Querying Multiple `service:action` Pairs (`-sa`)

```bash
# Query multiple actions across services in parallel
mim -sa s3:GetObject,s3:PutBucketPolicy,ec2:RunInstances

# Use wildcards and export as JSON or YAML
mim -sa "s3:Get*,ec2:Describe*" --format json
mim -sa s3:GetObject,s3:PutObject --format yaml
```

### 6. Metadata Cache Management & Schema Monitoring

```bash
# Update service index and refresh modified cached services
mim --update

# Pre-cache or refresh a specific service
mim s3 --update

# Clear local cache (~/.cache/mim)
mim --clear-cache

# Check for upstream AWS Service Reference schema changes
mim --check-schema
```

---

## 🛠️ Project Structure & Development

```text
mim/
├── aws_service_profiles/           # Main package
│   ├── __init__.py
│   ├── cli.py                      # Click CLI interface
│   ├── aws_client.py               # AWS Service Reference client & disk cache
│   ├── formatters.py               # Rich table, text, JSON, and YAML formatters
│   ├── models.py                   # Dataclasses for services, actions, operations & keys
│   ├── service_helper.py           # Service summary, validation & suggestions
│   ├── schema_monitor.py           # Bundled schema change detector
│   └── schemas/
│       └── baseline_schema.json    # Bundled baseline schema
├── schemas/
│   └── baseline_schema.json        # Repository baseline schema
├── scripts/
│   ├── schema_monitor.py           # CLI entry point for schema monitoring workflows
│   └── generate_change_summary.py  # Markdown report generator for GitHub Actions
├── tests/                          # Pytest unit & CLI integration test suite
├── .github/workflows/              # CI and daily schema monitoring workflows
├── pyproject.toml                  # PEP 621 / PEP 517 build configuration
├── setup.py                        # Setuptools compatibility configuration
└── requirements.txt                # Runtime dependencies
```

### Running Tests

```bash
pytest -v
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
