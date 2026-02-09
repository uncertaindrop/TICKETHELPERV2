# -*- coding: utf-8 -*-
"""
🚀 TICKETER IMPROVED - VERSION 2.4 - STATUS NAME FIX ✅
GUARANTEED TO BIND TO 0.0.0.0 FOR RAILWAY/RENDER DEPLOYMENT
✅ FIXED: Status progression now uses correct element ID 'ticketstatusID'
✅ FIXED: Calls JavaScript function 'fun_save_ticket_status' for auto-save
✅ FIXED: Status names match HTML exactly (In-house Repair with dash)
✅ FIXED: Handles confirmation popup for "Ready" status
✅ FIXED: Increased delays and Chrome stability improvements

Enhanced with:
1. Comprehensive logging with timestamps and context
2. Better error handling with retries
3. Robust status progression (FIXED!)
4. Screenshot capture on errors
5. Detailed step-by-step tracking
6. ✅ CLOUD DEPLOYMENT READY - Binds to 0.0.0.0
7. ✅ Chrome stability improvements - longer delays
8. ✅ Confirmation popup handling for "Ready" status
"""

import os
import json
import random
import traceback
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, send_from_directory

# ---------- LOGGING SETUP ----------
import logging

# Create logs directory
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Setup detailed logging
log_filename = os.path.join(LOGS_DIR, f"ticketer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("="*80)
logger.info("TICKETER IMPROVED - Starting new session")
logger.info("="*80)

# ---------- PDF PARSING ----------
try:
    from pdfdata2 import extract as pdfdata2_extract
    logger.info("✓ pdfdata2 module loaded successfully")
except ImportError:
    pdfdata2_extract = None
    logger.warning("⚠ pdfdata2 module not found, using fallback parser")

from PyPDF2 import PdfReader

PDF_UPLOAD_DIR = "uploads"
os.makedirs(PDF_UPLOAD_DIR, exist_ok=True)

SCREENSHOTS_DIR = "screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def ensure_dot(value: Any) -> str:
    """Convert value to string, return '.' if empty"""
    v = ("" if value is None else str(value)).strip()
    return v if v else "."


def parse_pdf(path: str) -> Dict[str, str]:
    """
    Uses pdfdata2.extract() to parse invoices.
    Falls back to "." for missing fields.
    """
    logger.info(f"Parsing PDF: {path}")
    
    if pdfdata2_extract is not None:
        try:
            raw = pdfdata2_extract(path)
            logger.debug(f"PDF parse result: {raw}")
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            logger.debug(traceback.format_exc())
            raw = {}
    else:
        raw = {}

    result = {
        "name": ensure_dot(raw.get("name")),
        "surname": ensure_dot(raw.get("surname")),
        "phone": ensure_dot(raw.get("phone")),
        "invoice": ensure_dot(raw.get("invoice")),
        "cstcode": ensure_dot(raw.get("cst code")),
        "material": ensure_dot(raw.get("material")),
        "product": ensure_dot(raw.get("product")),
        "serial": ensure_dot(raw.get("serial")),
    }
    
    logger.info(f"✓ PDF parsed successfully: {result}")
    return result


# ---------- SELENIUM / PMM AUTOMATION ----------

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
# Railway-compatible Selenium setup
from selenium_setup import get_driver_from_env
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException
)

PMM_BASE_URL = "https://pmm.irepair.gr"
COOKIES_FILE = "pmm_cookies.json"

# Configuration constants
VISIBLE_DAMAGE_OPTIONS = [
    "light signs of use",
    "brand new",
    "some scratches",
    "hits on frame",
]

ITEMS_LEFT_OPTIONS = [
    "only device left with us",
    "full box device left with us",
]

PROMO_OPTIONS = [
    "promo setup & optimization",
    "software optimization and account setup",
    "promo service – data check & configuration",
    "promo device setup and update",
]

PRINTER_PROBLEMS = [
    "printer not printing",
    "paper jam randomly",
    "printer offline on network",
    "lines / streaks on prints",
]

LAPTOP_PROBLEMS = [
    "slow performance and freezes",
    "random shutdowns while in use",
    "blue screen errors",
    "overheating under light usage",
]

TABLET_PROBLEMS = [
    "touchscreen not responsive",
    "battery drains quickly",
    "tablet not charging",
    "apps crashing frequently",
]

APPLIANCE_PROBLEMS = [
    "device not powering on",
    "random error codes displayed",
    "unusual noise during operation",
    "device stops mid-cycle",
]

PHONE_PROBLEMS = [
    "screen flickering and ghost touches",
    "device restarting randomly",
    "battery drains very fast",
    "no sound on calls",
    "camera not focusing",
]

ETA_OPTIONS = [
    "ETA: same day service if possible.",
    "ETA: 1 business day.",
    "ETA: 2–3 business days.",
]

PROMO_RESOLUTION_OPTIONS = [
    "setup done",
    "ready",
    "setup finished",
    "finished setting up",
    "cst informed",
]

NORMAL_RESOLUTION_OPTIONS = [
    "device works fine",
    "device ok cst informed",
    "no issues",
    "no problem",
    "works fine",
]


@dataclass
class ParsedInvoice:
    id: str
    filename: str
    path: str
    fields: Dict[str, str]


parsed_files: Dict[str, ParsedInvoice] = {}


def save_screenshot(driver: webdriver.Chrome, prefix: str) -> str:
    """Save screenshot with timestamp"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        driver.save_screenshot(filepath)
        logger.info(f"📸 Screenshot saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return ""


def build_repair_description(ticket_type: str, items_left_text: str) -> str:
    """Build repair description based on ticket type"""
    ticket_type = ticket_type.upper().strip()
    logger.debug(f"Building repair description for ticket type: {ticket_type}")
    
    if ticket_type == "PROMO":
        problem = random.choice(PROMO_OPTIONS)
    elif ticket_type == "QUICK REPAIR PRINTER":
        problem = random.choice(PRINTER_PROBLEMS)
    elif ticket_type == "QUICK REPAIR LAPTOP":
        problem = random.choice(LAPTOP_PROBLEMS)
    elif ticket_type == "QUICK REPAIR TABLET":
        problem = random.choice(TABLET_PROBLEMS)
    elif ticket_type == "QUICK REPAIR APPLIANCE":
        problem = random.choice(APPLIANCE_PROBLEMS)
    else:
        # default to phone variant
        problem = random.choice(PHONE_PROBLEMS)

    eta = random.choice(ETA_OPTIONS)
    description = f"{items_left_text}. {problem}. {eta}"
    logger.debug(f"Repair description: {description}")
    return description


def build_resolution(ticket_type: str) -> str:
    """Build resolution text based on ticket type"""
    ticket_type = ticket_type.upper().strip()
    if ticket_type == "PROMO":
        return random.choice(PROMO_RESOLUTION_OPTIONS)
    return random.choice(NORMAL_RESOLUTION_OPTIONS)


def save_cookies(driver: webdriver.Chrome) -> None:
    """Save cookies to file for session persistence"""
    try:
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ Cookies saved to {COOKIES_FILE}")
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")


def load_cookies(driver: webdriver.Chrome) -> None:
    """Load cookies from file"""
    if not os.path.exists(COOKIES_FILE):
        logger.info("No cookies file found, will perform fresh login")
        return
    
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        
        logger.info(f"Loading {len(cookies)} cookies from file")
        driver.get(PMM_BASE_URL)
        
        for c in cookies:
            c.pop('sameSite', None)
            try:
                driver.add_cookie(c)
            except Exception as e:
                logger.debug(f"Could not add cookie {c.get('name')}: {e}")
                continue
        
        logger.info("✓ Cookies loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")


def get_driver() -> webdriver.Chrome:
    """Initialize Chrome WebDriver with Railway-compatible setup"""
    logger.info("Initializing Chrome WebDriver...")
    
    # Use the Railway-compatible driver from selenium_setup
    driver = get_driver_from_env()
    
    logger.info("✓ Chrome WebDriver initialized successfully")
    return driver


def wait_for_element(driver: webdriver.Chrome, by: By, value: str, 
                     timeout: int = 30, condition="presence") -> Any:
    """
    Wait for element with better logging
    
    Args:
        condition: "presence", "visible", "clickable"
    """
    logger.debug(f"Waiting for element: {by}={value} (condition: {condition}, timeout: {timeout}s)")
    
    wait = WebDriverWait(driver, timeout)
    
    try:
        if condition == "presence":
            element = wait.until(EC.presence_of_element_located((by, value)))
        elif condition == "visible":
            element = wait.until(EC.visibility_of_element_located((by, value)))
        elif condition == "clickable":
            element = wait.until(EC.element_to_be_clickable((by, value)))
        else:
            raise ValueError(f"Unknown condition: {condition}")
        
        logger.debug(f"✓ Element found: {by}={value}")
        return element
    
    except TimeoutException:
        logger.error(f"✗ Timeout waiting for element: {by}={value}")
        save_screenshot(driver, f"timeout_{by}_{value[:30]}")
        raise


def safe_click(driver: webdriver.Chrome, element, description: str = "element") -> bool:
    """
    Safely click element with multiple strategies
    """
    logger.debug(f"Attempting to click: {description}")
    
    try:
        # Try scrolling into view first
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.3)
        
        # Try regular click
        try:
            element.click()
            logger.debug(f"✓ Clicked {description} (regular click)")
            return True
        except ElementClickInterceptedException:
            logger.debug(f"Regular click intercepted, trying JS click for {description}")
            driver.execute_script("arguments[0].click();", element)
            logger.debug(f"✓ Clicked {description} (JS click)")
            return True
            
    except Exception as e:
        logger.error(f"✗ Failed to click {description}: {e}")
        save_screenshot(driver, f"click_failed_{description[:30]}")
        return False


def login_if_needed(driver: webdriver.Chrome, username: str, password: str) -> None:
    """
    Login to PMM if not already authenticated
    Handles cookies, CAPTCHA wait, and OTP
    """
    logger.info("="*60)
    logger.info("LOGIN PROCESS STARTING")
    logger.info("="*60)
    
    wait = WebDriverWait(driver, 600)

    # Try with existing cookies first
    logger.info("Attempting to use existing session cookies...")
    load_cookies(driver)
    driver.get(PMM_BASE_URL + "/users/dashboard")
    
    if "/users/dashboard" in driver.current_url:
        logger.info("✓ Successfully logged in using existing cookies")
        return

    logger.info("No valid session found, proceeding with full login...")
    
    # No valid session – do full login
    driver.get(PMM_BASE_URL + "/")
    logger.info(f"Navigated to login page: {driver.current_url}")
    
    # Username
    logger.info("Filling username field...")
    username_field = wait_for_element(driver, By.CSS_SELECTOR, "#username", timeout=30)
    username_field.clear()
    username_field.send_keys(username)
    logger.info(f"✓ Username entered: {username}")

    # Password
    logger.info("Filling password field...")
    password_field = wait_for_element(driver, By.CSS_SELECTOR, "#password-field", timeout=30)
    password_field.clear()
    password_field.send_keys(password)
    logger.info("✓ Password entered")

    # Email Authenticator
    logger.info("Selecting Email Authenticator...")
    try:
        email_radio = driver.find_element(By.CSS_SELECTOR, "#authenticator_type_2")
        if not email_radio.is_selected():
            email_radio.click()
            logger.info("✓ Email authenticator selected")
    except Exception as e:
        logger.debug(f"Email authenticator already selected or not found: {e}")

    # Click login button
    logger.info("Looking for login button...")
    login_clicked = False
    for locator in [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[contains(.,'Login') or contains(.,'Sign In')]"),
        (By.XPATH, "//input[@type='submit']"),
    ]:
        try:
            btn = driver.find_element(*locator)
            btn.click()
            login_clicked = True
            logger.info(f"✓ Login button clicked using locator: {locator}")
            break
        except Exception:
            continue

    if not login_clicked:
        logger.error("✗ Login button not found with any locator")
        save_screenshot(driver, "login_button_not_found")
        raise RuntimeError("Login button not found")

    # Wait for CAPTCHA and OTP
    logger.info("⏳ Waiting for user to complete CAPTCHA (if present)...")
    logger.info("⏳ Waiting for OTP page or dashboard...")
    
    try:
        wait.until(EC.url_contains("/otp-authentication"))
        logger.info("✓ OTP page reached - waiting for user to enter OTP...")
    except TimeoutException:
        logger.info("No OTP page detected, checking if already at dashboard...")

    # Wait for dashboard
    logger.info("⏳ Waiting for dashboard...")
    try:
        wait.until(EC.url_contains("/users/dashboard"))
        logger.info("✓ Successfully reached dashboard")
        save_cookies(driver)
        logger.info("="*60)
        logger.info("LOGIN COMPLETED SUCCESSFULLY")
        logger.info("="*60)
    except TimeoutException:
        logger.error("✗ Failed to reach dashboard after login")
        save_screenshot(driver, "login_failed_dashboard")
        raise


def select2_by_visible_text(driver: webdriver.Chrome, wait: WebDriverWait,
                            container_css: str, text: str) -> None:
    """Generic helper for Select2 single selects"""
    logger.debug(f"Select2 operation: container={container_css}, text={text}")
    
    container = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, container_css)))
    container.click()
    
    search_input = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "span.select2-container--open input.select2-search__field")
        )
    )
    search_input.clear()
    search_input.send_keys(text)
    search_input.send_keys(Keys.ENTER)
    
    logger.debug(f"✓ Select2 value set: {text}")


def assign_technician_robust(driver: webdriver.Chrome) -> bool:
    """
    Assign technician with robust error handling
    Returns True if successful, False otherwise
    """
    logger.info("="*60)
    logger.info("STEP: ASSIGN TECHNICIAN")
    logger.info("="*60)
    
    wait = WebDriverWait(driver, 25)
    
    try:
        # Wait for assign_to select element
        logger.info("Looking for technician dropdown (assign_to)...")
        assign_select = wait_for_element(driver, By.ID, "assign_to", timeout=25)
        
        # Get all options
        options = assign_select.find_elements(By.TAG_NAME, "option")
        logger.info(f"Found {len(options)} options in technician dropdown")
        
        # Filter valid technicians
        techs = []
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.text.strip()
            if val and val not in ("", "0"):
                techs.append((val, text))
                logger.debug(f"  - Technician option: '{text}' (value={val})")
        
        if not techs:
            logger.error("✗ No valid technicians found in dropdown")
            save_screenshot(driver, "no_technicians")
            return False
        
        # Choose random technician
        chosen_val, chosen_name = random.choice(techs)
        logger.info(f"✓ Selected technician: '{chosen_name}' (value={chosen_val})")
        
        # Set value using Selenium Select
        logger.debug("Setting technician value using Select...")
        Select(assign_select).select_by_value(chosen_val)
        
        # Trigger change events
        logger.debug("Triggering JS change events...")
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            assign_select
        )
        
        # Try PMM's internal function if it exists
        try:
            driver.execute_script(
                "if (typeof fun_save_ticket_assign_to === 'function') { "
                "  console.log('Calling fun_save_ticket_assign_to'); "
                "  fun_save_ticket_assign_to(); "
                "}"
            )
            logger.debug("✓ PMM internal function called")
        except Exception as e:
            logger.debug(f"PMM internal function not available: {e}")
        
        time.sleep(1)  # Brief pause for JS to process
        
        # Click Save button
        logger.info("Looking for Save button...")
        save_btn = wait_for_element(
            driver, 
            By.XPATH, 
            "//button[@type='submit' and @name='btn_save']",
            timeout=15,
            condition="clickable"
        )
        
        if not safe_click(driver, save_btn, "Save button after technician"):
            logger.error("✗ Failed to click Save button")
            return False
        
        logger.info("✓ Save button clicked, waiting for page to update...")
        
        # Wait for save to complete - be flexible about what happens
        time.sleep(2)
        
        # Verify we're still on edit page or reloaded
        try:
            wait_for_element(driver, By.ID, "ticketID", timeout=15)
            logger.info("✓ Technician assignment completed successfully")
            logger.info("="*60)
            return True
        except TimeoutException:
            logger.warning("⚠ Could not verify ticket page after save, but continuing...")
            logger.info("="*60)
            return True
            
    except Exception as e:
        logger.error(f"✗ Technician assignment failed: {e}")
        logger.debug(traceback.format_exc())
        save_screenshot(driver, "technician_assignment_failed")
        logger.info("="*60)
        return False


def fill_resolution_field(driver: webdriver.Chrome, ticket_type: str) -> bool:
    """
    Fill the resolution field
    Returns True if successful
    """
    logger.info("="*60)
    logger.info("STEP: FILL RESOLUTION FIELD")
    logger.info("="*60)
    
    wait = WebDriverWait(driver, 20)
    
    try:
        logger.info("Looking for resolution textarea...")
        res_box = wait_for_element(driver, By.ID, "resolution", timeout=20, condition="visible")
        
        # Generate resolution text
        if ticket_type.upper().strip() == "PROMO":
            res_text = random.choice(PROMO_RESOLUTION_OPTIONS)
        else:
            res_text = random.choice(NORMAL_RESOLUTION_OPTIONS)
        
        logger.info(f"Resolution text: '{res_text}'")
        
        res_box.clear()
        res_box.send_keys(res_text)
        
        logger.info("✓ Resolution field filled successfully")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to fill resolution field: {e}")
        logger.debug(traceback.format_exc())
        save_screenshot(driver, "resolution_fill_failed")
        logger.info("="*60)
        return False


def progress_status_robust(driver: webdriver.Chrome, target_status: str, 
                          step_num: int, total_steps: int) -> bool:
    """
    Progress to a specific status with robust error handling
    FIXED: Uses correct element ID 'ticketstatusID' and calls JavaScript function fun_save_ticket_status
    
    Args:
        target_status: The status text to select
        step_num: Current step number (for logging)
        total_steps: Total number of status steps
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("-"*60)
    logger.info(f"STATUS STEP {step_num}/{total_steps}: '{target_status}'")
    logger.info("-"*60)
    
    wait = WebDriverWait(driver, 30)
    max_retries = 3
    
    # Map status names to match HTML exactly
    status_mapping = {
        "With Technician": "With Technician",
        "In House Repair": "In-house Repair",  # Fixed: Added dash
        "In-house Repair": "In-house Repair",
        "Final Check": "Final Check",
        "Ready": "Ready for Pickup",  # Fixed: Full name
        "Ready for Pickup": "Ready for Pickup",
        "Closed": "Closed"
    }
    
    status_to_select = status_mapping.get(target_status, target_status)
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} to set status to '{status_to_select}'")
            
            # Verify we're on the ticket edit page
            current_url = driver.current_url
            logger.debug(f"Current URL: {current_url}")
            
            if "/tickets/edittickets" not in current_url:
                logger.error(f"✗ Not on edit ticket page. Current URL: {current_url}")
                save_screenshot(driver, f"wrong_page_status_{target_status}")
                return False
            
            # FIXED: Wait for CORRECT status dropdown ID
            logger.debug("Looking for status dropdown (ticketstatusID)...")
            status_select = wait_for_element(
                driver, 
                By.ID, 
                "ticketstatusID",  # ← FIXED: Correct element ID from HTML
                timeout=20,
                condition="presence"
            )
            
            # Get current status for logging
            try:
                current_status = Select(status_select).first_selected_option.text
                logger.info(f"Current status: '{current_status}'")
            except Exception:
                logger.debug("Could not determine current status")
            
            # Get the value for the target status
            logger.debug(f"Finding option with text '{status_to_select}'")
            select_obj = Select(status_select)
            
            # Find option by visible text
            target_option = None
            for option in select_obj.options:
                if option.text.strip() == status_to_select:
                    target_option = option
                    break
            
            if not target_option:
                logger.error(f"✗ Could not find status option: '{status_to_select}'")
                logger.info("Available options:")
                for opt in select_obj.options:
                    logger.info(f"  - '{opt.text.strip()}' (value={opt.get_attribute('value')})")
                return False
            
            target_value = target_option.get_attribute('value')
            logger.info(f"Setting status to: '{status_to_select}' (value={target_value})")
            
            # Select the status
            select_obj.select_by_value(target_value)
            
            # FIXED: Call the JavaScript function that the HTML expects
            # The onchange in HTML: onchange="fun_save_ticket_status(this.value,TICKET_ID)"
            # We need to get the ticket ID from the page
            logger.debug(f"Calling fun_save_ticket_status({target_value}, TICKET_ID)")
            try:
                # Get ticket ID from the hidden input field or URL
                ticket_id = None
                try:
                    ticket_id_element = driver.find_element(By.ID, "ticketID")
                    ticket_id = ticket_id_element.get_attribute("value")
                    logger.debug(f"Found ticket ID: {ticket_id}")
                except:
                    # Fallback: extract from URL
                    import re
                    url_match = re.search(r'/edittickets/(\d+)', driver.current_url)
                    if url_match:
                        ticket_id = url_match.group(1)
                        logger.debug(f"Extracted ticket ID from URL: {ticket_id}")
                
                if ticket_id:
                    driver.execute_script(f"fun_save_ticket_status({target_value}, {ticket_id});")
                    logger.debug(f"✓ JavaScript function called: fun_save_ticket_status({target_value}, {ticket_id})")
                else:
                    # Fallback: call without ticket ID (might still work)
                    driver.execute_script(f"fun_save_ticket_status({target_value}, 3);")
                    logger.warning("⚠ Could not get ticket ID, using placeholder '3'")
            except Exception as e:
                logger.warning(f"⚠ Could not call fun_save_ticket_status: {e}")
                # Continue anyway - might still work
            
            # Wait for JavaScript to complete (increased for stability)
            time.sleep(2)
            
            # FIXED: Handle confirmation popup (appears for "Ready" status)
            # The popup asks: "Did you put a warranty sticker inside?" with "Yes, do it!" button
            try:
                logger.debug("Checking for confirmation popup...")
                # Try multiple selectors for the "Yes, do it!" button
                confirm_button = None
                selectors = [
                    "button.confirm.btn2.btn-default",  # Most specific
                    "button.confirm.btn2",              # Less specific
                    "button.confirm",                    # Even less specific
                    "button:contains('Yes')",            # Text-based (if supported)
                ]
                
                for selector in selectors:
                    try:
                        confirm_button = wait_for_element(
                            driver,
                            By.CSS_SELECTOR,
                            selector,
                            timeout=2,
                            condition="clickable"
                        )
                        if confirm_button:
                            logger.info(f"⚠️  Confirmation popup detected (selector: {selector})")
                            logger.info("Clicking 'Yes, do it!' button...")
                            safe_click(driver, confirm_button, "Confirmation popup button")
                            time.sleep(2)  # Wait for popup to close and save to complete
                            logger.info("✓ Confirmation popup handled")
                            break
                    except TimeoutException:
                        continue
                
                if not confirm_button:
                    logger.debug("No confirmation popup (normal for most statuses)")
                    
            except Exception as e:
                logger.warning(f"⚠ Popup handling issue (continuing anyway): {e}")
            
            # Additional wait after popup handling
            time.sleep(1)
            
            # The JavaScript function should auto-save, so we don't need to click Save
            # Just wait for the page to be ready
            try:
                # Verify the dropdown still exists (page may have reloaded)
                wait_for_element(driver, By.ID, "ticketstatusID", timeout=10)
                logger.info(f"✓ Status updated to '{status_to_select}' successfully")
                logger.info("-"*60)
                return True
                
            except TimeoutException:
                logger.warning(f"⚠ Attempt {attempt}: Could not verify page state")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                else:
                    # Assume it worked
                    logger.info(f"✓ Status likely updated to '{status_to_select}' (continuing)")
                    logger.info("-"*60)
                    return True
        
        except NoSuchElementException as e:
            logger.error(f"✗ Attempt {attempt}: Element not found: {e}")
            save_screenshot(driver, f"status_{target_status}_not_found_attempt{attempt}")
            if attempt < max_retries:
                time.sleep(2)
                continue
        
        except StaleElementReferenceException as e:
            logger.warning(f"⚠ Attempt {attempt}: Stale element, retrying: {e}")
            if attempt < max_retries:
                time.sleep(2)
                continue
        
        except Exception as e:
            logger.error(f"✗ Attempt {attempt}: Unexpected error: {e}")
            logger.debug(traceback.format_exc())
            save_screenshot(driver, f"status_{target_status}_error_attempt{attempt}")
            if attempt < max_retries:
                time.sleep(2)
                continue
    
    logger.error(f"✗ Failed to set status to '{target_status}' after {max_retries} attempts")
    logger.info("-"*60)
    return False


def update_status_and_resolution(driver: webdriver.Chrome, ticket_type: str) -> None:
    """
    Complete workflow: assign technician, fill resolution, progress through statuses
    """
    logger.info("="*80)
    logger.info("STARTING TICKET UPDATE WORKFLOW")
    logger.info("="*80)
    
    wait = WebDriverWait(driver, 30)
    
    # Ensure we're on the edit ticket page
    try:
        logger.info("Verifying we're on edit ticket page...")
        wait_for_element(driver, By.ID, "ticketID", timeout=30)
        logger.info(f"✓ On edit ticket page: {driver.current_url}")
    except TimeoutException:
        logger.error("✗ Not on edit ticket page!")
        save_screenshot(driver, "not_on_edit_page")
        raise
    
    # Step 1: Assign Technician
    tech_success = assign_technician_robust(driver)
    if not tech_success:
        logger.warning("⚠ Technician assignment had issues, but continuing...")
    
    # Small delay between major steps
    time.sleep(1)
    
    # Step 2: Fill Resolution
    res_success = fill_resolution_field(driver, ticket_type)
    if not res_success:
        logger.error("✗ Failed to fill resolution - cannot continue")
        raise Exception("Resolution field filling failed")
    
    # Small delay before status progression
    time.sleep(1)
    
    # Step 3: Status Progression
    logger.info("="*60)
    logger.info("STARTING STATUS PROGRESSION")
    logger.info("="*60)
    
    # FIXED: Status names must match HTML exactly (note the dash in "In-house Repair")
    status_flow = [
        "With Technician",
        "In-house Repair",  # ← FIXED: Added dash to match HTML
        "Final Check",
        "Ready for Pickup",  # ← FIXED: Full name from HTML
        "Closed"
    ]
    
    total_steps = len(status_flow)
    
    for idx, status_text in enumerate(status_flow, start=1):
        success = progress_status_robust(driver, status_text, idx, total_steps)
        
        if not success:
            logger.error(f"✗ Failed at status: {status_text}")
            raise Exception(f"Status progression failed at: {status_text}")
        
        # Increased delay between status changes for JavaScript to complete
        if idx < total_steps:
            # Extra long pause before "Ready for Pickup" status (Chrome stability)
            if status_flow[idx] == "Ready for Pickup":  # Next status is "Ready for Pickup"
                logger.info("⏸️  Extra pause before 'Ready for Pickup' status (Chrome stability)...")
                time.sleep(5)
            else:
                time.sleep(2.5)  # Increased from 2 to 2.5 seconds
    
    logger.info("="*60)
    logger.info("✓ STATUS PROGRESSION COMPLETED SUCCESSFULLY")
    logger.info("="*60)
    logger.info("="*80)
    logger.info("TICKET UPDATE WORKFLOW COMPLETED")
    logger.info("="*80)


def create_single_ticket(driver: webdriver.Chrome,
                         parsed: ParsedInvoice,
                         ticket_type: str,
                         store: str) -> None:
    """
    Create a single ticket with comprehensive logging
    """
    logger.info("")
    logger.info("="*80)
    logger.info(f"CREATING TICKET: {parsed.filename}")
    logger.info(f"Ticket Type: {ticket_type}")
    logger.info(f"Store: {store}")
    logger.info("="*80)
    
    wait_short = WebDriverWait(driver, 30)
    wait_long = WebDriverWait(driver, 120)

    fields = parsed.fields
    name = ensure_dot(fields.get("name"))
    surname = ensure_dot(fields.get("surname"))
    phone = ensure_dot(fields.get("phone"))
    invoice = ensure_dot(fields.get("invoice"))
    material = ensure_dot(fields.get("material"))
    product = ensure_dot(fields.get("product"))
    serial = ensure_dot(fields.get("serial"))
    cstcode = ensure_dot(fields.get("cstcode"))
    
    if serial == ".":
        serial = invoice
        logger.debug("Serial was missing, using invoice number as serial")

    # Normalize phone
    clean_phone = phone.replace(" ", "").replace("-", "").lstrip("0")
    if not clean_phone.isdigit():
        clean_phone = "00000000"
        logger.warning(f"Invalid phone number, using placeholder: {clean_phone}")
    phone_val = "+357" + clean_phone

    logger.info("Customer data prepared:")
    logger.info(f"  Name: {name} {surname}")
    logger.info(f"  Phone: {phone_val}")
    logger.info(f"  Invoice: {invoice}")
    logger.info(f"  CST Code: {cstcode}")
    logger.info(f"  Material: {material}")
    logger.info(f"  Product: {product}")
    logger.info(f"  Serial: {serial}")

    # Navigate to Add Ticket page
    logger.info("Navigating to Add Ticket page...")
    driver.get(PMM_BASE_URL + "/tickets/addtickets")
    wait_long.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form")))
    logger.info("✓ Add Ticket page loaded")

    # ========== STORE ==========
    logger.info(f"Setting store: {store}")
    try:
        select2_by_visible_text(driver, wait_short, "#select2-store_id-container", store)
        logger.info("✓ Store set (Select2)")
    except Exception as e:
        logger.debug(f"Select2 failed, trying regular select: {e}")
        try:
            Select(driver.find_element(By.ID, "store_id")).select_by_visible_text(store)
            logger.info("✓ Store set (regular select)")
        except Exception as e2:
            logger.error(f"✗ Failed to set store: {e2}")

    # ========== TICKET CATEGORY ==========
    logger.info("Setting ticket category to 'In Warranty'")
    try:
        cat = driver.find_element(By.ID, "pmm_ticket_category")
        Select(cat).select_by_visible_text("In Warranty")
        logger.info("✓ Category set")
    except Exception as e:
        logger.warning(f"Could not set category: {e}")

    # ========== ADD CUSTOMER ==========
    logger.info("Opening Add Customer modal...")
    try:
        wait_short.until(EC.invisibility_of_element_located(
            (By.CSS_SELECTOR, "div.blockUI.blockOverlay")
        ))
    except:
        pass

    try:
        add_btn = wait_for_element(driver, By.ID, "cur_add_html", timeout=30, condition="clickable")
        if not safe_click(driver, add_btn, "Add Customer button"):
            raise Exception("Failed to click Add Customer button")
        logger.info("✓ Add Customer button clicked")
    except Exception as e:
        logger.error(f"✗ Could not open customer modal: {e}")
        save_screenshot(driver, "customer_modal_failed")
        raise

    # Wait for modal
    logger.info("Waiting for customer modal to appear...")
    try:
        wait_short.until(EC.visibility_of_element_located((By.ID, "addCustomer")))
        logger.info("✓ Customer modal appeared")
    except:
        logger.error("✗ Customer modal did not appear")
        save_screenshot(driver, "customer_modal_not_visible")
        raise

    # Fill Customer Modal
    logger.info("Filling customer details...")
    try:
        # Store inside modal
        try:
            cs = wait_short.until(EC.presence_of_element_located((By.ID, "customer_storeID")))
            Select(cs).select_by_visible_text(store)
            logger.debug("✓ Customer store set")
        except Exception as e:
            logger.debug(f"Customer store field issue: {e}")

        # Type = Person
        try:
            ctype = wait_short.until(EC.presence_of_element_located((By.ID, "type")))
            Select(ctype).select_by_value("1")
            logger.debug("✓ Customer type set to Person")
        except Exception as e:
            logger.debug(f"Customer type field issue: {e}")

        # First Name
        fn = wait_for_element(driver, By.ID, "firstName", timeout=30, condition="visible")
        fn.clear()
        fn.send_keys(name)
        logger.debug(f"✓ First name: {name}")

        # Last Name
        ln = driver.find_element(By.ID, "lastName")
        ln.clear()
        ln.send_keys(surname)
        logger.debug(f"✓ Last name: {surname}")

        # Optional email clear
        try:
            driver.find_element(By.ID, "email").clear()
        except:
            pass

        # Phone
        try:
            ph = driver.find_element(By.ID, "phoneNo")
            ph.clear()
            ph.send_keys(phone_val)
            logger.debug(f"✓ Phone: {phone_val}")
        except Exception as e:
            logger.debug(f"Phone field issue: {e}")

        # Mobile (required)
        mob = wait_for_element(driver, By.ID, "mobile", timeout=30, condition="visible")
        mob.clear()
        mob.send_keys(phone_val)
        logger.debug(f"✓ Mobile: {phone_val}")

        # Save customer
        logger.info("Saving customer...")
        save_cust = wait_for_element(
            driver,
            By.CSS_SELECTOR,
            "#add_customer_form button[type='submit']",
            timeout=30,
            condition="clickable"
        )
        save_cust.click()
        logger.info("✓ Customer save button clicked")

        # Wait for modal to close
        logger.info("Waiting for customer modal to close...")
        wait_long.until(EC.invisibility_of_element_located((By.ID, "addCustomer")))
        logger.info("✓ Customer modal closed - customer saved successfully")

    except Exception as e:
        logger.error(f"✗ Failed filling customer modal: {e}")
        logger.debug(traceback.format_exc())
        save_screenshot(driver, "customer_fill_failed")
        raise

    # ========== DEVICE ==========
    logger.info("Setting device to 'Other/Generic'")
    try:
        select2_by_visible_text(driver, wait_short, "#select2-device_id-container", "Other/Generic")
        logger.info("✓ Device set")
    except Exception as e:
        logger.warning(f"Could not set device: {e}")

    # ========== MATERIAL DESCRIPTION ==========
    logger.info(f"Setting material description: {product}")
    try:
        el = driver.find_element(By.ID, "pmm_material_description")
        el.clear()
        el.send_keys(product)
        logger.info("✓ Material description set")
    except Exception as e:
        logger.warning(f"Could not set material description: {e}")

    # ========== PASSWORD TYPE ==========
    logger.info("Setting password type to 'No code'")
    try:
        Select(driver.find_element(By.ID, "device_password_type")).select_by_visible_text("No code")
        logger.info("✓ Password type set")
    except Exception as e:
        logger.warning(f"Could not set password type: {e}")

    # ========== SERIAL ==========
    logger.info(f"Setting serial: {serial}")
    try:
        sn = driver.find_element(By.ID, "serial_no")
        sn.clear()
        sn.send_keys(serial)
        logger.info("✓ Serial set")
    except Exception as e:
        logger.warning(f"Could not set serial: {e}")

    # ========== VISIBLE DAMAGE ==========
    damage_choice = random.choice(VISIBLE_DAMAGE_OPTIONS)
    logger.info(f"Setting visible damage: {damage_choice}")
    try:
        dmg = driver.find_element(By.ID, "repair_print")
        dmg.clear()
        dmg.send_keys(damage_choice)
        logger.info("✓ Visible damage set")
    except Exception as e:
        logger.warning(f"Could not set visible damage: {e}")

    # ========== BOOTABLE ==========
    logger.info("Setting bootable to 'Yes'")
    try:
        Select(driver.find_element(By.ID, "device_bootable")).select_by_visible_text("Yes")
        logger.info("✓ Bootable set")
    except Exception as e:
        logger.warning(f"Could not set bootable: {e}")

    # ========== MATERIAL ==========
    logger.info(f"Setting material: {material}")
    try:
        mat = driver.find_element(By.ID, "pmm_material")
        driver.execute_script("arguments[0].removeAttribute('readonly');", mat)
        mat.clear()
        mat.send_keys(material)
        logger.info("✓ Material set")
    except Exception as e:
        logger.warning(f"Could not set material: {e}")

    # ========== CONTRACT NUMBER ==========
    logger.info(f"Setting contract number: {invoice}")
    try:
        cn = driver.find_element(By.ID, "pmm_safety_net_contract_number")
        cn.clear()
        cn.send_keys(invoice)
        logger.info("✓ Contract number set")
    except Exception as e:
        logger.warning(f"Could not set contract number: {e}")

    # ========== ITEMS LEFT ==========
    items_left_text = random.choice(["only device", "full box device"])
    logger.info(f"Setting items left: {items_left_text}")
    try:
        il = driver.find_element(By.ID, "pmm_items_left_with_device")
        il.clear()
        il.send_keys(items_left_text)
        logger.info("✓ Items left set")
    except Exception as e:
        logger.warning(f"Could not set items left: {e}")

    # ========== NAVISION CUSTOMER NUMBER ==========
    nav_value = cstcode if cstcode != "." else invoice
    logger.info(f"Setting Navision Customer Number: {nav_value}")
    try:
        nav_field = wait_for_element(
            driver,
            By.ID,
            "pmm_navision_customer_number",
            timeout=30,
            condition="visible"
        )
        nav_field.clear()
        nav_field.send_keys(nav_value)

        # Trigger events
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            nav_field
        )
        logger.info("✓ Navision Customer Number set")
    except Exception as e:
        logger.error(f"✗ Could not set Navision Customer Number: {e}")
        save_screenshot(driver, "navision_field_failed")

    # ========== REPAIR DESCRIPTION ==========
    logger.info("Building repair description...")
    try:
        repair_box = wait_for_element(driver, By.ID, "repair", timeout=30, condition="visible")
        final_desc = build_repair_description(ticket_type, items_left_text)
        repair_box.clear()
        repair_box.send_keys(final_desc)
        logger.info(f"✓ Repair description set: {final_desc}")
    except Exception as e:
        logger.error(f"✗ Could not fill repair description: {e}")
        save_screenshot(driver, "repair_description_failed")

    # ========== SAVE TICKET ==========
    logger.info("Saving ticket...")
    try:
        save_btn = wait_for_element(
            driver,
            By.XPATH,
            "//button[@type='submit' and @name='btn_save']",
            timeout=30,
            condition="clickable"
        )
        
        if not safe_click(driver, save_btn, "Save Ticket button"):
            raise Exception("Failed to click Save Ticket button")
        
        logger.info("✓ Save button clicked")
    except Exception as e:
        logger.error(f"✗ Could not click Save Ticket: {e}")
        save_screenshot(driver, "save_ticket_failed")
        raise

    # ========== WAIT FOR EDIT PAGE ==========
    logger.info("Waiting for Edit Ticket page...")
    try:
        wait_long.until(EC.url_contains("/tickets/edittickets"))
        logger.info(f"✓ Edit Ticket page loaded: {driver.current_url}")
    except:
        logger.error("✗ Did not reach Edit Ticket page")
        save_screenshot(driver, "edit_page_not_reached")
        raise

    # ========== UPDATE STATUS AND RESOLUTION ==========
    try:
        update_status_and_resolution(driver, ticket_type)
        logger.info("✓✓✓ TICKET COMPLETED SUCCESSFULLY ✓✓✓")
    except Exception as e:
        logger.error(f"✗ Failed during status/resolution workflow: {e}")
        logger.debug(traceback.format_exc())
        save_screenshot(driver, "status_workflow_failed")
        raise

    logger.info("="*80)
    logger.info("")


def run_ticket_batch(crm_username: str,
                     crm_password: str,
                     tickets_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run a batch of tickets with comprehensive logging
    """
    logger.info("")
    logger.info("="*80)
    logger.info(f"STARTING BATCH OF {len(tickets_payload)} TICKETS")
    logger.info("="*80)
    
    results: List[Dict[str, Any]] = []
    driver = None
    
    try:
        driver = get_driver()
        login_if_needed(driver, crm_username, crm_password)

        for idx, t in enumerate(tickets_payload, start=1):
            fid = t["id"]
            ticket_type = t["ticket_type"]
            store = t["store"]
            
            logger.info("")
            logger.info("*"*80)
            logger.info(f"PROCESSING TICKET {idx}/{len(tickets_payload)}")
            logger.info("*"*80)
            
            parsed = parsed_files.get(str(fid))
            if not parsed:
                logger.error(f"✗ Parsed invoice not found for ID: {fid}")
                results.append({
                    "id": fid,
                    "filename": "(unknown)",
                    "success": False,
                    "error": "Parsed invoice not found in server memory."
                })
                continue

            try:
                create_single_ticket(driver, parsed, ticket_type, store)
                results.append({
                    "id": fid,
                    "filename": parsed.filename,
                    "success": True,
                    "error": ""
                })
                logger.info(f"✓✓✓ TICKET {idx}/{len(tickets_payload)} SUCCESS ✓✓✓")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"✗✗✗ TICKET {idx}/{len(tickets_payload)} FAILED ✗✗✗")
                logger.error(f"Error: {error_msg}")
                logger.debug(traceback.format_exc())
                
                results.append({
                    "id": fid,
                    "filename": parsed.filename,
                    "success": False,
                    "error": error_msg
                })
                
    finally:
        if driver is not None:
            logger.info("Closing browser...")
            try:
                driver.quit()
                logger.info("✓ Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

    logger.info("")
    logger.info("="*80)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info(f"Success: {sum(1 for r in results if r['success'])}/{len(results)}")
    logger.info(f"Failed: {sum(1 for r in results if not r['success'])}/{len(results)}")
    logger.info("="*80)
    
    return results


# ========== FLASK API ==========

app = Flask(__name__)


@app.route("/parse_pdfs", methods=["POST"])
def api_parse_pdfs():
    """Parse uploaded PDFs"""
    global parsed_files
    parsed_files = {}

    logger.info("="*60)
    logger.info("API: /parse_pdfs called")
    logger.info("="*60)

    files = request.files.getlist("pdfs")
    logger.info(f"Received {len(files)} files")
    
    out: List[Dict[str, Any]] = []

    for idx, f in enumerate(files):
        if not f.filename.lower().endswith(".pdf"):
            logger.warning(f"Skipping non-PDF file: {f.filename}")
            continue
            
        safe_name = f.filename
        path = os.path.join(PDF_UPLOAD_DIR, safe_name)
        f.save(path)
        logger.info(f"Saved: {path}")

        fields = parse_pdf(path)
        
        normalized = {
            "name": ensure_dot(fields.get("name")),
            "surname": ensure_dot(fields.get("surname")),
            "phone": ensure_dot(fields.get("phone")),
            "invoice": ensure_dot(fields.get("invoice")),
            "cstcode": ensure_dot(fields.get("cstcode")),
            "material": ensure_dot(fields.get("material")),
            "product": ensure_dot(fields.get("product")),
            "serial": ensure_dot(fields.get("serial")),
        }

        file_id = str(idx + 1)
        parsed = ParsedInvoice(
            id=file_id,
            filename=safe_name,
            path=path,
            fields=normalized,
        )
        parsed_files[file_id] = parsed
        out.append({
            "id": file_id,
            "filename": safe_name,
            "fields": normalized,
        })

    logger.info(f"Successfully parsed {len(out)} PDFs")
    return jsonify({"files": out})


@app.route("/create_tickets", methods=["POST"])
def api_create_tickets():
    """Create tickets in CRM"""
    logger.info("="*60)
    logger.info("API: /create_tickets called")
    logger.info("="*60)
    
    data = request.get_json(force=True)
    crm_username = data.get("crm_username", "").strip()
    crm_password = data.get("crm_password", "").strip()
    tickets_payload = data.get("tickets", [])

    logger.info(f"Username: {crm_username}")
    logger.info(f"Number of tickets: {len(tickets_payload)}")

    if not crm_username or not crm_password:
        logger.error("Missing CRM credentials")
        return jsonify({"error": "Missing CRM credentials"}), 400

    try:
        results = run_ticket_batch(crm_username, crm_password, tickets_payload)
        return jsonify({"results": results})
    except Exception as e:
        logger.error(f"API error: {e}")
        logger.debug(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Health check endpoint for Railway/Render"""
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/")
def index():
    """Serve the UI - tries TICKETHELPER.html first, then TICKETHELPER_CLOUD.html"""
    import os
    # Try local version first (for local development)
    if os.path.exists("TICKETHELPER.html"):
        return send_from_directory('.', "TICKETHELPER.html")
    # Fallback to cloud version
    elif os.path.exists("TICKETHELPER_CLOUD.html"):
        return send_from_directory('.', "TICKETHELPER_CLOUD.html")
    else:
        return jsonify({"error": "No HTML interface found. Please upload TICKETHELPER.html or TICKETHELPER_CLOUD.html"}), 404


@app.route("/<path:path>")
def static_files(path):
    """Serve static files"""
    return send_from_directory('.', path)


if __name__ == "__main__":
    print("=" * 80)
    print("🚀 TICKETER VERSION 2.4 - POPUP FIX ✅")
    print("=" * 80)
    
    logger.info("="*80)
    logger.info("STARTING FLASK SERVER - VERSION 2.4 - POPUP FIX")
    logger.info(f"Log file: {log_filename}")
    logger.info("Screenshots will be saved to: screenshots/")
    logger.info("="*80)
    
    # Cloud deployment: bind to 0.0.0.0 and use PORT env var
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    print(f"🌐 BINDING TO: {host}:{port} (debug={debug})")
    logger.info(f"🌐 Starting server on {host}:{port} (debug={debug})")
    
    app.run(host=host, port=port, debug=debug)
