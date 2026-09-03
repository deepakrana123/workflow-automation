import json


class WorkflowResponseParser:

    def parse(self, raw_response: str) -> dict:
        cleaned  = self._extract_json(raw_response)
        workflow = json.loads(cleaned)
        return self._normalize(workflow)

    # ── JSON extraction ───────────────────────────────────────────────────────

    def _extract_json(self, text: str) -> str:
        text  = text.strip()
        start = text.find("{")
        end   = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("json_not_found_in_response")

        return text[start : end + 1]

    # ── Normalisation ─────────────────────────────────────────────────────────

    def _normalize(self, data: dict) -> dict:
        # LLM returned an explicit error — surface it with a clear message
        # rather than falling through to "unsupported_workflow_format".
        if "error" in data and len(data) == 1:
            raise ValueError(f"llm_reported_error:{data['error']}")

        # Format 1 — already {"workflow": {...}}
        if "workflow" in data:
            workflow = data["workflow"]
            actions = [
                self._normalize_action(a)
                for a in workflow.get("actions", [])
            ]
            return {
                "workflow": {
                    "triggers": workflow.get("triggers", []),
                    "actions":  actions,
                }
            }

        # Format 2 — top-level {"triggers": [...], "actions": [...]}
        if "triggers" in data and "actions" in data:
            actions = [self._normalize_action(a) for a in data.get("actions", [])]
            return {
                "workflow": {
                    "triggers": data["triggers"],
                    "actions":  actions,
                }
            }

        # Format 3 — top-level {"trigger": "name", "actions": [...]}
        if "trigger" in data:
            actions = [self._normalize_action(a) for a in data.get("actions", [])]
            return {
                "workflow": {
                    "triggers": [{"name": data["trigger"]}],
                    "actions":  actions,
                }
            }

        raise ValueError("unsupported_workflow_format")

    def _normalize_action(self, action: dict) -> dict:
        action_name = action.get("name") or action.get("action")

        if not action_name:
            raise ValueError("action_name_missing")

        return {
            "name":         action_name,
            "dependencies": action.get("dependencies", []),
        }
