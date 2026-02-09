#!/usr/bin/env python3
import argparse
import requests
import sys
import json
import os

def main():
    parser = argparse.ArgumentParser(description="Dockerfile Optimizer CLI")
    parser.add_argument("--file", default="Dockerfile", help="Path to the Dockerfile to analyze")
    parser.add_argument("--server", default="http://localhost:8000/api", help="Backend API URL")
    parser.add_argument("--fail-on", default="HIGH", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], help="Fail the build if findings of this severity or higher are found")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: {args.file} not found.")
        sys.exit(1)

    with open(args.file, "r") as f:
        content = f.read()

    try:
        response = requests.post(
            f"{args.server}/analyze-dockerfile",
            json={"content": content},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"Error: Backend returned {response.status_code}")
            print(response.text)
            sys.exit(1)

        result = response.json()
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_summary(result, args.file)

        # Fail logic
        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        max_severity = 0
        
        findings = result.get("findings", [])
        for f in findings:
            sev = severity_map.get(f.get("severity", "LOW"), 1)
            if sev > max_severity:
                max_severity = sev
        
        if max_severity >= severity_map[args.fail_on]:
            if not args.json:
                print(f"\n❌ FAILED: Found issues with severity {args.fail_on} or higher.")
            sys.exit(1)
        else:
            if not args.json:
                print("\n✅ PASSED: No critical issues found.")

    except Exception as e:
        print(f"Error communicating with backend: {str(e)}")
        sys.exit(1)

def print_summary(result, filename):
    print(f"\n--- Analysis Results for {filename} ---")
    
    summary = result.get("summary", {})
    print(f"Scan Status: {summary.get('security_scan_status', 'N/A')}")
    print(f"Layer Count: {summary.get('layer_count', 0)}")
    print(f"Runs as Root: {'Yes' if summary.get('runs_as_root') else 'No'}")
    
    findings = result.get("findings", [])
    if not findings:
        print("\nNo issues found.")
    else:
        print("\nFindings:")
        for f in findings:
            icon = "🔴" if f['severity'] in ['HIGH', 'CRITICAL'] else "🟡" if f['severity'] == "MEDIUM" else "⚪"
            print(f"{icon} [{f['severity']}] {f['message']}")
            if f.get('recommendation'):
                print(f"   💡 {f['recommendation']}")

    if "recommendation" in result:
        print("\n✨ Optimization Available!")
        print("Run with --json to see the full optimized Dockerfile.")

if __name__ == "__main__":
    main()
