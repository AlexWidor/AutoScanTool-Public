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

def fetch_auth_cookie():
    import json, os
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.dirname(os.path.abspath(__file__))
    from playwright.sync_api import Playwright, sync_playwright

    print("Bitte logge dich im ASM ein. Der Browser wird automatisch geschlossen, sobald die Cookies gespeichert wurden.")

    def load_cookies(context):
        try:
            with open('cookies.json', 'r') as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
        except FileNotFoundError:
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
            with browser.new_context(locale="de-DE", timezone_id="Europe/Berlin") as context:
                load_cookies(context)

                page = context.new_page()
                page.goto("https://school.apple.com/", wait_until="networkidle")

                # Make really sure that the page is loaded to get cookies
                page.wait_for_timeout(3000)
                page.wait_for_load_state("domcontentloaded")
                
                # Wait for the element with id "cw-aria-live-region" to load
                page.frame_locator("iframe[name=\"MainPortal\"]").get_by_label("Geräte", exact=True).click(timeout=0) 
                

                auth_cookies = extract_auth_cookies(context)
                if auth_cookies is None:
                    print("Fehler beim Abrufen der Authentifizierungs-Cookies. Bitte gib diese manuell ein.")
                    auth_cookies = input("Cookie eingeben: ")
                    return auth_cookies
                else:
                    save_cookies(context)
                    return auth_cookies
    
    with sync_playwright() as playwright:
        return run(playwright)
    
if __name__ == '__main__':
    fetch_auth_cookie()