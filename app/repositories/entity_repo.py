"""
app/repositories/entity_repo.py

Entity payload retrieval.

NOTE: This is a placeholder stub that returns mock data.
Replace with actual DB queries when entity models are implemented.
"""


def get_payload(db, entity_type: str, entity_id: str) -> dict:
    """
    Retrieve entity payload by type and id.

    Returns an empty dict if entity type is unknown.
    """
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
