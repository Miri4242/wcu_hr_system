#!/usr/bin/env python3
# Railway deployment check

import os
import sys

def check_deployment():
    """Check if all required files exist for Railway deployment"""
    
    required_files = [
        'app.py',
        'requirements.txt', 
        'Procfile',
        'templates/admin.html',
        'templates/base_page.html',
        'static/css/style.css'
    ]
    
    print("🚀 Railway Deployment Check")
    print("=" * 40)
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} - MISSING!")
            all_good = False
    
    print("\n📁 Templates directory:")
    if os.path.exists('templates'):
        templates = [f for f in os.listdir('templates') if f.endswith('.html')]
        print(f"   Found {len(templates)} HTML files")
        for template in sorted(templates):
            print(f"   - {template}")
    else:
        print("   ❌ Templates directory missing!")
        all_good = False
    
    print(f"\n{'✅ READY FOR DEPLOYMENT' if all_good else '❌ DEPLOYMENT WILL FAIL'}")
    
    if all_good:
        print("\n🔧 Next steps:")
        print("1. Railway will auto-deploy from Git push")
        print("2. Check Railway logs for build status")
        print("3. Test admin panel: /admin")
        print("4. Login: miryusif@wcu.edu.az / Admin123")
    
    return all_good

if __name__ == "__main__":
    check_deployment()