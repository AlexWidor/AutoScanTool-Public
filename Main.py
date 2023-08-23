import asyncio, os

# Set enviroment table to empty to use chromium bundled with pyinstaller
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.dirname(os.path.abspath(__file__))

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


    async def process_barcode(self, total_barcodes=60):
        # Import necessary modules
        from alive_progress import alive_bar
        import os, csv, datetime
        
        invalid = None
        skipped = None
        last_serial = None
        
        # Initialize progress bar
        with alive_bar(total_barcodes) as bar:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')  # Clear console
                
                # Display last scanned serial
                if invalid:
                    bar.text("\033[91mUngültiger Barcode. Er sollte mit 'S' beginnen und 11 Wörter lang sein.\033[0m")

                elif skipped:
                    bar.text("Seriennummer übersprungen, bereits vorhanden.")
        
                elif last_serial:
                    bar.text(f'Letzte gescannte Seriennummer: {last_serial}')
                
                # Get barcode input
                input_barcode = await asyncio.get_event_loop().run_in_executor(None, input, '')
                
                # Exit condition
                if input_barcode.lower() == 'exit':
                    await self.iserv.close()
                    break

                # Validate barcode
                if not input_barcode.startswith('S') and len(input_barcode.split(' ')) != 11:
                    invalid = True
                    continue
                else:
                    invalid = False

                # Extract and update serial number
                serial_number = input_barcode[1:]
                last_serial = serial_number  

                # Prepare data for CSV
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                school_name = self.selected_school[0]
                data = [school_name, serial_number, current_time]

                # Check if serial number already exists in CSV
                if not os.path.isfile('output.csv'):
                    with open('output.csv', 'w') as file:
                        pass

                with open('output.csv', 'r') as file:
                    reader = csv.reader(file)
                    if any(serial_number in row for row in reader):
                        skipped = True
                    else:
                        skipped = False

                        # Send serial number to MDM
                        status, result = self.send_to_mdm(self.session, serial_number, self.selected_school[1], self.cfg)

                        # Update session if necessary
                        if isinstance(result, type(self.session)):
                            self.session = result

                        # Handle unsuccessful send
                        if not status:
                            print(f"\033[91mFehler beim Senden der Seriennummer {serial_number} an Apple MDM.\033[0m")
                            await self.iserv.close()
                            break
                        
                        # Write data to CSV
                        with open('output.csv', 'a', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow(data)
                        print("Wrote")
                        bar()

                        # Reset timer task
                        if self.timer_task:
                            self.timer_task.cancel()
                        self.timer_task = asyncio.create_task(self.wait_and_press())
                
    async def wait_and_press(self):
        await asyncio.sleep(30.0)
        await self.iserv.press_DEP()

        print("\033[94mDEP Profile zugewiesen.\033[0m")
def main():
    manager = IServManager()
    
    selected_school_index = manager.input_manager.get_school_selection(manager.session, manager.cfg)
    manager.selected_school = manager.schools[selected_school_index]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager.iserv.start())

    loop.run_until_complete(manager.iserv.login())
    loop.run_until_complete(manager.process_barcode())

if __name__ == "__main__":
    main()