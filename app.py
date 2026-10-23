"""propose: application entrypoint -- run this to execute the full project lifecycle.
input: .env, configs/default.yaml, trained model from artifacts/training/models/.
output: project runs, user receives results and visualizations."""

from src.config.config import settings


def main() -> int:
    """run the application entrypoint."""
    print(f"project: {settings.PROJECT_NAME}")
    print(f"environment: {settings.ENV}")
    return 0


if __name__ == "__main__":
    main()
