from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.scheduler import inventory_scheduler
from app.models.restaurant import Restaurant
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()


class FileSyncSchedule(BaseModel):
    restaurant_id: int
    file_path: str
    schedule_time: str  # Format: "HH:MM" (e.g., "09:30")
    schedule_type: str = "daily"  # "daily" or "hourly"


class SheetsSyncSchedule(BaseModel):
    restaurant_id: int
    spreadsheet_id: str
    range_name: str = "A:Z"
    credentials_path: str
    schedule_time: str  # Format: "HH:MM"
    schedule_type: str = "daily"  # "daily" or "hourly"


class ScheduleResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None


@router.post("/schedule/file", response_model=ScheduleResponse)
def schedule_file_sync(schedule: FileSyncSchedule, db: Session = Depends(get_db)):
    """Schedule automatic file synchronization"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == schedule.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Validate schedule time format
    try:
        time_parts = schedule.schedule_time.split(":")
        if len(time_parts) != 2 or not all(part.isdigit() for part in time_parts):
            raise ValueError("Invalid time format")
        
        hour, minute = int(time_parts[0]), int(time_parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Time out of range")
            
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid schedule_time format. Use HH:MM (e.g., '09:30')"
        )
    
    # Validate schedule type
    if schedule.schedule_type not in ["daily", "hourly"]:
        raise HTTPException(
            status_code=400,
            detail="schedule_type must be 'daily' or 'hourly'"
        )
    
    # Add to scheduler
    result = inventory_scheduler.add_file_sync_schedule(
        schedule.restaurant_id,
        schedule.file_path,
        schedule.schedule_time,
        schedule.schedule_type
    )
    
    return ScheduleResponse(**result)


@router.post("/schedule/sheets", response_model=ScheduleResponse)
def schedule_sheets_sync(schedule: SheetsSyncSchedule, db: Session = Depends(get_db)):
    """Schedule automatic Google Sheets synchronization"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == schedule.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Validate schedule time format
    try:
        time_parts = schedule.schedule_time.split(":")
        if len(time_parts) != 2 or not all(part.isdigit() for part in time_parts):
            raise ValueError("Invalid time format")
        
        hour, minute = int(time_parts[0]), int(time_parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Time out of range")
            
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid schedule_time format. Use HH:MM (e.g., '09:30')"
        )
    
    # Validate schedule type
    if schedule.schedule_type not in ["daily", "hourly"]:
        raise HTTPException(
            status_code=400,
            detail="schedule_type must be 'daily' or 'hourly'"
        )
    
    # Add to scheduler
    result = inventory_scheduler.add_sheets_sync_schedule(
        schedule.restaurant_id,
        schedule.spreadsheet_id,
        schedule.range_name,
        schedule.credentials_path,
        schedule.schedule_time,
        schedule.schedule_type
    )
    
    return ScheduleResponse(**result)


@router.delete("/schedule/{restaurant_id}", response_model=ScheduleResponse)
def remove_schedule(
    restaurant_id: int, 
    sync_type: str = "all",
    db: Session = Depends(get_db)
):
    """Remove scheduled synchronization for a restaurant"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Validate sync_type
    if sync_type not in ["all", "file", "sheets"]:
        raise HTTPException(
            status_code=400,
            detail="sync_type must be 'all', 'file', or 'sheets'"
        )
    
    result = inventory_scheduler.remove_schedule(restaurant_id, sync_type)
    return ScheduleResponse(**result)


@router.get("/schedule/{restaurant_id}")
def get_restaurant_schedules(restaurant_id: int, db: Session = Depends(get_db)):
    """Get scheduled syncs for a specific restaurant"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    result = inventory_scheduler.get_schedules(restaurant_id)
    return result


@router.get("/schedule")
def get_all_schedules():
    """Get all scheduled syncs"""
    result = inventory_scheduler.get_schedules()
    return result


@router.post("/schedule/{restaurant_id}/sync-now", response_model=ScheduleResponse)
def manual_sync_now(
    restaurant_id: int, 
    sync_type: str = "all",
    db: Session = Depends(get_db)
):
    """Manually trigger synchronization for a restaurant"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Validate sync_type
    if sync_type not in ["all", "file", "sheets"]:
        raise HTTPException(
            status_code=400,
            detail="sync_type must be 'all', 'file', or 'sheets'"
        )
    
    result = inventory_scheduler.manual_sync_now(restaurant_id, sync_type)
    return ScheduleResponse(**result)


@router.get("/schedule/status")
def get_scheduler_status():
    """Get scheduler status and statistics"""
    return {
        "scheduler_running": inventory_scheduler.running,
        "total_schedules": len(inventory_scheduler.sync_configs),
        "schedules_by_type": {
            "file": len([k for k in inventory_scheduler.sync_configs.keys() if "file" in k]),
            "sheets": len([k for k in inventory_scheduler.sync_configs.keys() if "sheets" in k])
        },
        "example_schedule_times": [
            "09:00",  # 9 AM
            "12:00",  # Noon
            "18:00",  # 6 PM
            "23:30"   # 11:30 PM
        ],
        "supported_schedule_types": ["daily", "hourly"]
    }