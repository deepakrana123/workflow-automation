import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def try_call_ollama(prompt: str):

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        return {
            "success": True,
            "output": data["response"],
            "provider": "ollama",
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e),
            "provider": "ollama",
        }