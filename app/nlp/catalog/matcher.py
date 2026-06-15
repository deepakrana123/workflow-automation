from collections import Counter
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CatalogMatchResult:
    workflow_type: Optional[str]
    matched_triggers: List
    matched_actions: List
    trigger_names: List[str]
    action_names: List[str]


class CatalogMatcher:
    def __init__(self, trigger_repository, action_repository):
        self.trigger_repository = trigger_repository
        self.action_repository = action_repository

    def match(self, user_request: str) -> CatalogMatchResult:
        normalized_text = self._normalize(user_request)
        triggers = self.trigger_repository.get_active()
        actions = self.action_repository.get_active()
        matched_triggers = self._match_triggers(normalized_text, triggers)
        matched_actions = self._match_actions(normalized_text, actions)
        workflow_type = self._detect_workflow_type(matched_triggers, matched_actions)

        return CatalogMatchResult(
            workflow_type=workflow_type,
            trigger_names=[trigger.name for trigger in matched_triggers],
            action_names=[action.name for action in matched_actions],
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

    def _detect_workflow_type(self, matched_triggers, matched_actions) -> Optional[str]:
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
            terms.append(self._catalog_text(item.name))
        if item.display_name:
            terms.append(self._catalog_text(item.display_name))
        if item.aliases:
            for alias in item.aliases:
                terms.append(self._catalog_text(alias))
        return terms

    @staticmethod
    def _normalize(text: str) -> str:
        import re
        return re.sub(r'\s+', ' ', text.lower().strip())

    @staticmethod
    def _catalog_text(value: str) -> str:
        return value.replace("_", " ").lower()
