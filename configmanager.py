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
            print("Headless kann im config auf 'false' gesetzt werden, um den Browser beim Ausführen zu sehen.")
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

def save_credentials(iserv_username, iserv_password, iserv_admin_password, mdm_Apple_ID=None, mdm_password=None):
    try:
        with open("credentials.txt", 'w') as credfile:
            credfile.write(f"iserv_username: {iserv_username}\n")
            credfile.write(f"iserv_password: {iserv_password}\n")
            credfile.write(f"iserv_admin_password: {iserv_admin_password}\n")
    except Exception as e:
        print(f"Error saving IServ credentials: {e}")
    try:
        with open("credentials.txt", 'a') as credfile:
            credfile.write(f"mdm_Apple_ID: {mdm_Apple_ID}\n")
            credfile.write(f"mdm_password: {mdm_password}\n")
    except Exception as e:
        print(f"Error saving MDM credentials: {e}")
        
def load_iserv_credentials():
    iserv_username = None
    iserv_password = None
    iserv_admin_password = None
    try:
        with open("credentials.txt", 'r') as credfile:
            lines = credfile.readlines()
            iserv_username = lines[0].split(": ")[1].strip()
            iserv_password = lines[1].split(": ")[1].strip()
            iserv_admin_password = lines[2].split(": ")[1].strip()
    except Exception as e:
        raise

    return iserv_username, iserv_password, iserv_admin_password

def load_mdm_credentials():
    mdm_Apple_ID = None
    mdm_password = None
    try:
        with open("credentials.txt", 'r') as credfile:
            lines = credfile.readlines()
            mdm_Apple_ID = lines[3].split(": ")[1].strip()
            mdm_password = lines[4].split(": ")[1].strip()
    except FileNotFoundError:
        print("Info nicht gefunden. Bitte geben Sie Ihre ASM-Anmeldeinformationen ein.")
    except Exception as e:
        print(f"Error loading MDM credentials: {e}")
        raise

    return mdm_Apple_ID, mdm_password