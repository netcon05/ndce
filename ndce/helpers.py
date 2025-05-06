from types import SimpleNamespace
from typing import Dict


class NestedNamespace(SimpleNamespace):
    """
    Class for converting python dictionaries into
    js like objects to get values using dot notation
    """
    def __init__(self, dictionary: Dict, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            else:
                self.__setattr__(key, value)
