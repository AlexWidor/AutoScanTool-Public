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
            print("Headless kann im config auf 'false' gesetzt werden")
            ymlfile.write("headless: true\n")
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