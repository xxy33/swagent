"""Pydantic models for request/response schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    """Detection task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class UploadResponse(BaseModel):
    """Response for file upload."""
    session_id: str
    file_count: int
    files: List[str]
    message: str


class ClearResponse(BaseModel):
    """Response for clearing uploaded files."""
    session_id: str
    cleared: bool
    message: str


class DetectionTask(BaseModel):
    """Detection task definition."""
    id: str
    name: str
    name_en: str
    description: str


class DetectionRequest(BaseModel):
    """Request to start detection."""
    session_id: str
    tasks: List[str] = Field(..., min_length=1, description="List of task IDs")
    city_name: str = Field(..., min_length=1, description="City name for report")
    # VL 模型配置
    vl_base_url: str = Field(..., min_length=1, description="VL model base URL")
    vl_api_key: str = Field(..., min_length=1, description="VL model API key")
    vl_model: str = Field(..., min_length=1, description="VL model name")
    # LLM 模型配置
    llm_base_url: str = Field(..., min_length=1, description="LLM base URL")
    llm_api_key: str = Field(..., min_length=1, description="LLM API key")
    llm_model: str = Field(..., min_length=1, description="LLM model name")
    # SAM2 模型配置 (可选)
    sam2_url: Optional[str] = Field(None, description="SAM2 service URL")
    sam2_api_key: Optional[str] = Field(None, description="SAM2 API key")
    sam2_model: Optional[str] = Field(None, description="SAM2 model name")


class DetectionResponse(BaseModel):
    """Response for starting detection."""
    task_id: str
    session_id: str
    status: TaskStatus
    message: str


class ProgressEvent(BaseModel):
    """Progress event for SSE."""
    task_id: str
    current: int
    total: int
    percentage: float
    current_file: Optional[str] = None
    message: str
    status: TaskStatus
    timestamp: datetime = Field(default_factory=datetime.now)


class TaskStatusResponse(BaseModel):
    """Response for task status query."""
    task_id: str
    session_id: str
    status: TaskStatus
    progress: float
    current_file: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class DetectionResult(BaseModel):
    """Detection result for a single image."""
    filename: str
    detected: bool
    confidence: Optional[float] = None
    detections: List[Dict[str, Any]] = []
    output_path: Optional[str] = None


class ResultsResponse(BaseModel):
    """Response for detection results."""
    session_id: str
    task_id: str
    status: TaskStatus
    total_images: int
    processed_images: int
    detected_count: int
    results: List[DetectionResult]
    report_path: Optional[str] = None
    statistics: Dict[str, Any] = {}


class SampleImage(BaseModel):
    """Sample image for display."""
    original: str
    processed: str
    filename: str
    detected: bool
