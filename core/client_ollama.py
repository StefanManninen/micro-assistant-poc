import requests
import json

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.generate_url = f"{base_url}/api/generate"
        self.chat_url = f"{base_url}/api/chat"

    def ask_gemma_core(self, user_prompt, context_history=None):
        """Talking to gemma3:270m for dialogue and intent analysis."""
        payload = {
            "model": "gemma3:270m",
            "prompt": user_prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }
        try:
            response = requests.post(self.generate_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error when calling gemma3:270m: {str(e)}"

    def ask_function_router(self, system_context, tool_schemas):
        """Sending intent and available tools to functiongemma."""
        # FunctionGemma often expects system instructions with JSON schemas
        prompt = f"Context: {system_context}\nAvailable Tools: {json.dumps(tool_schemas)}\nSelect the correct tool or return 'no_tool'."
        
        payload = {
            "model": "functiongemma",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0} # Extremely deterministic
        }
        try:
            response = requests.post(self.generate_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"no_tool" # Crash fallback