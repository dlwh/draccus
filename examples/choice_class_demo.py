from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import draccus

# logging.basicConfig(level=logging.DEBUG)


@dataclass
class ComputeConfig:
    """Config for training resources"""

    # The number of workers for training
    workers: int = field(default=8)
    # The number of workers for training
    eval_workers: Optional[int] = field(default=None)

    def __post_init__(self):
        # A builtin method of dataclasses, used for post-processing our configuration.
        self.eval_workers = self.eval_workers or self.workers


@dataclass
class OptimConfig(draccus.ChoiceRegistry):
    learning_rate: float = 0.001


@OptimConfig.register_subclass("adam")
class AdamConfig(OptimConfig):
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1e-8


@OptimConfig.register_subclass("sgd")
class SGDConfig(OptimConfig):
    momentum: float = 0.9
    nesterov: bool = False


@dataclass
class LogConfig:
    """Config for logging arguments"""

    # The experiment name
    exp_name: str = field(default="default_exp")
    # The experiment root folder path
    exp_root: Path = field(default=Path("/share/experiments"))

    @property
    def exp_dir(self) -> Path:
        # Properties are great for arguments that can be derived from existing ones
        return self.exp_root / self.exp_name


# TrainConfig will be our main configuration class.
# Notice that default_factory is the standard way to initialize a class argument in dataclasses


@dataclass
class TrainConfig:
    log: LogConfig = LogConfig()
    compute: ComputeConfig = ComputeConfig()
    optim: OptimConfig = AdamConfig()


@draccus.wrap()
def main(cfg: TrainConfig):
    print(f"Training {cfg.log.exp_name}...")
    print(f"\tUsing optimizer {cfg.optim}")
    print(f"\tUsing {cfg.compute.workers} workers and {cfg.compute.eval_workers} evaluation workers")
    print(f"\tSaving to {cfg.log.exp_dir}")
    print(draccus.dump(cfg))


if __name__ == "__main__":
    main()
