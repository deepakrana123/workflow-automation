from app.models.action_definitions import ActionDefinition
class ActionDefinitionRepository:

    def __init__(self, db):
        self.db = db

    def get_active(self):

        return (
            self.db.query(ActionDefinition)
            .filter(ActionDefinition.active.is_(True))
            .all()
        )