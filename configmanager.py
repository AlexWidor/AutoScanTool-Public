import os
import yaml

# Constants
MDM_URL = "https://ws.school.apple.com/devices/ee/devices/v2/device/batch/assign"
SCHOOLS_URL = "https://ws.school.apple.com/devices/ee/org/servers/filtered"
HEADERS = {
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

# Load configuration from YAML file, create if not existing
def load_config():
    if not os.path.exists("config.yaml"):
        with open("config.yaml", 'w') as ymlfile:
            print("First time setup: Creating config.yaml")
            print("Headless kann im config auf 'true' gesetzt werden")
            ymlfile.write("headless: false  # Wenn auf 'true' gesetzt, wird der Browser im Hintergrund ausgefuehrt\n")
            ymlfile.write("school_id: null\n")
            ymlfile.write("cookie: null\n")

    with open("config.yaml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    HEADLESS = cfg['headless']
    return cfg, HEADLESS

def save_config(config):
    with open("config.yaml", 'r') as ymlfile:
        existing_config = yaml.safe_load(ymlfile)

    # Update the existing config with the new config data
    existing_config.update(config)

    with open("config.yaml", 'w') as ymlfile:
        yaml.safe_dump(existing_config, ymlfile)

class CredentialManager:
    def __init__(self):
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64, os

        self.Fernet = Fernet
        self.hashes = hashes
        self.PBKDF2HMAC = PBKDF2HMAC
        self.base64 = base64
        self.os = os

    def get_key(self, masterpassword: str, salt: bytes):
        masterpassword = masterpassword.encode()
        kdf = self.PBKDF2HMAC(algorithm=self.hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key = self.base64.urlsafe_b64encode(kdf.derive(masterpassword))
        return key

    def save_credentials(self, masterpassword, iserv_username=None, iserv_masterpassword=None, iserv_admin_masterpassword=None, mdm_Apple_ID=None, mdm_masterpassword=None):
        salt = self.os.urandom(16)
        key = self.get_key(masterpassword, salt)
        f = self.Fernet(key)
        iserv_credentials = f"{iserv_username}\n{iserv_masterpassword}\n{iserv_admin_masterpassword}"
        encrypted_iserv_credentials = f.encrypt(iserv_credentials.encode())
        
        encrypted_mdm_credentials = b''  # Initialize as empty byte string

        if mdm_Apple_ID and mdm_masterpassword:
            mdm_credentials = f"{mdm_Apple_ID}\n{mdm_masterpassword}"
            encrypted_mdm_credentials = f.encrypt(mdm_credentials.encode())
        
        with open("credentials.txt", 'wb') as credfile:
            credfile.write(salt + encrypted_iserv_credentials + encrypted_mdm_credentials)

    def load_credentials(self, masterpassword):
        from cryptography.fernet import InvalidToken
        import sys
        from main import main

        try:
            with open("credentials.txt", 'rb') as credfile:
                data = credfile.read()
                salt, encrypted_credentials = data[:16], data[16:]
            key = self.get_key(masterpassword, salt)
            f = self.Fernet(key)

            # Decrypt and split credentials
            decrypted_credentials = f.decrypt(encrypted_credentials).decode().split('\n')

            # Assign iserv credentials
            iserv_username, iserv_password, iserv_admin_password = decrypted_credentials[:3]

            # Assign mdm credentials if they exist
            if len(decrypted_credentials) >= 5:
                mdm_Apple_ID, mdm_password = decrypted_credentials[3:5]
            else:
                mdm_Apple_ID, mdm_password = None, None

            return iserv_username, iserv_password, iserv_admin_password, mdm_Apple_ID, mdm_password
        except InvalidToken:
            os.system("cls")
            print("\033[91mUngültiges Passwort angegeben. Bitte versuchen Sie es erneut.\033[0m")
            
            main()