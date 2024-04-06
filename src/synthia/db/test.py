import asyncio
import csv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from huggingface_hub import HfApi, HfFolder  # type: ignore
from uvicorn import run
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, validator
from typing import Any

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

hf_api = HfApi()
data_list: list[dict[str, str]] = []
BATCH_SIZE = 20  # Number of successful requests before uploading

data_list_lock = asyncio.Lock()


class InputData(BaseModel):
    field: str = Field(..., max_length=1000)
    subject: str = Field(..., max_length=1000)
    target: str = Field(..., max_length=1000)
    detail: str = Field(..., max_length=1000)
    abstraction: str = Field(..., max_length=1000)
    explanation: str = Field(..., max_length=1000)
    score: str = Field(..., max_length=1000)
    signature: str = Field(..., max_length=1000)
    timestamp: str = Field(..., max_length=1000)

    @validator("*")
    def check_field_length(cls, value: Any):
        if len(value) > 1000:
            raise ValueError(
                "Field length exceeds the maximum allowed length of 1000 characters"
            )
        return value


def validate_data(data: InputData) -> bool:
    # Validation -> handled by Pydantic
    return True


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"An error occurred: {str(exc)}"},
    )


async def upload_to_hf(data_list: list[dict[str, str]]) -> None:
    token = HfFolder.get_token()
    if token is None:
        raise HTTPException(
            status_code=500, detail="Hugging Face authentication failed"
        )

    dataset_repo = "agicommies/test"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"src/synthia/db/data/vali_run_{timestamp}.csv"
    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "field",
                "subject",
                "target",
                "detail",
                "abstraction",
                "explanation",
                "score",
            ],
        )
        writer.writeheader()
        writer.writerows(data_list)

    hf_api.upload_file(
        path_or_fileobj=filename,
        path_in_repo=filename,
        repo_id=dataset_repo,
        repo_type="dataset",
        token=token,
    )


@app.post("/upload/")
@limiter.limit("15/hour")  # type: ignore
@limiter.limit("1/minute")  # type: ignore
async def upload_to_hugging_face(data: InputData, request: Request):
    print("received")
    global data_list
    try:
        async with data_list_lock:
            data_list.append(
                {
                    "field": data.field,
                    "subject": data.subject,
                    "target": data.target,
                    "detail": data.detail,
                    "abstraction": data.abstraction,
                    "explanation": data.explanation,
                    "score": data.score,
                }
            )
            if len(data_list) == BATCH_SIZE:
                await upload_to_hf(data_list)
                data_list = []

        return {"message": "Data received successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process data: {str(e)}")


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)
