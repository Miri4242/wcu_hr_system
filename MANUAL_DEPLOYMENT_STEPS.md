# Manual Deployment Steps - Employees Page Fix

## Problemin Təsviri
VPS-də employees səhifəsi "Error loading employees" xətası verir. Local-da işləyir, amma VPS-də işləmir.

## Dəyişdirilən Fayllar

### 1. app.py
- API error handling yaxşılaşdırıldı
- Session konfiqurasiyası CGI mode üçün əlavə edildi
- Test endpoint əlavə edildi (`/api/test`)
- Daha ətraflı logging

### 2. templates/employees.html
- JavaScript error handling yaxşılaşdırıldı
- Console logging əlavə edildi
- Response status yoxlanması

### 3. run.cgi
- Virtual environment path düzəldildi (venv → .venv)
- Error logging əlavə edildi
- Exception handling

## Deployment Addımları

### Variant 1: FTP/SFTP ilə (Ən Asan)

1. **FileZilla və ya digər FTP client aç**

2. **VPS-ə qoşul:**
   - Host: `ftp.your-domain.com` və ya VPS IP
   - Username: `wcuteing`
   - Password: [sizin parolunuz]
   - Port: 21 (FTP) və ya 22 (SFTP)

3. **Aşağıdakı faylları yüklə:**
   ```
   Local                                    → VPS Path
   ─────────────────────────────────────────────────────────────
   app.py                                   → /home/wcuteing/public_html/hr.wcu.edu.az/app.py
   run.cgi                                  → /home/wcuteing/public_html/hr.wcu.edu.az/run.cgi
   templates/employees.html                 → /home/wcuteing/public_html/hr.wcu.edu.az/templates/employees.html
   diagnose_vps.py                          → /home/wcuteing/public_html/hr.wcu.edu.az/diagnose_vps.py
   VPS_DEPLOYMENT_GUIDE.md                  → /home/wcuteing/public_html/hr.wcu.edu.az/VPS_DEPLOYMENT_GUIDE.md
   ```

4. **run.cgi faylının icazələrini düzəlt:**
   - FTP client-də run.cgi faylına sağ klik
   - "File permissions" və ya "CHMOD" seç
   - 755 (rwxr-xr-x) qoy
   - Və ya SSH ilə: `chmod +x run.cgi`

### Variant 2: SSH ilə (Daha Sürətli)

1. **VPS-ə SSH ilə qoşul:**
   ```bash
   ssh wcuteing@your_vps_ip
   ```

2. **Layihə qovluğuna keç:**
   ```bash
   cd /home/wcuteing/public_html/hr.wcu.edu.az
   ```

3. **Backup yarat (təhlükəsizlik üçün):**
   ```bash
   cp app.py app.py.backup
   cp run.cgi run.cgi.backup
   cp templates/employees.html templates/employees.html.backup
   ```

4. **Faylları redaktə et:**
   
   **app.py-ni redaktə et:**
   ```bash
   nano app.py
   ```
   
   Aşağıdakı dəyişiklikləri et:
   - Session konfiqurasiyası əlavə et (sətir 53-dən sonra)
   - API error handling-i yaxşılaşdır (sətir 2257-dən başlayaraq)
   - Test endpoint əlavə et (sətir 2256-dan əvvəl)

   **run.cgi-ni redaktə et:**
   ```bash
   nano run.cgi
   ```
   
   İlk sətri dəyişdir:
   ```python
   #!/home/wcuteing/public_html/hr.wcu.edu.az/.venv/bin/python
   ```
   
   Error logging əlavə et (faylın sonuna)

   **templates/employees.html-i redaktə et:**
   ```bash
   nano templates/employees.html
   ```
   
   JavaScript fetch funksiyasını yaxşılaşdır (sətir 258-dən başlayaraq)

5. **İcazələri düzəlt:**
   ```bash
   chmod +x run.cgi
   chmod +x diagnose_vps.py
   ```

### Variant 3: Git ilə (Əgər Git istifadə edirsizsə)

1. **Local-da commit et:**
   ```bash
   git add app.py run.cgi templates/employees.html
   git commit -m "Fix employees page API error handling"
   git push origin main
   ```

2. **VPS-də pull et:**
   ```bash
   ssh wcuteing@your_vps_ip
   cd /home/wcuteing/public_html/hr.wcu.edu.az
   git pull origin main
   chmod +x run.cgi
   ```

## Test Etmə

### 1. Diaqnostika İşlət

```bash
ssh wcuteing@your_vps_ip
cd /home/wcuteing/public_html/hr.wcu.edu.az
source .venv/bin/activate
python diagnose_vps.py
```

Gözlənilən nəticə:
```
✅ Database connected successfully
✅ Total persons in database: XXX
✅ Active employees (Administrative): XXX
```

### 2. Test Endpoint-i Yoxla

Browser-də aç:
```
https://hr.wcu.edu.az/run.cgi/api/test
```

Gözlənilən cavab:
```json
{
  "status": "ok",
  "message": "API is working",
  "logged_in": true,
  "db_connected": true
}
```

### 3. Employees Səhifəsini Test Et

1. Browser-də aç: `https://hr.wcu.edu.az/run.cgi/employees`
2. Developer Tools aç (F12)
3. Console tab-ına bax
4. Aşağıdakı mesajları görməlisiniz:
   ```
   🔍 Fetching active employees - term: '', page: 1
   🔍 Response status: 200
   🔍 Response data: {employees: Array(12), pagination: {...}, ...}
   ✅ Loaded 12 employees
   ```

### 4. Log-lara Bax (Əgər problem varsa)

```bash
# CGI error log
tail -f /home/wcuteing/public_html/hr.wcu.edu.az/cgi_errors.log

# Apache error log (əgər icazəniz varsa)
tail -f /var/log/apache2/error.log
```

## Mümkün Problemlər və Həllər

### Problem 1: "500 Internal Server Error"

**Səbəb:** run.cgi faylının icazələri düzgün deyil

**Həll:**
```bash
chmod 755 run.cgi
```

### Problem 2: "Login required" error

**Səbəb:** Session işləmir və ya login olmamısınız

**Həll:**
1. Browser-də login olun
2. Cookie-ləri yoxlayın
3. Session konfiqurasiyasını yoxlayın

### Problem 3: "Database connection error"

**Səbəb:** .env faylında database məlumatları düzgün deyil

**Həll:**
```bash
# .env faylını yoxla
cat .env

# Database məlumatlarını test et
python diagnose_vps.py
```

### Problem 4: Virtual environment tapılmır

**Səbəb:** run.cgi-də path düzgün deyil

**Həll:**
```bash
# Virtual environment-in yerini yoxla
ls -la /home/wcuteing/public_html/hr.wcu.edu.az/.venv/bin/python

# run.cgi-də path-i düzəlt
nano run.cgi
```

### Problem 5: "No module named 'app'"

**Səbəb:** sys.path düzgün konfiqurasiya olunmayıb

**Həll:**
run.cgi faylında yoxla:
```python
sys.path.insert(0, "/home/wcuteing/public_html/hr.wcu.edu.az")
```

## Əlavə Qeydlər

### Hostgator Xüsusiyyətləri

1. **CGI Mode:** Hostgator shared hosting-də CGI mode istifadə olunur
2. **Python Path:** Virtual environment-in tam path-i lazımdır
3. **Permissions:** run.cgi faylı executable olmalıdır (755)
4. **Logs:** cgi_errors.log faylında error-lar yazılır

### Performance

CGI mode hər request üçün Python interpreter-i yenidən başladır. Bu normal-dır və gözləniləndir.

### Security

- SECRET_KEY-i .env faylında saxlayın
- Database credentials-ı .env faylında saxlayın
- .env faylını git-ə əlavə etməyin (.gitignore-da olmalıdır)

## Yardım Lazımdırsa

Əgər problem davam edərsə, aşağıdakı məlumatları göndərin:

1. **Diaqnostika nəticəsi:**
   ```bash
   python diagnose_vps.py > diagnostic_output.txt
   ```

2. **CGI error log:**
   ```bash
   tail -100 cgi_errors.log > error_log.txt
   ```

3. **Browser console screenshot**

4. **Test endpoint cavabı:**
   ```bash
   curl https://hr.wcu.edu.az/run.cgi/api/test > api_test.txt
   ```

## Uğurlar!

Bu dəyişikliklər employees səhifəsini VPS-də düzəltməlidir. Əgər hələ də problem varsa, yuxarıdakı test addımlarını izləyin və log-ları yoxlayın.
