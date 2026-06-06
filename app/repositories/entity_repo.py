def fetch_entity_payload(db, entity_type, entity_id):
    if entity_type == "loan":
        return {
            "loan_id": entity_id,
            "customer_type": "vip",
            "salary": 90000,
            "complaints": 3,
            "loan_amount": 100000,
        }
    if entity_type == "ticket":
        return {"ticket_id": entity_id, "priority": "high"}
    return {}
