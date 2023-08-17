import sys, asyncio, os

# Set enviroment table to empty to use chromium bundled with pyinstaller
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = ''

class IServManager:
    def __init__(self):
        from AutoIserv import AutoIserv
        from AppleMDM import create_session, fetch_schools, send_to_mdm
        from configmanager import load_config
        from inputmanager import InputManager

        self.iserv = AutoIserv()
        self.cfg, _ = load_config()
        self.cookie = InputManager().get_cookie()
        self.session = create_session(self.cookie)
        self.schools, self.session = fetch_schools(self.session, self.cfg)
        self.send_to_mdm = send_to_mdm
        self.input_manager = InputManager()
        self.timer_task = None

    async def process_barcode(self):
        while True:
            input_barcode = await asyncio.get_event_loop().run_in_executor(None, input, "Scan-Barcode (oder 'exit' eingeben, um zu beenden): ")
            if input_barcode.lower() == 'exit':
                await self.iserv.close()
                break

            # Check if the barcode is valid
            if not input_barcode.startswith('S') and len(input_barcode.split(' ')) != 11:
                print("\033[91mUngültiger Barcode. Er sollte mit 'S' beginnen und 11 Wörter lang sein.\033[0m")
                continue

            serial_number = input_barcode[1:]


            # TODO: This should be moved to a separate function
            import csv
            import datetime

            # Get current time
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Get school name
            school_name = self.selected_school[0]  # Extract the school name from the tuple

            # Prepare data
            data = [school_name, serial_number, current_time]



            # Check if output.csv ex    ists, if not, create it
            if not os.path.isfile('output.csv'):
                with open('output.csv', 'w') as file:
                    pass

            # Check if serial number is already in CSV
            with open('output.csv', 'r') as file:
                reader = csv.reader(file)
                if any(serial_number in row for row in reader):
                    print(f"Seriennummer {serial_number} existiert bereits. Übersprungen.")
                    print(f"Manuell im CSV entfernen, um erneut zu scannen. (WIP)")
                    sys.stdout.write('\033[2K\033[1G')
                else:
                    # Send to MDM
                    
                    # Get status and result, assign result to self.session
                    # It is important to use selected_school[1] instead of selected_school[0] because the first element is the school name
                    status, result = self.send_to_mdm(self.session, serial_number, self.selected_school[1], self.cfg)

                    # Check if result is a session object before assigning it to self.session
                    if isinstance(result, type(self.session)):
                        self.session = result

                    # Check status for error handling
                    if status:
                        print(f"\033[92mSeriennummer {serial_number} erfolgreich an Apple MDM gesendet.\033[0m")
                    else:
                        print(f"\033[91mFehler beim Senden der Seriennummer {serial_number} an Apple MDM.\033[0m")
                        await self.iserv.close()
                        break
                    
                    # Implement counter
                    if 'counter' not in globals():
                        global counter
                        counter = 1
                    else:
                        counter += 1
                    print(f"{counter} Barcodes processed.")
                
                    # Write data to CSV
                    with open('output.csv', 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([data[0], data[1], data[2]])
                    # TODO: End of function
            


            if self.timer_task:
                self.timer_task.cancel()
            self.timer_task = asyncio.create_task(self.wait_and_press())

    async def wait_and_press(self):
        await asyncio.sleep(30.0)
        await self.iserv.press_DEP()

        sys.stdout.write('\033[2K\033[1G')
        print("\033[94mDEP Profile zugewiesen.\033[0m")
        print("Warte auf Barcode ('exit' eingeben, um zu beenden): ", end='', flush=True)

def main():
    import pygetwindow
    manager = IServManager()
    
    selected_school_index = manager.input_manager.get_school_selection(manager.session, manager.cfg)
    manager.selected_school = manager.schools[selected_school_index]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager.iserv.start())

    window = pygetwindow.getWindowsWithTitle('Chromium')[0]
    window.minimize()
    loop.run_until_complete(manager.iserv.login())
    loop.run_until_complete(manager.process_barcode())

if __name__ == "__main__":
    main()