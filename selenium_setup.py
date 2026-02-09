# -*- coding: utf-8 -*-
"""
Railway-compatible Selenium Chrome setup with configurable headless mode
FIXED: Added critical flags for Railway environment
"""
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)


def get_chrome_driver(headless=True):
    """
    Get Chrome WebDriver configured for Railway deployment
    
    Args:
        headless: Run headlessly (True) or with GUI (False) for debugging
    
    Returns:
        Configured Chrome WebDriver instance
    """
    logger.info(f"Initializing Chrome WebDriver (headless={headless})...")
    
    chrome_options = Options()
    
    # Headless configuration
    if headless:
        chrome_options.add_argument('--headless=new')  # New headless mode
        chrome_options.add_argument('--disable-gpu')
        logger.info("Running in headless mode")
    else:
        chrome_options.add_argument("--start-maximized")
        logger.info("Running in headed mode")
    
    # CRITICAL: Essential arguments for Railway/containerized environments
    chrome_options.add_argument('--no-sandbox')  # CRITICAL for Docker
    chrome_options.add_argument('--disable-dev-shm-usage')  # CRITICAL for limited /dev/shm
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-setuid-sandbox')  # Additional sandbox bypass
    
    # Additional stability flags for Railway
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--single-process')  # Run in single process mode
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-breakpad')
    chrome_options.add_argument('--disable-client-side-phishing-detection')
    chrome_options.add_argument('--disable-component-extensions-with-background-pages')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-ipc-flooding-protection')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_argument('--metrics-recording-only')
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--no-zygote')  # CRITICAL for single process
    
    # Performance optimizations
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--silent')
    
    # Anti-detection features (from original code)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-notifications')
    
    # User agent to avoid detection
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Window size for consistent rendering
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Binary location - Railway uses system Chrome
    chrome_bin = os.getenv('GOOGLE_CHROME_BIN', '/usr/bin/google-chrome')
    if os.path.exists(chrome_bin):
        chrome_options.binary_location = chrome_bin
        logger.info(f"Using Chrome binary: {chrome_bin}")
    else:
        logger.info("Using default Chrome binary (system will find it)")
    
    # ChromeDriver path - Railway uses system chromedriver
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')
    
    try:
        # Try with explicit path first
        if os.path.exists(chromedriver_path):
            service = Service(
                executable_path=chromedriver_path,
                log_path='/tmp/chromedriver.log'  # Verbose logging for debugging
            )
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info(f"Chrome driver initialized with path: {chromedriver_path}")
        else:
            # Fallback: let selenium find it
            logger.info("ChromeDriver not found at expected path, using auto-detection")
            service = Service(log_path='/tmp/chromedriver.log')
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver initialized with auto-detection")
        
        # Set page load timeout
        driver.set_page_load_timeout(120)
        
        logger.info("✓ Chrome WebDriver initialized successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to initialize Chrome driver: {e}")
        # Log chromedriver verbose output if available
        try:
            with open('/tmp/chromedriver.log', 'r') as f:
                logger.error(f"ChromeDriver log:\n{f.read()}")
        except:
            pass
        raise


def get_driver_from_env():
    """
    Get driver based on HEADLESS environment variable
    
    Set HEADLESS=false in Railway for debugging (won't show browser but helps troubleshooting)
    Default is headless mode (HEADLESS=true or not set)
    """
    headless_str = os.getenv('HEADLESS', 'true').lower()
    headless = headless_str in ('true', '1', 'yes')
    
    logger.info(f"HEADLESS env var: '{headless_str}' -> headless={headless}")
    return get_chrome_driver(headless=headless)


if __name__ == '__main__':
    # Test the setup
    print("\n" + "="*60)
    print("Testing Chrome driver setup...")
    print("="*60 + "\n")
    
    driver = get_driver_from_env()
    print(f"✓ Driver created successfully")
    print(f"✓ Chrome version: {driver.capabilities['browserVersion']}")
    print(f"✓ ChromeDriver version: {driver.capabilities['chrome']['chromedriverVersion'].split()[0]}")
    
    driver.get('https://www.google.com')
    print(f"✓ Loaded page: {driver.title}")
    
    driver.quit()
    print("\n✓ Test completed successfully\n")