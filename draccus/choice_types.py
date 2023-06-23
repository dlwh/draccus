"""
A Choice Type aka "Sum Type" is a type that can be one of several types. Typically this is through subtyping,
but could be a tagged union or something else.

Typically you'll write a config like this:

```yaml
model:
    type: gpt
    pdrop: 0.1
    layers: 3
```

with a class hierarchy that looks like this:

```python
class ModelConfig(ChoiceRegistry):
    pass

@ModelConfig.register_subclass("gpt")
class GPTConfig(ModelConfig):
    pdrop: float
    layers: int
```

In Draccus, we allow two different kinds of choice types:
* "Closed" choice types, where the set of possible types is fixed before argument parsing/configuration.
* "Open" choice types, where the set of possible types is not fixed.

For config parsing, this distinction doesn't matter that much, but for help generation, it matters quite a bit.

For now, Draccus choice types are implemented as classes that conform to a protocol. The protocol defines
a "get_class_choice(name)" method that returns the class corresponding to the given name, along with a few
other methods.

We may add support for Unions.

All registered types must be *dataclasses*
"""

import functools
from typing import Any, Callable, ClassVar, Dict, Optional, Protocol, Type, TypeVar, overload, runtime_checkable


T = TypeVar("T")


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

    @classmethod
    def get_choice_name(cls, subcls: Type) -> str:
        """
        Returns the name of the given subclass of this choice type.
        """
        ...


class ChoiceRegistry(ChoiceType):
    _choice_registry: ClassVar[Dict[str, Type]] = {}

    @classmethod
    def get_choice_class(cls, name: str) -> Any:
        return cls._choice_registry[name]

    @classmethod
    def get_known_choices(cls) -> Dict[str, Any]:
        return cls._choice_registry

    @classmethod
    def get_choice_name(cls, subcls: Type) -> str:
        for name, choice_type in cls._choice_registry.items():
            if choice_type == subcls:
                return name
        raise ValueError(f"Cannot find choice name for {subcls}")

    @classmethod
    def is_open_choice(cls) -> bool:
        return False

    @overload
    @classmethod
    def register_choice_type(cls, name: str, choice_type: Type) -> Type[T]:
        ...

    @overload
    @classmethod
    def register_choice_type(cls, name: str) -> Callable[[Type[T]], Type[T]]:
        ...

    @classmethod
    def register_choice_type(cls, name: str, choice_type: Optional[Type[T]] = None):
        if choice_type is None:
            return functools.partial(cls.register_choice_type, name)
        if name in cls._choice_registry:
            other_choice_type = cls._choice_registry[name]
            if other_choice_type != choice_type:
                raise ValueError(
                    f"Cannot register {choice_type} as {name} because {other_choice_type} is already registered as"
                    f" {name}"
                )

        cls._choice_registry[name] = choice_type
        return choice_type


# TODO: add plugin registry
