import urllib.parse


def create_dsn(
    driver: str | None,
    username: str,
    password: str,
    host: str,
    port: int | None,
    database: str,
) -> str:
    driver_str = f"+{driver}" if driver else ""
    passwd_str = urllib.parse.quote_plus(password) if password else ""
    return f"mysql{driver_str}://{username}:{passwd_str}@{host}:{port}/{database}"
