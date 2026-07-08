class VectorRetriever:
    def __init__(self, repository):
        self.repository = repository

    def search_action(self, embedding, limit: int = 20):
        raise NotImplementedError

    def search_triggers(self, embedding, limit: int = 20):
        raise NotImplementedError
