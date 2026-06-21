import requests

r = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:7b",
        "prompt": "hello",
        "stream": False
    },
    timeout=60
)

print(r.json())