#!/usr/bin/env python3
"""
Gecikme Takip Sistemi - Otomatik Scheduler
Her 5 dakikada bir çalışanların gecikme durumunu kontrol eder ve email gönderir.
"""

import schedule
import time
import threading
from datetime import datetime, date
import logging
from late_arrival_system import check_all_employees_late_arrivals, update_monthly_statistics, get_system_settings

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('late_arrival_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LateArrivalScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        
    def check_late_arrivals_job(self):
        """Gecikme kontrolü işi"""
        try:
            logger.info("🔍 Starting scheduled late arrival check...")
            
            # Sistem ayarlarını kontrol et
            settings = get_system_settings()
            
            if settings.get('auto_check_enabled', 'true').lower() != 'true':
                logger.info("⏸️  Auto check is disabled, skipping...")
                return
            
            # Hafta sonu kontrolü
            today = date.today()
            if today.weekday() >= 5 and settings.get('weekend_check_enabled', 'false').lower() != 'true':
                logger.info("📅 Weekend check disabled, skipping...")
                return
            
            # Çalışma saatleri kontrolü (08:00 - 18:00 arası)
            current_time = datetime.now().time()
            work_start = datetime.strptime('08:00', '%H:%M').time()
            work_end = datetime.strptime('18:00', '%H:%M').time()
            
            if not (work_start <= current_time <= work_end):
                logger.info(f"⏰ Outside work hours ({current_time}), skipping...")
                return
            
            # Gecikme kontrolü yap
            check_all_employees_late_arrivals()
            
            logger.info("✅ Scheduled late arrival check completed")
            
        except Exception as e:
            logger.error(f"❌ Scheduled check error: {e}")
            import traceback
            traceback.print_exc()
    
    def update_statistics_job(self):
        """Aylık istatistikleri güncelle (günde bir kez)"""
        try:
            logger.info("📊 Updating monthly statistics...")
            update_monthly_statistics()
            logger.info("✅ Monthly statistics updated")
        except Exception as e:
            logger.error(f"❌ Statistics update error: {e}")
    
    def start_scheduler(self):
        """Scheduler'ı başlat"""
        logger.info("🚀 Starting Late Arrival Scheduler...")
        
        # Her 5 dakikada bir gecikme kontrolü
        schedule.every(5).minutes.do(self.check_late_arrivals_job)
        
        # Her gün saat 23:00'da istatistik güncelleme
        schedule.every().day.at("23:00").do(self.update_statistics_job)
        
        # İlk çalıştırmada bir kez kontrol yap
        logger.info("🔍 Running initial check...")
        self.check_late_arrivals_job()
        
        self.running = True
        
        # Scheduler loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # 30 saniye bekle
            except KeyboardInterrupt:
                logger.info("⏹️  Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Hata durumunda 1 dakika bekle
    
    def start_background(self):
        """Scheduler'ı arka planda başlat"""
        if self.thread and self.thread.is_alive():
            logger.warning("⚠️  Scheduler already running")
            return
        
        self.thread = threading.Thread(target=self.start_scheduler, daemon=True)
        self.thread.start()
        logger.info("🔄 Scheduler started in background")
    
    def stop(self):
        """Scheduler'ı durdur"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️  Scheduler stopped")
    
    def status(self):
        """Scheduler durumunu göster"""
        if self.running and self.thread and self.thread.is_alive():
            return "🟢 Running"
        else:
            return "🔴 Stopped"

def main():
    """Ana fonksiyon"""
    scheduler = LateArrivalScheduler()
    
    try:
        logger.info("="*60)
        logger.info("🏢 WCU HR LATE ARRIVAL MONITORING SYSTEM")
        logger.info("="*60)
        logger.info("📋 Configuration:")
        logger.info("   - Check interval: Every 5 minutes")
        logger.info("   - Work hours: 08:00 - 18:00")
        logger.info("   - Statistics update: Daily at 23:00")
        logger.info("   - Weekend checks: Configurable")
        logger.info("="*60)
        
        # Sistem ayarlarını göster
        settings = get_system_settings()
        logger.info("⚙️  Current settings:")
        logger.info(f"   - Auto check enabled: {settings.get('auto_check_enabled', 'true')}")
        logger.info(f"   - Weekend check enabled: {settings.get('weekend_check_enabled', 'false')}")
        logger.info(f"   - Work start time: {settings.get('work_start_time', '09:00:00')}")
        logger.info(f"   - Late threshold: {settings.get('late_threshold_minutes', '15')} minutes")
        logger.info(f"   - Email enabled: {settings.get('email_enabled', 'true')}")
        
        logger.info("="*60)
        logger.info("🚀 Starting scheduler... Press Ctrl+C to stop")
        logger.info("="*60)
        
        # Scheduler'ı başlat
        scheduler.start_scheduler()
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Stopping scheduler...")
        scheduler.stop()
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()