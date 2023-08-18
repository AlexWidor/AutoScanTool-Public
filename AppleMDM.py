import requests


# Create a session with the given cookie
def create_session(cookie):
    from configmanager import HEADERS
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update({'Cookie': cookie})
    return session

# Send the serial number to the MDM server, return True if the request was successful
def send_to_mdm(session, serial_number, school_id, config):
    from configmanager import MDM_URL, HEADERS
    body = {
        "items": [{"client_id": str(school_id), "data": {"serial_number": serial_number}}],
        "operation_data": {"target_server_uid": str(school_id)}
    }
    response = session.post(MDM_URL, headers=HEADERS, json=body)
    response_data = response.json()
    if "data" in response_data and "uid" in response_data["data"]:
        # print(f"Success: {response.text}")
        return True, session
    else:
        print(f"Error: {response.text}")
        return False, session


def fetch_schools(session, config):
    from configmanager import SCHOOLS_URL
    data = {"sort_by": [{"sort_key": "server-name", "direction": "asc"}]}
    response = session.post(SCHOOLS_URL, json=data)
    if response.status_code == 200:
        response_data = response.json()
        data_body = response_data.get('data_body', [])
        return [(school_data[1], school_data[0]) for school_data in data_body], session
    else:
        return [], session

def fetch_auth_cookie(apple_id: str, apple_password: str):
    import json, os
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.dirname(os.path.abspath(__file__))
    from playwright.sync_api import Playwright, sync_playwright

    print("Haben Sie einen Moment Geduld...")
    print("Bitte nicht mit dem Browser interagieren.")

    def load_cookies(context):
        try:
            with open('cookies.json', 'r') as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
        except FileNotFoundError:
            pass

    def sign_in(page, apple_id, apple_password):
        try:
            if page.locator("#auth-container").is_visible():
                iframe_element_handle = page.locator("#aid-auth-widget-iFrame").element_handle()
                iframe = iframe_element_handle.content_frame()
                iframe.locator("#account_name_text_field").click()
                iframe.locator("#account_name_text_field").fill(apple_id)
                iframe.wait_for_timeout(1000)
                iframe.locator("#account_name_text_field").press("Enter")

                iframe.locator("#password_text_field").click()
                iframe.locator("#password_text_field").fill(apple_password)
                iframe.wait_for_timeout(1000)
                iframe.locator("#password_text_field").press("Enter")

            else:
                print("Not found")
                
        except:
            pass

    def two_factor_auth(page):
        if page.locator("#auth-container").is_visible():
            iframe_element_handle = page.locator("#aid-auth-widget-iFrame").element_handle()
            iframe = iframe_element_handle.content_frame()
            
            while True:
                sms_code = input("Enter SMS Code: ")
                if len(sms_code) != 6:
                    print("Ungültiger Code. Er sollte 6 Ziffern lang sein. Bitte erneut versuchen.")
                    continue
                for i, digit in enumerate(sms_code, start=0):  # start from 0 as index is 0-based
                    print(i, digit)
                    iframe.fill(f'#char{i}', digit)  # replace '#char{i}' with the actual selector of your input field
                break
            
            iframe.wait_for_timeout(1000)
            iframe.get_by_role("button", name="Vertrauen", exact=True).click()

        else:
            pass

    def save_cookies(context):
        cookies = context.cookies()
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f)

    def extract_auth_cookies(context):
        cookies = context.cookies()
        return '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies if cookie['name'] in ['myacinfo', 'apple_eesession']])

    def run(playwright: Playwright) -> None:
        import pygetwindow

        with playwright.chromium.launch(headless=False) as browser:  # Headless mode is not supported by Apple
            with browser.new_context(locale="de-DE", timezone_id="Europe/Berlin") as context:
                load_cookies(context)

                page = context.new_page()

                # Minimize the browser window
                window = pygetwindow.getWindowsWithTitle('Chromium')[0]
                window.minimize()

                page.goto("https://school.apple.com/", wait_until="domcontentloaded")

                sign_in(page, apple_id, apple_password)
                two_factor_auth(page)
                
                page.wait_for_load_state("networkidle", timeout=10000)
                
                save_cookies(context)
                auth_cookies = extract_auth_cookies(context)

                return auth_cookies
    
    with sync_playwright() as playwright:
        return run(playwright)
