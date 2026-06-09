
from app.models.trigger_definitions import TriggerDefinition

class TriggerDefinitionRepository:

    def __init__(self, db):
        self.db = db

    def get_active(self):

        return (
            self.db.query(TriggerDefinition)
            .filter(TriggerDefinition.active.is_(True))
            .all()
        )