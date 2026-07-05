class DocumentExtractionError(Exception):
    """Raised when document extraction failed"""

    pass

class WorkflowExtractionError(Exception):
    """ Raised when document filed form extraction"""
    pass


class RepositoryError(Exception):
    """Raised when database persistence fails."""
    pass