from typing import List, Type
from .BaseOverview import BaseOverview

REGISTRY: List[Type[BaseOverview]] = []

def register(cls: Type[BaseOverview]) -> Type[BaseOverview]:
    if cls not in REGISTRY:
        REGISTRY.append(cls)
    return cls