import json


def repair_json(text: str):
    try:
        return {"success": True, "data": json.loads(text)}
    except Exception:
        return {"success": False}

