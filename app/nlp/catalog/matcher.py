from collections import Counter
from dataclasses import dataclass
from typing import List, Optional

from app.core.logger import logger


@dataclass
class CatalogMatchResult:
    workflow_type: Optional[str]
    matched_triggers: List
    matched_actions: List
    trigger_names: List[str]
    action_names: List[str]


class CatalogMatcher:
    def __init__(
        self,
        trigger_repository,
        action_repository,
        semantic_retriever=None,
    ):
        self.trigger_repository = trigger_repository
        self.action_repository = action_repository
        self.semantic_retriever = semantic_retriever

    def match(self, db, user_request: str) -> CatalogMatchResult:
        normalized_text = self._normalize(user_request)

        triggers = self.trigger_repository.get_active()
        actions = self.action_repository.get_active()

        # Keyword matching
        keyword_triggers = self._match_triggers(
            normalized_text,
            triggers,
        )

        keyword_actions = self._match_actions(
            normalized_text,
            actions,
        )

        # Semantic fallback — call retrieve once, unpack both
        semantic_triggers = []
        semantic_actions = []

        if self.semantic_retriever:
            if not keyword_triggers or not keyword_actions:
                sem_triggers, sem_actions = self.semantic_retriever.retrieve(
                    db,
                    user_request,
                )
                if not keyword_triggers:
                    semantic_triggers = sem_triggers
                if not keyword_actions:
                    semantic_actions = sem_actions

        # Merge keyword + semantic
        matched_triggers = self._merge(
            keyword_triggers,
            semantic_triggers,
        )

        matched_actions = self._merge(
            keyword_actions,
            semantic_actions,
        )

        logger.info(
            "keyword_triggers=%s",
            [x.name for x in keyword_triggers],
        )

        logger.info(
            "semantic_triggers=%s",
            [x.name for x in semantic_triggers],
        )

        logger.info(
            "final_triggers=%s",
            [x.name for x in matched_triggers],
        )

        logger.info(
            "keyword_actions=%s",
            [x.name for x in keyword_actions],
        )

        logger.info(
            "semantic_actions=%s",
            [x.name for x in semantic_actions],
        )

        logger.info(
            "final_actions=%s",
            [x.name for x in matched_actions],
        )

        workflow_type = self._detect_workflow_type(
            matched_triggers,
            matched_actions,
        )

        return CatalogMatchResult(
            workflow_type=workflow_type,
            trigger_names=[
                trigger.name
                for trigger in matched_triggers
            ],
            action_names=[
                action.name
                for action in matched_actions
            ],
            matched_triggers=matched_triggers,
            matched_actions=matched_actions,
        )

    def _match_triggers(self, normalized_text: str, triggers):
        matches = []

        for trigger in triggers:
            searchable_terms = self._build_search_terms(trigger)

            for searchable_text in searchable_terms:
                if searchable_text in normalized_text:
                    matches.append(trigger)
                    break

        return matches

    def _match_actions(self, normalized_text: str, actions):
        matches = []

        for action in actions:
            searchable_terms = self._build_search_terms(action)

            for searchable_text in searchable_terms:
                if searchable_text in normalized_text:
                    matches.append(action)
                    break

        return matches

    def _detect_workflow_type(
        self,
        matched_triggers,
        matched_actions,
    ) -> Optional[str]:

        workflow_counter = Counter()

        for trigger in matched_triggers:
            if trigger.workflow_type:
                workflow_counter[trigger.workflow_type] += 1

        for action in matched_actions:
            if action.workflow_type:
                workflow_counter[action.workflow_type] += 1

        if not workflow_counter:
            return None

        return workflow_counter.most_common(1)[0][0]

    def _build_search_terms(self, item):
        terms = []

        if item.name:
            terms.append(
                self._catalog_text(item.name)
            )

        if item.display_name:
            terms.append(
                self._catalog_text(item.display_name)
            )

        if item.aliases:
            for alias in item.aliases:
                terms.append(
                    self._catalog_text(alias)
                )

        return terms

    def _merge(
        self,
        keyword_matches,
        semantic_matches,
    ):
        merged = {}

        for item in keyword_matches:
            merged[item.id] = item

        for item in semantic_matches:
            if item.id not in merged:
                merged[item.id] = item

        return list(merged.values())

    @staticmethod
    def _normalize(text: str) -> str:
        import re

        return re.sub(
            r"\s+",
            " ",
            text.lower().strip(),
        )

    @staticmethod
    def _catalog_text(value: str) -> str:
        return value.replace(
            "_",
            " ",
        ).lower()