import re


def normalize(text: str) -> str:
    return text.lower().strip()


def extract_days(text: str):
    match = re.search(r"(\d+)\s*days?", normalize(text))
    return int(match.group(1)) if match else None


def extract_fallback(text: str):
    text = text.lower()
    fallback_map = {
        "escalate": "escalate_case",
        "senior officer": "assign_senior_officer",
        "manager": "assign_senior_officer",
        "close case": "close_case",
        "close": "close_case",
        "remind": "send_reminder",
        "send reminder": "send_reminder",
    }
    patterns = [
        r"fallback to (.+)",
        r"if fail[s]?\s+(.+)",
        r"else\s+(.+)",
        r"on failure\s+(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phrase = match.group(1).strip()
            for key, action in fallback_map.items():
                if key in phrase:
                    return action
    return None


def extract_amount_threshold(text: str):
    text = normalize(text)

    patterns = [
        r"amount\s*[>]=?\s*(\d+)",
        r"amount.*?(?:exceeds|greater than|more than)\s*(\d+)",
        r"above\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    return None


def extract_risk_flag(text: str):
    text = normalize(text)
    if "risky" in text or "risk" in text:
        return True
    return None


def extract_flags(text: str):
    text = normalize(text)
    return {
        "vip": "vip" in text,
        "premium": "premium" in text,
        "urgent": "urgent" in text,
    }


def extract_entity_refs(text: str):
    refs = {}

    loan = re.search(r"\bLN\d+\b", text, re.I)
    ticket = re.search(r"\bTK\d+\b", text, re.I)
    customer = re.search(r"\bCU\d+\b", text, re.I)
    case = re.search(r"\bCASE\d+\b", text, re.I)

    if loan:
        refs["loan_id"] = loan.group().upper()
    if ticket:
        refs["ticket_id"] = ticket.group().upper()
    if customer:
        refs["customer_id"] = customer.group().upper()
    if case:
        refs["case_id"] = case.group().upper()

    return refs


def extract_retry(text: str):
    text = normalize(text)

    patterns = [
        r"retry\s+(\d+)\s+times",
        r"retry\s+(\d+)",
        r"try\s+(\d+)\s+times",
        r"attempt\s+(\d+)\s+times",
        r"max\s+retry\s+(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    return None


def extract_channel(text: str):
    text = normalize(text)

    channel_map = {
        "sms": "sms",
        "email": "email",
        "mail": "email",
        "whatsapp": "whatsapp",
        "push": "push",
        "call": "call",
        "phone": "call",
    }

    for word, channel in channel_map.items():
        if word in text:
            return channel

    return None


def extract_config(text: str):
    config = {}
    retry = extract_retry(text)
    channel = extract_channel(text)
    if retry is not None:
        config["retry_max"] = retry
    if channel:
        config["channel"] = channel
    return config


def extract_all(text: str):
    return {
        "days": extract_days(text),
        "amount_threshold": extract_amount_threshold(text),
        "risk_flag": extract_risk_flag(text),
        "flags": extract_flags(text),
        "entity_refs": extract_entity_refs(text),
        "config": extract_config(text),
        "fallback": extract_fallback(text),
    }
