"""Dashboard placeholder: prints settings only. Use src.pipeline.team_run for the implemented workflow."""

from src.config.config import settings


def main() -> int:
    """run the application entrypoint."""
    print(f"project: {settings.PROJECT_NAME}")
    print(f"environment: {settings.ENV}")
    return 0


if __name__ == "__main__":
    main()
