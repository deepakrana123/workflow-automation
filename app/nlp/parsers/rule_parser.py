import re
from app.nlp.models import ParseNode


class RuleParser:
    STEP_PATTERN = re.compile(
        r"@(?P<step>\d+)"
        r"(?:\s+@depends\((?P<deps>.*?)\))?"
        r"\s*:\s*"
        r"(?P<event>\w+)\s*->\s*(?P<action>\w+)",
        re.MULTILINE,
    )

    def parse(self, text: str) -> list[ParseNode]:
        nodes = []
        for match in self.STEP_PATTERN.finditer(text):
            step_id = match.group("step")
            event = match.group("event")
            action = match.group("action")
            raw_deps = match.group("deps")
            deps = []
            if raw_deps:
                deps = [
                    dep.strip().replace("@", "")
                    for dep in raw_deps.split(",")
                    if dep.strip()
                ]
            nodes.append(
                ParseNode(
                    step_id=step_id,
                    event=event,
                    action=action,
                    depends_on=deps,
                )
            )
        return nodes
