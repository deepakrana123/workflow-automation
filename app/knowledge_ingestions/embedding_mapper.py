from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.semantic.embedding_provider import EmbeddingProvider
from app.retrieval.hybrid_retriever import HybridRetriever


class EmbeddingMapper:
    def __init__(
        self, repository: WorkflowRepository, hybrid_retriever: HybridRetriever
    ):
        self.repository = repository
        self.hybrid = hybrid_retriever

    def map_actions(self):
        actions = self.repository.get_unmapped_actions()
        for action in actions:
            query = f"{action.extract_name}{action.description}"
            embedding = self.hybrid.embed(action.extract_name)
            #   /  result = self.repository.find_best_action(embedding)
            # if result is None:
            #     continue
            # matched_action, distance = result
            # similarity = 1.0 - float(distance)
            # self.repository.update_action_mapping(
            #     mapping_id=action.id,
            #     action_definitation_id=matched_action.id,
            #     similarity_score=similarity,
            #     confidence=similarity,
            # )
            candidates = self.hybrid.search_actions(
                query=query, embedding=embedding, limit=20
            )
            if not candidates:
                continue

            best = candidates[0]

            self.repository.update_action_mapping(
                mapping_id=action.id,
                action_definitation_id=best.entity.id,
                similarity_score=best.rrf_score,
                confidence=best.rrf_score,
            )

    def map_triggers(self):
        triggers = self.repository.get_unmapped_triggers()
        for trigger in triggers:
            query = f"{trigger.extract_name}{trigger.description}"
            embedding = self.hybrid.embed(trigger.extracted_name)
            # result = self.repository.find_best_trigger(embedding)
            # if result is None:
            #     continue
            # mapped_trigger, distance = result
            # similarity = 1.0 - float(distance)
            # self.repository.update_trigger_mapping(
            #     mapping_id=trigger.id,
            #     trigger_definitation_id=mapped_trigger.id,
            #     similarity_score=similarity,
            #     confidence=similarity,
            # )
            candidates = self.hybrid.search_actions(
                query=query, embedding=embedding, limit=20
            )
            if not candidates:
                continue

            best = candidates[0]

            self.repository.update_trigger_mapping(
                mapping_id=trigger.id,
                trigger_definitation_id=best.entity.id,
                similarity_score=best.rrf_score,
                confidence=best.rrf_score,
            )
