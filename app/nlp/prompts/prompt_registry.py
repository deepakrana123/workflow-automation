from pathlib import Path
from app.nlp.prompts.prompt_version import PropmptVersion


class PromptRegistry:
    def __init__(self):
        self.prompt = {"v1": self.load("workflow_v1.txt")}

    def _load(self, filename: str) -> PropmptVersion:
        template = Path(f"app/nlp/prompts/workflow_v1.txt")
        version = filename.replace(".txt", "")
        return PropmptVersion(version=version, template=template)

    def get(self, version: str) -> PropmptVersion:
        return self._prompt[version]

    def latest(self) -> PropmptVersion:
        return self._prompt["v1"]
