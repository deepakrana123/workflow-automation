"""
app/nlp/prompts/prompt_version_store.py

In-memory store for active prompt versions and rollback state.

Tracks:
    { prompt_name: { active_version, previous_version, updated_at } }

Rules:
- Starts with "v1" as active for every known prompt.
- set_active() promotes a version — saves current as previous_version.
- rollback() swaps active ↔ previous_version.
- If no previous_version exists, rollback raises ValueError.

Thread-safety: single-process. Back with Redis when multi-worker is needed.
"""

import time
from app.core.logger import logger

# Auto-rollback threshold: if this many consecutive failures happen on the
# active version, rollback is triggered automatically.
AUTO_ROLLBACK_THRESHOLD = 5


class PromptVersionStore:

    def __init__(self, default_version: str = "v1"):
        self._default = default_version
        # { prompt_name: { active, previous, updated_at, consecutive_failures } }
        self._store: dict[str, dict] = {}

    def _get(self, prompt_name: str) -> dict:
        if prompt_name not in self._store:
            self._store[prompt_name] = {
                "active": self._default,
                "previous": None,
                "updated_at": time.time(),
                "consecutive_failures": 0,
            }
        return self._store[prompt_name]

    # ------------------------------------------------------------------ #
    #  Read                                                                #
    # ------------------------------------------------------------------ #

    def get_active(self, prompt_name: str) -> str:
        return self._get(prompt_name)["active"]

    def get_previous(self, prompt_name: str) -> str | None:
        return self._get(prompt_name)["previous"]

    def get_state(self, prompt_name: str) -> dict:
        state = self._get(prompt_name)
        return {
            "prompt_name": prompt_name,
            "active_version": state["active"],
            "previous_version": state["previous"],
            "consecutive_failures": state["consecutive_failures"],
            "updated_at": state["updated_at"],
        }

    def get_all_states(self) -> list[dict]:
        return [self.get_state(name) for name in sorted(self._store.keys())]

    # ------------------------------------------------------------------ #
    #  Write                                                               #
    # ------------------------------------------------------------------ #

    def set_active(self, prompt_name: str, version: str) -> None:
        """Promote a version to active. Saves current as previous."""
        state = self._get(prompt_name)
        old = state["active"]
        state["previous"] = old
        state["active"] = version
        state["updated_at"] = time.time()
        state["consecutive_failures"] = 0
        logger.info(
            "prompt_version_activated",
            extra={
                "extra_data": {
                    "prompt_name": prompt_name,
                    "from": old,
                    "to": version,
                }
            },
        )

    def rollback(self, prompt_name: str) -> str:
        """
        Revert active version to previous_version.
        Returns the version that was rolled back to.
        Raises ValueError if no previous version exists.
        """
        state = self._get(prompt_name)
        previous = state["previous"]
        if not previous:
            raise ValueError(
                f"No previous version to roll back to for prompt '{prompt_name}'."
            )
        current = state["active"]
        state["active"] = previous
        state["previous"] = current
        state["updated_at"] = time.time()
        state["consecutive_failures"] = 0
        logger.warning(
            "prompt_version_rolled_back",
            extra={
                "extra_data": {
                    "prompt_name": prompt_name,
                    "from": current,
                    "to": previous,
                }
            },
        )
        return previous

    # ------------------------------------------------------------------ #
    #  Auto-rollback tracking                                              #
    # ------------------------------------------------------------------ #

    def record_failure(self, prompt_name: str) -> bool:
        """
        Increment consecutive failure counter.
        Returns True if auto-rollback threshold is reached.
        """
        state = self._get(prompt_name)
        state["consecutive_failures"] += 1
        if state["consecutive_failures"] >= AUTO_ROLLBACK_THRESHOLD:
            if state["previous"]:
                return True
        return False

    def record_success(self, prompt_name: str) -> None:
        """Reset consecutive failure counter on success."""
        self._get(prompt_name)["consecutive_failures"] = 0


# Module-level singleton
version_store = PromptVersionStore()
