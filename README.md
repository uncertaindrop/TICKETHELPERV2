# 🚀 TICKETER - Railway Ready

Automated ticket creation system for PMM CRM with Railway deployment support.

## ✨ What's New - Railway Edition

- ✅ **Railway/Docker Ready** - Runs headlessly in containers
- ✅ **No webdriver-manager** - Uses system Chrome/ChromeDriver
- ✅ **Configurable Headless Mode** - Toggle via environment variable
- ✅ **Production Optimized** - Proper error handling and logging
- ✅ **Health Checks** - Built-in endpoint monitoring

## 📋 Features

### Main Application (TICKETER.py)
- PDF invoice parsing and automatic ticket creation
- Multiple ticket types support (PROMO, QUICK REPAIR, etc.)
- Automatic technician assignment
- Status progression workflow
- Screenshot capture on errors
- Comprehensive logging

### Bonus Helper (BONUSHELPER/monthly_ticket_counter.py)
- Monthly ticket counting per store
- Google Sheets integration
- Multiple store support across Cyprus locations

## 🚢 Railway Deployment

### Quick Deploy

1. **Create New GitHub Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Railway ready"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy to Railway**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect the Dockerfile and deploy

3. **Set Environment Variables in Railway**
   ```
   HEADLESS=true
   PORT=5000
   HOST=0.0.0.0
   DEBUG=false
   ```

4. **Access Your App**
   - Railway will provide a public URL
   - Visit it to access the TICKETER interface

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEADLESS` | `true` | Run Chrome headlessly (required for Railway) |
| `PORT` | `5000` | Port to bind Flask server |
| `HOST` | `0.0.0.0` | Host to bind (Railway requires 0.0.0.0) |
| `DEBUG` | `false` | Flask debug mode (keep false in production) |
| `GOOGLE_CHROME_BIN` | `/usr/bin/google-chrome` | Chrome binary path (auto-set) |
| `CHROMEDRIVER_PATH` | `/usr/local/bin/chromedriver` | ChromeDriver path (auto-set) |

## 🔧 Local Development

### With Docker (Recommended - simulates Railway)

```bash
# Build image
docker build -t ticketer .

# Run with environment variables
docker run -p 5000:5000 \
  -e HEADLESS=true \
  -e DEBUG=false \
  ticketer
```

### Without Docker (Local machine)

```bash
# Install dependencies
pip install -r requirements.txt

# Run in headed mode (to see browser)
export HEADLESS=false
python TICKETER.py

# Or headless mode
export HEADLESS=true
python TICKETER.py
```

**Note:** Without Docker, you need Chrome and ChromeDriver installed on your system.

## 📁 Project Structure

```
.
├── TICKETER.py              # Main Flask application
├── selenium_setup.py        # Railway-compatible Selenium config
├── pdfdata2.py              # PDF parsing logic
├── requirements.txt         # Python dependencies
├── Dockerfile               # Railway/Docker configuration
├── .dockerignore           # Docker build exclusions
├── .gitignore              # Git exclusions
├── TICKETHELPER.html       # Web UI
├── BONUSHELPER/            # Bonus scripts folder
│   ├── monthly_ticket_counter.py
│   └── pmm_auth.py         # Shared authentication module
├── logs/                   # Application logs (generated)
├── screenshots/            # Error screenshots (generated)
└── uploads/                # PDF uploads (generated)
```

## 🎯 Key Changes from Original

### ✅ Fixed for Railway

1. **Selenium Driver Initialization**
   - **Before:** Used `webdriver-manager` (fails on Railway)
   - **After:** Uses system Chrome + ChromeDriver from Dockerfile

2. **Headless Mode**
   - **Before:** Commented out, manual toggle
   - **After:** Controlled via `HEADLESS` env var, defaults to `true`

3. **Docker Support**
   - **Before:** No Dockerfile
   - **After:** Production-ready Dockerfile with Chrome + ChromeDriver

4. **Dependencies**
   - **Before:** Included `webdriver-manager`
   - **After:** Removed, uses system binaries

### 📝 Code Changes

**TICKETER.py:**
```python
# Old
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# New
from selenium_setup import get_driver_from_env
driver = get_driver_from_env()  # Handles headless automatically
```

**BONUSHELPER/pmm_auth.py:**
```python
# Same pattern - replaced webdriver-manager with selenium_setup
```

## 🐛 Debugging on Railway

### View Logs
```bash
# In Railway dashboard
Project → Deployments → View Logs
```

### Common Issues

**Issue: Chrome binary not found**
```
Solution: Dockerfile installs it automatically
Check: Railway logs should show Chrome version during build
```

**Issue: ChromeDriver version mismatch**
```
Solution: Dockerfile automatically matches versions
Check: Both Chrome and ChromeDriver versions in build logs
```

**Issue: Can't see browser**
```
Solution: This is expected in headless mode
Use: Screenshots are saved to screenshots/ folder
Debug: Check logs for detailed step-by-step progress
```

### Debug Screenshots

The application automatically captures screenshots on errors:
```python
# Screenshots saved to: screenshots/
# Format: {error_type}_{timestamp}.png
```

These screenshots work even in headless mode and can be downloaded from Railway's logs or via API.

## 🔐 Security Notes

- **Credentials:** Hardcoded in scripts (consider using env vars)
- **Cookies:** Saved to `pmm_cookies.json` for session persistence
- **Non-root User:** Docker runs as `appuser` (UID 1000) for security

## 📊 Health Check

The application includes a health check endpoint:

```bash
# Check if service is running
curl http://your-railway-url.up.railway.app/health

# Expected response:
{
  "status": "healthy",
  "headless": "true",
  "chrome_bin": "/usr/bin/google-chrome",
  "chromedriver": "/usr/local/bin/chromedriver"
}
```

## 🎓 Testing Before Deploy

Always test locally with Docker before deploying:

```bash
# Build
docker build -t ticketer-test .

# Run
docker run -p 5000:5000 -e HEADLESS=true ticketer-test

# Test in browser
open http://localhost:5000
```

If it works locally in Docker, it will work on Railway.

## 📞 Support

For issues:
1. Check Railway logs first
2. Verify environment variables are set
3. Test locally with Docker
4. Check that Chrome/ChromeDriver versions match

## 🚀 Quick Deploy Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created and linked to repo
- [ ] Environment variables set (`HEADLESS=true`, etc.)
- [ ] Deployment succeeded (check Railway dashboard)
- [ ] Health endpoint returns 200 OK
- [ ] Test ticket creation with sample PDF

---

**Version:** 2.4 Railway Edition  
**Status:** ✅ Production Ready  
**Last Updated:** February 2026
