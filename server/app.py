import os

import uvicorn

from environment.main import app as fastapi_app

app = fastapi_app


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("environment.main:app", host=host, port=port)


if __name__ == "__main__":
    main()


__all__ = ["app", "main"]
