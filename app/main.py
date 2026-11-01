"""FastAPI application cho Auto Bypass."""
from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from app.bypasser import LinkBypasser
from app.security import URLSecurityError, validate_input_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Auto Bypass", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://khanhos.github.io", "http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
semaphore = asyncio.Semaphore(1)
bypasser = LinkBypasser()

class BypassRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: Annotated[HttpUrl, Field(max_length=2048)]

@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/api/health")
async def health():
    return {"status": "online", "browser_configured": True}

@app.post("/api/bypass")
async def bypass_endpoint(payload: BypassRequest):
    url = str(payload.url)
    try:
        url = validate_input_url(url)
    except URLSecurityError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_OR_UNSUPPORTED_URL", "message": str(exc)}) from exc
    if semaphore.locked():
        raise HTTPException(status_code=429, detail={"code": "BUSY", "message": "Máy chủ đang xử lý một link khác. Vui lòng thử lại sau."})
    async with semaphore:
        logger.info("Nhận yêu cầu xử lý Link4m")
        return await bypasser.bypass(url)
