from typing import Dict
import abc


class JSONDict(abc.ABC):
    @abc.abstractmethod
    def to_dict(self) -> Dict:
        return {}
