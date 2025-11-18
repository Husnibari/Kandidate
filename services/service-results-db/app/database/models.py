from typing import List, Dict, Annotated
from pydantic import BaseModel, Field, StringConstraints
from services.shared_models import AnalysisResult


class Job(BaseModel):
    job_id: str = Field(alias="_id")
    correlation_id: str
    jd_text: str
    status: str = "pending"
    expected_files: int = 0
    results: List[AnalysisResult] = []
    errors: List[Dict[str, str]] = []
    created_at: str


class CreateJobRequest(BaseModel):
    job_id: Annotated[str, StringConstraints(min_length=1, max_length=100)] = Field(description="Unique job identifier")
    correlation_id: Annotated[str, StringConstraints(min_length=1, max_length=100)] = Field(description="Correlation ID for tracking")
    jd_text: Annotated[str, StringConstraints(min_length=1, max_length=50000)] = Field(description="Job description text")
    file_count: Annotated[int, Field(gt=0, le=1000)] = Field(description="Number of expected files")


class AddFilesRequest(BaseModel):
    file_count: Annotated[int, Field(gt=0, le=1000)] = Field(description="Number of files to add")


class UpdateStatusRequest(BaseModel):
    status: str = Field(description="New status value")
