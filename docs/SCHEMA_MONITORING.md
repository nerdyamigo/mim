# AWS API Schema Monitoring

This system automatically monitors the AWS Service Reference API for schema changes and alerts you when new fields, data types, or structural changes are detected.

## 🎯 Purpose

The AWS Service Reference API occasionally adds new fields, data types, or modifies the structure of service metadata. This monitoring system helps you:

- **Stay Updated**: Automatically detect when AWS adds new fields or data types
- **Maintain Compatibility**: Ensure your CLI supports all available AWS features
- **Track Changes**: Keep a historical record of API schema evolution
- **Get Alerts**: Receive notifications when action is needed

## 🔧 How It Works

### 1. Schema Analysis
The monitor analyzes a sample of AWS services and extracts:
- **Top-level fields** (e.g., `Name`, `Actions`, `Resources`, `ConditionKeys`)
- **Action fields** (e.g., `Name`, `ActionConditionKeys`, `Resources`)
- **Resource fields** (e.g., `Name`, `ARNFormats`, `ConditionKeys`)
- **Condition key fields** (e.g., `Name`, `Types`)
- **Data types** (e.g., `String`, `ARN`, `Bool`, `ArrayOfString`)

### 2. Change Detection
The system compares current schema against a baseline to detect:
- ✅ **New fields** added to any level
- ✅ **New data types** for condition keys
- ✅ **Removed fields** (rare but possible)
- ✅ **Structural changes** in field combinations

### 3. Automated Alerts
When changes are detected:
- 🚨 **GitHub Issue** created with detailed change report
- 📊 **Schema files** updated in the repository
- 💬 **Slack notification** (if configured)
- 📋 **Workflow summary** with actionable insights

## 🚀 Quick Start

### Initial Setup

1. **Create Initial Baseline**
   ```bash
   # Run locally
   python scripts/schema_monitor.py --create-baseline --sample-size 20
   
   # Or trigger GitHub Action
   # Go to Actions → "Create Schema Baseline" → Run workflow
   ```

2. **Enable Monitoring**
   - The daily monitoring workflow is automatically enabled
   - Runs every day at 9 AM UTC
   - Can be triggered manually anytime

### Local Usage

```bash
# Create baseline (first time)
python scripts/schema_monitor.py --create-baseline

# Monitor for changes
python scripts/schema_monitor.py

# Custom sample size
python scripts/schema_monitor.py --sample-size 15

# JSON output for integration
python scripts/schema_monitor.py --output-format json
```

## 📊 GitHub Actions Workflows

### Daily Monitoring (`.github/workflows/schema-monitor.yml`)
- **Schedule**: Daily at 9 AM UTC
- **Trigger**: Can be run manually with custom parameters
- **Actions**: Detects changes, creates issues, sends notifications

### Baseline Creation (`.github/workflows/create-baseline.yml`)
- **Trigger**: Manual workflow dispatch
- **Purpose**: Create or recreate the baseline schema
- **Use Case**: Initial setup or after major AWS API changes

## 🔍 Understanding the Output

### When Changes Are Detected

```markdown
## 🔍 AWS API Schema Changes Detected

### 🆕 New Fields:
- **condition_key_fields**: Documentation, Examples
- **action_fields**: Deprecation, ReplacementAction

### 📊 New Data Types: DateTime, IPAddress

💡 **Action Required**: Review these changes and update the AWS Service Profiles CLI accordingly.
```

### Example Actions Needed

When new fields are detected, you might need to:

1. **Update extraction logic** in `aws_client.py`
2. **Add new formatters** in `formatters.py` 
3. **Update CLI options** in `cli.py`
4. **Add tests** for new functionality
5. **Update documentation** and examples

## 📁 File Structure

```
schemas/
├── baseline_schema.json           # Current baseline
├── schema_20240126_143052.json   # Historical snapshots
└── schema_20240127_091234.json   # (timestamps when changes detected)

scripts/
└── schema_monitor.py              # Main monitoring script

.github/workflows/
├── schema-monitor.yml             # Daily monitoring
└── create-baseline.yml            # Baseline creation
```

## ⚙️ Configuration Options

### Monitoring Script Parameters

```bash
--create-baseline     # Create new baseline instead of monitoring
--sample-size N       # Number of services to analyze (default: 10)
--output-format       # text or json output
```

### GitHub Actions Variables

Set these in your repository settings:

- `SLACK_WEBHOOK_URL` (optional): For Slack notifications
- Workflows use `GITHUB_TOKEN` automatically

### Customizing Sample Size

- **Default**: 10 services (fast, covers major patterns)
- **Comprehensive**: 20-30 services (slower, more thorough)
- **Minimal**: 5 services (fastest, basic detection)

## 🔧 Troubleshooting

### Common Issues

1. **"No baseline schema found"**
   - Run baseline creation first
   - Check `schemas/` directory exists

2. **"Error fetching metadata"**
   - Check internet connection
   - AWS API might be temporarily unavailable
   - Increase timeout in script if needed

3. **"No changes detected" but you expect changes**
   - Increase sample size
   - Check if changes are in services not being sampled
   - Review baseline timestamp

### Manual Verification

```bash
# Check current AWS API structure manually
curl -s "https://servicereference.us-east-1.amazonaws.com/v1/s3/s3.json" | jq keys

# Compare with your baseline
cat schemas/baseline_schema.json | jq .top_level_fields
```

## 🎛️ Advanced Usage

### Custom Service Analysis

Modify `schema_monitor.py` to analyze specific services:

```python
# In analyze_services_sample method
specific_services = ['s3', 'ec2', 'lambda', 'iam']
sample_services = [s for s in services if s['service'] in specific_services]
```

### Integration with CI/CD

The monitor exits with code 1 when changes are detected, making it suitable for CI/CD pipelines:

```bash
if ! python scripts/schema_monitor.py; then
    echo "Schema changes detected - manual review required"
    exit 1
fi
```

### Custom Notifications

Extend the GitHub Actions workflow to send notifications to other systems (email, Teams, Discord, etc.).

## 📈 Benefits

- **Proactive Updates**: Know about AWS changes before your users report missing features
- **Historical Tracking**: Maintain a record of AWS API evolution
- **Automated Workflow**: No manual checking required
- **Detailed Reports**: Understand exactly what changed and where
- **Version Control**: Schema changes are tracked in Git

## 🤝 Contributing

To improve the monitoring system:

1. Enhance field detection in `extract_schema_structure()`
2. Add new comparison logic in `compare_schemas()`
3. Improve notification formats
4. Add support for other AWS APIs beyond Service Reference

---

**💡 Pro Tip**: After setting up monitoring, you'll never miss AWS API updates again! The system will automatically alert you to new capabilities you can add to your CLI.