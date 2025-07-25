import os, time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from .ps_utils import ps_target_frame, ps_find_retry

load_dotenv()  # Load .env into environment

USERNAME = os.getenv("PEOPLESOFT_USERNAME")
PASSWORD = os.getenv("PEOPLESOFT_PASSWORD")
TEST = 'no'
print(f"Using test mode: {TEST}")
if TEST == 'yes':
    PS_BASE_URL = os.getenv("PEOPLESOFT_TEST_ENV", "https://kdhr92.hosted.cherryroad.com/")
else:
    PS_BASE_URL = os.getenv("PEOPLESOFT_ENV")

print(f"Using username: {USERNAME}")

EMPLIDS = ['104457', '126538']  # Replace with target list of EMPLIDs or query them dynamically

def process_search_results(page, emplid):
    result_index = 1

    while True:
        print(f"📄 Processing result #{result_index} for EMPLID {emplid}")
        process_payline_rows(page, emplid)

        # Try clicking “Next in List”
        frame = ps_target_frame(page)
        try:
            # Active button
            next_result_btn = frame.get_by_role("button", name="Next in List")
            next_result_btn.click()
            page.wait_for_load_state('networkidle')
            result_index += 1
        except:
            # Inactive fallback: check if the "Next in List" is just an <a> with no click handler
            inactive_btn = frame.locator("a").filter(has_text="Next in List")
            if inactive_btn.count() > 0:
                print("Reached end of search results.")
                break
            else:
                raise Exception("❌ Could not find 'Next in List' navigation.")

def process_payline_rows(page, emplid):
    row_index = 0
    save_needed = False
    frame = ps_target_frame(page)

    while True:
        try:
            hours_field = ps_find_retry(page, f"PAY_OTH_EARNS_OTH_HRS$0")
            ok_box = ps_find_retry(page, f"PAY_EARNINGS_OK_TO_PAY$0")
            job_box = ps_find_retry(page, f"PAY_EARNINGS_JOB_PAY$0")
            
            hours = hours_field.input_value().strip()
            ok_is_checked = ok_box.is_checked()
            job_is_checked = job_box.is_checked()

            # Convert to float if possible
            numeric_hours = float(hours) if hours else 0.0

            print(f"{emplid} row {row_index}: Hours = '{hours}', OK to Pay = {ok_is_checked}")
            #TODO: Add a check for Reg Salary input box and it is populated, set to zero
            # If no hours but OK to Pay is checked → uncheck it
            if numeric_hours == 0 and ok_is_checked:
                print(f"→ Unchecking OK to Pay for row {row_index}")
                ok_box.uncheck()
                # addchg_win0 gets triggered automatically via onchange/onblur in PS
                save_needed = True
                #page.pause()  # Pause to allow any async changes to complete
            if numeric_hours == 0 and job_box.is_enabled() and job_is_checked:
                if job_box.is_checked():
                    print(f"→ Unchecking Job Pay box for row {row_index}")
                    job_box.uncheck()
                    save_needed = True
            else:
                print(f"⚠️ Job Pay box is disabled for row {row_index}, skipping.")
        except Exception as e:
            print(f"⚠️ Could not process row {row_index}: {e}")
            break  # No more rows likely

        # Check if "Show next row" is available
        active_next_btn = frame.get_by_role("button", name="Show next row")
        inactive_img = frame.get_by_role("img", name="Show next row (inactive")

        if active_next_btn.count() > 0:
            try:
                active_next_btn.first.click()
                # Wait for next row to render (we don’t want to pause long if unnecessary)
                ps_find_retry(page, f"PAY_EARNINGS_OK_TO_PAY${row_index + 1}", timeout=800)
                row_index += 1
            except Exception as e:
                print(f"⚠️ Failed to click 'Show next row': {e}")
                break
        elif inactive_img.count() > 0:
            print("🛑 'Show next row' is inactive — stopping row loop.")
            break
        else:
            print("⚠️ Could not determine next row control — stopping.")
            break
    
    # Save if we changed anything
    if save_needed:
        try:
            print("💾 Changes detected — saving...")
            save_button = frame.get_by_role("button", name="Save")
            save_button.click()
            page.wait_for_timeout(1000)
        except Exception as e:
            print(f"❌ Failed to click Save: {e}")

with sync_playwright() as p:
    t0 = time.time()
    print("Starting PeopleSoft uncheck bot...")
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(PS_BASE_URL)

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

        page.goto(PS_BASE_URL + "psp/KDHP92/EMPLOYEE/HRMS/c/MANAGE_PAYROLL_PROCESS_US.PAY_SHEET_LINE.USA?")
        page.wait_for_load_state('networkidle')

        # Fill in EMPLID
        ps_find_retry(page, "PAY_LINE_WORK_EMPLID").fill(emplid)
        # Press Enter to search
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        # Press Tab then enter to go to the first row result
        page.keyboard.press("Tab")
        page.keyboard.press("Enter")
        

        process_search_results(page, emplid)

    browser.close()
    t1 = time.time()
    print(f"✅ Uncheck bot completed in {t1 - t0:.2f} seconds.")
    print(f"Average time per EMPLID: {(t1 - t0) / len(EMPLIDS):.2f} seconds.")
    print("All done! 🎉")
