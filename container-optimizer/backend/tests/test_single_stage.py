import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.suggestors.dockerfile_suggestor import suggest_dockerfile

def test_single_stage_suggestions():
    print("Testing Single-Stage Suggestions...")
    
    # Test cases for Python
    python_image = {"runtime": "python", "total_size_mb": 100}
    python_runtime = {"runs_as_root": True}
    python_misconfigs = []
    
    python_report = suggest_dockerfile(python_image, python_runtime, python_misconfigs)
    python_dockerfile = python_report["dockerfile"]
    
    print("Checking Python Dockerfile...")
    from_count = python_dockerfile.upper().count("FROM")
    assert from_count == 1, f"Expected 1 FROM instruction for Python, found {from_count}"
    assert "AS builder" not in python_dockerfile, "Should not contain build stages for simple Python"
    
    # Test cases for Node
    node_image = {"runtime": "node", "total_size_mb": 150}
    node_runtime = {"runs_as_root": True}
    node_misconfigs = []
    
    node_report = suggest_dockerfile(node_image, node_runtime, node_misconfigs)
    node_dockerfile = node_report["dockerfile"]
    
    print("Checking Node Dockerfile...")
    from_count = node_dockerfile.upper().count("FROM")
    assert from_count == 1, f"Expected 1 FROM instruction for Node, found {from_count}"
    assert "AS builder" not in node_dockerfile, "Should not contain build stages for simple Node"

    # Test cases for Go (should still be multi-stage as it benefits significantly)
    go_image = {"runtime": "go", "total_size_mb": 300}
    go_runtime = {"runs_as_root": True}
    go_misconfigs = []
    
    go_report = suggest_dockerfile(go_image, go_runtime, go_misconfigs)
    go_dockerfile = go_report["dockerfile"]
    
    print("Checking Go Dockerfile (Should stay multi-stage)...")
    # Count only lines that start with FROM (ignoring case and whitespace)
    from_lines = [line for line in go_dockerfile.splitlines() if line.strip().upper().startswith("FROM ")]
    from_count = len(from_lines)
    assert from_count == 2, f"Expected 2 FROM instructions for Go, found {from_count}: {from_lines}"
    assert "AS builder" in go_dockerfile, "Go should still use multi-stage"

    print("--- SINGLE-STAGE SUGGESTION TEST PASSED ---")

if __name__ == "__main__":
    try:
        test_single_stage_suggestions()
    except AssertionError as e:
        print(f"--- TEST FAILED: {e} ---")
        sys.exit(1)
    except Exception as e:
        print(f"--- UNEXPECTED ERROR: {e} ---")
        sys.exit(1)
