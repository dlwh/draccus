import argparse
import dataclasses
import inspect
from dataclasses import Field
from functools import cached_property
from typing import Dict, Optional, Type

from ..choice_types import CHOICE_TYPE_KEY, ChoiceType
from ..parsers.decoding import has_custom_decoder
from ..utils import canonicalize_union, is_union
from . import FieldWrapper, docstring
from .wrapper import AggregateWrapper, Wrapper


class ChoiceWrapper(AggregateWrapper[Type[ChoiceType]]):
    def __init__(
        self,
        choice_type: Type[ChoiceType],
        name: Optional[str] = None,
        # default: Optional[Union[Dataclass, Dict]] = None,
        parent: Optional[Wrapper] = None,
        _field: Optional[dataclasses.Field] = None,
        preferred_help: str = docstring.HelpOrder.inline,
    ):
        self.choice_type = choice_type
        self._name = name
        # TODO: need to use the default
        # self.default = default
        self._parent = parent
        self._field = _field

        # preferred parse for docstring / help text in < inline | above | below >
        self.preferred_help = preferred_help

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
            help_text = docstring.get_preferred_help_text(doc, preferred_help=self.preferred_help)
            if help_text is not None:
                return help_text
        class_doc = self.choice_type.__doc__ or ""
        if class_doc.startswith(f"{self.choice_type.__name__}("):
            return ""  # The base dataclass doc looks confusing, remove it
        return class_doc

    def register_actions(self, parser: argparse.ArgumentParser) -> None:
        group = parser.add_argument_group(title=self.title, description=self.description)
        children = self._children

        # Register the type argument. If closed, it's a choice between the known types, otherwise a string description
        dest = self.dest
        if dest is None:
            arg_name = CHOICE_TYPE_KEY
        else:
            arg_name = f"{dest}.{CHOICE_TYPE_KEY}"

        group.add_argument(
            f"--{arg_name}",
            choices=list(children.keys()),
            help=f"Which type of {self.title} to use",
            required=self.required,
        )

        for child in self._children.values():
            from .dataclass_wrapper import DataclassWrapper

            assert isinstance(child, DataclassWrapper)
            child.register_actions(parser)

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


class UnionWrapper(AggregateWrapper[type]):
    def __init__(
        self,
        union: type,
        name: Optional[str] = None,
        parent: Optional[Wrapper] = None,
        _field: Optional[dataclasses.Field] = None,
        preferred_help: str = docstring.HelpOrder.inline,
    ):
        self.union = canonicalize_union(union)
        self._name = name
        self._parent = parent
        self._field = _field

        # preferred parse for docstring / help text in < inline | above | below >
        self.preferred_help = preferred_help

        self._required: bool = False

        # if None is in the union, then it's optional
        self._required = type(None) not in self.union.__args__

        self._explicit: bool = False

    @property
    def name(self) -> str:
        return self._name or self.union.__name__

    @property  # type: ignore
    def required(self) -> bool:  # type: ignore
        return self._required

    @property
    def field(self) -> Optional[Field]:
        return self._field

    @property
    def type(self) -> Type:
        return self.union

    @property
    def title(self) -> str:
        try:
            title = self.union.__qualname__
        except AttributeError:
            try:
                title = self.union.__name__
            except AttributeError:
                title = str(self.union)
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
            help_text = docstring.get_preferred_help_text(doc, preferred_help=self.preferred_help)
            if help_text is not None:
                return help_text
        class_doc = self.union.__doc__ or ""
        return class_doc

    def register_actions(self, parser: argparse.ArgumentParser) -> None:
        # In Pyrallis/Draccus, Unions are implicitly resolved with no tag, unlike Choices
        group = parser.add_argument_group(title=self.title, description=self.description)
        children = self._children

        has_field_wrapper = False

        for child in children.values():
            from .dataclass_wrapper import DataclassWrapper

            if isinstance(child, DataclassWrapper):
                child.register_actions(parser)
            elif isinstance(child, FieldWrapper):
                has_field_wrapper = True
            elif child is None:
                pass
            elif isinstance(child, ChoiceWrapper):
                child.register_actions(parser)
            else:
                raise ValueError(f"Unexpected child type: {child}")

        if has_field_wrapper:
            if self._field is None:
                help_text: Optional[str] = None
            elif self.parent is not None and self._field is not None:
                doc = docstring.get_attribute_docstring(self.parent.type, self._field.name)
                help_text = docstring.get_preferred_help_text(doc, preferred_help=self.preferred_help)
            else:
                help_text = None

            group.add_argument(
                f"--{self.dest}",
                required=False,
                help=help_text,
            )

    @cached_property
    def _children(self) -> Dict[str, Optional[Wrapper]]:
        from .dataclass_wrapper import DataclassWrapper
        from .field_wrapper import FieldWrapper

        def _wrap_child(child: Type) -> Optional[Wrapper]:
            if has_custom_decoder(child):
                assert self._field is not None
                field = FieldWrapper(parent=self.parent, field=self._field, preferred_help=self.preferred_help)
                field.required = False
                return field
            elif dataclasses.is_dataclass(child):
                return DataclassWrapper(
                    child, name=self.name, parent=self.parent, _field=self._field, preferred_help=self.preferred_help
                )
            elif inspect.isclass(child) and issubclass(child, ChoiceType):
                return ChoiceWrapper(child, parent=self.parent, _field=self._field, preferred_help=self.preferred_help)
            elif is_union(child):
                return UnionWrapper(child, parent=self.parent, _field=self._field, preferred_help=self.preferred_help)
            elif child is None or child is type(None):
                return None
            else:
                raise ValueError(f"Unexpected child type: {child}")

        return {child.__name__: _wrap_child(child) for child in self.union.__args__}
