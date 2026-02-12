import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.suggestors.dockerfile_suggestor import suggest_dockerfile

def test_build_aware_suggestions():
    print("Testing Build-Aware Suggestions...")
    
    # Test cases for Python (Now multi-stage for apps)
    python_image = {"runtime": "python", "total_size_mb": 100}
    python_runtime = {"runs_as_root": True}
    python_misconfigs = []
    
    python_report = suggest_dockerfile(python_image, python_runtime, python_misconfigs)
    python_dockerfile = python_report["dockerfile"]
    
    print("Checking Python Dockerfile...")
    # Count only lines that start with FROM (ignoring case and whitespace)
    from_lines = [line for line in python_dockerfile.splitlines() if line.strip().upper().startswith("FROM ")]
    from_count = len(from_lines)
    assert from_count == 2, f"Expected 2 FROM instructions for Python App, found {from_count}: {from_lines}"
    assert "AS builder" in python_dockerfile, "Python App should use a builder stage"
    
    # Test cases for Node (Now multi-stage and production-correct)
    node_image = {"runtime": "node", "total_size_mb": 150}
    node_runtime = {"runs_as_root": True}
    node_misconfigs = []
    
    node_report = suggest_dockerfile(node_image, node_runtime, node_misconfigs)
    node_dockerfile = node_report["dockerfile"]
    
    print("Checking Node Dockerfile...")
    from_lines = [line for line in node_dockerfile.splitlines() if line.strip().upper().startswith("FROM ")]
    from_count = len(from_lines)
    assert from_count == 2, f"Expected 2 FROM instructions for Node App, found {from_count}: {from_lines}"
    assert 'CMD ["node", "server.js"]' in node_dockerfile, "Node App should use production runner, not npm run dev"
    assert "COPY --chown=node:node . ." in node_dockerfile, "Should use --chown for security"

    print("--- BUILD-AWARE SUGGESTION TEST PASSED ---")

if __name__ == "__main__":
    try:
        test_build_aware_suggestions()
    except AssertionError as e:
        print(f"--- TEST FAILED: {e} ---")
        sys.exit(1)
    except Exception as e:
        print(f"--- UNEXPECTED ERROR: {e} ---")
        sys.exit(1)
