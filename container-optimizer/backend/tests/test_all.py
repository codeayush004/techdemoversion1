import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.report.report_builder import build_static_report
from unittest.mock import patch

def test_static_analysis_integrity():
    print("Testing Static Analysis Integrity...")
    dockerfile = """
FROM node:18
RUN apt-get update && apt-get install -y gcc
ARG GITHUB_TOKEN=ghp_test12345
EXPOSE 8080
CMD ["node", "app.js"]
"""
    # Mock AI to isolate local logic
    with patch('app.core.report.report_builder.optimize_with_ai') as mock_ai:
        mock_ai.return_value = {
            "optimized_dockerfile": "FROM node:18-slim...",
            "explanation": ["Multi-stage build used"],
            "security_warnings": ["AI identified high risk"]
        }
        
        report = build_static_report(dockerfile)
        
        # 1. Check Findings formatting
        findings = report["findings"]
        print(f"Total findings: {len(findings)}")
        for f in findings:
            print(f"- {f['category']}: {f['message']}")
            assert "category" in f
            assert "message" in f
            assert "severity" in f

        # 2. Check Deduplication
        ai_findings = [f for f in findings if f["category"] == "AI"]
        static_findings = [f for f in findings if f["category"] == "ANALYSIS"]
        print(f"AI Findings: {len(ai_findings)}")
        print(f"Static Findings: {len(static_findings)}")
        
        # 3. Check specific detections
        messages = [f["message"].lower() for f in findings]
        assert any("exposed secret" in m for m in messages), "Should detect the GitHub Token"
        assert any("gcc" in m or "build tools" in m for f in report["misconfigurations"] for m in [f["message"].lower()]), "Should detect GCC"

    print("--- INTEGRITY TEST PASSED ---")

if __name__ == "__main__":
    try:
        test_static_analysis_integrity()
    except AssertionError as e:
        print(f"--- INTEGRITY TEST FAILED: {e} ---")
        sys.exit(1)
    except Exception as e:
        print(f"--- UNEXPECTED ERROR: {e} ---")
        sys.exit(1)
