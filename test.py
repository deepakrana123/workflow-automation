from app.db.session import SessionLocal

from app.nlp.catalog.triggerRepository import TriggerDefinitionRepository
from app.nlp.catalog.actionRepository import ActionDefinitionRepository

from app.nlp.catalog.matcher import CatalogMatcher


def main():

    db = SessionLocal()

    try:

        trigger_repo = TriggerDefinitionRepository(db)

        action_repo = ActionDefinitionRepository(db)

        matcher = CatalogMatcher(
            trigger_repo,
            action_repo,
        )

        result = matcher.match(
            "when payment due send reminder and escalate case"
        )

        print(result)

    finally:
        db.close()


if __name__ == "__main__":
    main()