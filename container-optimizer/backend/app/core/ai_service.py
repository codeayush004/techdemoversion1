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
You are an expert Docker and DevSecOps engineer. Your task is to analyze a Docker image/Dockerfile and provide an industry-ready, SECURE, and OPTIMIZED multi-stage replacement.

### CONTEXT:
Image: {image_context.get('image', 'unknown')}
Detected Runtime: {image_context.get('runtime', 'unknown')}
Misconfigurations Found: {json.dumps(image_context.get('misconfigurations', []), indent=2)}

### ORIGINAL DOCKERFILE CONTENT (If provided):
{dockerfile_content or "Not provided. Use image metadata and misconfigurations above."}

### REQUIREMENTS:
1. Use MULTI-STAGE builds where appropriate.
   - CRITICAL for Python: If using multi-stage, dependencies installed in the build stage MUST be available in the final stage. Use a virtual environment (venv) in `/opt/venv` and copy it, or use `--user` and copy `.local`.
2. Use minimal base images (slim, alpine, distroless).
3. NEVER run as root. Create and use a non-root user.
4. Add a HEALTHCHECK.
5. Identify and fix security risks (like volume-mounted docker sockets, exposed secrets, etc.).
6. Use modern BuildKit features like --mount=type=cache where applicable.
7. Provide a DETAILED explanation for every change made.
8. Ensure the Dockerfile is FUNCTIONAL. Don't skip copying dependencies if the runtime needs them.

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

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a specialized Docker Optimization AI. You only output valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
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
