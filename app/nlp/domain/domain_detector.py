from collections import Counter
from typing import Optional


class DomainDetector:
    def detect(self, matched_triggers, matched_actions) -> Optional[str]:
        domain_counter = Counter()
        for trigger in matched_triggers:
            if getattr(trigger,'workflow_type',None):
                domain_counter[trigger.workflow_type]+=1
        for action in matched_actions:
            if getattr(action,'workflow_type',None):
                domain_counter[action.workflow_type]+=1
        if not domain_counter:
            return None
        return domain_counter.most_common(1)[0][0]