import logging

import uvicorn  # type: ignore
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.api.api import api_router
from app.core.settings.settings import API_VERSION
from app.core.settings.settings import BACKEND_CORS_ORIGINS
from app.core.settings.settings import PROJECT_NAME


def get_application() -> FastAPI:
    application = FastAPI(
        title=PROJECT_NAME, openapi_url=f"{API_VERSION}/openapi.json"
    )

    init_middlewares(application)

    application.include_router(api_router)
    return application


def init_middlewares(application: FastAPI) -> None:
    origins = []
    if BACKEND_CORS_ORIGINS:
        origins_raw = BACKEND_CORS_ORIGINS.split(",")
        for origin in origins_raw:
            origins.append(origin.strip())
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


app = get_application()


@app.exception_handler(Exception)
async def validation_exception_handler(request, err):
    detail = err.args[0]
    if isinstance(detail, list) or isinstance(detail, tuple):
        detail = str(detail[0])
    if isinstance(detail, str):
        detail.replace('"', "'").replace("\n", " ")
    error = f"Failed to execute {request.method} on {request.url}: {detail}"
    logging.error(error)
    return JSONResponse(status_code=500, content={"error": error})


if __name__ == "__main__":

    uvicorn.run(app=app, host="127.0.0.1", port=8000, log_level="info")
