from abc import ABC, abstractmethod

from app.execution.python.base.generate_model import GeneratedFile


class FileGenerator(ABC):

    @abstractmethod
    def generate(
        self,
        payload: dict,
        configuration: dict,
    ) -> GeneratedFile:
        pass
