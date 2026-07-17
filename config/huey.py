from pathlib import Path

from huey import SqliteHuey

from config import settings

huey = SqliteHuey(
    'web-cmw',
    filename=str(Path(settings.HUEY_DB_PATH)),
)
