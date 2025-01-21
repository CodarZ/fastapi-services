from pathlib import Path

from fastapi import FastAPI

from backend.core.config import settings

app = FastAPI()


if __name__ == "__main__":
    try:
        import uvicorn

        uvicorn.run(
            app=f"{Path(__file__).stem}:app",
            host=settings.UVICORN_HOST,
            port=settings.UVICORN_PORT,
            reload=settings.UVICORN_RELOAD,
        )
        print("✨ 服务启动了")
    except Exception as e:
        print(f"❌ FastAPI start filed: {e}")
