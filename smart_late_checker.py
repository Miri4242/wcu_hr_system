#!/usr/bin/env python3
"""
Akıllı Gecikme Kontrol Sistemi
Gerçek zamanlı kontrol yapar
"""

import threading
import time
from datetime import datetime, date, time as dt_time
import logging
from late_arrival_system import check_all_employees_late_arrivals, get_system_settings

logger = logging.getLogger(__name__)

class SmartLateChecker:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_check = None
        self.checked_employees_today = set()  # Bugün kontrol edilen çalışanlar
        
    def reset_daily_cache(self):
        """Günlük cache'i sıfırla"""
        now = datetime.now()
        if self.last_check and self.last_check.date() != now.date():
            self.checked_employees_today.clear()
            logger.info("🔄 Daily cache reset - new day started")
    
    def should_check_now(self):
        """Şimdi kontrol yapılmalı mı?"""
        now = datetime.now()
        current_time = now.time()
        
        # Çalışma saatleri (07:00 - 20:00)
        work_start = dt_time(7, 0)
        work_end = dt_time(20, 0)
        
        if not (work_start <= current_time <= work_end):
            return False
        
        # Sistem ayarları kontrol
        settings = get_system_settings()
        if settings.get('auto_check_enabled', 'true').lower() != 'true':
            return False
        
        # İlk çalıştırma
        if not self.last_check:
            return True
        
        # Son kontrolden 1 dakika geçti mi?
        time_diff = (now - self.last_check).total_seconds()
        if time_diff < 60:  # 1 dakika
            return False
        
        return True
    
    def get_check_intervals(self):
        """Kontrol aralıklarını belirle"""
        now = datetime.now()
        current_time = now.time()
        
        # Sabah yoğun kontrol (07:00 - 10:00) - Her 1 dakika
        if dt_time(7, 0) <= current_time <= dt_time(10, 0):
            return 60  # 1 dakika
        
        # Öğle yoğun kontrol (12:00 - 14:00) - Her 2 dakika
        elif dt_time(12, 0) <= current_time <= dt_time(14, 0):
            return 120  # 2 dakika
        
        # Normal saatler - Her 5 dakika
        else:
            return 300  # 5 dakika
    
    def smart_worker(self):
        """Akıllı worker thread"""
        logger.info("🧠 Smart late checker started")
        
        while self.running:
            try:
                # Günlük cache sıfırlama
                self.reset_daily_cache()
                
                # Kontrol zamanı mı?
                if self.should_check_now():
                    logger.info("🔍 Running smart late arrival check...")
                    
                    # Kontrol yap
                    check_all_employees_late_arrivals()
                    self.last_check = datetime.now()
                    
                    logger.info("✅ Smart check completed")
                
                # Dinamik bekleme süresi
                sleep_time = self.get_check_intervals()
                logger.debug(f"💤 Sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"❌ Smart worker error: {e}")
                time.sleep(60)  # Hata durumunda 1 dakika bekle
    
    def start(self):
        """Smart checker'ı başlat"""
        if self.running:
            logger.warning("⚠️  Smart checker already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.smart_worker, daemon=True)
        self.thread.start()
        logger.info("🚀 Smart late checker started successfully")
    
    def stop(self):
        """Smart checker'ı durdur"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️  Smart late checker stopped")
    
    def status(self):
        """Checker durumu"""
        if self.running and self.thread and self.thread.is_alive():
            return {
                'status': 'running',
                'last_check': self.last_check.isoformat() if self.last_check else None,
                'checked_today': len(self.checked_employees_today),
                'next_check_in': self.get_check_intervals()
            }
        else:
            return {'status': 'stopped'}

# Global smart checker instance
smart_checker = SmartLateChecker()