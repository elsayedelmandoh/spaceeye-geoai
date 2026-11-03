import duckdb

from chatbot.app.core.config import get_settings


def get_db_connection() -> duckdb.DuckDBPyConnection:
    """Open the SpaceEye database in read-only mode."""
    settings = get_settings()

    if not settings.database_path.exists():
        raise FileNotFoundError(
            f"SpaceEye database not found: {settings.database_path}"
        )

    return duckdb.connect(
        database=str(settings.database_path),
        read_only=True,
    )
