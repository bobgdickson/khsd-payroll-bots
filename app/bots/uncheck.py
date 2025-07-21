import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()  # Load .env into environment

USERNAME = os.getenv("PEOPLESOFT_USERNAME")
PASSWORD = os.getenv("PEOPLESOFT_PASSWORD")
print(f"Using username: {USERNAME}")
EMPLIDS = ['104457']  # Replace with your list

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

    page.wait_for_timeout(3000)
    page.goto("https://hcm.kernhigh.org/psp/KDHP92/EMPLOYEE/HRMS/c/MANAGE_PAYROLL_PROCESS_US.PAY_SHEET_LINE.USA")

    for emplid in EMPLIDS:
        # 1. Wait for the EMPLID input field  This is currently failing even though login works
        emplid_input = page.locator('input#PAY_LINE_WORK_EMPLID')
        emplid_input.wait_for()

        # 2. Fill in EMPLID
        emplid_input.fill(emplid)

        # 3. Simulate pressing Enter to trigger the search
        emplid_input.press("Enter")

        # Wait one second and then prese tab, then enter to select the first result
        page.wait_for_timeout(1000)
        page.keyboard.press("Tab")
        page.keyboard.press("Enter")

        # Or: click the search button directly if more reliable
        # page.click('input[name="PTS_CFG_CL_WRK_PTS_SRCH_BTN"]')

        # 4. Wait for search results to load (you'll need to adjust this to your UI)
        page.wait_for_selector('#PAY_EARNINGS_OK_TO_PAY\\$chk\\$0')

        # 5. Read checkbox and hours as before
        checkbox = page.locator('#PAY_EARNINGS_OK_TO_PAY\\$chk\\$0')
        hours_field = page.locator('#trPAY_OTH_EARNS\\$0_row1 td input').first

        print(f"{emplid}: Checked = {checkbox.is_checked()}, Hours = {hours_field.input_value()}")

    browser.close()
