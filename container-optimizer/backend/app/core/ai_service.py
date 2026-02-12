import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def optimize_with_ai(image_context: dict, dockerfile_content: str = None):
    """
    Calls Groq AI to perform deep optimization of a Dockerfile or Image.
    """
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not found in environment")

    # Construct the prompt
    prompt = f"""
You are an expert Docker and DevSecOps engineer. Your task is to analyze a Docker image/Dockerfile and provide an industry-ready, SECURE, and OPTIMIZED replacement.

### CONTEXT:
Image: {image_context.get('image', 'unknown')}
Detected Runtime: {image_context.get('runtime', 'unknown')}
Misconfigurations Found: {json.dumps(image_context.get('misconfigurations', []), indent=2)}

### ORIGINAL DOCKERFILE CONTENT (If provided):
{dockerfile_content or "Not provided. Use image metadata and misconfigurations above."}

### OUTPUT FORMAT:
Your response must be a VALID JSON object with the following keys:
- "optimized_dockerfile": The complete string of the new Dockerfile.
- "dockerignore": Recommended .dockerignore content.
- "explanation": An array of strings explaining the key changes.
- "security_warnings": An array of specific security alerts discovered.

DO NOT include any conversation or markdown outside the JSON object.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_message = """You are a specialized Docker Optimization AI. You ONLY output valid JSON.
CRITICAL MANDATES for logic accuracy:
1. TRUTHFULNESS: 
   - NEVER suggest a tool (curl, wget, ping) in a CMD or HEALTHCHECK unless you explicitly install it in the SAME stage using a package manager (apt/apk).
   - Prefer native healthchecks (e.g., Python `socket` module) over installing external tools whenever possible.
2. CONSISTENCY & TAGS:
   - Match the base image family (Debian vs Alpine). If the original is Debian, stay Debian-based (use `-slim-bookworm`).
   - For Nginx, Redis, Postgres, and MySQL, use stable version tags (e.g., `nginx:1.27.2`) or `-alpine` if size is priority.
3. ARCHITECTURE & PERFORMANCE:
   - MANDATE: Use Multi-Stage builds ONLY when a complex build/compilation step is present (e.g., `npm run build`, `go build`, `mvn package`) or if removing compilers (GCC) saves >80MB.
   - MANDATE: For simple runner scripts (e.g., Python/Node apps with no compilation/build phase), you MUST use a SINGLE-STAGE optimized build. Perform all installs and aggressive CLEANUP (apt-get purge, rm cache) in the same `RUN` layer to keep it lean.
   - MANDATE: For web/app frameworks, the final stage MUST use a production runner (e.g., `node server.js`, `gunicorn`, or a static server) and NEVER a dev server (`npm run dev`).
   - MANDATE: Always `COPY` dependency files (`requirements.txt`, `package.json`, `go.mod`) and install BEFORE doing `COPY . .`.
4. SECURITY:
   - Always implement a non-root USER. 
   - Ensure explicit ownership: Use `COPY --chown=appuser:appgroup . .` or run `chown` AFTER all files are copied to ensure no files remain owned by root.
   - Use fixed tags. NEVER use 'latest'.
5. OUTPUT CONTENT:
   - Your 'explanation' must provide technical 'Why' (e.g., "Used a single-stage build with aggressive layer cleanup because a builder stage adds unnecessary complexity for a simple script").
   - Your 'dockerignore' MUST include common bloat: `venv/`, `.git/`, `node_modules/`, `__pycache__/`, `.env`.
6. DEDUPLICATION TAGS:
   - Prefix security warnings with: `[RUN_AS_ROOT]`, `[NO_VERSION_PINNING]`, `[MISSING_HEALTHCHECK]`, `[SECRET_EXPOSURE]`, `[DEV_SERVER_IN_PROD]`.
"""

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"Groq API Error Status: {response.status_code}")
            print(f"Groq API Error Response: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        
        # Parse the JSON string from the AI response
        ai_response_content = data['choices'][0]['message']['content']
            
        return json.loads(ai_response_content)
        
    except Exception as e:
        print(f"Groq API Error: {e}")
        raise Exception(f"Failed to communicate with AI: {str(e)}")
