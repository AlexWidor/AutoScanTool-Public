# AutoASM

AutoASM is a Python-based automation tool designed to simplify the interaction process with IServ and the Apple School Manager (ASM). It utilizes the Playwright library to automate browser-based tasks on IServ and ASM.

## Features

- Provides a selection of schools from the Mobile Device Management (MDM) system for you to choose from.
- Operates autonomously, requiring no user intervention during the process.
- Awaits your barcode scan of an iPad to proceed with assignment.
- Records data in a CSV file for convenient access and archival.
- Counts unique entries to ensure accuracy.

## Getting Started


- Python 3.x
- Playwright library

### Installation

AutoASM can be utilized by executing the bundled executable (exe) file available in the releases section of the GitHub repository. This method simplifies the process and eliminates the need to worry about dependencies or setup.

For manual installation, the following prerequisites must be met:

# Prerequisites

1. Install the required Python packages by running the following command:
   ```
   pip install -r requirements.txt
   ```
2. Install the Chromium browser for Playwright with the following command:
   ```
   playwright install chromium
   ```
## Usage

1. **Execute the main script:** 
   - **Using the executable file:** Open the exe file, preferably in its own folder as it will create files.
   - **Using Python script:** Run the `main.py` script using Python. Make sure you are in the correct directory where `main.py` is located. Use the following command in your terminal:
   ```
   python main.py
   ```

2. **Input your credentials:** The script will prompt for your IServ and MDM credentials each time you run it.
    - For IServ, input your username, password, and admin password.
    - For MDM, input your Apple ID and password.

3. **Obtain cookies:** The script logs into Apple School Manager to obtain cookies. Avoid browser interaction during this process and follow console instructions.

4. **Select a school:** After fetching cookies, you will get a list of all schools in the MDM. Select your school in the Console. Your selection will be saved for quickstart on the next execution.

5. **Log into IServ:** The script will initiate a browser session and log into IServ.

6. **Wait for a barcode scan:** The script will then wait for a barcode scan. Typing 'exit' will close the browser session and terminate the script.

7. **Assign iPads:** Each scan sends the Serial Number to Apple MDM and starts a 10-second timer. After the timer executes, the iPads will be assigned using IServ.

## Limitations

- The script currently does not support loading and saving of credentials due to the lack of encryption implementation.
- Only 9th iPads are supported at the moment.

## Future Enhancements

- Implement encrypted password storage.
- Extend support to other iPad models.

## Changelog

- Automated retrieval of Apple-MDM cookies using Playwright. (Completed)
- Simplified IServ URLs input using Regex, considering a database as an alternative. (Completed, Database Ongoing)
