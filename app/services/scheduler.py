import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.restaurant import Restaurant
from app.services.inventory_sync import inventory_sync_service
from typing import Dict, Any, Optional
import logging
import json
import os

logger = logging.getLogger(__name__)


class InventoryScheduler:
    """Scheduler for automatic inventory synchronization"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.sync_configs = {}  # Store sync configurations per restaurant
        
    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Inventory scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Inventory scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def add_file_sync_schedule(
        self, 
        restaurant_id: int, 
        file_path: str, 
        schedule_time: str,
        schedule_type: str = "daily"
    ) -> Dict[str, Any]:
        """Add a scheduled file sync for a restaurant"""
        try:
            config_key = f"restaurant_{restaurant_id}_file"
            
            # Store configuration
            self.sync_configs[config_key] = {
                "restaurant_id": restaurant_id,
                "file_path": file_path,
                "schedule_time": schedule_time,
                "schedule_type": schedule_type,
                "last_sync": None,
                "sync_type": "file"
            }
            
            # Schedule the job
            if schedule_type == "daily":
                schedule.every().day.at(schedule_time).do(
                    self._sync_file_job, restaurant_id, file_path
                ).tag(config_key)
            elif schedule_type == "hourly":
                schedule.every().hour.do(
                    self._sync_file_job, restaurant_id, file_path
                ).tag(config_key)
            
            return {
                "success": True,
                "message": f"Scheduled {schedule_type} sync at {schedule_time} for restaurant {restaurant_id}"
            }
            
        except Exception as e:
            logger.error(f"Error adding file sync schedule: {e}")
            return {"success": False, "error": str(e)}
    
    def add_sheets_sync_schedule(
        self,
        restaurant_id: int,
        spreadsheet_id: str,
        range_name: str,
        credentials_path: str,
        schedule_time: str,
        schedule_type: str = "daily"
    ) -> Dict[str, Any]:
        """Add a scheduled Google Sheets sync for a restaurant"""
        try:
            config_key = f"restaurant_{restaurant_id}_sheets"
            
            # Store configuration
            self.sync_configs[config_key] = {
                "restaurant_id": restaurant_id,
                "spreadsheet_id": spreadsheet_id,
                "range_name": range_name,
                "credentials_path": credentials_path,
                "schedule_time": schedule_time,
                "schedule_type": schedule_type,
                "last_sync": None,
                "sync_type": "sheets"
            }
            
            # Schedule the job
            if schedule_type == "daily":
                schedule.every().day.at(schedule_time).do(
                    self._sync_sheets_job, restaurant_id, spreadsheet_id, range_name, credentials_path
                ).tag(config_key)
            elif schedule_type == "hourly":
                schedule.every().hour.do(
                    self._sync_sheets_job, restaurant_id, spreadsheet_id, range_name, credentials_path
                ).tag(config_key)
            
            return {
                "success": True,
                "message": f"Scheduled {schedule_type} Google Sheets sync at {schedule_time} for restaurant {restaurant_id}"
            }
            
        except Exception as e:
            logger.error(f"Error adding sheets sync schedule: {e}")
            return {"success": False, "error": str(e)}
    
    def remove_schedule(self, restaurant_id: int, sync_type: str = "all") -> Dict[str, Any]:
        """Remove scheduled syncs for a restaurant"""
        try:
            removed = 0
            
            if sync_type == "all" or sync_type == "file":
                config_key = f"restaurant_{restaurant_id}_file"
                if config_key in self.sync_configs:
                    schedule.clear(config_key)
                    del self.sync_configs[config_key]
                    removed += 1
            
            if sync_type == "all" or sync_type == "sheets":
                config_key = f"restaurant_{restaurant_id}_sheets"
                if config_key in self.sync_configs:
                    schedule.clear(config_key)
                    del self.sync_configs[config_key]
                    removed += 1
            
            return {
                "success": True,
                "message": f"Removed {removed} scheduled sync(s) for restaurant {restaurant_id}"
            }
            
        except Exception as e:
            logger.error(f"Error removing schedule: {e}")
            return {"success": False, "error": str(e)}
    
    def get_schedules(self, restaurant_id: Optional[int] = None) -> Dict[str, Any]:
        """Get all scheduled syncs"""
        if restaurant_id:
            # Filter by restaurant
            filtered_configs = {
                k: v for k, v in self.sync_configs.items() 
                if v["restaurant_id"] == restaurant_id
            }
            return {"schedules": filtered_configs}
        else:
            return {"schedules": self.sync_configs}
    
    def _sync_file_job(self, restaurant_id: int, file_path: str):
        """Execute scheduled file sync job"""
        try:
            logger.info(f"Starting scheduled file sync for restaurant {restaurant_id}")
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return
            
            db = next(get_db())
            try:
                result = inventory_sync_service.sync_from_file(file_path, restaurant_id, db)
                
                # Update last sync time
                config_key = f"restaurant_{restaurant_id}_file"
                if config_key in self.sync_configs:
                    self.sync_configs[config_key]["last_sync"] = datetime.now().isoformat()
                
                if result.get("success"):
                    logger.info(f"Scheduled file sync completed for restaurant {restaurant_id}: {result.get('stats')}")
                else:
                    logger.error(f"Scheduled file sync failed for restaurant {restaurant_id}: {result.get('error')}")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in scheduled file sync for restaurant {restaurant_id}: {e}")
    
    def _sync_sheets_job(self, restaurant_id: int, spreadsheet_id: str, range_name: str, credentials_path: str):
        """Execute scheduled Google Sheets sync job"""
        try:
            logger.info(f"Starting scheduled Google Sheets sync for restaurant {restaurant_id}")
            
            if not os.path.exists(credentials_path):
                logger.error(f"Credentials file not found: {credentials_path}")
                return
            
            db = next(get_db())
            try:
                result = inventory_sync_service.sync_from_google_sheets(
                    spreadsheet_id, range_name, restaurant_id, db, credentials_path
                )
                
                # Update last sync time
                config_key = f"restaurant_{restaurant_id}_sheets"
                if config_key in self.sync_configs:
                    self.sync_configs[config_key]["last_sync"] = datetime.now().isoformat()
                
                if result.get("success"):
                    logger.info(f"Scheduled Google Sheets sync completed for restaurant {restaurant_id}: {result.get('stats')}")
                else:
                    logger.error(f"Scheduled Google Sheets sync failed for restaurant {restaurant_id}: {result.get('error')}")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in scheduled Google Sheets sync for restaurant {restaurant_id}: {e}")
    
    def manual_sync_now(self, restaurant_id: int, sync_type: str = "all") -> Dict[str, Any]:
        """Manually trigger sync for a restaurant"""
        results = []
        
        try:
            if sync_type == "all" or sync_type == "file":
                config_key = f"restaurant_{restaurant_id}_file"
                if config_key in self.sync_configs:
                    config = self.sync_configs[config_key]
                    self._sync_file_job(restaurant_id, config["file_path"])
                    results.append("file sync triggered")
            
            if sync_type == "all" or sync_type == "sheets":
                config_key = f"restaurant_{restaurant_id}_sheets"
                if config_key in self.sync_configs:
                    config = self.sync_configs[config_key]
                    self._sync_sheets_job(
                        restaurant_id,
                        config["spreadsheet_id"],
                        config["range_name"],
                        config["credentials_path"]
                    )
                    results.append("sheets sync triggered")
            
            return {
                "success": True,
                "message": f"Manual sync triggered: {', '.join(results)}"
            }
            
        except Exception as e:
            logger.error(f"Error in manual sync: {e}")
            return {"success": False, "error": str(e)}


# Global scheduler instance
inventory_scheduler = InventoryScheduler()