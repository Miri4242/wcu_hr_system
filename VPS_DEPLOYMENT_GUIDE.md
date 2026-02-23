# VPS Deployment Guide - Employees Page Fix

## Problem
Employees səhifəsi VPS-də "Error loading employees" xətası verir və heç bir işçi göstərmir.

## Həll Addımları

### 1. VPS-ə Qoşul
```bash
ssh your_username@your_vps_ip
cd /path/to/your/project
```

### 2. Diaqnostika İşlət
```bash
# Virtual environment-i aktivləşdir
source .venv/bin/activate

# Diaqnostika scriptini işlət
python diagnose_vps.py
```

Bu script yoxlayacaq:
- Python versiyası
- Environment variables (.env faylı)
- Database bağlantısı
- Flask app faylı
- Virtual environment
- Lazımi paketlər

### 3. Yeni Dəyişiklikləri Yüklə

```bash
# Git pull (əgər git istifadə edirsinizsə)
git pull origin main

# Və ya faylları manual olaraq yükləyin:
# - app.py (yenilənmiş API error handling ilə)
# - templates/employees.html (yenilənmiş JavaScript ilə)
```

### 4. Flask App-ı Yenidən Başlat

```bash
# Restart script-i işlət
chmod +x restart_app.sh
./restart_app.sh

# Və ya manual:
pkill -f "python.*app.py"
nohup python app.py > flask_app.log 2>&1 &
```

### 5. Log-lara Bax

```bash
# Flask app log-larına bax
tail -f flask_app.log

# Və ya nohup.out
tail -f nohup.out
```

### 6. Test Et

#### Browser Console-da Test:
1. VPS URL-ni aç: `https://hr.wcu.edu.az/run.cgi/employees`
2. Browser Developer Tools-u aç (F12)
3. Console tab-ına bax
4. Aşağıdakı mesajları görməlisiniz:
   - `🔍 Fetching active employees - term: '', page: 1`
   - `🔍 Response status: 200`
   - `✅ Loaded X employees`

#### API Test:
```bash
# Test endpoint-i yoxla
curl https://hr.wcu.edu.az/run.cgi/api/test

# Employees API-ni yoxla
curl https://hr.wcu.edu.az/run.cgi/api/employees_list?category=active
```

## Əsas Dəyişikliklər

### 1. app.py - API Error Handling
- Daha ətraflı error mesajları
- HTTP status code-lar (401, 500)
- Traceback logging
- Test endpoint əlavə edildi

### 2. templates/employees.html - JavaScript Logging
- Response status yoxlanması
- Ətraflı error mesajları
- Console logging

## Mümkün Problemlər və Həllər

### Problem 1: Database Connection Error
```
❌ Database connection failed
```

**Həll:**
```bash
# .env faylını yoxla
cat .env

# Database məlumatlarının düzgün olduğunu təsdiq et
# Əgər lazımdırsa, .env faylını düzəlt
```

### Problem 2: Login Required Error
```
❌ API: User not logged in
```

**Həll:**
- Browser-də login olduğunuzdan əmin olun
- Session cookie-lərini yoxlayın
- Əgər lazımdırsa, yenidən login olun

### Problem 3: Flask App İşləmir
```
No existing Flask process found
```

**Həll:**
```bash
# Virtual environment-i aktivləşdir
source .venv/bin/activate

# Flask-i başlat
python app.py

# Və ya background-da:
nohup python app.py > flask_app.log 2>&1 &
```

### Problem 4: Port Problemi
```
Address already in use
```

**Həll:**
```bash
# İşləyən Flask prosesini tap və öldür
ps aux | grep python
kill -9 <process_id>

# Və ya
pkill -f "python.*app.py"
```

## Hostgator Xüsusi Qeydlər

Hostgator VPS-də Python app-ları işlətmək üçün:

1. **CGI Mode**: Əgər CGI mode istifadə edirsizsə, `.htaccess` faylını yoxlayın
2. **Passenger**: Əgər Passenger istifadə edirsizsə, `passenger_wsgi.py` lazımdır
3. **Port**: Default Flask port (5000) əvəzinə Hostgator-un təyin etdiyi portu istifadə edin

## Əlavə Yardım

Əgər problem davam edərsə:

1. Flask app log-larını göndərin: `flask_app.log`
2. Browser console screenshot-unu göndərin
3. Diaqnostika nəticələrini göndərin: `python diagnose_vps.py`

## Əlaqə

Əgər köməyə ehtiyacınız varsa, aşağıdakı məlumatları göndərin:
- VPS OS və versiyası
- Python versiyası
- Flask versiyası
- Error mesajları (log-lardan)
- Browser console log-ları
