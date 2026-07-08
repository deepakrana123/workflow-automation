class KeywordRetriever:
    def __init__(self,repository):
        self.repository=repository
    
    def search_action(self,query:str,limit:int=20):
        raise NotImplementedError
    
    
    def search_triggers(self,query:str,limit:int=20):
        raise NotImplementedError