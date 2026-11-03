from abc import ABC, abstractmethod

from torch import Tensor


class Embedder(ABC):
    # THIS IS AN ABSTRACT OBJECT, YOU NEED TO IMPLEMENT YOUR ON EMBEDDER
    
    dim: int
    name: str

    @abstractmethod
    def get_embedding(self, text: str) -> Tensor:
        ...