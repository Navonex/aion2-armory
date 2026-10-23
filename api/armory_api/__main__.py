"""Start: Webserver auf Port 8000 (Tabellen und Datenbankordner legt create_app beim Start an)."""
import uvicorn

from . import logs


def main() -> None:
    logs.setup()
    uvicorn.run("armory_api.main:create_app", factory=True, host="0.0.0.0", port=8000,
                proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
