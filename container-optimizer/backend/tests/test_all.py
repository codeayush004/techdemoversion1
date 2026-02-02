import sys
import os
import unittest
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.report.report_builder import build_static_report

SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), "scenarios")

class TestDockerfileOptimizer(unittest.TestCase):
    
    @patch('app.core.report.report_builder.optimize_with_ai')
    @patch('app.core.report.report_builder.analyze_dockerfile_security')
    def run_scenario(self, filename, mock_security, mock_ai):
        # Setup mocks
        mock_ai.return_value = {
            "optimized_dockerfile": "FROM alpine\nCMD ['echo', 'mocked']",
            "explanation": ["Mocked for testing"],
            "security_warnings": []
        }
        mock_security.return_value = {
            "status": "ok",
            "total_vulnerabilities": 0,
            "vulnerabilities": []
        }
        
        filepath = os.path.join(SCENARIOS_DIR, filename)
        with open(filepath, "r") as f:
            content = f.read()
        
        report = build_static_report(content)
        runtime = report.get('image_analysis', {}).get('runtime', 'unknown')
        findings = [f.lower() for f in report["findings"]]
        
        return runtime, findings

    def test_python_bad(self):
        runtime, findings = self.run_scenario("python_bad.dockerfile")
        self.assertEqual(runtime, "python")
        self.assertTrue(any("exposed secret" in f for f in findings))
        self.assertTrue(any("root user" in f for f in findings))

    def test_node_bad(self):
        runtime, findings = self.run_scenario("node_bad.dockerfile")
        self.assertEqual(runtime, "node")
        self.assertTrue(any("excessive port range" in f for f in findings))
        self.assertTrue(any("build tools" in f for f in findings))

    def test_go_bad(self):
        runtime, findings = self.run_scenario("go_bad.dockerfile")
        self.assertEqual(runtime, "go")
        self.assertTrue(any("version not pinned" in f for f in findings))

    def test_java_bad(self):
        runtime, findings = self.run_scenario("java_bad.dockerfile")
        self.assertEqual(runtime, "java")
        self.assertTrue(any("secret" in f for f in findings))

    def test_hard_case(self):
        runtime, findings = self.run_scenario("hard_case.dockerfile")
        self.assertTrue(any("docker.sock" in f for f in findings))
        self.assertTrue(any("heavy base image" in f for f in findings))

if __name__ == "__main__":
    unittest.main()
