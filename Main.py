import asyncio, atexit, os, yaml, requests
from playwright.async_api import async_playwright

class ConfigManager:
    """Manages configuration settings."""

    @staticmethod
    def load_config(key):
        """Loads configuration from YAML file, creates it if not existing."""
        default_config = {
            "headless": False,
            "school_id": None,
            "cookie": None,
            "mdm_url": "https://ws.school.apple.com/devices/ee/devices/v2/device/batch/assign",
            "schools_url": "https://ws.school.apple.com/devices/ee/org/servers/filtered",
            "headers": {
                "accept": "*/*",
                "accept-language": "en-gb",
                "content-type": "text/plain;charset=UTF-8",
                "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"115\", \"Chromium\";v=\"115\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "Referer": "https://school.apple.com/"
            }
        }

        if not os.path.exists("config.yaml"):
            with open("config.yaml", 'w') as ymlfile:
                print("First time setup: Creating config.yaml")
                print("Headless kann im config umgeschaltet werden")
                yaml.safe_dump(default_config, ymlfile)
        
        with open("config.yaml", 'r') as ymlfile:
            cfg = yaml.safe_load(ymlfile)

        # Check if all keys in default_config exist in the loaded config
        for k, v in default_config.items():
            if k not in cfg:
                cfg[k] = v

        # Save the updated config back to the file
        with open("config.yaml", 'w') as ymlfile:
            yaml.safe_dump(cfg, ymlfile)

        return cfg.get(key, None)
    
    @staticmethod
    def save_config(key, value):
        """Saves a configuration value to the YAML file."""
        with open("config.yaml", 'r') as ymlfile:
            cfg = yaml.safe_load(ymlfile)

        # Update the config value
        cfg[key] = value

        # Save the updated config back to the file
        with open("config.yaml", 'w') as ymlfile:
            yaml.safe_dump(cfg, ymlfile)
    

class InputManager:
    def __init__(self):
        self.user_inputs = {}


    def get_iserv_credentials(self):
        import os
        self.user_inputs['iserv_username'] = input("Bitte geben Sie Ihren IServ-Benutzernamen ein: ")
        self.user_inputs['iserv_password'] = input("Bitte geben Sie Ihr IServ-Passwort ein: ")
        self.user_inputs['iserv_admin_password'] = input("Bitte geben Sie Ihr IServ-Admin-Passwort ein (falls leer, wird das normale Passwort verwendet): ")
        if not self.user_inputs['iserv_admin_password']:
            self.user_inputs['iserv_admin_password'] = self.user_inputs['iserv_password']
            print("Admin-Passwort wurde nicht angegeben. Normales Passwort wird als Admin-Passwort verwendet.")

        # Save the entered credentials
        # self.credential_manager.save_credentials(self.masterpassword, self.user_inputs['iserv_username'], self.user_inputs['iserv_password'], self.user_inputs['iserv_admin_password'])
        os.system('cls' if os.name == 'nt' else 'clear')

        return self.user_inputs['iserv_username'], self.user_inputs['iserv_password'], self.user_inputs['iserv_admin_password']
    
    def get_iserv_url(self):
        import re

        url = input("IServ-URL Ihrer Schule eingeben: ")
        match = re.search(r'(https://.*?/iserv)', url)
        if match:
            self.user_inputs['iserv_url'] = match.group(1) + '/admin/mdm/ios/dep'
        else:
            print("Die eingegebene URL entspricht nicht dem erwarteten Format. Bitte stellen sicher, dass die URL mit 'https://' beginnt und '/iserv' enthält.")
            self.user_inputs['iserv_url'] = None

        return self.user_inputs['iserv_url']

    def get_school_selection(self, session):

        # Load the previously selected school from the config and fetch all schools
        previous_school_idx = ConfigManager.load_config("selected_school_idx")
        schools, session = AppleMDM.fetch_schools(session)

        # If a school was previously selected, ask the user if they want to continue with that
        if previous_school_idx is not None:
            print(f"Die zuvor ausgewählte Schule war: {schools[previous_school_idx][0]}")
            continue_with_previous = input("Möchten Sie mit dieser Schule fortfahren? (J/n): ")
            if continue_with_previous.lower() not in ['n']:
                return previous_school_idx

        # If no school was previously selected, or the user chose not to continue with it, list all schools
        for idx, school in enumerate(schools):
            print(f"{idx + 1}. {school[0]}")

        # Prompt the user to select a school and validate the input
        while True:
            school_number = input("Wählen Sie die Schule, indem Sie ihre Nummer eingeben: ")
            try:
                # Convert the input to an integer and adjust for zero-indexing
                self.user_inputs['selected_school_idx'] = int(school_number) - 1

                # Check if the selected school index is within the valid range
                if 0 <= self.user_inputs['selected_school_idx'] < len(schools):
                    break
                else:
                    print("Ungültige Eingabe. Bitte geben Sie eine gültige Schulnummer ein.")

            except ValueError:
                print("Ungültige Eingabe. Bitte geben Sie eine Zahl ein.")

        # Save the selected school index to the configuration
        ConfigManager.save_config('selected_school_idx', self.user_inputs['selected_school_idx'])
        return self.user_inputs['selected_school_idx']
    
    def get_cookie(self):
        import requests
        # Import load_config and save_config from configmanager class
        fetch_auth_cookie = AppleMDM.fetch_auth_cookie
        
        cookie = ConfigManager.load_config("cookie")
        if cookie is not None:
            try:
                response = requests.post("https://ws.school.apple.com/devices/ee/org/servers/filtered", cookies={'cookie': cookie})
                response.raise_for_status()
                print("Cookie ist gültig.")
            except Exception as err:
                print(err)
                print("Cookie ist nicht gültig. Ein neues wird abgerufen...")
                cookie = fetch_auth_cookie()
                if cookie is None:
                    print("Das Abrufen eines neuen Cookies ist fehlgeschlagen. Bitte gib es manuell ein.")
                    cookie = input("Cookie eingeben: ")
                ConfigManager.save_config("cookie", cookie)
        else:
            print("Kein Cookie in der Konfiguration gefunden. Ein neues wird abgerufen...")
            cookie = fetch_auth_cookie()
            if cookie is None:
                print("Das Abrufen eines neuen Cookies ist fehlgeschlagen. Bitte gib es manuell ein.")
                cookie = input("ookie eingeben: ")
            ConfigManager.save_config("cookie", cookie)
        
        return cookie

class AppleMDM:
    """Handles interactions with Apple MDM."""

    @staticmethod
    def create_session(cookie):
        session = requests.Session()
        session.headers.update(ConfigManager.load_config("headers"))
        session.cookies.update({'Cookie': cookie})
        return session

    @staticmethod
    def send_to_mdm(session, serial_number, school_id):
        body = {
            "items": [{"client_id": str(school_id), "data": {"serial_number": serial_number}}],
            "operation_data": {"target_server_uid": str(school_id)}
        }
        response = session.post(ConfigManager.load_config("mdm_url"), headers=ConfigManager.load_config("headers"), json=body)
        response_data = response.json()
        if "data" in response_data and "uid" in response_data["data"]:
            return True, session
        else:
            print(f"Error: {response.text}")
            return False, session

    @staticmethod
    def fetch_schools(session):
        data = {"sort_by": [{"sort_key": "server-name", "direction": "asc"}]}
        response = session.post(ConfigManager.load_config("schools_url"), json=data)
        if response.status_code == 200:
            response_data = response.json()
            data_body = response_data.get('data_body', [])
            return [(school_data[1], school_data[0]) for school_data in data_body], session
        else:
            return [], session

    @staticmethod
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


class AutoIserv:
    """Handles interactions with IServ."""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = ConfigManager.load_config("headless")

        # Register the cleanup function
        atexit.register(self.cleanup)

    def cleanup(self):
        """Cleans up resources."""
        asyncio.run(self._cleanup())

    async def _cleanup(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def start(self):
        """Starts the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(locale="de-DE", timezone_id="Europe/Berlin")
        self.page = await self.context.new_page()

    async def login(self):
        """Logs into IServ."""
        input_manager = InputManager()  # Create an instance of InputManager

        await self.page.goto(input_manager.get_iserv_url())  # Go to IServ login page

        # Get credentials from user
        self.iserv_username, self.iserv_password, self.iserv_admin_password = input_manager.get_iserv_credentials()

        # Fill in the credentials and click the login button, this might break if IServ changes the login page
        await self.page.get_by_placeholder("Account").click()
        await self.page.get_by_placeholder("Account").fill(self.iserv_username)
        await self.page.get_by_placeholder("Passwort").click()
        await self.page.get_by_placeholder("Passwort").fill(self.iserv_password)
        await self.page.get_by_role("button", name=" Anmelden").click()
        await self.page.locator("#admin_login_form_password").click()
        await self.page.locator("#admin_login_form_password").fill(self.iserv_admin_password)
        await self.page.get_by_role("button", name=" Anmelden").click()
        


    async def press_DEP(self):
        """Presses the DEP button."""
        await self.page.get_by_role("link", name=" DEP-Profile zuweisen").click()

    async def close(self):
        """Closes the browser."""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def run(self):
        """Runs the AutoIserv process."""
        await self.start()
        await self.login()
        input("Enter drücken, um das Programm zu beenden.")
        await self.close()

class Orchestrator:
    """Orchestrator class to manage the overall process."""
    

    def __init__(self):
        self.iserv = AutoIserv()
        self.cookie = InputManager().get_cookie()
        self.session = self.create_session(self.cookie)
        self.schools, self.session = self.fetch_schools(self.session)
        self.input_manager = InputManager()
        self.timer_task = None

    def create_session(self, cookie):
        """Creates a session with the given cookie."""
        session = requests.Session()
        session.headers.update(ConfigManager.load_config("headers"))
        session.cookies.update({'Cookie': cookie})
        return session

    def send_to_mdm(self, session, serial_number, school_id):
        """Sends the serial number to the MDM server."""
        body = {
            "items": [{"client_id": str(school_id), "data": {"serial_number": serial_number}}],
            "operation_data": {"target_server_uid": str(school_id)}
        }
        response = session.post(ConfigManager.load_config("mdm_url"), headers=ConfigManager.load_config("headers"), json=body)
        response_data = response.json()
        if "data" in response_data and "uid" in response_data["data"]:
            return True, session
        else:
            raise Exception(f"Error: {response.text}")


    def fetch_schools(self, session):
        """Fetches schools."""
        data = {"sort_by": [{"sort_key": "server-name", "direction": "asc"}]}
        response = session.post(ConfigManager.load_config("schools_url"), json=data)
        if response.status_code == 200:
            response_data = response.json()
            data_body = response_data.get('data_body', [])
            return [(school_data[1], school_data[0]) for school_data in data_body], session
        else:
            return [], session

    async def process_barcode(self, total_barcodes=0):
        from alive_progress import alive_bar
        import os, csv, datetime

        self.invalid = None
        self.skipped = None
        self.last_serial = None

        with open('output.csv', 'a+', newline='') as file, alive_bar(total_barcodes) as bar:
            writer = csv.writer(file)
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')

                self.display_bar_status(bar)

                input_barcode = await asyncio.get_event_loop().run_in_executor(None, input, '')

                if input_barcode.lower() == 'exit':
                    await self.iserv.close()
                    break

                if not self.is_valid_barcode(input_barcode):
                    self.invalid = True
                    continue
                else:
                    self.invalid = False

                serial_number = input_barcode[1:]
                self.last_serial = serial_number

                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                school_name = self.selected_school[0]
                data = [school_name, serial_number, current_time]

                reader = csv.reader(file)
                if any(serial_number in row for row in reader):
                    self.skipped = True
                    continue
                else:
                    self.skipped = False
                    await self.process_serial_number(serial_number, data, writer, bar)

    def display_bar_status(self, bar):
        if self.invalid:
            bar.text("\033[91mInvalid barcode. It should start with 'S' and be 11 words long.\033[0m")
        elif self.skipped:
            bar.text("Serial number skipped, already exists.")
        elif self.last_serial:
            bar.text(f'Last scanned serial number: {self.last_serial}')

    def is_valid_barcode(self, barcode):
        return barcode.startswith('S') and len(barcode.split(' ')) == 11

    async def process_serial_number(self, serial_number, data, writer, bar):
        status, result = self.send_to_mdm(self.session, serial_number, self.selected_school[1])

        if isinstance(result, type(self.session)):
            self.session = result

        if not status:
            print(f"\033[91mError sending serial number {serial_number} to Apple MDM.\033[0m")
            await self.iserv.close()
            return

        writer.writerow(data)
        print("Wrote")
        bar()

        if self.timer_task:
            self.timer_task.cancel()
        self.timer_task = asyncio.create_task

    async def wait_and_press(self):
        """Waits and presses the DEP button."""
        await asyncio.sleep(30)  # wait for 30 seconds
        await self.iserv.press_DEP()

def main():
    """Main function."""
    manager = Orchestrator()

    selected_school_index = manager.input_manager.get_school_selection(manager.session)
    manager.selected_school = manager.schools[selected_school_index]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager.iserv.start())
    loop.run_until_complete(manager.iserv.login())

    # Ask how many barcodes should be processed
    while True:
        try:
            total_barcodes = int(input('Wie viele Barcodes sollen verarbeitet werden? '))
            break
        except ValueError:
            print("Ungültige Eingabe. Bitte geben Sie eine Zahl ein.")
    loop.run_until_complete(manager.process_barcode(total_barcodes))

if __name__ == "__main__":
    main()