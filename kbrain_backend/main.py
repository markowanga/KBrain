import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from storage import BaseStorage, MemoryStorage, FileStorage

# Storage type configuration (can be set via environment variable)
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file")  # "memory" or "file"
STORAGE_DIR = os.getenv("STORAGE_DIR", "data")

app = FastAPI(title="KBrain API")

# Initialize storage backend
storage: BaseStorage
if STORAGE_TYPE == "memory":
    storage = MemoryStorage()
    print("Using in-memory storage (volatile)")
else:
    storage = FileStorage(storage_dir=STORAGE_DIR)
    print(f"Using file-based storage in '{STORAGE_DIR}' directory (persistent)")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests
class SetItemRequest(BaseModel):
    key: str
    value: Any


class SetManyRequest(BaseModel):
    items: Dict[str, Any]


class DeleteManyRequest(BaseModel):
    keys: List[str]


# Basic endpoints
@app.get("/")
async def root():
    return {"message": "Hello World from KBrain API!"}


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "kbrain-backend",
        "storage_type": STORAGE_TYPE,
        "storage_count": await storage.count()
    }


# Storage API endpoints
@app.get("/api/storage/stats")
async def get_storage_stats():
    """Get storage statistics."""
    return {
        "storage_type": STORAGE_TYPE,
        "total_items": await storage.count(),
        "keys": await storage.list_keys()
    }


@app.get("/api/storage/item/{key}")
async def get_item(key: str):
    """Get a single item by key."""
    value = await storage.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    return {"key": key, "value": value}


@app.post("/api/storage/item")
async def set_item(request: SetItemRequest):
    """Set a single item."""
    success = await storage.set(request.key, request.value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store item")
    return {"key": request.key, "success": True}


@app.delete("/api/storage/item/{key}")
async def delete_item(key: str):
    """Delete a single item by key."""
    success = await storage.delete(key)
    if not success:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    return {"key": key, "deleted": True}


@app.get("/api/storage/exists/{key}")
async def check_exists(key: str):
    """Check if a key exists."""
    exists = await storage.exists(key)
    return {"key": key, "exists": exists}


@app.get("/api/storage/keys")
async def list_keys(prefix: Optional[str] = None):
    """List all keys, optionally filtered by prefix."""
    keys = await storage.list_keys(prefix)
    return {"keys": keys, "count": len(keys)}


@app.get("/api/storage/all")
async def get_all_items():
    """Get all stored items."""
    items = await storage.get_all()
    return {"items": items, "count": len(items)}


@app.post("/api/storage/many")
async def set_many_items(request: SetManyRequest):
    """Set multiple items at once."""
    success = await storage.set_many(request.items)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store items")
    return {"count": len(request.items), "success": True}


@app.delete("/api/storage/many")
async def delete_many_items(request: DeleteManyRequest):
    """Delete multiple items at once."""
    deleted_count = await storage.delete_many(request.keys)
    return {"requested": len(request.keys), "deleted": deleted_count}


@app.delete("/api/storage/clear")
async def clear_storage():
    """Clear all storage."""
    success = await storage.clear()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear storage")
    return {"cleared": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
