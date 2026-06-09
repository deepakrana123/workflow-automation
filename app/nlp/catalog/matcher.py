from collections import Counter
from dataclasses import dataclass
from typing import List,Optional


@dataclass
class CatalogMatchResult:
    workflow_type:Optional[str]
    triggers:List[str]
    actions:List[str]


class CatalogMatcher:
    def __init__(self,trigger_repository,action_repository):
        self.trigger_repository=trigger_repository
        self.action_repository=action_repository
    
    def match(self,user_request:str)->CatalogMatcher:
        normalized_text=self._normalize(user_request)
        
        triggers=self.trigger_repository.get_active()
        actions=self.action_repository.get_active()
        
        matched_triggers = self._match_triggers(
            normalized_text,
            triggers
        )
        matched_actions = self._match_actions(
            normalized_text,
            actions
        )
        
        workflow_type=self._detect_workflow_type(
            matched_triggers,
            matched_actions
        )
        
        return CatalogMatchResult(
            workflow_type=workflow_type,
            triggers=[trigger.name for trigger in matched_triggers],
            actions=[action.name for action in matched_actions],

        )
    
    def _match_triggers(self,normalized_text:str,triggers):
        matches=[]
        for trigger in triggers:
            searchable_text=self._catalog_text(trigger.name)
            if searchable_text in normalized_text:
                matches.append(trigger)
        return matches
    
    def _match_actions(self,normalized_text:str,actions):
        matches=[]
        for action in actions:
            searchable_text=self._catalog_text(action.name)
            if searchable_text in normalized_text:
                matches.append(action)
        return matches
    
    def _detect_workflow_type(
        self,matched_triggers,matched_actions
    )->Optional[str]:
        workflow_counter=Counter()
        for trigger in matched_triggers:
            if trigger.workflow_type:
                workflow_counter[trigger.workflow_type]+=1
        for action in matched_actions:
            if action.workflow_type:
                workflow_counter[action.workflow_type]+=1
        if not workflow_counter:
            return None
        return workflow_counter.most_common(1)[0][0]
    
    
    @staticmethod
    def _normalize(text:str)->str:
        return text.lower().strip()
    
    @staticmethod
    def _catalog_text(value:str)->str:
        return value.replace("_"," ").lower()