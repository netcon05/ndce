from types import SimpleNamespace
from typing import Dict


class NestedNamespace(SimpleNamespace):
    def __init__(self, dictionary: Dict, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            else:
                self.__setattr__(key, value)
