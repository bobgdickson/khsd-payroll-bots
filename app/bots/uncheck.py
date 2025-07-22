import os, time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

load_dotenv()  # Load .env into environment

USERNAME = os.getenv("PEOPLESOFT_USERNAME")
PASSWORD = os.getenv("PEOPLESOFT_PASSWORD")
print(f"Using username: {USERNAME}")
EMPLIDS = ['104457', '151622']  # Replace with your list

def ps_target_frame(page):
    """Get the main PeopleSoft frame, usually 'TargetContent'."""
    return page.frame(name="TargetContent")

def ps_find(page, label_or_selector, timeout=5000):
    """
    Try to find an input inside PeopleSoft intelligently.
    - First tries get_by_role("textbox", name=label)
    - Then input[name=...] or input[id=...]
    - Then full recursive DOM crawl fallback (TODO: optional)
    """
    frame = ps_target_frame(page)

    # Try get_by_role with accessible name (label)
    try:
        locator = frame.get_by_role("textbox", name=label_or_selector)
        locator.wait_for(timeout=timeout)
        return locator
    except PlaywrightTimeoutError:
        pass

    # Try input[name=...] or id=...
    try:
        locator = frame.locator(f'input[name="{label_or_selector}"], input[id="{label_or_selector}"]')
        locator.wait_for(timeout=timeout)
        return locator
    except PlaywrightTimeoutError:
        pass

    # Optional: add full recursive fallback here if needed

    raise Exception(f"❌ Could not find '{label_or_selector}' using role or input name/id.")

def ps_find_retry(page, label_or_selector, timeout=5000, retries=3, delay=1):
    """
    Retry wrapper for ps_find in case frame is still refreshing or being detached.
    """
    for attempt in range(retries):
        try:
            return ps_find(page, label_or_selector, timeout)
        except Exception as e:
            print(f"Retry {attempt + 1} for '{label_or_selector}' (reason: {e})")
            time.sleep(delay)
    raise Exception(f"❌ Failed to find '{label_or_selector}' after {retries} attempts.")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://hcm.kernhigh.org")

    # Step 2: Wait and fill email
    page.wait_for_selector('input#i0116')
    page.fill('input#i0116', USERNAME)
    page.click('input[type="submit"]')  # "Next" button

    # Step 3: Wait and fill password
    page.wait_for_selector('input#i0118')
    page.fill('input#i0118', PASSWORD)
    page.click('input[type="submit"]')  # "Sign in" button

    page.wait_for_load_state('networkidle')

    for emplid in EMPLIDS:

        page.goto("https://hcm.kernhigh.org/psp/KDHP92/EMPLOYEE/HRMS/c/MANAGE_PAYROLL_PROCESS_US.PAY_SHEET_LINE.USA")
        page.wait_for_load_state('networkidle')

        if emplid == '151622':
            page.pause()  # Pause for debugging
        # Fill in EMPLID
        ps_find_retry(page, "PAY_LINE_WORK_EMPLID").fill(emplid)
        # Press Enter to search
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        # Press Tab then enter to go to the first row result
        page.keyboard.press("Tab")
        page.keyboard.press("Enter")
        

        # Check if OK to Pay box is checked
        ok_box = ps_find(page, "PAY_EARNINGS_OK_TO_PAY$0")
        print("OK to Pay:", ok_box.is_checked())

        # Get hours field value
        hours = ps_find(page, "PAY_OTH_EARNS_OTH_HRS$0").input_value()

        print(f"{emplid}: Checked = {ok_box.is_checked()}, Hours = {hours}")

    browser.close()
