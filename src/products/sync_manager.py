"""
Synchronization Manager Module
Handles automatic synchronization between SIC and local database
"""
import threading
import time
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timedelta

from .product_manager import ProductManager

logger = logging.getLogger(__name__)

class SyncManager:
    """Manages automatic synchronization between SIC and local database"""
    
    def __init__(self, product_manager: ProductManager, sync_interval: int = 300):
        self.product_manager = product_manager
        self.sync_interval = sync_interval  # seconds
        self.is_running = False
        self.sync_thread = None
        self.last_sync_attempt = None
        self.sync_callbacks = []
        self.auto_sync_enabled = True
        
    def add_sync_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback to be called after sync operations"""
        self.sync_callbacks.append(callback)
    
    def remove_sync_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove sync callback"""
        if callback in self.sync_callbacks:
            self.sync_callbacks.remove(callback)
    
    def _notify_callbacks(self, result: Dict[str, Any]):
        """Notify all registered callbacks of sync result"""
        for callback in self.sync_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Error in sync callback: {e}")
    
    def start_auto_sync(self):
        """Start automatic synchronization in background thread"""
        if self.is_running:
            logger.warning("Auto sync is already running")
            return
        
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info("Auto sync started")
    
    def stop_auto_sync(self):
        """Stop automatic synchronization"""
        self.is_running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        logger.info("Auto sync stopped")
    
    def _sync_loop(self):
        """Main synchronization loop"""
        while self.is_running:
            try:
                if self.auto_sync_enabled:
                    result = self.perform_sync()
                    self._notify_callbacks(result)
                    self.last_sync_attempt = datetime.now()
                
                # Wait for next sync interval
                for _ in range(self.sync_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                time.sleep(30)  # Wait 30 seconds before retrying
    
    def perform_sync(self, force: bool = False) -> Dict[str, Any]:
        """Perform synchronization operation"""
        sync_result = {
            'timestamp': datetime.now(),
            'success': False,
            'products_synced': 0,
            'movements_synced': 0,
            'errors': [],
            'duration': 0,
            'forced': force
        }
        
        start_time = time.time()
        
        try:
            logger.info("Starting synchronization with SIC")
            
            # Check if we should skip sync (unless forced)
            if not force and not self._should_sync():
                sync_result['skipped'] = True
                sync_result['reason'] = 'Sync not needed at this time'
                return sync_result
            
            # Perform the actual sync
            result = self.product_manager.sync_with_sic()
            
            sync_result.update({
                'success': result['success'],
                'products_synced': result['products_synced'],
                'movements_synced': result['movements_synced'],
                'errors': result['errors']
            })
            
            if result['success']:
                logger.info(f"Sync completed successfully: {result['products_synced']} products, {result['movements_synced']} movements")
            else:
                logger.warning(f"Sync completed with errors: {result['errors']}")
                
        except Exception as e:
            error_msg = f"Sync failed with exception: {e}"
            logger.error(error_msg)
            sync_result['errors'].append(error_msg)
        
        finally:
            sync_result['duration'] = time.time() - start_time
        
        return sync_result
    
    def _should_sync(self) -> bool:
        """Determine if synchronization should be performed"""
        try:
            # Check if SIC is available
            if not self.product_manager.check_sic_connection():
                return False
            
            # Check if enough time has passed since last sync
            if self.last_sync_attempt:
                time_since_last = datetime.now() - self.last_sync_attempt
                if time_since_last < timedelta(seconds=self.sync_interval):
                    return False
            
            # Check if there are pending movements
            pending_movements = self.product_manager.local_db.get_pending_movements()
            if pending_movements:
                return True
            
            # Check sync status
            sync_status = self.product_manager.local_db.get_sync_status()
            
            # Sync if we haven't synced in a while
            if sync_status.get('ultima_sincronizacao'):
                last_sync = datetime.fromisoformat(sync_status['ultima_sincronizacao'])
                if datetime.now() - last_sync > timedelta(hours=1):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if should sync: {e}")
            return False
    
    def force_sync(self) -> Dict[str, Any]:
        """Force immediate synchronization"""
        return self.perform_sync(force=True)
    
    def set_sync_interval(self, interval: int):
        """Set synchronization interval in seconds"""
        self.sync_interval = max(60, interval)  # Minimum 1 minute
        logger.info(f"Sync interval set to {self.sync_interval} seconds")
    
    def enable_auto_sync(self):
        """Enable automatic synchronization"""
        self.auto_sync_enabled = True
        logger.info("Auto sync enabled")
    
    def disable_auto_sync(self):
        """Disable automatic synchronization"""
        self.auto_sync_enabled = False
        logger.info("Auto sync disabled")
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        try:
            sync_status = self.product_manager.get_sync_status()
            
            stats = {
                'auto_sync_running': self.is_running,
                'auto_sync_enabled': self.auto_sync_enabled,
                'sync_interval': self.sync_interval,
                'last_sync_attempt': self.last_sync_attempt.isoformat() if self.last_sync_attempt else None,
                'sic_available': sync_status.get('sic_available', False),
                'offline_mode': sync_status.get('offline_mode', True),
                'total_products': sync_status.get('total_produtos', 0),
                'last_successful_sync': sync_status.get('ultima_sincronizacao'),
                'status': sync_status.get('status', 'unknown')
            }
            
            # Check for pending operations
            pending_movements = self.product_manager.local_db.get_pending_movements()
            stats['pending_movements'] = len(pending_movements)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting sync statistics: {e}")
            return {'error': str(e)}
    
    def test_sync_connection(self) -> Dict[str, Any]:
        """Test connection to SIC for synchronization"""
        try:
            success = self.product_manager.check_sic_connection()
            
            result = {
                'success': success,
                'timestamp': datetime.now().isoformat(),
                'offline_mode': self.product_manager.offline_mode
            }
            
            if success:
                result['message'] = 'SIC connection successful'
            else:
                result['message'] = 'SIC connection failed - operating in offline mode'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'message': f'Error testing connection: {e}',
                'offline_mode': True
            }