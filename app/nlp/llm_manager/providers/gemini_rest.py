import requests
import os

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent?key={API_KEY}"
)


def try_call_gemini_rest(prompt: str):

    try:

        response = requests.post(
            URL,
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        text = (
            data["candidates"][0]
            ["content"]["parts"][0]
            ["text"]
        )

        return {
            "success": True,
            "provider": "gemini",
            "output": text,
        }

    except Exception as e:

        return {
            "success": False,
            "provider": "gemini",
            "error": str(e),
        }