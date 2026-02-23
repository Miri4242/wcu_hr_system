#!/bin/bash

# VPS-ə deployment script
# Bu script-i local maşınınızda işlədin və faylları VPS-ə yükləyin

VPS_USER="wcuteing"
VPS_HOST="your_vps_ip_or_domain"
VPS_PATH="/home/wcuteing/public_html/hr.wcu.edu.az"

echo "🚀 Deploying to VPS..."

# 1. Upload updated files
echo "📤 Uploading files..."
scp app.py ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/
scp run.cgi ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/
scp templates/employees.html ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/templates/
scp diagnose_vps.py ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/
scp VPS_DEPLOYMENT_GUIDE.md ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/

# 2. Set permissions
echo "🔐 Setting permissions..."
ssh ${VPS_USER}@${VPS_HOST} "chmod +x ${VPS_PATH}/run.cgi"
ssh ${VPS_USER}@${VPS_HOST} "chmod +x ${VPS_PATH}/diagnose_vps.py"

# 3. Run diagnostics
echo "🔍 Running diagnostics..."
ssh ${VPS_USER}@${VPS_HOST} "cd ${VPS_PATH} && source .venv/bin/activate && python diagnose_vps.py"

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Test the application: https://hr.wcu.edu.az/run.cgi/employees"
echo "2. Check logs if needed: ssh ${VPS_USER}@${VPS_HOST} 'tail -f ${VPS_PATH}/cgi_errors.log'"
