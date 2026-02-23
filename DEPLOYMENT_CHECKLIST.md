# Deployment Checklist - Employees Page Fix

## 📋 Pre-Deployment

### Local Test
- [ ] Flask app local-da işləyir
- [ ] Employees səhifəsi local-da işləyir
- [ ] API endpoint-lər cavab verir
- [ ] `python test_api_locally.py` uğurlu keçir
- [ ] Browser console-da error yoxdur

### Faylları Hazırla
- [ ] `app.py` - yenilənmiş versiya
- [ ] `run.cgi` - yenilənmiş versiya
- [ ] `templates/employees.html` - yenilənmiş versiya
- [ ] `diagnose_vps.py` - yeni fayl
- [ ] `.env` - database məlumatları düzgün

## 🚀 Deployment

### Variant 1: FTP ilə
- [ ] FileZilla və ya FTP client aç
- [ ] VPS-ə qoşul (ftp.your-domain.com)
- [ ] Backup yarat (app.py.backup, run.cgi.backup)
- [ ] `app.py` yüklə
- [ ] `run.cgi` yüklə
- [ ] `templates/employees.html` yüklə
- [ ] `diagnose_vps.py` yüklə
- [ ] `run.cgi` icazələrini 755 et
- [ ] `diagnose_vps.py` icazələrini 755 et

### Variant 2: SSH ilə
- [ ] SSH ilə VPS-ə qoşul
- [ ] Layihə qovluğuna keç
- [ ] Backup yarat
- [ ] Faylları yüklə (scp və ya git)
- [ ] İcazələri düzəlt (`chmod +x run.cgi`)
- [ ] Virtual environment aktivləşdir

### Variant 3: Git ilə
- [ ] Local-da commit et
- [ ] Git push et
- [ ] VPS-də git pull et
- [ ] İcazələri düzəlt

## 🧪 Testing

### 1. Diaqnostika
- [ ] SSH ilə VPS-ə qoşul
- [ ] `python diagnose_vps.py` işlət
- [ ] Bütün yoxlamalar ✅ olmalıdır
- [ ] Database bağlantısı işləyir
- [ ] Active employees sayı düzgündür (161)

### 2. Test Endpoint
- [ ] Browser-də aç: `https://hr.wcu.edu.az/run.cgi/api/test`
- [ ] Status: "ok" olmalıdır
- [ ] logged_in: true olmalıdır
- [ ] db_connected: true olmalıdır

### 3. Employees Səhifəsi
- [ ] Browser-də aç: `https://hr.wcu.edu.az/run.cgi/employees`
- [ ] Login olun (əgər lazımdırsa)
- [ ] Developer Tools aç (F12)
- [ ] Console tab-ına bax
- [ ] "🔍 Fetching active employees" mesajı görünür
- [ ] "✅ Loaded X employees" mesajı görünür
- [ ] Employee cards göstərilir
- [ ] Administrative tab-da 161 employees göstərilir
- [ ] Search işləyir
- [ ] Pagination işləyir
- [ ] School tab işləyir
- [ ] Teachers tab işləyir

### 4. Functionality Test
- [ ] Employee card-a klik edəndə employee logs-a gedir
- [ ] Email link-i işləyir (Outlook açılır)
- [ ] Phone link-i işləyir
- [ ] Search input-a yazanda axtarış işləyir
- [ ] Pagination button-ları işləyir
- [ ] Category tab-ları arasında keçid işləyir

## 🐛 Debugging (Əgər problem varsa)

### Log-ları Yoxla
- [ ] `tail -f cgi_errors.log` yoxla
- [ ] Browser console-da error-lara bax
- [ ] Network tab-da API request-lərə bax
- [ ] Response status code-ları yoxla

### Ümumi Problemlər
- [ ] 500 Error → İcazələri yoxla (chmod 755 run.cgi)
- [ ] Login required → Browser-də login ol
- [ ] Database error → .env faylını yoxla
- [ ] Virtual env error → run.cgi-də path-i yoxla
- [ ] No employees → API response-u yoxla

## 📊 Success Criteria

### Minimum Requirements
- [ ] Employees səhifəsi açılır
- [ ] Heç olmasa 1 employee göstərilir
- [ ] Error mesajı yoxdur

### Full Success
- [ ] Administrative: 161 employees
- [ ] School: XX employees (düzgün say)
- [ ] Teachers: XX employees (düzgün say)
- [ ] Bütün employee cards göstərilir
- [ ] Search işləyir
- [ ] Pagination işləyir
- [ ] Category tabs işləyir
- [ ] Browser console-da error yoxdur

## 📝 Post-Deployment

### Monitoring
- [ ] 5 dəqiqə sonra yenidən yoxla
- [ ] Başqa browser-də test et
- [ ] Başqa user ilə login olub test et
- [ ] Mobile-da test et (əgər mümkünsə)

### Documentation
- [ ] Deployment tarixini qeyd et
- [ ] Əgər problem varsa, həllini qeyd et
- [ ] Log-ları arxivlə (backup)

### Cleanup
- [ ] Backup faylları saxla (app.py.backup)
- [ ] Test faylları sil (əgər lazım deyilsə)
- [ ] Köhnə log-ları təmizlə

## 🎯 Rollback Plan (Əgər problem varsa)

### Sürətli Rollback
- [ ] Backup faylları bərpa et:
  ```bash
  cp app.py.backup app.py
  cp run.cgi.backup run.cgi
  cp templates/employees.html.backup templates/employees.html
  ```
- [ ] İcazələri düzəlt
- [ ] Test et

### Tam Rollback
- [ ] Git-də əvvəlki commit-ə qayıt
- [ ] Faylları yenidən yüklə
- [ ] Test et

## ✅ Final Checklist

- [ ] Deployment uğurlu oldu
- [ ] Bütün test-lər keçdi
- [ ] Heç bir error yoxdur
- [ ] User-lər səhifəni istifadə edə bilir
- [ ] Sənədləşmə tamamlandı
- [ ] Team-ə məlumat verildi

## 📞 Support

Əgər problem varsa:
- [ ] Diaqnostika nəticəsini yığ
- [ ] Log-ları yığ
- [ ] Screenshot-lar çək
- [ ] Support-a müraciət et

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Status:** [ ] Success  [ ] Failed  [ ] Partial
**Notes:** _______________________________________________
