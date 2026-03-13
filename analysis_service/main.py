from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from analysis_service.schemas import AnalyzeRequest, AnalyzeResponse
from analysis_service import services


@asynccontextmanager
async def lifespan(app: FastAPI):
    services.load_models()
    yield

app = FastAPI(
    title="Review Analysis Service",
    description="Sentiment classification and aspect extraction for reviews.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=422, detail="Text must not be empty.")

    try:
        result = services.analyze(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return AnalyzeResponse(**result)
