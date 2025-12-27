"""FastAPI application main file."""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
import io

from app.config import settings
from app.s3_operations import list_objects, upload_file, download_file, delete_file
from app.db_operations import check_db_connection, create_item, get_items, get_item

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)


# Pydantic models
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: str


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    import os
    import socket
    
    # Get container/host info if available
    hostname = socket.gethostname()
    
    # Try to get image info from environment (if set during deployment)
    image_tag = os.getenv("IMAGE_TAG", "unknown")
    container_name = os.getenv("HOSTNAME", hostname)
    
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "hostname": hostname,
        "container_name": container_name,
        "image_tag": image_tag,
        "aws_region": os.getenv("AWS_REGION", "unknown"),
        "s3_bucket": os.getenv("S3_BUCKET_NAME", "not configured"),
    }


# S3 endpoints
@app.get("/s3/list")
async def s3_list(prefix: Optional[str] = None):
    """List objects in S3 bucket."""
    try:
        objects = list_objects(prefix=prefix)
        return {
            "bucket": settings.s3_bucket_name,
            "count": len(objects),
            "objects": objects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/s3/upload")
async def s3_upload(key: str, file: UploadFile = File(...)):
    """Upload file to S3."""
    try:
        file_content = await file.read()
        result = upload_file(file_content, key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/s3/download/{key:path}")
async def s3_download(key: str):
    """Download file from S3."""
    try:
        file_content = download_file(key)
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={key.split('/')[-1]}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/s3/delete/{key:path}")
async def s3_delete(key: str):
    """Delete file from S3."""
    try:
        result = delete_file(key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Database endpoints
@app.get("/db/status")
async def db_status():
    """Check database connection status."""
    return check_db_connection()


@app.post("/db/create", response_model=ItemResponse)
async def db_create(item: ItemCreate):
    """Create a new item in the database."""
    try:
        result = create_item(item.name, item.description)
        return ItemResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/db/read", response_model=List[ItemResponse])
async def db_read(limit: int = 100, offset: int = 0):
    """Read items from database."""
    try:
        items = get_items(limit=limit, offset=offset)
        return [ItemResponse(**item) for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/db/read/{item_id}", response_model=ItemResponse)
async def db_read_item(item_id: int):
    """Read a single item by ID."""
    try:
        item = get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return ItemResponse(**item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

