# Diese Klasse ist für die Interaktion mit IServ zuständig (Anmelden, Geräte hinzufügen, etc.)
from inputmanager import InputManager
from configmanager import load_config
from playwright.async_api import async_playwright
import asyncio

import atexit
import asyncio
from inputmanager import InputManager
from configmanager import load_config
from playwright.async_api import async_playwright

class AutoIserv:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        _, self.headless = load_config()

        # Register the cleanup function
        atexit.register(self.cleanup)

    def cleanup(self):
        if self.context:
            asyncio.run(self.context.close())
        if self.browser:
            asyncio.run(self.browser.close())
        if self.playwright:
            asyncio.run(self.playwright.stop())

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def login(self):
        input_manager = InputManager()  # Create an instance of InputManager

        await self.page.goto(input_manager.get_iserv_url())  # Go to IServ login page

        # Get credentials from user
        self.iserv_username, self.iserv_password, self.iserv_admin_password = input_manager.get_iserv_credentials()

        # Login to IServ
        await self.page.get_by_placeholder("Account").click()
        await self.page.get_by_placeholder("Account").fill(self.iserv_username)
        await self.page.get_by_placeholder("Account").press("Tab")
        await self.page.get_by_placeholder("Passwort").fill(self.iserv_password)
        await self.page.get_by_role("button", name=" Anmelden").click()
        await self.page.locator("#admin_login_form_password").click()
        await self.page.locator("#admin_login_form_password").fill(self.iserv_admin_password)
        await self.page.get_by_role("button", name=" Anmelden").click()


    async def press_DEP(self):
        await self.page.get_by_role("link", name=" DEP-Profile zuweisen").click()

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def run(self):
        await self.start()
        await self.login()
        input("Enter drücken, um das Programm zu beenden.")
        await self.close()

if __name__ == "__main__":
    auto_iserv = AutoIserv()
    asyncio.run(auto_iserv.run())
