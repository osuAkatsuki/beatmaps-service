import urllib.parse


def create_dsn(
    driver: str | None,
    username: str,
    password: str,
    host: str,
    port: int | None,
    database: str,
) -> str:
    dsn = f"mysql://"
    if driver:
        dsn += f"{driver}:"
    dsn += f"{username}:{urllib.parse.quote_plus(password)}@{host}"
    if port:
        dsn += f":{port}"
    dsn += f"/{database}"
    return dsn
