<!--
<p align="center"><img src="https://raw.githubusercontent.com/eladrich/pyrallis/master/docs/pyrallis_logo.png" alt="logo" width="70%" /></p>

<p align="center">
<a href="https://badge.fury.io/py/draccus"><img src="https://badge.fury.io/py/pyrallis.svg" alt="PyPI version" height="18"></a>
    <a href="https://github.com/eladrich/pyrallis/actions/workflows/pytest.yml"><img src="https://github.com/eladrich/pyrallis/actions/workflows/pytest.yml/badge.svg" alt="PyTest" height="18"></a>
    <a href="https://pepy.tech/project/pyrallis"><img src="https://pepy.tech/badge/pyrallis" alt="Downloads" height="18"></a>
    <a href="#contributors-"><img src="https://img.shields.io/badge/all_contributors-2-orange.svg" alt="All Contributors" height="18"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" height="18"></a>
</p>

 -->

# Draccus - Slightly Less Simple Configuration with Dataclasses

> Draccus: "A large herbivorous reptilian creature, known for their ability to breathe fire."

Draccus is a fork of the excellent [Pyrallis](https://github.com/eladrich/pyrallis) library, but with
a few changes to make it more suitable for more complex use cases. The main changes are:

* Support for subtyping configs (that is, choosing between different configs based on a parameter)
* Support for including config files in config files
* Better support for containers of configs (e.g. a list of configs)

I swear I didn't want to fork it, but the Pyrallis devs (understandably) didn't want to merge some of these.


<p align="center"><img src="https://github.com/eladrich/pyrallis/raw/master/docs/argparse2pyrallis.gif" alt="GIF" width="100%" /></p>

## Why `draccus`?

We support everything in Pyrallis (see their examples), but also support subtyping and including config files within
config files. We try to maintain the original repository's simple, clean approach.

With `draccus` your configuration is linked directly to your pre-defined `dataclass`, allowing you to easily create
different configuration structures, including nested ones, using an object-oriented design. The parsed arguments are
used to initialize your `dataclass`, inheriting the corresponding type hints and code completion features.

## My First Draccus Example

(This example is the same as in Pyrallis. Draccus differs mainly in advanced features like subtyping.)

Here's a simple example of how to use `draccus` to parse arguments into a `dataclass`:

```python
from dataclasses import dataclass
import draccus


@dataclass
class TrainConfig:
    """Training Config for Machine Learning"""
    workers: int = 8               # The number of workers for training
    exp_name: str = 'default_exp'  # The experiment name


@draccus.wrap()
def main(cfg: TrainConfig):
    print(f"Training {cfg.exp_name} with {cfg.workers} workers...")
```

The arguments can then be specified using command-line arguments, a `yaml` configuration file, or both.

```console
$ python train_model.py --config_path=some_config.yaml --exp_name=my_first_exp
Training my_first_exp with 42 workers...
```
Assuming the following configuration file
```yaml
exp_name: my_yaml_exp
workers: 42

model:
  type: bert
  num_layers: 24
  num_heads: 24
  hidden_size: 1024
  dropout: 0.2
```

## Inclusion of Config Files

(This is a difference from Pyrallis.)

We support including config files from other config files via [pyyaml-include](https://github.com/tanbro/pyyaml-include).
This is useful for splitting up your config into multiple files, or for including a base config file in your config.

It works like this:

```yaml
# model_config.yaml
type: bert
num_layers: 24
num_heads: 24
hidden_size: 1024
dropout: 0.2
```

```yaml
# train_config.yaml
exp_name: my_yaml_exp
workers: 42
model: !include model_config.yaml
```

### Inclusion of config files using Command Line Arguments using `include ` keyword

You can use `include` keyword in the command line arguments to include a config file in a nested way.

It works like this:
```yaml
# model_config.yaml
type: bert_cli
num_layers: 48
num_heads: 48
```

```yaml
# train_config.yaml
exp_name: my_yaml_exp
workers: 42
model: 
  type: bert
  num_layers: 24
  num_heads: 24
```

Using `python train_model.py --config_path=train_config.yaml --model="include model_config.yaml"` 
will give `cfg.model.type = 'bert_cli'`

### Including Configs at Top Level

PyYAML, upon which draccus is based, supports a common YAML extension `<<` for merging keys from multiple maps.
We can combine this with `!include` to include a config file:

```yaml
# base_config.yaml
type: bert
lr: 0.001

# train_config.yaml
<<: !include base_config.yaml
exp_name: my_yaml_exp
```

(I don't love this syntax, but it's consistent with PyYAML.)

## More Flexible Configuration with Choice Types

(This is a difference from Pyrallis.)

Choice Types, aka "Sum Types" or "Tagged Unions", are a powerful way to define a choice of types that can be selected at
runtime. For instance, you might want to choose what kind of model to train, or what kind of optimizer to use.

Draccus provides a `ChoiceRegistry` class that lets you define a choice of types that can be selected at runtime. You
can then use the `register_subclass` decorator to register a subclass of your choice type. The `type` field of the
choice type is used to select the subclass.

Here's a modified version of the example above, where we use a `ChoiceRegistry` to define a choice of model types:

```python
from dataclasses import dataclass
import draccus


# Choice Registry lets you define a choice of implementations that can be selected at runtime
@dataclass
class ModelConfig(draccus.ChoiceRegistry):
    pass


@ModelConfig.register_subclass('gpt')
@dataclass
class GPTConfig(ModelConfig):
    """GPT Model Config"""
    num_layers: int = 12
    num_heads: int = 12
    hidden_size: int = 768


@ModelConfig.register_subclass('bert')
@dataclass
class BERTConfig(ModelConfig):
    """BERT Model Config"""
    num_layers: int = 12
    num_heads: int = 12
    hidden_size: int = 768
    dropout: float = 0.1


@dataclass
class TrainConfig:
    """Training Config for Machine Learning"""
    workers: int = 8                  # The number of workers for training
    exp_name: str = 'default_exp'     # The experiment name

    model: ModelConfig = GPTConfig()  # The model configuration


@draccus.wrap()
def main(cfg: TrainConfig):
    print(f"Training {cfg.exp_name} with {cfg.workers} workers...")
```

The arguments can then be specified using command-line arguments, a `yaml` configuration file, or both.

```console
$ python train_model.py --config_path=some_config.yaml --exp_name=my_first_exp
Training my_first_exp with 42 workers...
```
Assuming the following configuration file
```yaml
exp_name: my_yaml_exp
workers: 42

model:
  type: bert
  num_layers: 24
  num_heads: 24
  hidden_size: 1024
  dropout: 0.2
```

# Everything below here is from Pyrallis. I'll update it eventually.

(It all still applies, substituting `draccus` for `pyrallis`.)

### Key Features
Building on that design `pyrallis` offers some really enjoyable features including

* Builtin IDE support for autocompletion and linting thanks to the structured config. 🤓
* Joint reading from command-line and a config file, with support for specifying a default config file. 😍
* Support for builtin dataclass features, such as `__post_init__` and `@property` 😁
* Support for nesting and inheritance of dataclasses, nested arguments are automatically created! 😲
* A magical `@pyrallis.wrap()` decorator for wrapping your main class 🪄
* Easy extension to new types using `pyrallis.encode.register` and `pyrallis.decode.register` 👽
* Easy loading and saving of existing configurations using `pyrallis.dump` and `pyrallis.load` 💾
* Magical `--help` creation from dataclasses, taking into account the comments as well! 😎
* Support for multiple configuration formats (`yaml`, `json`,`toml`) using `pyrallis.set_config_type` ⚙️


## Getting to Know The `pyrallis` API in 5 Simple Steps 🐲

The best way to understand the full `pyrallis` API is through examples, let's get started!

###  🐲 1/5 `pyrallis.parse` for `dataclass` Parsing 🐲

Creation of an argparse configuration is really simple, just use `pyrallis.parse` on your predefined dataclass.

```python
from dataclasses import dataclass, field
import draccus


@dataclass
class TrainConfig:
    """ Training config for Machine Learning """
    # The number of workers for training
    workers: int = field(default=8)
    # The experiment name
    exp_name: str = field(default='default_exp')


def main():
    cfg = draccus.parse(config_class=TrainConfig)
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')


if __name__ == '__main__':
    main()
```
> Not familiar with `dataclasses`? you should probably check the [Python Tutorial](https://docs.python.org/3/library/dataclasses.html) and come back here.

The config can then be parsed directly from command-line
```console
$ python train_model.py --exp_name=my_first_model
Training my_first_model with 8 workers...
```
Oh, and `pyrallis` also generates an `--help` string automatically using the comments in your dataclass 🪄

```console
$ python train_model.py --help
usage: train_model.py [-h] [--config_path str] [--workers int] [--exp_name str]

optional arguments:
  -h, --help      show this help message and exit
  --config_path str    Path for a config file to parse with pyrallis (default:
                  None)

TrainConfig:
   Training config for Machine Learning

  --workers int   The number of workers for training (default: 8)
  --exp_name str  The experiment name (default: default_exp)
```



### 🐲 2/5 The `pyrallis.wrap` Decorator 🐲
Don't like the `pyrallis.parse` syntax?
```python
def main():
    cfg = pyrallis.parse(config_class=TrainConfig)
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
```
One can equivalently use the `pyrallis.wrap` syntax 😎
```python
@pyrallis.wrap()
def main(cfg: TrainConfig):
    # The decorator automagically uses the type hint to parsers arguments into TrainConfig
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
```
We will use this syntax for the rest of our tutorial.


### 🐲 3/5 Better Configs Using Inherent `dataclass` Features 🐲
When using a dataclass we can add additional functionality using existing `dataclass` features, such as the `post_init` mechanism or `@properties` :grin:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import draccus


@dataclass
class TrainConfig:
    """ Training config for Machine Learning """
    # The number of workers for training
    workers: int = field(default=8)
    # The number of workers for evaluation
    eval_workers: Optional[int] = field(default=None)
    # The experiment name
    exp_name: str = field(default='default_exp')
    # The experiment root folder path
    exp_root: Path = field(default=Path('/share/experiments'))

    def __post_init__(self):
        # A builtin method of dataclasses, used for post-processing our configuration.
        self.eval_workers = self.eval_workers or self.workers

    @property
    def exp_dir(self) -> Path:
        # Properties are great for arguments that can be derived from existing ones
        return self.exp_root / self.exp_name


@draccus.wrap()
def main(cfg: TrainConfig):
    print(f'Training {cfg.exp_name}...')
    print(f'\tUsing {cfg.workers} workers and {cfg.eval_workers} evaluation workers')
    print(f'\tSaving to {cfg.exp_dir}')
```

```console
$ python -m train_model.py --exp_name=my_second_exp --workers=42
Training my_second_exp...
    Using 42 workers and 42 evaluation workers
    Saving to /share/experiments/my_second_exp
```
> Notice that in all examples we use the explicit `dataclass.field` syntax. This isn't a requirement of `pyrallis` but rather a style choice. As some of your arguments will probably require `dataclass.field` (mutable types for example) we find it cleaner to always use the same notation.


### 🐲 4/5 Building Hierarchical Configurations 🐲
Sometimes configs get too complex for a flat hierarchy 😕, luckily `pyrallis` supports nested dataclasses 💥

```python

@dataclass
class ComputeConfig:
    """ Config for training resources """
    # The number of workers for training
    workers: int = field(default=8)
    # The number of workers for evaluation
    eval_workers: Optional[int] = field(default=None)

    def __post_init__(self):
        # A builtin method of dataclasses, used for post-processing our configuration.
        self.eval_workers = self.eval_workers or self.workers


@dataclass
class LogConfig:
    """ Config for logging arguments """
    # The experiment name
    exp_name: str = field(default='default_exp')
    # The experiment root folder path
    exp_root: Path = field(default=Path('/share/experiments'))

    @property
    def exp_dir(self) -> Path:
        # Properties are great for arguments that can be derived from existing ones
        return self.exp_root / self.exp_name

# TrainConfig will be our main configuration class.
# Notice that default_factory is the standard way to initialize a class argument in dataclasses

@dataclass
class TrainConfig:
    log: LogConfig = field(default_factory=LogConfig)
    compute: ComputeConfig = field(default_factory=ComputeConfig)

@pyrallis.wrap()
def main(cfg: TrainConfig):
    print(f'Training {cfg.log.exp_name}...')
    print(f'\tUsing {cfg.compute.workers} workers and {cfg.compute.eval_workers} evaluation workers')
    print(f'\tSaving to {cfg.log.exp_dir}')
```
The argument parse will be updated accordingly
```console
$ python train_model.py --log.exp_name=my_third_exp --compute.eval_workers=2
Training my_third_exp...
    Using 8 workers and 2 evaluation workers
    Saving to /share/experiments/my_third_exp
```

### 🐲 5/5 Easy Serialization with `pyrallis.dump` 🐲
As your config get longer you will probably want to start working with configuration files. Pyrallis supports encoding a dataclass configuration into a `yaml` file 💾

The command `pyrallis.dump(cfg, open('run_config.yaml','w'))` will result in the following `yaml` file
```yaml
compute:
  eval_workers: 2
  workers: 8
log:
  exp_name: my_third_exp
  exp_root: /share/experiments
```
> `pyrallis.dump` extends `yaml.dump` and uses the same syntax.

Configuration files can also be loaded back into a dataclass, and can even be used together with the command-line arguments.
```python
cfg = pyrallis.parse(config_class=TrainConfig,
                              config_path='/share/configs/config.yaml')

# or the decorator synrax
@pyrallis.wrap(config_path='/share/configs/config.yaml')

# or with the CONFIG argument
python my_script.py --log.exp_name=readme_exp --config_path=/share/configs/config.yaml

# Or if you just want to load from a .yaml without cmd parsing
cfg = pyrallis.load(TrainConfig, '/share/configs/config.yaml')
```
> Command-line arguments have a higher priority and will override the configuration file


Finally, one can easily extend the serialization to support new types 🔥
```python
# For decoding from cmd/yaml
pyrallis.decode.register(np.ndarray,np.asarray)

# For encoding to yaml
pyrallis.encode.register(np.ndarray, lambda x: x.tolist())

# Or with the wrapper version instead
@pyrallis.encode.register
def encode_array(arr : np.ndarray) -> str:
    return arr.tolist()
```

#### 🐲 That's it you are now a `pyrallis` expert! 🐲



## Why Another Parsing Library?
<img src="https://imgs.xkcd.com/comics/standards_2x.png" alt="XKCD 927 - Standards" width="70%" />

> XKCD 927 - Standards

The builtin `argparse` has many great features but is somewhat outdated :older_man: with one its greatest weakness being the lack of typing. This has led to the development of many great libraries tackling different weaknesses of `argparse` (shout out for all the great projects out there! You rock! :metal:).

In our case, we were looking for a library that would  support the vanilla `dataclass` without requiring dedicated classes, and would have a loading interface from both command-line and files. The closest candidates were `hydra` and `simple-parsing`, but they weren't exactly what we were looking for. Below are the pros and cons from our perspective:
#### [Hydra](https://github.com/facebookresearch/hydra)
A framework for elegantly configuring complex applications from Facebook Research.
* Supports complex configuration from multiple files and allows for overriding them from command-line.
* Does not support non-standard types, does not play nicely with `datclass.__post_init__`and requires a `ConfigStore` registration.
#### [SimpleParsing](https://github.com/lebrice/SimpleParsing)
A framework for simple, elegant and typed Argument Parsing by Fabrice Normandin
* Strong integration with `argparse`, support for nested configurations together with standard arguments.
* No support for joint loading from command-line and files, dataclasses are still wrapped by a Namespace, requires dedicated classes for serialization.

We decided to create a simple hybrid of the two approaches, building from `SimpleParsing` with some `hydra` features in mind. The result, `pyrallis`, is a simple library that that is relatively low on features, but hopefully excels at what it does.

If `pyrallis` isn't what you're looking for we strongly advise you to give `hydra` and `simpleParsing` a try (where other interesting option include `click`, `ext_argpase`, `jsonargparse`, `datargs` and `tap`). If you do :heart: `pyrallis` then welcome aboard! We're gonna have a great journey together! 🐲

## Tips and Design Choices

### Beware of Mutable Types (or use pyrallis.field)
Dataclasses are great (really!) but using mutable fields can sometimes be confusing. For example, say we try to code the following dataclass
```python
@dataclass
class OptimConfig:
    worker_inds: List[int] = []
    # Or the more explicit version
    worker_inds: List[int] = field(default=[])
```
As `[]` is mutable we would actually initialize every instance of this dataclass with the same list instance, and thus is not allowed. Instead `dataclasses` would direct you the default_factory function, which calls a factory function for generating the field in every new instance of your dataclass.

```python
worker_inds: List[int] = field(default_factory=list)
```

Now, this works great for empty collections, but what would be the alternative for
```python
worker_inds: List[int] = field(default=[1,2,3])
```
Well, you would have to create a dedicated factory function that regenerates the object, for example
```python
worker_inds: List[int] = field(default_factory=lambda : [1,2,3])
```
Kind of annoying and could be confusing for a new guest reading your code :confused: Now, while this isn't really related to parsing/configuration we decided it could be nice to offer a sugar-syntax for such cases as part of `pyrallis`

```python
from draccus import field

worker_inds: List[int] = field(default=[1, 2, 3], is_mutable=True)
```
The `pyrallis.field` behaves like the regular `dataclasses.field` with an additional `is_mutable` flag. When toggled, the `default_factory` is created automatically, offering the same functionally with a more reader-friendly syntax.



### Uniform Parsing Syntax
For parsing files we opted for `yaml` as our format of choice, following `hydra`, due to its concise format.
Now, let us assume we have the following `.yaml` file which `yaml` successfully handles:
```yaml
compute:
  worker_inds: [0,2,3]
```
Intuitively we would also want users to be able to use the same syntax
```cmd
python my_app.py --compute.worker_inds=[0,2,3]
```

However, the more standard syntax for an argparse application would be
```cmd
python my_app.py --compute.worker_inds 0 2 3
```

We decided to use the same syntax as in the `yaml` files to avoid confusion when loading from multiple sources.

Not a `yaml` fun? `pyrallis` also supports `json` and `toml` formats using `pyrallis.set_config_type('json')` or `with pyrallis.config_type('json'):`



# TODOs:
- [x] Fix error with default Dict and List
>         Underlying error: No decoding function for type ~KT, consider using pyrallis.decode.register
- [x] Refine the `--help` command
> For example the `options` argument is confusing there
- [ ] Add a test to `omit_defaults`
## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://about.me/ido.weiss"><img src="https://avatars.githubusercontent.com/u/10072365?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Ido Weiss</b></sub></a><br /><a href="#design-idow09" title="Design">🎨</a> <a href="#ideas-idow09" title="Ideas, Planning, & Feedback">🤔</a></td>
    <td align="center"><a href="https://github.com/yairf11"><img src="https://avatars.githubusercontent.com/u/13931256?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Yair Feldman</b></sub></a><br /><a href="#design-yairf11" title="Design">🎨</a> <a href="#ideas-yairf11" title="Ideas, Planning, & Feedback">🤔</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
