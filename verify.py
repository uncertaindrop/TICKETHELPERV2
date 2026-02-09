#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick verification script - checks files without requiring dependencies
"""
import os
import sys

print("="*60)
print("🧪 TICKETER Railway Setup Verification")
print("="*60)

all_good = True

# Test 1: Check selenium_setup.py exists
print("\n[1] selenium_setup.py...")
if os.path.exists("selenium_setup.py"):
    print("    ✓ Found")
else:
    print("    ✗ NOT FOUND")
    all_good = False

# Test 2: Check Dockerfile
print("\n[2] Dockerfile...")
if os.path.exists("Dockerfile"):
    with open("Dockerfile", "r") as f:
        content = f.read()
        if "google-chrome" in content and "chromedriver" in content:
            print("    ✓ Found with Chrome + ChromeDriver")
        else:
            print("    ✗ Missing Chrome/ChromeDriver setup")
            all_good = False
else:
    print("    ✗ NOT FOUND")
    all_good = False

# Test 3: Check requirements.txt
print("\n[3] requirements.txt...")
if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r") as f:
        content = f.read()
        if "webdriver-manager" in content:
            print("    ✗ ERROR: webdriver-manager still present!")
            all_good = False
        else:
            print("    ✓ Clean (no webdriver-manager)")
else:
    print("    ✗ NOT FOUND")
    all_good = False

# Test 4: Check main files
print("\n[4] Main application files...")
files = ["TICKETER.py", "pdfdata2.py", "TICKETHELPER.html"]
for f in files:
    if os.path.exists(f):
        print(f"    ✓ {f}")
    else:
        print(f"    ✗ {f} missing")
        all_good = False

# Test 5: Check TICKETER.py uses new selenium setup
print("\n[5] TICKETER.py integration...")
if os.path.exists("TICKETER.py"):
    with open("TICKETER.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "from selenium_setup import" in content:
            print("    ✓ Uses selenium_setup")
        else:
            print("    ✗ Still uses old webdriver-manager")
            all_good = False
        
        if "webdriver_manager" in content.lower():
            print("    ✗ WARNING: Still references webdriver_manager")
            all_good = False
else:
    print("    ✗ TICKETER.py not found")
    all_good = False

# Test 6: Check BONUSHELPER
print("\n[6] BONUSHELPER integration...")
bonus_auth = "BONUSHELPER/pmm_auth.py"
if os.path.exists(bonus_auth):
    with open(bonus_auth, "r", encoding="utf-8") as f:
        content = f.read()
        if "from selenium_setup import" in content:
            print("    ✓ BONUSHELPER/pmm_auth.py updated")
        else:
            print("    ✗ BONUSHELPER/pmm_auth.py still uses webdriver-manager")
            all_good = False
else:
    print("    ⚠ BONUSHELPER/pmm_auth.py not checked")

# Test 7: Check directories
print("\n[7] Required directories...")
for d in ["logs", "screenshots", "uploads"]:
    if os.path.exists(d):
        print(f"    ✓ {d}/")
    else:
        print(f"    ⚠ {d}/ will be created on first run")

# Test 8: Check configuration files
print("\n[8] Configuration files...")
config_files = [".dockerignore", ".gitignore", "railway.json", "README.md"]
for f in config_files:
    if os.path.exists(f):
        print(f"    ✓ {f}")
    else:
        print(f"    ⚠ {f} missing (optional)")

print("\n" + "="*60)
if all_good:
    print("✅ ALL CRITICAL CHECKS PASSED")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Test locally: docker build -t ticketer . && docker run -p 5000:5000 ticketer")
    print("2. Create GitHub repo and push code")
    print("3. Deploy to Railway from GitHub")
    print("4. Set env vars: HEADLESS=true, PORT=5000")
    print("\n💡 Tip: Check README.md for detailed instructions")
    sys.exit(0)
else:
    print("❌ SOME CHECKS FAILED")
    print("="*60)
    print("\nPlease review errors above before deploying")
    sys.exit(1)
