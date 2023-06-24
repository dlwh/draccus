import argparse
import dataclasses
from dataclasses import _MISSING_TYPE
from logging import getLogger
from typing import Dict, List, Optional, Type, Union, cast

from draccus.utils import Dataclass, DataclassType

from .. import utils
from ..choice_types import ChoiceType

# from ..parsers.decoding import get_decoding_fn, has_custom_decoder
from . import docstring
from .choice_wrapper import ChoiceWrapper
from .field_wrapper import FieldWrapper
from .wrapper import AggregateWrapper, Wrapper


logger = getLogger(__name__)


class DataclassWrapper(AggregateWrapper[Type[Dataclass]]):
    def __init__(
        self,
        dataclass: Type[Dataclass],
        name: Optional[str] = None,
        # TODO(dlwh): they aren't using the defaults?
        default: Optional[Union[Dataclass, Dict]] = None,
        parent: Optional["Wrapper"] = None,
        _field: Optional[dataclasses.Field] = None,
    ):
        self.dataclass = dataclass
        self._name = name
        self.default = default

        self._required: bool = False
        self._explicit: bool = False
        self._children: List[Wrapper] = []
        self._parent = parent
        # the field of the parent, which contains this child dataclass.
        self._field = _field

        # the default values
        self._defaults: List[Dataclass] = []

        if default:
            # TODO(dlwh): I don't like this
            self.defaults = [default]  # type: ignore

        self.optional: bool = False

        for field in dataclasses.fields(self.dataclass):  # type: ignore
            child = _wrap_field(self, field)
            if child is not None:
                self._children.append(child)

    def register_actions(self, parser: argparse.ArgumentParser) -> None:
        group = parser.add_argument_group(title=self.title, description=self.description)

        for child in self._children:
            if isinstance(child, AggregateWrapper):
                child.register_actions(parser)
            elif isinstance(child, FieldWrapper):
                child.add_action(group)

    @property
    def name(self) -> str:
        # TODO(dlwh): I don't like this
        return self._name  # type: ignore

    @property
    def parent(self) -> Optional["Wrapper"]:
        return self._parent

    # @property
    # def defaults(self) -> List[Dataclass]:
    #     raise NotImplementedError("This should be overridden")
    #     if self._defaults:
    #         return self._defaults
    #     if self._field is None:
    #         return []
    #     assert self.parent is not None
    #     if self.parent.defaults:
    #         self._defaults = []
    #         for default in self.parent.defaults:
    #             if default is None:
    #                 default = None
    #             else:
    #                 default = getattr(default, self.name)
    #             self._defaults.append(default)
    #     else:
    #         try:
    #             default_field_value = utils.default_value(self._field)
    #         except TypeError as e:
    #             # utils.default_value tries to construct the field to get default value and might fail
    #             # if the field has some required arguments
    #             logger.debug(f"Could not get default value for field '{self._field.name}'\n\tUnderlying Error: {e}")
    #             default_field_value = dataclasses.MISSING
    #         if isinstance(default_field_value, _MISSING_TYPE):
    #             self._defaults = []
    #         else:
    #             self._defaults = [default_field_value]
    #     return self._defaults
    #
    # @defaults.setter
    # def defaults(self, value: List[Dataclass]):
    #     self._defaults = value

    @property
    def title(self) -> str:
        title = self.dataclass.__qualname__
        if self.dest is not None:  # Show name if exists
            title += f" ['{self.dest}']"
        return title

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
        class_doc = self.dataclass.__doc__ or ""
        if class_doc.startswith(f"{self.dataclass.__name__}("):
            return ""  # The base dataclass doc looks confusing, remove it
        return class_doc

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: bool):
        self._required = value
        for child_wrapper in self._children:
            child_wrapper.required = value

    @property
    def field(self) -> Optional[dataclasses.Field]:
        return self._field

    @property
    def type(self) -> Type[Dataclass]:
        return self.dataclass


def _wrap_field(parent: Optional[Wrapper], field: dataclasses.Field) -> Optional[Wrapper]:
    if not field.init:
        return None

    # elif has_custom_decoder(field.type):
    #     field_wrapper = field_wrapper_class(field, parent=self, prefix=self.prefix)
    #     logger.debug(f"wrapped field at {field_wrapper.dest} has a default value of {field_wrapper.default}")
    #     return field_wrapper
    elif utils.is_choice_type(field.type):
        return ChoiceWrapper(cast(Type[ChoiceType], field.type), field.name, parent=parent, _field=field)

    elif utils.is_tuple_or_list_of_dataclasses(field.type):
        raise NotImplementedError(
            f"Field {field.name} is of type {field.type}, which isn't supported yet. (container of a dataclass type)"
        )

    elif dataclasses.is_dataclass(field.type):
        # handle a nested dataclass attribute
        dataclass, name = (cast(DataclassType, field.type)), field.name
        child_wrapper = DataclassWrapper(dataclass, name, parent=parent, _field=field)
        return child_wrapper

    elif utils.contains_dataclass_type_arg(field.type):
        # TODO(dlwh): I don't like this
        dataclass = utils.get_dataclass_type_arg(field.type)  # type: ignore
        name = field.name
        child_wrapper = DataclassWrapper(dataclass, name, default=None, parent=parent, _field=field)
        child_wrapper.required = False
        child_wrapper.optional = True
        return child_wrapper

    else:
        # a normal attribute
        field_wrapper = FieldWrapper(field, parent=parent)
        logger.debug(f"wrapped field at {field_wrapper.dest} has a default value of {field_wrapper.default}")
        # self._children.append(field_wrapper)
        return field_wrapper
