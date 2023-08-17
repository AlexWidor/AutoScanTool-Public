class InputManager:
    def __init__(self):
        from configmanager import CredentialManager
        self.user_inputs = {}
        self.masterpassword = None
        self.credential_manager = CredentialManager()

    def get_masterpassword(self):
        import getpass
        if self.masterpassword is None:
            self.masterpassword = getpass.getpass("Bitte geben Sie Ihr Masterpasswort ein: ")
        return self.masterpassword

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

    def get_mdm_credentials(self):
        import os

        # Get the master password
        self.masterpassword = self.get_masterpassword()

        # Check if credentials file exists
        if not os.path.exists("credentials.txt") or os.path.getsize("credentials.txt") == 0:
            # If not, create an empty file
            with open('credentials.txt', 'w') as f:
                f.write('')
            MDM_APPLE_ID = input("ASM-Apple-ID: ")
            MDM_PASSWORD = input("ASM-Passwort: ")
        else:
            # Try to load credentials
            MDM_APPLE_ID, MDM_PASSWORD, _, _, _  = self.credential_manager.load_credentials(self.masterpassword)

            # If credentials are not found, ask the user for them
            if MDM_APPLE_ID is None or MDM_PASSWORD is None:
                MDM_APPLE_ID = input("ASM-Apple-ID: ")
                MDM_PASSWORD = input("ASM-Passwort: ")

        # Save the entered credentials
        self.credential_manager.save_credentials(self.masterpassword, MDM_APPLE_ID, MDM_PASSWORD)

        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')

        return MDM_APPLE_ID, MDM_PASSWORD
    
    def get_iserv_url(self):
        import re

        url = input("Bitte geben Sie die IServ-URL Ihrer Schule ein: ")
        match = re.search(r'(https://.*?/iserv)', url)
        if match:
            self.user_inputs['iserv_url'] = match.group(1) + '/admin/mdm/ios/dep'
        else:
            print("Die eingegebene URL entspricht nicht dem erwarteten Format. Bitte stellen Sie sicher, dass die URL mit 'https://' beginnt und '/iserv' enthält.")
            self.user_inputs['iserv_url'] = None

        return self.user_inputs['iserv_url']

    def get_save_iserv(self):
        self.user_inputs['save_iserv'] = input("Möchten Sie Ihre IServ-Anmeldeinformationen speichern? (j/N): ")
        return self.user_inputs['save_iserv'].lower() in ['j', 'y']

    def get_save_mdm(self):
        self.user_inputs['save_mdm'] = input("Möchten Sie Ihre MDM-Anmeldeinformationen speichern? (j/N): ")
        return self.user_inputs['save_mdm'].lower() in ['j', 'y']

    def get_school_selection(self, session, config):
        from AppleMDM import fetch_schools
        from configmanager import load_config, save_config
        import os

        # Load the previously selected school from the config and fetch all schools
        cfg, _ = load_config()
        previous_school_idx = cfg.get('selected_school_idx', None)
        schools, session = fetch_schools(session, config)

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
        save_config({'selected_school_idx': self.user_inputs['selected_school_idx']})
        return self.user_inputs['selected_school_idx']
    
    def get_cookie(self):
        import requests
        from configmanager import load_config, save_config
        from AppleMDM import fetch_auth_cookie
        
        config, _ = load_config()
        cookie = config.get('cookie', None)
        if cookie is not None:
            try:
                response = requests.post("https://ws.school.apple.com/devices/ee/org/servers/filtered", cookies={'cookie': cookie})
                response.raise_for_status()
                print("Cookie is valid.")
            except Exception as err:
                print(err)
                print("Cookie is not valid. Fetching a new one...")
                apple_id, apple_password = self.get_mdm_credentials()
                cookie = fetch_auth_cookie(apple_id, apple_password)
                if cookie is None:
                    print("Failed to fetch a new cookie. Please enter it manually.")
                    cookie = input("Please enter the cookie: ")
                config['cookie'] = cookie
                save_config(config)
        else:
            print("No cookie found in config. Fetching a new one...")
            apple_id, apple_password = self.get_mdm_credentials()
            cookie = fetch_auth_cookie(apple_id, apple_password)
            if cookie is None:
                print("Failed to fetch a new cookie. Please enter it manually.")
                cookie = input("Please enter the cookie: ")
            config['cookie'] = cookie
            save_config(config)
        
        return cookie
        

