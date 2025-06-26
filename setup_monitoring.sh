#!/bin/bash

# AWS Service Profiles Schema Monitoring Setup Script
# This script sets up automated monitoring for AWS API schema changes

set -e

echo "🚀 Setting up AWS Service Profiles Schema Monitoring..."
echo

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p schemas
mkdir -p .github/workflows
mkdir -p docs

# Check if Python script exists
if [ ! -f "scripts/schema_monitor.py" ]; then
    echo "❌ Error: scripts/schema_monitor.py not found!"
    echo "Please ensure you're running this script from the project root directory."
    exit 1
fi

# Create initial baseline schema
echo "📊 Creating initial baseline schema..."
echo "This will analyze 15 AWS services to establish a baseline..."
python3 scripts/schema_monitor.py --create-baseline --sample-size 15

# Check if baseline was created successfully
if [ -f "schemas/baseline_schema.json" ]; then
    echo "✅ Baseline schema created successfully!"
    
    # Show baseline summary
    echo
    echo "📈 Baseline Summary:"
    python3 -c "
import json
with open('schemas/baseline_schema.json', 'r') as f:
    data = json.load(f)

print(f'  • Services analyzed: {len(data.get(\"analyzed_services\", []))}')
print(f'  • Top-level fields: {len(data.get(\"top_level_fields\", []))}')
print(f'  • Action fields: {len(data.get(\"action_fields\", []))}')
print(f'  • Resource fields: {len(data.get(\"resource_fields\", []))}')
print(f'  • Condition key fields: {len(data.get(\"condition_key_fields\", []))}')
print(f'  • Data types: {len(data.get(\"data_types\", []))}')
print(f'  • Created: {data.get(\"timestamp\", \"Unknown\")}')
"
else
    echo "❌ Error: Baseline schema creation failed!"
    exit 1
fi

echo
echo "🔧 Setup Instructions:"
echo
echo "1. 📤 Commit and push the baseline schema to GitHub:"
echo "   git add schemas/ docs/ .github/"
echo "   git commit -m '🔍 Add AWS API schema monitoring system'"
echo "   git push"
echo
echo "2. ⚙️ Enable GitHub Actions workflows:"
echo "   • Go to your GitHub repository"
echo "   • Click on the 'Actions' tab"
echo "   • Enable workflows if prompted"
echo
echo "3. 🔔 Optional: Configure notifications:"
echo "   • Set SLACK_WEBHOOK_URL in repository variables for Slack alerts"
echo "   • Customize notification settings in .github/workflows/schema-monitor.yml"
echo
echo "4. ✅ Test the monitoring:"
echo "   • Go to Actions → 'AWS Schema Monitor' → 'Run workflow'"
echo "   • Or wait for the daily automatic run at 9 AM UTC"
echo

echo "📚 Documentation:"
echo "   • Read docs/SCHEMA_MONITORING.md for detailed usage"
echo "   • Run 'python3 scripts/schema_monitor.py --help' for options"
echo

echo "🎯 What happens next:"
echo "   • Daily monitoring will check for AWS API changes"
echo "   • New fields/data types will trigger GitHub issues"
echo "   • Schema history will be maintained in schemas/ directory"
echo "   • You'll be alerted to update your CLI when needed"
echo

echo "✨ Schema monitoring setup completed successfully!"

# Test the monitoring once
echo
echo "🧪 Testing monitoring (should show no changes)..."
if python3 scripts/schema_monitor.py; then
    echo "✅ Monitoring test passed!"
else
    echo "ℹ️  Changes detected in test run (this is normal if different services were sampled)"
fi

echo
echo "🎉 All done! Your AWS Service Profiles CLI now has automated schema monitoring."
echo "Check the documentation at docs/SCHEMA_MONITORING.md for more details."