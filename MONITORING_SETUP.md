# 🔍 AWS API Schema Monitoring Setup

This repository now includes automated monitoring for AWS Service Reference API changes!

## 🚀 Quick Setup

1. **Run the setup script:**
   ```bash
   ./setup_monitoring.sh
   ```

2. **Commit to GitHub:**
   ```bash
   git add .
   git commit -m "🔍 Add AWS API schema monitoring system"
   git push
   ```

3. **Enable workflows in GitHub:**
   - Go to Actions tab in your GitHub repository
   - Enable workflows if prompted

## 🎯 What You Get

### Automated Daily Monitoring
- **Daily checks** at 9 AM UTC for AWS API changes
- **GitHub Issues** created automatically when changes detected
- **Schema history** maintained in `schemas/` directory

### Alert Types
- 🆕 **New fields** (e.g., new metadata in actions/resources)
- 📊 **New data types** (e.g., new condition key types)
- 🗑️ **Removed fields** (rare but possible)
- 🔄 **Structural changes** (field combinations)

### Example Alert
When AWS adds new fields, you'll get a GitHub issue like:

```markdown
## 🔍 AWS API Schema Changes Detected

### 🆕 New Fields:
- **condition_key_fields**: Documentation, Examples
- **action_fields**: DeprecationDate, ReplacementAction

### 📊 New Data Types: DateTime, IPAddress

💡 **Action Required**: Review these changes and update the AWS Service Profiles CLI accordingly.
```

## 📂 Files Added

```
scripts/
└── schema_monitor.py           # Core monitoring script

.github/workflows/
├── schema-monitor.yml          # Daily monitoring workflow
└── create-baseline.yml         # Baseline creation workflow

schemas/
└── baseline_schema.json        # Current API schema baseline

docs/
└── SCHEMA_MONITORING.md        # Detailed documentation
```

## 🔧 Manual Usage

```bash
# Check for changes now
python3 scripts/schema_monitor.py

# Create new baseline
python3 scripts/schema_monitor.py --create-baseline

# Analyze more services for better coverage
python3 scripts/schema_monitor.py --create-baseline --sample-size 25
```

## 🎛️ Configuration

### GitHub Actions Variables (Optional)
- `SLACK_WEBHOOK_URL`: Enable Slack notifications

### Customization
- Modify sample size in workflows
- Adjust monitoring frequency
- Customize notification formats

## 📈 Benefits

- **Never miss AWS updates** - Get notified when new capabilities are available
- **Proactive maintenance** - Update your CLI before users notice missing features
- **Change tracking** - Historical record of AWS API evolution
- **Zero manual effort** - Fully automated monitoring and alerting

## 🤝 Next Steps

1. ✅ Complete the GitHub setup above
2. 📖 Read `docs/SCHEMA_MONITORING.md` for detailed documentation
3. 🔔 Configure optional Slack notifications
4. 🧪 Test by running the "AWS Schema Monitor" workflow manually

---

**🎉 Your AWS Service Profiles CLI now has state-of-the-art change detection!**

The system will automatically alert you when AWS adds new fields, helping you keep your CLI up-to-date with the latest AWS capabilities.