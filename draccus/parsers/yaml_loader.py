# Copyright 2025 The Board of Trustees of the Leland Stanford Junior University
# SPDX-License-Identifier: MIT


import os

import yaml  # type: ignore
import yaml.representer  # type: ignore
from yaml import MappingNode
from yaml.constructor import ConstructorError  # type: ignore


def include_constructor(loader, node):
    filename = os.path.normpath(os.path.join(os.path.dirname(loader.stream.name), node.value))
    with open(filename, "r") as f:
        return yaml.load(f, loader.__class__)


class ConstructorWithGoodInclusion(yaml.constructor.SafeConstructor, yaml.representer.SafeRepresenter):
    def __init__(self):
        yaml.constructor.SafeConstructor.__init__(self)
        yaml.representer.SafeRepresenter.__init__(self)

    # this is a hack to get around the fact that inclusion doesn't work with the merge key <<
    def flatten_mapping(self, node):
        merge = []
        index = 0
        while index < len(node.value):
            key_node, value_node = node.value[index]
            if key_node.tag == "tag:yaml.org,2002:merge":
                del node.value[index]
                # this is the difference from the original method
                if value_node.tag == "!include":
                    value = self.construct_object(value_node)
                    value = self.represent_data(value)
                    if isinstance(value, MappingNode):
                        merge.extend(value.value)
                    else:
                        raise ConstructorError(
                            "while constructing a mapping",
                            node.start_mark,
                            "expected included node to be mapping for merging, but found %s" % value_node.id,
                            value_node.start_mark,
                        )
                elif isinstance(value_node, yaml.MappingNode):
                    self.flatten_mapping(value_node)
                    merge.extend(value_node.value)
                elif isinstance(value_node, yaml.SequenceNode):
                    submerge = []
                    for subnode in value_node.value:
                        if not isinstance(subnode, yaml.MappingNode):
                            raise ConstructorError(
                                "while constructing a mapping",
                                node.start_mark,
                                "expected a mapping for merging, but found %s" % subnode.id,
                                subnode.start_mark,
                            )
                        self.flatten_mapping(subnode)
                        submerge.append(subnode.value)
                    submerge.reverse()
                    for value in submerge:
                        merge.extend(value)
                else:
                    raise ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        "expected a mapping or list of mappings for merging, but found %s" % value_node.id,
                        value_node.start_mark,
                    )
            elif key_node.tag == "tag:yaml.org,2002:value":
                key_node.tag = "tag:yaml.org,2002:str"
                index += 1
            else:
                index += 1
        if merge:
            node.value = merge + node.value


class FullLoaderWithInclusion(yaml.FullLoader, ConstructorWithGoodInclusion):
    def __init__(self, *args, **kwargs):
        yaml.FullLoader.__init__(self, *args, **kwargs)
        ConstructorWithGoodInclusion.__init__(self)


class SafeLoaderWithInclusion(yaml.SafeLoader, ConstructorWithGoodInclusion):
    def __init__(self, *args, **kwargs):
        yaml.SafeLoader.__init__(self, *args, **kwargs)
        ConstructorWithGoodInclusion.__init__(self)


FullLoaderWithInclusion.add_constructor("!include", include_constructor)
SafeLoaderWithInclusion.add_constructor("!include", include_constructor)
