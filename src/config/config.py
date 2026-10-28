"""
propose: load typed settings from .env, provide absolute paths.
input: .env (env vars).
output: Settings singleton with resolved absolute paths.
"""

from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """holds strongly-typed configuration loaded from .env."""
    BASE_DIR: Path = Path(__file__).resolve().parents[2]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "spaceeye-geoai"
    ENV: str = "development"

    # Raw relative targets from config
    _DATA_REL: Path = Path("data")
    _ARTIFACTS_REL: Path = Path("artifacts")
    _LOGS_REL: Path = Path("logs")
    _FIGURES_REL: Path = Path("evals/figures")


    # Exposed strongly-typed absolute paths
    @computed_field
    @property
    def DATA_DIR(self) -> Path:
        return self.BASE_DIR / self._DATA_REL

    @computed_field
    @property
    def ARTIFACTS_DIR(self) -> Path:
        return self.BASE_DIR / self._ARTIFACTS_REL

    @computed_field
    @property
    def LOGS_DIR(self) -> Path:
        return self.BASE_DIR / self._LOGS_REL

    @computed_field
    @property
    def FIGURES_DIR(self) -> Path:
        return self.BASE_DIR / self._FIGURES_REL

    def create_required_directories(self) -> None:
        """bootstraps essential template data structures."""
        for dir_path in [self.DATA_DIR, self.ARTIFACTS_DIR, self.LOGS_DIR, self.FIGURES_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Instantiate and immediately bootstrap directory tree safely
settings = Settings()
settings.create_required_directories()
