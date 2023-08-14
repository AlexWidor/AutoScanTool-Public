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
    from configmanager import MDM_URL
    body = {
        "items": [{"client_id": school_id, "data": {"serial_number": serial_number}}],
        "operation_data": {"target_server_uid": school_id}
    }
    response = session.post(MDM_URL, json=body)
    return response.status_code == 200, session  # Return True if the request was successful

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
            time.sleep(1)
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Sign in with your Apple ID").press("Enter")
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Password").click()
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Password").fill(apple_password)
            time.sleep(1)
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label("Password").press("Enter")
            if page.frame_locator("iframe[name=\"aid-auth-widget\"]").locator("#sign_in_form").is_visible():
                page.frame_locator("iframe[name=\"aid-auth-widget\"]").locator("#sign_in_form").click()
        else:
            print("No sign in form found")

    def two_factor_auth(page):
        if page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_role("heading", name="Two-factor authentication").is_visible():
            sms_code = input("Please enter the SMS code: ")
            for i, digit in enumerate(sms_code, start=1):
                page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_label(f"Digit {i}").fill(digit)
            page.frame_locator("iframe[name=\"aid-auth-widget\"]").get_by_role("button", name="Trust", exact=True).click()
        else:
            print("No two-factor authentication form found")

    def save_cookies(context):
        cookies = context.cookies()
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f)

    def extract_auth_cookies(context):
        cookies = context.cookies()
        return '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies if cookie['name'] in ['myacinfo', 'apple_eesession']])

    def run(playwright: Playwright) -> None:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()

        load_cookies(context)

        page = context.new_page()
        page.goto("https://school.apple.com/")
        
        time.sleep(5)
        sign_in(page, apple_id, apple_password)
        time.sleep(5)
        two_factor_auth(page)

        page.goto("https://school.apple.com/#/main/users")

        save_cookies(context)
        auth_cookies = extract_auth_cookies(context)

        context.close()
        browser.close()

        return auth_cookies

    with sync_playwright() as playwright:
        return run(playwright)

if __name__ == '__main__':
    fetch_auth_cookie('apple_id', 'apple_password')