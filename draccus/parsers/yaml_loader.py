import yaml  # type: ignore
import yamlinclude


class FullLoaderWithInclusion(yaml.FullLoader):
    pass


class SafeLoaderWithInclusion(yaml.SafeLoader):
    pass


yamlinclude.YamlIncludeConstructor.add_to_loader_class(FullLoaderWithInclusion, relative=True)
yamlinclude.YamlIncludeConstructor.add_to_loader_class(SafeLoaderWithInclusion, relative=True)
