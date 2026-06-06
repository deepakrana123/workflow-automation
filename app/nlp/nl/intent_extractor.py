"""
Rule-based intent extractor.

Input:  natural language sentence
Output: {"trigger": str, "actions": list[str]}

No LLM. No embeddings. No vector search. No RAG.
Extraction is longest-match dictionary lookup over the normalized sentence.
"""

from app.nlp.nl.patterns import TRIGGER_PATTERNS, ACTION_PATTERNS


class UnknownTriggerError(ValueError):
    pass


class UnknownActionError(ValueError):
    pass


class IntentExtractor:
    """
    Extracts trigger and ordered action list from a natural language sentence.

    Algorithm:
      1. Normalize input to lowercase.
      2. Split on "when" to isolate the trigger clause.
      3. Split the remainder on action separators (then, and, ,).
      4. Longest-match lookup against TRIGGER_PATTERNS and ACTION_PATTERNS.
    """

    # Words that delimit separate actions in a sentence
    _ACTION_SEPARATORS = ("then", "and", ",")

    # Sentence opener — everything before this is ignored
    _TRIGGER_OPENER = "when"

    def extract(self, sentence: str) -> dict:
        """
        Extract intent from a natural language workflow sentence.

        Args:
            sentence: e.g. "When payment is due send reminder then notify manager"

        Returns:
            {"trigger": "payment_due", "actions": ["send_reminder", "notify_manager"]}

        Raises:
            ValueError: if sentence is empty
            UnknownTriggerError: if trigger phrase is not in the registry
            UnknownActionError: if any action phrase is not in the registry
        """
        text = sentence.strip().lower()
        if not text:
            raise ValueError("sentence is empty")

        trigger_clause, action_clause = self._split_trigger_action(text)
        trigger = self._match_trigger(trigger_clause)
        actions = self._match_actions(action_clause)

        return {"trigger": trigger, "actions": actions}

    def _split_trigger_action(self, text: str) -> tuple[str, str]:
        """
        Split sentence into (trigger_clause, action_clause).

        "when payment is due send reminder ..." → ("payment is due", "send reminder ...")
        """
        if self._TRIGGER_OPENER in text:
            after_when = text.split(self._TRIGGER_OPENER, 1)[1].strip()
        else:
            after_when = text

        # Trigger clause ends at the first action phrase match
        # We scan for the earliest position where an action phrase begins
        earliest_pos = len(after_when)
        for phrase in ACTION_PATTERNS:
            pos = after_when.find(phrase)
            if pos != -1 and pos < earliest_pos:
                earliest_pos = pos

        trigger_clause = after_when[:earliest_pos].strip()
        action_clause = after_when[earliest_pos:].strip()
        return trigger_clause, action_clause

    def _match_trigger(self, trigger_clause: str) -> str:
        """
        Longest-match lookup of trigger clause against TRIGGER_PATTERNS.
        """
        best_match = None
        best_len = 0
        for phrase, canonical in TRIGGER_PATTERNS.items():
            if phrase in trigger_clause and len(phrase) > best_len:
                best_match = canonical
                best_len = len(phrase)

        if not best_match:
            raise UnknownTriggerError(
                f"trigger not recognized: {trigger_clause!r}"
            )
        return best_match

    def _match_actions(self, action_clause: str) -> list[str]:
        """
        Split action clause on separators then longest-match each segment.
        Preserves left-to-right order (sequential dependency chain).
        """
        segments = self._split_on_separators(action_clause)
        actions = []
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            canonical = self._match_single_action(segment)
            actions.append(canonical)

        if not actions:
            raise UnknownActionError(
                f"no actions recognized in: {action_clause!r}"
            )
        return actions

    def _split_on_separators(self, text: str) -> list[str]:
        """Split action clause on 'then', 'and', ','."""
        parts = [text]
        for sep in self._ACTION_SEPARATORS:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts
        return parts

    def _match_single_action(self, segment: str) -> str:
        """Longest-match a single action segment."""
        best_match = None
        best_len = 0
        for phrase, canonical in ACTION_PATTERNS.items():
            if phrase in segment and len(phrase) > best_len:
                best_match = canonical
                best_len = len(phrase)

        if not best_match:
            raise UnknownActionError(
                f"action not recognized: {segment!r}"
            )
        return best_match
