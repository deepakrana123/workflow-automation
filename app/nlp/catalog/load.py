from sqlalachemy.orm import Session
from app.models.trigger_definitions import TriggerDefinition
from app.models.action_definitions import ActionDefinition


class CatalogLoader:
    def load(self,db:Session):
        triggers=(
            db.query(TriggerDefinition).filter(TriggerDefinition.active==True).all()
            
        )
        actions=(
            db.query(ActionDefinition).filter(ActionDefinition.active==True).all()
        )
        return {
             "triggers": triggers,
            "actions": actions,
        }