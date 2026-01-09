#!/usr/bin/env python3
"""
Railway için Background Scheduler
Flask uygulaması içinde çalışacak background thread
"""

import threading
import time
from datetime import datetime, date
import logging
from late_arrival_system import check_all_employees_late_arrivals, update_monthly_statistics, get_system_settings

# Logging setup
logger = logging.getLogger(__name__)

class BackgroundScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_check = None
        self.last_stats_update = None
        
    def should_check_now(self):
        """Şimdi kontrol yapılmalı mı?"""
        now = datetime.now()
        
        # İlk çalıştırma
        if not self.last_check:
            return True
        
        # 5 dakika geçti mi?
        time_diff = (now - self.last_check).total_seconds()
        if time_diff < 300:  # 5 dakika = 300 saniye
            return False
        
        # Çalışma saatleri kontrolü (08:00 - 18:00)
        current_time = now.time()
        work_start = datetime.strptime('08:00', '%H:%M').time()
        work_end = datetime.strptime('18:00', '%H:%M').time()
        
        if not (work_start <= current_time <= work_end):
            return False
        
        # Hafta sonu kontrolü
        settings = get_system_settings()
        if now.weekday() >= 5 and settings.get('weekend_check_enabled', 'false').lower() != 'true':
            return False
        
        # Auto check enabled mi?
        if settings.get('auto_check_enabled', 'true').lower() != 'true':
            return False
        
        return True
    
    def should_update_stats(self):
        """İstatistikleri güncelle mi?"""
        now = datetime.now()
        
        # İlk çalıştırma veya gün değişti mi?
        if not self.last_stats_update:
            return True
        
        # Gün değişti mi?
        if self.last_stats_update.date() != now.date():
            return True
        
        return False
    
    def background_worker(self):
        """Background worker thread"""
        logger.info("🔄 Background scheduler started")
        
        while self.running:
            try:
                # Gecikme kontrolü
                if self.should_check_now():
                    logger.info("🔍 Running background late arrival check...")
                    check_all_employees_late_arrivals()
                    self.last_check = datetime.now()
                    logger.info("✅ Background check completed")
                
                # İstatistik güncelleme
                if self.should_update_stats():
                    logger.info("📊 Updating monthly statistics...")
                    update_monthly_statistics()
                    self.last_stats_update = datetime.now()
                    logger.info("✅ Statistics updated")
                
                # 60 saniye bekle
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Background worker error: {e}")
                time.sleep(120)  # Hata durumunda 2 dakika bekle
    
    def start(self):
        """Background scheduler'ı başlat"""
        if self.running:
            logger.warning("⚠️  Background scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.background_worker, daemon=True)
        self.thread.start()
        logger.info("🚀 Background scheduler started successfully")
    
    def stop(self):
        """Background scheduler'ı durdur"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️  Background scheduler stopped")
    
    def status(self):
        """Scheduler durumu"""
        if self.running and self.thread and self.thread.is_alive():
            return {
                'status': 'running',
                'last_check': self.last_check.isoformat() if self.last_check else None,
                'last_stats_update': self.last_stats_update.isoformat() if self.last_stats_update else None
            }
        else:
            return {'status': 'stopped'}

# Global scheduler instance
background_scheduler = BackgroundScheduler()