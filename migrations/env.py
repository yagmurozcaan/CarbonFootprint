from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
import sys
import os
from dotenv import load_dotenv

# Alembic config objesi
config = context.config

# Logger ayarları
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Proje dizinini import yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# .env dosyasını oku
load_dotenv()

DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SQLALCHEMY_URL = (
    f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_DATABASE}"
    f"?driver={DB_DRIVER.replace(' ', '+')}"
)

# database.py içindeki Base metadata'yı import et
from models.model import Base
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(
        url=SQLALCHEMY_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(SQLALCHEMY_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
