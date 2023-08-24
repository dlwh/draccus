"""Abstract Wrapper base-class for the FieldWrapper and DataclassWrapper."""
import argparse
from abc import ABC, abstractmethod
from dataclasses import Field
from typing import Generic, List, Optional, Type

from draccus.utils import T

# We can think of a Wrapper as a node in a tree, where the root is the DataclassWrapper for the root dataclass, and the
# leaves are the FieldWrappers. (So internal nodes are DataclassWrappers, for now.)


class Wrapper(Generic[T], ABC):
    @property
    def dest(self) -> str:
        """Where the attribute will be stored in the Namespace."""
        if self.parent is None:
            return self.name
        lineage_names: List[str] = [w.name for w in self.lineage()]
        if lineage_names[-1] is None:  # root usually won't have a name
            lineage_names = lineage_names[:-1]

        r = list(reversed([self.name, *lineage_names]))
        return ".".join(r)

    def lineage(self) -> List["Wrapper"]:
        lineage: List[Wrapper] = []
        parent = self.parent
        while parent is not None:
            lineage.append(parent)
            parent = parent.parent
        return lineage

    @property
    def nesting_level(self) -> int:
        return len(self.lineage())
        level = 0
        parent = self.parent
        while parent is not None:
            parent = parent.parent
            level += 1
        return level

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def parent(self) -> Optional["Wrapper"]:
        pass

    @property
    @abstractmethod
    def required(self) -> bool:
        pass

    @required.setter
    @abstractmethod
    def required(self, value: bool):
        pass

    @property
    @abstractmethod
    def field(self) -> Optional[Field]:
        pass

    @property
    @abstractmethod
    def type(self) -> Type:
        pass


class AggregateWrapper(Wrapper[T]):
    """Wrapper for types that have fields (i.e. Dataclasses and Choices)."""

    @abstractmethod
    def register_actions(self, parser: argparse.ArgumentParser) -> None:
        pass
