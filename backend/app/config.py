import os
import json
from typing import Optional
from dotenv import load_dotenv


def get_env() -> str:
    return os.getenv("ENV", "development")

def _secret_db_url_from_aws() -> Optional[str]:
    load_dotenv()
    secret_id = (
        os.getenv("DB_SECRET_ARN")
        or os.getenv("DB_SECRET_NAME")
        or os.getenv("DB_SECRET_ID")
    )
    print(f"#### secret_id: {secret_id}")
    if not secret_id:
        return None
    try:
        import boto3
        region = os.getenv("AWS_REGION")
        client = boto3.client("secretsmanager", region_name=region) if region else boto3.client("secretsmanager")
        resp = client.get_secret_value(SecretId=secret_id)
        secret = resp.get("SecretString")
        data = json.loads(secret) if secret else {}
        host = data.get("host")
        port = data.get("port")
        username = data.get("username")
        password = data.get("password")
        database = data.get("dbname") or data.get("database")
        print(f"#### host: {host}, port: {port}, username: {username}, password: {password}, database: {database}")
        if not all([host, port, username, password, database]):
            return None
        url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        return url
    except Exception:
        return None

def get_database_url() -> str:
    secret_url = _secret_db_url_from_aws()
    print(f"#### secret_url: {secret_url}")
    if secret_url:
        return _append_ssl(secret_url)
    env = get_env()
    key_map = {
        "development": "DATABASE_URL_DEV",
        "test": "DATABASE_URL_TEST",
        "production": "DATABASE_URL_PROD",
    }
    url = os.getenv(key_map.get(env, "DATABASE_URL_DEV")) or os.getenv("DATABASE_URL")
    if not url:
        return "sqlite:///./smart_rating.db"
    return _append_ssl(url)

def _append_ssl(url: str) -> str:
    if url.startswith("postgresql") and "sslmode=" not in url:
        sep = '&' if '?' in url else '?'
        return f"{url}{sep}sslmode=require"
    return url
