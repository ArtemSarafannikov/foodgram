import os

from app.repositories.postgres_orm import PostgresRepo
from app.repositories.sqlite_orm import SQLiteRepo

repo = 0

db_type = os.getenv("DATABASE_URL")
if db_type and db_type.startswith("postgresql"):
    repo = PostgresRepo()
else:
    repo = SQLiteRepo()