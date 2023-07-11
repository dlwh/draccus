import yaml  # type: ignore
import yamlinclude
from yaml.constructor import ConstructorError


class ConstructorWithGoodInclusion(yaml.constructor.SafeConstructor):
    # this is a hack to get around the fact that yamlinclude doesn't work with the merge key <<
    def flatten_mapping(self, node):
        merge = []
        index = 0
        while index < len(node.value):
            key_node, value_node = node.value[index]
            if key_node.tag == 'tag:yaml.org,2002:merge':
                del node.value[index]
                # this is the difference from the original method
                if value_node.tag == yamlinclude.YamlIncludeConstructor.DEFAULT_TAG_NAME:
                    value = self.construct_object(value_node)
                    if isinstance(value, dict):
                        merge.extend(value.items())
                    else:
                        raise ConstructorError("while constructing a mapping", node.start_mark,
                                               "expected included node to be mapping for merging, but found %s"
                                               % value_node.id, value_node.start_mark)
                elif isinstance(value_node, yaml.MappingNode):
                    self.flatten_mapping(value_node)
                    merge.extend(value_node.value)
                elif isinstance(value_node, yaml.SequenceNode):
                    submerge = []
                    for subnode in value_node.value:
                        if not isinstance(subnode, yaml.MappingNode):
                            raise ConstructorError("while constructing a mapping",
                                                   node.start_mark,
                                                   "expected a mapping for merging, but found %s"
                                                   % subnode.id, subnode.start_mark)
                        self.flatten_mapping(subnode)
                        submerge.append(subnode.value)
                    submerge.reverse()
                    for value in submerge:
                        merge.extend(value)
                else:
                    raise ConstructorError("while constructing a mapping", node.start_mark,
                                           "expected a mapping or list of mappings for merging, but found %s"
                                           % value_node.id, value_node.start_mark)
            elif key_node.tag == 'tag:yaml.org,2002:value':
                key_node.tag = 'tag:yaml.org,2002:str'
                index += 1
            else:
                index += 1
        if merge:
            node.value = merge + node.value

class FullLoaderWithInclusion(yaml.FullLoader, ConstructorWithGoodInclusion):
    pass


class SafeLoaderWithInclusion(yaml.SafeLoader, ConstructorWithGoodInclusion):
    pass


yamlinclude.YamlIncludeConstructor.add_to_loader_class(FullLoaderWithInclusion, relative=True)
yamlinclude.YamlIncludeConstructor.add_to_loader_class(SafeLoaderWithInclusion, relative=True)

