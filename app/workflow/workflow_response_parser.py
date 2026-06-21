import json


class WorkflowResponseParser:
    # def parse(self, raw_response: str):
    #     cleaned = self._extract_json(raw_response)
    #     workflow = json.loads(cleaned)
    #     return self._normalize(workflow)
    def parse(self, raw_response: str):
        cleaned = self._extract_json(raw_response)
        workflow = json.loads(cleaned)

        return self._normalize(workflow)

    def _extract_json(self, text: str) -> str:

        text = text.strip()

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("json_not_found_in_response")

        return text[start : end + 1]

    def _normalize(self, data):

        # format 1
        if "workflow" in data:
            return data

        # format 2
        if "triggers" in data and "actions" in data:

            actions = [
                self._normalize_action(action) for action in data.get("actions", [])
            ]
            return {
                "workflow": {
                    "triggers": data["triggers"],
                    "actions": actions,
                }
            }

        # format 3
        if "trigger" in data:

            actions = [
                self._normalize_action(action) for action in data.get("actions", [])
            ]
            return {
                "workflow": {
                    "triggers": [{"name": data["trigger"]}],
                    "actions": actions,
                }
            }

        raise ValueError("unsupported_workflow_format")

    def _normalize_action(self, action):

        action_name = action.get("name") or action.get("action")

        if not action_name:
            raise ValueError("action_name_missing")

        return {
            "name": action_name,
            "dependencies": action.get("dependencies", []),
        }
