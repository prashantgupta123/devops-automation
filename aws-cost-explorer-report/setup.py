#!/usr/bin/env python3
"""
Setup script for AWS Cost Explorer Report
"""

import os
import shutil
import subprocess
import sys

def install_requirements():
    """Install required Python packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install requirements")
        return False

def setup_config():
    """Setup configuration file"""
    if os.path.exists('account_details.json'):
        print("✓ account_details.json already exists")
        return True
    
    if os.path.exists('account_details_template.json'):
        try:
            shutil.copy('account_details_template.json', 'account_details.json')
            print("✓ Created account_details.json from template")
            print("  Please edit account_details.json with your AWS account details")
            return True
        except Exception as e:
            print(f"✗ Failed to create config file: {e}")
            return False
    else:
        print("✗ Template file not found")
        return False

def make_scripts_executable():
    """Make shell scripts executable"""
    scripts = ['prowler-script.sh', 'scout-script.sh', 'run_report.py']
    for script in scripts:
        if os.path.exists(script):
            try:
                os.chmod(script, 0o755)
                print(f"✓ Made {script} executable")
            except Exception as e:
                print(f"✗ Failed to make {script} executable: {e}")

def main():
    """Main setup function"""
    print("AWS Cost Explorer Report - Setup")
    print("=" * 40)
    
    success = True
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Setup configuration
    if not setup_config():
        success = False
    
    # Make scripts executable
    make_scripts_executable()
    
    print("\n" + "=" * 40)
    if success:
        print("Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit account_details.json with your AWS account details")
        print("2. Run: python run_report.py")
    else:
        print("Setup completed with errors. Please check the output above.")
    print("=" * 40)

if __name__ == "__main__":
    main()