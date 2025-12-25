#!/usr/bin/env python3
# Check templates directory

import os
import sys

def check_templates():
    """Check if templates exist"""
    print("🔄 Checking templates directory...")
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    
    # Check if templates directory exists
    templates_dir = "templates"
    if os.path.exists(templates_dir):
        print(f"✅ Templates directory exists: {templates_dir}")
        
        # List all template files
        template_files = []
        for root, dirs, files in os.walk(templates_dir):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        print(f"📄 Found {len(template_files)} template files:")
        for template in sorted(template_files):
            print(f"   - {template}")
            
        # Check specifically for admin.html
        admin_template = os.path.join(templates_dir, "admin.html")
        if os.path.exists(admin_template):
            print(f"✅ admin.html exists: {admin_template}")
            with open(admin_template, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   Size: {len(content)} characters")
        else:
            print(f"❌ admin.html NOT found: {admin_template}")
    else:
        print(f"❌ Templates directory NOT found: {templates_dir}")
        
    # Check Flask template loading
    try:
        from flask import Flask
        app = Flask(__name__)
        print(f"✅ Flask template folder: {app.template_folder}")
        print(f"   Absolute path: {os.path.abspath(app.template_folder)}")
    except Exception as e:
        print(f"❌ Flask error: {e}")

if __name__ == "__main__":
    check_templates()