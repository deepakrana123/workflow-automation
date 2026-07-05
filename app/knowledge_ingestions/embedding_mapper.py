from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from sentence_transformers import SentenceTransformer


class EmbeddingMapper:
    def __init__(self, repository: WorkflowRepository):
        self.repository = repository
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def map_actions(self):
        actions = self.repository.get_unmapped_actions()
        for action in actions:
            embedding = self.model.encode(
                action.extract_name, normalize_embeddings=True
            )
            matched_action, distance = self.repository.find_best_action(embedding)
            # if distance > 0.40:
            #     continue
            self.repository.update_action_mapping(
                mapping_id = action.id,
                action_definitation_id=matched_action.id,
                similarity_score=float(distance),
                confidence=float(distance)
            )

    def map_triggers(self):
        triggers = self.repository.get_unmapped_triggers()
        for trigger in triggers:
            embedding = self.model.encode(
                trigger.extracted_name, normalize_embeddings=True
            )
            mapped_trigger, distance = self.repository.find_best_trigger(embedding)
           
            self.repository.update_trigger_mapping(
                mapping_id=trigger.id,
                trigger_definitation_id=mapped_trigger.id,
                similarity_score=float(distance),
                confidence=float(distance)
            )
