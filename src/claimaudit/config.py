"""Experiment paths resolve relative to their configuration file."""
from dataclasses import dataclass
import math
from pathlib import Path
import re
import tomllib

from claimaudit.schemas import require_text


@dataclass(frozen=True)
class EmbeddingConfig:
    model_id: str
    revision: str
    threshold: float
    device: str = "cpu"
    batch_size: int = 32
    cache_dir: Path = Path(".cache/huggingface")
    local_files_only: bool = False

    def __post_init__(self) -> None:
        require_text("model_id", self.model_id)
        if not isinstance(self.revision, str) or not re.fullmatch(r"[0-9a-f]{40}", self.revision):
            raise ValueError("revision must be an immutable 40-character model commit SHA")
        if type(self.threshold) not in (int, float) or not math.isfinite(self.threshold) or not -1 <= self.threshold <= 1:
            raise ValueError("threshold must be finite and in [-1, 1]")
        if self.device not in ("cpu", "cuda", "mps"):
            raise ValueError("device must be cpu, cuda, or mps")
        if type(self.batch_size) is not int or self.batch_size < 1:
            raise ValueError("batch_size must be a positive integer")
        if type(self.local_files_only) is not bool:
            raise ValueError("local_files_only must be a boolean")
        if not isinstance(self.cache_dir, Path):
            raise ValueError("cache_dir must be a pathlib.Path")


@dataclass(frozen=True)
class NLIConfig:
    model_id: str
    revision: str
    threshold: float
    device: str = "cpu"
    batch_size: int = 16
    cache_dir: Path = Path(".cache/huggingface")
    local_files_only: bool = False
    max_length: int = 512

    def __post_init__(self) -> None:
        require_text("model_id", self.model_id)
        if not isinstance(self.revision, str) or not re.fullmatch(r"[0-9a-f]{40}", self.revision):
            raise ValueError("revision must be an immutable 40-character model commit SHA")
        if type(self.threshold) not in (int, float) or not math.isfinite(self.threshold) or not 0 <= self.threshold <= 1:
            raise ValueError("NLI threshold must be finite and in [0, 1]")
        if self.device not in ("cpu", "cuda", "mps"):
            raise ValueError("device must be cpu, cuda, or mps")
        if type(self.batch_size) is not int or self.batch_size < 1:
            raise ValueError("batch_size must be a positive integer")
        if type(self.max_length) is not int or self.max_length < 4:
            raise ValueError("max_length must be an integer >= 4")
        if type(self.local_files_only) is not bool:
            raise ValueError("local_files_only must be a boolean")
        if not isinstance(self.cache_dir, Path):
            raise ValueError("cache_dir must be a pathlib.Path")


@dataclass(frozen=True)
class StructureConfig:
    numeric_checks: bool = True
    comparison_checks: bool = True
    absolute_tolerance: float = 1e-9
    relative_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        if type(self.numeric_checks) is not bool or type(self.comparison_checks) is not bool:
            raise ValueError("Structural check switches must be booleans")
        for name in ("absolute_tolerance", "relative_tolerance"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite nonnegative number")


@dataclass(frozen=True)
class EvaluationConfig:
    manifest: Path
    bootstrap_samples: int = 2000

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, Path):
            raise ValueError("manifest must be a pathlib.Path")
        if type(self.bootstrap_samples) is not int or self.bootstrap_samples < 1:
            raise ValueError("bootstrap_samples must be a positive integer")


@dataclass(frozen=True)
class ExperimentConfig:
    dataset: Path
    seed: int = 42
    embedding: EmbeddingConfig | None = None
    nli: NLIConfig | None = None
    structure: StructureConfig | None = None
    evaluation: EvaluationConfig | None = None

    def __post_init__(self) -> None:
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be an integer in [0, 2**32)")
        if not isinstance(self.dataset, Path):
            raise ValueError("dataset must be a pathlib.Path")

    @classmethod
    def load(cls, path: Path) -> "ExperimentConfig":
        path = path.resolve()
        with path.open("rb") as handle:
            values = tomllib.load(handle)
        unknown = values.keys() - {"dataset", "seed", "embedding", "nli", "structure", "evaluation"}
        if unknown:
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")
        dataset = values.get("dataset")
        require_text("dataset", dataset)
        models = {}
        for name, config_type in (("embedding", EmbeddingConfig), ("nli", NLIConfig)):
            if name not in values:
                continue
            options = values[name]
            if not isinstance(options, dict):
                raise ValueError(f"{name} must be a TOML table")
            options = dict(options)
            cache_dir = options.get("cache_dir", "../.cache/huggingface")
            require_text("cache_dir", cache_dir)
            options["cache_dir"] = (path.parent / cache_dir).resolve()
            models[name] = config_type(**options)
        if "structure" in values:
            if not isinstance(values["structure"], dict):
                raise ValueError("structure must be a TOML table")
            models["structure"] = StructureConfig(**values["structure"])
        if "evaluation" in values:
            if not isinstance(values["evaluation"], dict):
                raise ValueError("evaluation must be a TOML table")
            options = dict(values["evaluation"])
            require_text("manifest", options.get("manifest"))
            options["manifest"] = (path.parent / options["manifest"]).resolve()
            models["evaluation"] = EvaluationConfig(**options)
        return cls((path.parent / dataset).resolve(), values.get("seed", 42), **models)
