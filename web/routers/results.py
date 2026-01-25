"""Results query API router."""
import os
import re
import zipfile
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from web.config import OUTPUT_DIR, UPLOAD_DIR
from web.models.schemas import ResultsResponse, SampleImage, DetectionResult, TaskStatus
from web.services.progress_tracker import progress_tracker

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/{session_id}")
async def get_results(session_id: str, task_id: Optional[str] = None):
    """Get detection results for a session."""
    output_dir = OUTPUT_DIR / session_id

    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    # Get task status if task_id provided
    status = TaskStatus.COMPLETED
    if task_id:
        task = await progress_tracker.get_task(task_id)
        if task:
            status = task.status

    # Collect results
    results = []
    detected_count = 0

    # Look for result files
    result_files = list(output_dir.glob("*.json"))

    # Also check for processed images
    processed_images = list(output_dir.glob("*_result.*"))

    # Build results from available data
    upload_dir = UPLOAD_DIR / session_id
    if upload_dir.exists():
        for img_file in upload_dir.iterdir():
            if img_file.is_file():
                # Check if there's a corresponding result
                result_path = output_dir / f"{img_file.stem}_result{img_file.suffix}"
                detected = result_path.exists()
                if detected:
                    detected_count += 1

                results.append(DetectionResult(
                    filename=img_file.name,
                    detected=detected,
                    output_path=str(result_path) if detected else None
                ))

    # Look for report file
    report_path = None
    for report_file in output_dir.glob("*.md"):
        report_path = str(report_file)
        break

    # Calculate statistics
    total_images = len(results)
    statistics = {
        "total_images": total_images,
        "detected_count": detected_count,
        "detection_rate": round(detected_count / total_images * 100, 1) if total_images > 0 else 0
    }

    return {
        "session_id": session_id,
        "task_id": task_id,
        "status": status,
        "total_images": total_images,
        "processed_images": total_images,
        "detected_count": detected_count,
        "results": results,
        "report_path": report_path,
        "statistics": statistics
    }


@router.get("/{session_id}/report")
async def download_report(session_id: str):
    """Download the detection report (markdown only, for preview)."""
    output_dir = OUTPUT_DIR / session_id

    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    # Find report file
    report_files = list(output_dir.glob("*.md"))
    if not report_files:
        raise HTTPException(status_code=404, detail="Report not found")

    report_path = report_files[0]
    return FileResponse(
        path=str(report_path),
        filename=report_path.name,
        media_type="text/markdown"
    )


@router.get("/{session_id}/report/download")
async def download_report_zip(session_id: str):
    """Download the detection report as ZIP with images."""
    output_dir = OUTPUT_DIR / session_id
    upload_dir = UPLOAD_DIR / session_id

    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    # Find report file
    report_files = list(output_dir.glob("*.md"))
    if not report_files:
        raise HTTPException(status_code=404, detail="Report not found")

    report_path = report_files[0]

    # Read report content
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()

    # Find all image references in markdown
    # Patterns: ![alt](path) or <img src="path">
    image_pattern = r'!\[.*?\]\((.*?)\)|<img[^>]+src=["\']([^"\']+)["\']'
    matches = re.findall(image_pattern, report_content)

    # Collect all referenced images
    referenced_images = set()
    for match in matches:
        img_path = match[0] or match[1]
        if img_path:
            referenced_images.add(img_path)

    # Create temporary ZIP file
    temp_dir = tempfile.mkdtemp()
    zip_filename = f"report_{session_id}.zip"
    zip_path = Path(temp_dir) / zip_filename

    # Modified report content with relative paths
    modified_report = report_content

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add images folder
        images_added = set()

        for img_ref in referenced_images:
            img_path = Path(img_ref)

            # Try to find the image in output_dir or upload_dir
            actual_path = None
            if img_path.is_absolute() and img_path.exists():
                actual_path = img_path
            elif (output_dir / img_path.name).exists():
                actual_path = output_dir / img_path.name
            elif (upload_dir / img_path.name).exists():
                actual_path = upload_dir / img_path.name
            elif img_path.exists():
                actual_path = img_path

            if actual_path and actual_path.exists():
                # Add to zip in images folder
                zip_img_path = f"images/{actual_path.name}"
                if actual_path.name not in images_added:
                    zipf.write(actual_path, zip_img_path)
                    images_added.add(actual_path.name)

                # Update reference in report
                modified_report = modified_report.replace(img_ref, zip_img_path)

        # Also add all processed images from output_dir
        for img_file in output_dir.glob("*"):
            if img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp']:
                if img_file.name not in images_added:
                    zipf.write(img_file, f"images/{img_file.name}")
                    images_added.add(img_file.name)

        # Add modified report
        zipf.writestr("report.md", modified_report)

    return FileResponse(
        path=str(zip_path),
        filename=zip_filename,
        media_type="application/zip"
    )


@router.get("/{session_id}/samples")
async def get_sample_images(session_id: str, limit: int = 10):
    """Get sample images for display (original and processed pairs)."""
    output_dir = OUTPUT_DIR / session_id
    upload_dir = UPLOAD_DIR / session_id

    if not output_dir.exists() or not upload_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    samples = []
    count = 0

    for img_file in upload_dir.iterdir():
        if count >= limit:
            break
        if not img_file.is_file():
            continue

        # Look for processed version
        result_path = output_dir / f"{img_file.stem}_result{img_file.suffix}"

        if result_path.exists():
            samples.append(SampleImage(
                original=f"/api/results/{session_id}/image/original/{img_file.name}",
                processed=f"/api/results/{session_id}/image/processed/{img_file.stem}_result{img_file.suffix}",
                filename=img_file.name,
                detected=True
            ))
            count += 1
        else:
            # Include some non-detected samples too
            samples.append(SampleImage(
                original=f"/api/results/{session_id}/image/original/{img_file.name}",
                processed=f"/api/results/{session_id}/image/original/{img_file.name}",
                filename=img_file.name,
                detected=False
            ))
            count += 1

    return {"session_id": session_id, "samples": samples}


@router.get("/{session_id}/image/original/{filename}")
async def get_original_image(session_id: str, filename: str):
    """Get original uploaded image."""
    image_path = UPLOAD_DIR / session_id / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(str(image_path))


@router.get("/{session_id}/image/processed/{filename}")
async def get_processed_image(session_id: str, filename: str):
    """Get processed result image."""
    image_path = OUTPUT_DIR / session_id / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(str(image_path))
