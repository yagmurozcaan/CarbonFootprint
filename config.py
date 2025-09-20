import pyodbc
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from io import StringIO
from dotenv import dotenv_values


import os
from cryptography.fernet import Fernet

key = os.environ.get("FERNET_KEY")
if not key:
    raise ValueError("FERNET_KEY ortam değişkeni bulunamadı!")

FERNET_KEY = key.encode()
fernet = Fernet(FERNET_KEY)

# Şifreli .env dosyasını aç
with open(".env.enc", "rb") as f:
    encrypted_data = f.read()

decrypted_data = fernet.decrypt(encrypted_data).decode()
env_vars = dotenv_values(stream=StringIO(decrypted_data))

DB_DRIVER = env_vars.get("DB_DRIVER")
DB_SERVER = env_vars.get("DB_SERVER")
DB_DATABASE = env_vars.get("DB_DATABASE")
DB_USER = env_vars.get("DB_USER")
DB_PASSWORD = env_vars.get("DB_PASSWORD")


try:
    conn = pyodbc.connect(
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
    )
    print("config.py : pyodbc ile bağlantı başarılı!")
except pyodbc.Error as e:
    print("config.py : pyodbc bağlantı hatası:", e)
    conn = None

# --- SQLAlchemy bağlantısı ---
SQLALCHEMY_URL = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_DATABASE}?driver={DB_DRIVER.replace(' ', '+')}"
try:
    engine = create_engine(SQLALCHEMY_URL, echo=True)
    SessionLocal = sessionmaker(bind=engine)
    print("config.py: SQLAlchemy engine hazır!")
except Exception as e:
    print("config.py: SQLAlchemy engine hatası:", e)
    engine = None
    SessionLocal = None
