"""Abstract Wrapper base-class for the FieldWrapper and DataclassWrapper."""
import abc
from abc import ABC, abstractmethod
from argparse import _ActionsContainer
from dataclasses import Field
from typing import Generic, List, Optional

from draccus.utils import T


class Wrapper(Generic[T], ABC):
    @property
    @abstractmethod
    def wrapped(self) -> T:
        pass

    @property
    def dest(self) -> str:
        """Where the attribute will be stored in the Namespace."""
        if self.parent is None:
            return self.name
        lineage_names: List[str] = [w.name for w in self.lineage()]
        if lineage_names[-1] is None:  # root usually won't have a name
            lineage_names = lineage_names[:-1]
        return ".".join(reversed([self.name] + lineage_names))

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

    @abstractmethod
    def register_actions(self, parser: _ActionsContainer) -> None:
        pass
