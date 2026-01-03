# 🚀 QUICK START - Get Running in 5 Minutes

## ⚡ Prerequisites Check

```powershell
# Check Python version (MUST be 3.11 or 3.12)
python --version
```

**If Python 3.14:** Download Python 3.11.7 from https://www.python.org/downloads/release/python-3117/

---

## 📋 5-Step Setup

### Step 1: Get Python 3.11/3.12 ⏱️ 2 min

**Windows:** https://www.python.org/downloads/release/python-3117/
- Download "Windows installer (64-bit)"
- Run installer
- ✅ CHECK "Add Python to PATH"
- Click "Install Now"

**Verify:**
```powershell
python --version  # Should show "Python 3.11.x" or "3.12.x"
```

---

### Step 2: Create Environment ⏱️ 1 min

```powershell
# Navigate to project
cd C:\Users\sarva\Downloads\Log_classification_system-main

# Remove old Python 3.14 venv
Remove-Item -Recurse -Force venv

# Create new venv with Python 3.11/3.12
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1
```

**Success:** Command prompt shows `(venv)` prefix

---

### Step 3: Install Packages ⏱️ 2-3 min

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Success:** No red error messages, ends with "Successfully installed..."

---

### Step 4: Verify ⏱️ 30 sec

```powershell
# Check Python version in venv
python --version  # Must be 3.11 or 3.12

# Run validation
python validate_system.py
```

**Success:** 
```
✅ ALL CORE SYSTEMS OPERATIONAL
```

---

### Step 5: Start Server ⏱️ 10 sec

```powershell
# Start the API server
python server.py
```

**Success:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🎉 You're Live!

### Test It:

**Browser:** http://127.0.0.1:8000/docs

**PowerShell:**
```powershell
# Test classification
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/classify" `
  -Form @{
    log_message = "Failed login attempt from 192.168.1.100"
    source = "WebServer"
  } | ConvertTo-Json
```

**Expected Response:**
```json
{
  "classification": "Security Alert",
  "processing_time_ms": 2.31,
  "timestamp": "2026-01-02T..."
}
```

---

## 🐛 Troubleshooting

### "Python 3.14" error?
❌ **Problem:** Python 3.14 not compatible
✅ **Fix:** Install Python 3.11.7 from link in Step 1

### "Module not found" error?
❌ **Problem:** Wrong venv or not activated
✅ **Fix:**
```powershell
.\venv\Scripts\Activate.ps1  # See (venv) prefix
pip install -r requirements.txt
```

### "Port already in use"?
❌ **Problem:** Server already running
✅ **Fix:**
```powershell
Get-Process -Name python | Stop-Process -Force
python server.py
```

### "GROQ_API_KEY not set"?
❌ **Problem:** .env file issue
✅ **Fix:** File should already exist, but verify:
```powershell
Get-Content .env | Select-String "GROQ_API_KEY"
```

---

## ✅ Success Checklist

- [ ] Python 3.11 or 3.12 installed
- [ ] Old venv removed
- [ ] New venv created & activated (see `(venv)`)
- [ ] Packages installed successfully
- [ ] `validate_system.py` shows all ✓
- [ ] Server starts without errors
- [ ] API responds at http://127.0.0.1:8000/docs
- [ ] Classification works

---

## 📚 Next Steps

1. **Test More:** Try different log messages in Swagger UI
2. **CSV Batch:** Upload CSV file at POST `/classify/`
3. **Monitor:** Check `/metrics` and `/health` endpoints
4. **Docker:** Run `docker-compose up -d` for production

---

## 🆘 Still Stuck?

1. Read [PYTHON_SETUP_GUIDE.md](PYTHON_SETUP_GUIDE.md) for detailed steps
2. Check Python version: `python --version`
3. Check venv active: Look for `(venv)` in prompt
4. Verify packages: `pip list | Select-String "transformers"`

---

**Time to Production:** ~5 minutes  
**Difficulty:** Easy  
**Support:** All setup files included
