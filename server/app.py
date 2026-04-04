from __future__ import annotations
import os
import uvicorn

from server.main import app


def main() -> None:
    """
    Entry point called by the `server` console script defined in
    [project.scripts] of pyproject.toml, and by the OpenEnv runner.
    """
    uvicorn.run(
        "server.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        workers=1,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()