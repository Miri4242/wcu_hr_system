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
        
        # 2 dakika geçti mi? (Daha sık kontrol)
        time_diff = (now - self.last_check).total_seconds()
        if time_diff < 120:  # 2 dakika = 120 saniye
            return False
        
        # Çalışma saatleri kontrolü (07:00 - 19:00) - Daha geniş aralık
        current_time = now.time()
        work_start = datetime.strptime('07:00', '%H:%M').time()
        work_end = datetime.strptime('19:00', '%H:%M').time()
        
        if not (work_start <= current_time <= work_end):
            return False
        
        # Hafta sonu kontrolü - Hafta sonu da çalışsın
        settings = get_system_settings()
        # Hafta sonu kontrolünü kaldırdık, her gün çalışsın
        
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
                
                # 30 saniye bekle (Daha sık kontrol)
                time.sleep(30)
                
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