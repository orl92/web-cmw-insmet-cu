from huey import SqliteHuey

from config import settings

HUEY_DB_PATH = settings.BASE_DIR / 'huey.db'

huey = SqliteHuey(
    'web-cmw',
    filename=str(HUEY_DB_PATH),
)
