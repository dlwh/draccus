import dataclasses
from argparse import _ActionsContainer, _ArgumentGroup
from dataclasses import Field
from functools import cached_property
from typing import Dict, Optional, Type

from ..choice_types import CHOICE_TYPE_KEY, ChoiceType
from ..parsers.decoding import has_custom_decoder
from . import docstring
from .wrapper import Wrapper


class ChoiceWrapper(Wrapper):
    def __init__(
        self,
        choice_type: Type[ChoiceType],
        name: Optional[str] = None,
        # default: Optional[Union[Dataclass, Dict]] = None,
        parent: Optional[Wrapper] = None,
        _field: Optional[dataclasses.Field] = None,
    ):
        self.choice_type = choice_type
        self._name = name
        # TODO: need to use the default
        # self.default = default
        self._parent = parent
        self._field = _field

        self._required: bool = False
        self._explicit: bool = False

    @property
    def title(self) -> str:
        title = self.choice_type.__qualname__
        if self.dest is not None:  # Show name if exists
            title += f" ['{self.dest}']"
        return title

    @property
    def parent(self) -> Optional["Wrapper"]:
        return self._parent

    @property
    def description(self) -> str:
        if self.parent and self._field:
            doc = docstring.get_attribute_docstring(self.parent.type, self._field.name)
            if doc is not None:
                if doc.docstring_below:
                    return doc.docstring_below
                elif doc.comment_above:
                    return doc.comment_above
                elif doc.comment_inline:
                    return doc.comment_inline
        class_doc = self.choice_type.__doc__ or ""
        if class_doc.startswith(f"{self.choice_type.__name__}("):
            return ""  # The base dataclass doc looks confusing, remove it
        return class_doc

    def register_actions(self, parser: _ActionsContainer) -> None:
        # group = parser.add_argument_group(title=self.title, description=self.description)
        group = _SuppressingArgumentGroup(parser, title=self.title, description=self.description)

        children = self._children

        # register the type argument. If closed, it's a choice between the known types, otherwise just a string with a fancy desc
        dest = self.dest
        if dest is None:
            arg_name = CHOICE_TYPE_KEY
        else:
            arg_name = f"{dest}.{CHOICE_TYPE_KEY}"

        if self.choice_type.is_open_choice():
            group.add_argument(
                f"--{arg_name}",
                help=f"Which type of {self.title} to use. Known types: {', '.join(children.keys())}",
                required=self.required,
            )
        else:
            group.add_argument(
                f"--{arg_name}",
                choices=list(children.keys()),
                help=f"Which type of {self.title} to use",
                required=self.required,
            )

        for child in self._children.values():
            # TODO: need to suppress conflicts among the choices
            child.register_actions(group)

    @cached_property
    def _children(self) -> Dict[str, Wrapper]:
        from .dataclass_wrapper import DataclassWrapper

        def _wrap_child(child: Type) -> Wrapper:
            if not dataclasses.is_dataclass(child):
                raise ValueError(f"Expected a dataclass, got {child}")
            if has_custom_decoder(child):
                raise ValueError(f"Cannot use class with custom decoder as choice type: {child}")

            # because we "substitute" the choice type for the child, we need to make sure that
            # the child's parent is the same as the choice type's parent
            return DataclassWrapper(child, parent=self.parent, _field=self._field, name=self.name)

        return {name: _wrap_child(child) for name, child in self.choice_type.get_known_choices().items()}

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: bool):
        self._required = value
        for child_wrapper in self._children.values():
            child_wrapper.required = value

    @property
    def name(self) -> str:
        return self._name or self.choice_type.__name__

    @property
    def field(self) -> Optional[Field]:
        return self._field

    @property
    def type(self) -> Type:
        return self.choice_type


class _SuppressingArgumentGroup(_ArgumentGroup):
    def __init__(self, container, *args, **kwargs):
        kwargs = {**kwargs, "conflict_handler": "ignore"}
        super().__init__(container, *args, **kwargs)

    def add_argument(self, *args, **kwargs):
        return super().add_argument(*args, **kwargs)

    def add_argument_group(self, *args, **kwargs):
        group = _SuppressingArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group

    def add_mutually_exclusive_group(self, *args, **kwargs):
        raise NotImplementedError("Mutually exclusive groups are not supported for choice types")

    def _handle_conflict_ignore(self, action, conflicting_actions):
        pass