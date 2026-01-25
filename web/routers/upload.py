"""File upload API router."""
import os
import uuid
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from web.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE
from web.models.schemas import UploadResponse, ClearResponse

router = APIRouter(prefix="/api/upload", tags=["upload"])


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


@router.post("/images", response_model=UploadResponse)
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload multiple images and return a session ID."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Generate session ID
    session_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    uploaded_files = []
    errors = []

    for file in files:
        # Skip non-image files
        if not file.filename:
            continue

        # Get the actual filename (handle folder uploads)
        filename = Path(file.filename).name

        if not is_allowed_file(filename):
            errors.append(f"Skipped {filename}: unsupported format")
            continue

        # Check file size
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            errors.append(f"Skipped {filename}: file too large")
            continue

        # Save file
        file_path = session_dir / filename

        # Handle duplicate filenames
        counter = 1
        original_stem = file_path.stem
        while file_path.exists():
            file_path = session_dir / f"{original_stem}_{counter}{file_path.suffix}"
            counter += 1

        with open(file_path, "wb") as f:
            f.write(content)

        uploaded_files.append(file_path.name)

    if not uploaded_files:
        # Clean up empty session directory
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(
            status_code=400,
            detail="No valid image files uploaded. " + "; ".join(errors) if errors else "No valid image files."
        )

    message = f"Successfully uploaded {len(uploaded_files)} files"
    if errors:
        message += f". Warnings: {'; '.join(errors)}"

    return UploadResponse(
        session_id=session_id,
        file_count=len(uploaded_files),
        files=uploaded_files,
        message=message
    )


@router.get("/files/{session_id}")
async def list_files(session_id: str):
    """List uploaded files for a session."""
    session_dir = UPLOAD_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    files = [f.name for f in session_dir.iterdir() if f.is_file()]
    return {"session_id": session_id, "files": files, "count": len(files)}


@router.delete("/clear/{session_id}", response_model=ClearResponse)
async def clear_files(session_id: str):
    """Clear all uploaded files for a session."""
    session_dir = UPLOAD_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        shutil.rmtree(session_dir)
        return ClearResponse(
            session_id=session_id,
            cleared=True,
            message="All files cleared successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear files: {str(e)}")
