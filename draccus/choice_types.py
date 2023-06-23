"""
A Choice Type aka "Sum Type" is a type that can be one of several types. Typically this is through subtyping,
but could be a tagged union or something else.

In Draccus, we allow two different kinds of choice types:
* "Closed" choice types, where the set of possible types is fixed before argument parsing/configuration.
* "Open" choice types, where the set of possible types is not fixed.

For config parsing, this distinction doesn't matter that much, but for help generation, it matters quite a bit.

For now, Draccus choice types are implemented as classes that conform to a protocol. The protocol defines
a "get_class_choice(name)" method that returns the class corresponding to the given name, along with a few
other methods.

We may add support for Unions.
"""

from typing import Any, ClassVar, Dict, Protocol, runtime_checkable


CHOICE_TYPE_KEY = "type"
"""name of key to use in configuration to specify the type of a choice type"""


@runtime_checkable
class ChoiceType(Protocol):
    @classmethod
    def get_choice_class(cls, name: str) -> Any:
        ...

    @classmethod
    def get_known_choices(cls) -> Dict[str, Any]:
        ...

    @classmethod
    def is_open_choice(cls) -> bool:
        """
        Returns True if this is an open choice type, False otherwise.
        """
        ...


class ChoiceRegistry(ChoiceType):
    _choice_registry: ClassVar[Dict[str, Any]] = {}

    @classmethod
    def get_choice_class(cls, name: str) -> Any:
        return cls._choice_registry[name]

    @classmethod
    def get_known_choices(cls) -> Dict[str, Any]:
        return cls._choice_registry

    @classmethod
    def is_open_choice(cls) -> bool:
        return False

    @classmethod
    def register_choice_type(cls, name: str, choice_type: Any) -> None:
        if name in cls._choice_registry:
            other_choice_type = cls._choice_registry[name]
            if other_choice_type != choice_type:
                raise ValueError(
                    f"Cannot register {choice_type} as {name} because {other_choice_type} is already registered as"
                    f" {name}"
                )

        cls._choice_registry[name] = choice_type


# def choice_registry(cls: Type[T]) -> Type[T]:
#     """Convenience decorator for registering a class as an open choice type. Adds the necessary class variables
#     and methods to the class for it to be a valid choice type. Also adds a "register_choice_type" method
#     to the class for registering subclasses.
#     """
#
#     cls._choice_registry: ClassVar[Dict[str, Any]] = {}
#     cls.get_choice_class = ChoiceRegistry.get_choice_class
#     cls.get_known_choices = ChoiceRegistry.get_known_choices
#     cls.is_open_choice = ChoiceRegistry.is_open_choice
#     cls.register_choice_type = ChoiceRegistry.register_choice_type
#
#     return cls

# TODO: add plugin registry
