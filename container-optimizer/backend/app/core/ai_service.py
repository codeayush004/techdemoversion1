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
   - NEVER assume files exist unless shown in the original Dockerfile or build commands.
2. CONSISTENCY:
   - Match the base image family (Debian/Ubuntu vs Alpine). If the original is Debian, the optimized version MUST stay Debian-based.
   - TAG ACCURACY: Use `python:3.11-slim-bookworm` or `node:20-slim`. 
   - IMPORTANT: For Nginx, Redis, Postgres, and MySQL, DO NOT add '-slim' as it often doesn't exist for these; use the stable version tag (e.g., `nginx:1.27.2`) or the `-alpine` variant if size is the priority.
3. EXPERT REASONING:
   - Your 'explanation' must provide technical 'Why' (e.g., "Reduced image size by 40% using multi-stage builds and excluding build-time dependencies like gcc").
4. SECURITY:
   - Always implement a non-root USER with proper permissions.
   - Use fixed tags. NEVER use 'latest'.
5. DEDUPLICATION TAGS:
   - For every security warning, you MUST prefix it with a technical ID in brackets if applicable. 
   - Examples: `[RUN_AS_ROOT]`, `[NO_VERSION_PINNING]`, `[MISSING_HEALTHCHECK]`, `[SECRET_EXPOSURE]`, `[HEAVY_IMAGE]`.
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
