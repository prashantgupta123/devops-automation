#!/usr/bin/env python3
"""
AWS Cost Explorer Report Generator
Runs cost analysis and generates Excel report
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main execution function"""
    print("AWS Cost Explorer Report Generator")
    print("=" * 50)
    
    # Check if account_details.json exists
    if not os.path.exists('account_details.json'):
        print("Error: account_details.json not found!")
        print("Please create account_details.json with your AWS account details.")
        sys.exit(1)
    
    # Step 1: Generate cost breakdown JSON
    if not run_command([sys.executable, 'function.py'], "Generating cost breakdown data"):
        print("Failed to generate cost data. Exiting.")
        sys.exit(1)
    
    # Step 2: Generate Excel report
    if not run_command([sys.executable, 'excel_export.py'], "Generating Excel report"):
        print("Failed to generate Excel report. Exiting.")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("Report generation completed successfully!")
    print("Files generated:")
    print("- cost_breakdown_by_region.json")
    print("- aws_cost_report.xlsx")
    print("="*50)

if __name__ == "__main__":
    main()