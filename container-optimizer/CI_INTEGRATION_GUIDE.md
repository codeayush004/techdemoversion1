# CI/CD Integration Guide: Dockerfile Optimizer Gate

Integrate Antigravity's optimization intelligence directly into your build pipeline to prevent insecure or unoptimized containers from reaching production.

## 🚀 Overview
The CI integration works by running a lightweight CLI scanner (`bin/optimizer-cli.py`) during your Pull Request flow. It analyzes your Dockerfile and acts as a "Gate"—blocking the merge if critical issues are found, while providing an AI-optimized replacement in a PR comment.

## 🛠️ Step 1: Add the CLI Tool
Copy `bin/optimizer-cli.py` to your repository. Ensure it is executable.

```bash
chmod +x bin/optimizer-cli.py
```

## 🤖 Step 2: Configure GitHub Actions
Create a new file at `.github/workflows/optimizer-gate.yml` and paste the following template:

```yaml
name: Dockerfile Optimizer Gate

on:
  pull_request:
    paths:
      - '**/Dockerfile*'

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write # Required to post comments
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      
      - name: Run Optimizer Scan
        env:
          OPTIMIZER_SERVER: ${{ secrets.OPTIMIZER_API_URL }}
        run: |
          python3 bin/optimizer-cli.py --file Dockerfile --server "$OPTIMIZER_SERVER" --json > scan_result.json
```

## 🔑 Step 3: Set up Secrets
In your GitHub Repository:
1. Go to **Settings > Secrets and variables > Actions**.
2. Add a new repository secret: `OPTIMIZER_API_URL`.
   - Use your Azure public IP: `http://40.65.144.231:8000/api` (or your local tunnel if testing).

## 🛡️ How the "Permission Gate" Works
1. When you open a PR, the scan runs automatically.
2. It posts a side-by-side comparison in a PR comment.
3. If findings are **HIGH** or **CRITICAL**, the CI check will **FAIL**.
4. **To Proceed (Granting Permission):**
   - **Option A (The Good Way):** Replace your Dockerfile content with the "Optimized Dockerfile Preview" provided in the comment.
   - **Option B (The Fast Way):** If you want to bypass the gate for a specific reason, you can adjust the `--fail-on` flag in the workflow to `CRITICAL` or `OFF`.

## 📈 CLI Usage Refrence
| Flag | Description | Default |
| :--- | :--- | :--- |
| `--file` | Path to Dockerfile | `Dockerfile` |
| `--server` | Backend API URL | `http://localhost:8000/api` |
| `--fail-on` | Severity threshold to fail | `HIGH` |
| `--json` | Output raw JSON data | `False` |
