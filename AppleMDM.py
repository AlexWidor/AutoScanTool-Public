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
    import json, time
    from playwright.sync_api import Playwright, sync_playwright
    print("\033[91mBitte NICHT mit dem Browser interagieren!\033[0m")

    def load_cookies(context):
        try:
            with open('cookies.json', 'r') as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
        except FileNotFoundError:
            pass

    def sign_in(page, apple_id, apple_password):
        if page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_role("heading", name="Manage your organisation’s devices, apps and accounts.").is_visible():
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Sign in with your Apple ID").click(timeout=5000)
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Sign in with your Apple ID").fill(apple_id)
            page.wait_for_timeout(1000)
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Sign in with your Apple ID").press("Enter")
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Password").click()
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Password").fill(apple_password)
            page.wait_for_timeout(1000)
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Password").press("Enter")
            if page.frame_locator("iframe[name=\"aid-auth-widget\"]").locator("#sign_in_form").is_visible():
                page.frame_locator("iframe[name=\"aid-auth-widget\"]").locator("#sign_in_form").click()
        else:
            pass

    def two_factor_auth(page):
        if page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_role("heading", name="Two-factor authentication").is_visible():
            sms_code = input("SMS-Code eingeben: ")
            for i, digit in enumerate(sms_code, start=1):
                page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label(f"Digit {i}").fill(digit)
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_role("button", name="Trust", exact=True).click()
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
        with playwright.chromium.launch(headless=False) as browser:  # Headless mode is not supported by Apple
            with browser.new_context() as context:
                load_cookies(context)

                page = context.new_page()
                page.goto("https://school.apple.com/")
                
                page.wait_for_timeout(5000)
                sign_in(page, apple_id, apple_password)
                page.wait_for_timeout(5000)
                two_factor_auth(page)

                page.goto("https://school.apple.com/#/main/users")
                
                save_cookies(context)
                auth_cookies = extract_auth_cookies(context)

                return auth_cookies
    
    with sync_playwright() as playwright:
        return run(playwright)
