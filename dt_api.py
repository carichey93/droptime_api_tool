import sys
from datetime import datetime as dt, timedelta
from pathlib import Path

import requests
import yaml
from requests.exceptions import RequestException
from ruamel.yaml import YAML

"""
Droptime API Interaction Module

This module is designed to facilitate interactions with the Droptime API, providing a set of functionalities for 
managing API sessions, making API calls, and processing the responses. It supports operations such as establishing new 
API sessions, fetching and refreshing session details, making generic API calls with automatic session management, and
specifically fetching and formatting dispatch data within a given date range.

Usage:
The module is intended to be used as a standalone script or imported into larger projects requiring interaction with 
the Droptime API. It expects command-line arguments specifying the start and end dates for dispatch data retrieval and 
the path to the configuration file when run as a script. Ensure the configuration file adheres to the required schema 
and includes all necessary authentication and identification fields.

Example command:
python droptime_api_module.py 2021-01-01 2021-01-31 path/to/config.yml
"""

BASE_URL = "https://api.droptime.net/API.aspx"

# Fields required from the YAML configuration file
REQUIRED_FIELDS = [
    "CompanyID",
    "Manager",
    "Passcode",
    "SessionID",
    "SessionPassword",
    "UserName",
]


def load_config(config_file: str) -> dict:
    """
    Load and validate configuration from a YAML file.

    Parameters:
    - config_file: Path to the YAML configuration file.

    Returns:
    - A dictionary containing the configuration data.
    """
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)
        if not all(field in config for field in REQUIRED_FIELDS):
            raise ValueError("Configuration file is missing required fields.")
    return config


def fetch_new_session(config: dict) -> dict:
    """
    Modified to handle connection errors and attempt to regenerate credentials.
    """
    try:
        session_params = {key: config[key] for key in REQUIRED_FIELDS if key in config}
        session_params["Method"] = "StartAPISession"
        response = requests.get(BASE_URL, params=session_params)
        response.raise_for_status()  # Ensure the API call was successful
        data = response.json()

        if "SessionInformation" not in data:
            raise ValueError(f"Unexpected API response: {data}")

        return data["SessionInformation"]
    except Exception as e:
        print(f"Connection error: {e}")
        raise


def update_config_file(config_file: str, updates: dict):
    """
    Update specific fields in a YAML configuration file using ruamel.yaml to preserve formatting.

    Parameters:
    - config_file: Path to the YAML configuration file.
    - updates: Dictionary containing the updates to apply.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(config_file, "r") as file:
        config = yaml.load(file)

    # Update only the specified fields
    for field in REQUIRED_FIELDS:
        if field in updates:
            config[field] = updates[field]

    with open(config_file, "w") as file:
        yaml.dump(config, file)


def get_or_refresh_session(config_file: str) -> dict:
    """
    Retrieve or refresh the session by either using existing session details or fetching a new session.

    Parameters:
    - config_file: Path to the YAML configuration file.

    Returns:
    - A dictionary containing the current session information.
    """
    config = load_config(config_file)
    session_info = fetch_new_session(config)
    config.update(session_info)
    update_config_file(config_file, config)
    return config


def make_api_call(
    method: str, start_date: str, end_date: str, config_file: str, attempt=1
) -> dict:
    """
    Make a generic API call, using the configuration loaded from the specified file. If an error code indicates
    that new credentials are needed, fetch a new session and retry.

    Parameters:
    - method: The API method to call.
    - start_date: Start date for the data request.
    - end_date: End date for the data request.
    - config_file: Path to the YAML configuration file where the API credentials and session details are stored.
    - attempt: Current attempt number, used to prevent infinite recursion.

    Returns:
    - The JSON response from the API call.
    """
    config = load_config(config_file)

    # Prepare the parameters for the API call
    api_params = {key: config[key] for key in REQUIRED_FIELDS if key in config}
    api_params.update({"Method": method, "StartTime": start_date, "EndTime": end_date})

    if "SessionID" in config and "SessionPassword" in config:
        api_params.update(
            {"SessionID": config["SessionID"], "SP": config["SessionPassword"]}
        )

    try:
        response = requests.get(BASE_URL, params=api_params)
        response.raise_for_status()  # Ensure the API call was successful
        data = response.json()

        # Check for an error code in the response
        if data.get("ErrorCode") == "1" and attempt <= 2:  # Prevents infinite recursion
            print(
                "Error code received indicating invalid credentials. Fetching new session..."
            )
            get_or_refresh_session(config_file)
            # Retry the API call with new credentials
            return make_api_call(method, start_date, end_date, config_file, attempt + 1)

        return data
    except RequestException as e:
        print(f"API call failed due to connection error: {e}")
        # In a real scenario, you might want to handle retries or log the error appropriately
        raise


def get_data(start_date: str, end_date: str, config_file: str) -> list:
    """
    Fetch and format dispatch data for a specified date range using the configuration from the given file.

    Parameters:
    - start_date: Start date for the dispatch data request.
    - end_date: End date for the dispatch data request.
    - config_file: Path to the YAML configuration file.

    Returns:
    - A list of dictionaries containing formatted dispatch data.
    """
    data = make_api_call("getDispatchInfo", start_date, end_date, config_file)
    return [reformat_dispatch(dispatch) for dispatch in data.get("Items", [])]


def reformat_dispatch(dispatch: dict) -> dict:
    """
    Reformat a single dispatch entry by extracting and reformatting details from the dispatch,
    including initial data, 'fields', and 'lineitems', into a more readable format.

    Parameters:
    - dispatch: A dictionary containing a single dispatch entry.

    Returns:
    - A dictionary with the reformatted dispatch entry.
    """

    # Initialize reformatted with initial data, excluding 'fields' and 'lineitems'
    initial_keys = [
        "shiftid",
        "startdatetime",
        "enddatetime",
        "dispatchnotes",
        "tph",
        "tpr",
        "totalsy",
    ]
    reformatted = {key: dispatch.get(key) for key in initial_keys if key in dispatch}

    # Process and reformat 'crew' if present
    crew_data = dispatch.get("crew", {})
    if (
        isinstance(crew_data, dict)
        and "firstname" in crew_data
        and "lastname" in crew_data
    ):
        reformatted["crew"] = f"{crew_data['firstname']} {crew_data['lastname']}"

    # Process 'fields' list to extract each item and convert into key-value pairs
    for field in dispatch.get("fields", []):
        catname = field.get("catname")
        item_value = field.get("itemdesc") or field.get("itemvalue")

        # Special handling to concatenate 'items' if it's a list
        if isinstance(item_value, list):
            item_value = "; ".join(
                [item.get("itemdesc", "") for item in item_value if "itemdesc" in item]
            )

        # Update the reformatted dict with the extracted value
        if catname and item_value is not None:
            reformatted[catname] = item_value

    # Process 'lineitems' to aggregate attributes into single strings separated by semicolons for multiple entries
    lineitems_attributes = {
        "phase": [],
        "phasedesc": [],
        "qty": [],
        "notes": [],
        "mix": [],
        "mixdesc": [],
        "job": [],
    }
    for item in dispatch.get("lineitems", []):
        for key in lineitems_attributes.keys():
            if key in item and item[key] is not None:
                if key == "job":
                    job_str = str(item[key]).strip("; ").strip()
                    if job_str not in lineitems_attributes[key]:
                        lineitems_attributes[key].append(job_str)
                else:
                    lineitems_attributes[key].append(str(item[key]))

    # Combine values for each attribute from all lineitems and assign to reformatted
    for key, values in lineitems_attributes.items():
        reformatted[key] = "; ".join(values)

    # Calculate and add 'Material Tonnage' by summing all values in the 'qty' column
    if "qty" in reformatted:
        try:
            # Convert each quantity to a float and sum them up
            total_tonnage = sum(
                float(qty.strip())
                for qty in reformatted["qty"].split(";")
                if qty.strip()
            )
        except ValueError:
            # In case of any non-numeric values, set total tonnage to 0 or handle as needed
            total_tonnage = 0
        reformatted["Material Tonnage"] = total_tonnage

    return reformatted


def summarize_results(results: list):
    """
    Print a summary of dispatch results to the console.

    Parameters:
    - results: A list of dictionaries containing dispatch data.
    """
    for entry in results:
        # Print Project
        print(
            f"Project: {entry.get('Job Number', 'N/A')} - {entry.get('Job Name', 'N/A')}"
        )

        # Print Crew
        print(f"Crew: {entry.get('crew', 'N/A')}")

        # Print Load Out Time
        print(f"Load Out Time: {entry.get('Plant Load Out', 'N/A')}")

        # Print Paving Start Time
        print(f"Paving Start Time: {entry.get('Paving Start', 'N/A')}")

        # Print Line Items table header
        print(
            "\n{:<20} {:<50} {:<10} {:<30}".format(
                "Phase", "Description", "Quantity", "Notes"
            )
        )
        print("-" * 120)  # For separating the header and data

        # Print each line item
        for lineitem in entry.get("lineitems", []):
            # Set default value if value is None type
            phase_value = lineitem.get("phase") or "N/A"
            phase_desc_value = lineitem.get("phasedesc") or "N/A"
            qty_value = lineitem.get("qty") or "N/A"
            notes_value = lineitem.get("notes") or "N/A"

            print(
                "{:<20} {:<50} {:<10} {:<30}".format(
                    phase_value, phase_desc_value, qty_value, notes_value
                )
            )

        # Separator for different projects
        print("\n" + "-" * 120 + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: script.py start_date end_date config_file_path")
        sys.exit(1)

    start, end, input_config = sys.argv[1:4]
    schedule = get_data(start, end, input_config)
    summarize_results(schedule)
