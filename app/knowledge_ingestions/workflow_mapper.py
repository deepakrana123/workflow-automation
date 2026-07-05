from app.knowledge_ingestions.schemas import WorkflowExtraction


class WorkflowMapper:
    """Maps extracted workflow data into persistence-ready dictionaries."""
    def to_dict(self,workflow:WorkflowExtraction)->dict:
        return workflow.model_dump()