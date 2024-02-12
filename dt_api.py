import sys
import requests
import yaml
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
    Fetch a new session from the Droptime API using the provided configuration,
    ensuring only required fields are sent in the request.

    Parameters:
    - config: A dictionary containing the necessary configuration for the API call.

    Returns:
    - A dictionary containing the new session information.
    """
    # Filter the config to include only the fields required for starting a new session
    session_params = {key: config[key] for key in REQUIRED_FIELDS if key in config}

    # Specify the method for starting a new API session
    session_params["Method"] = "StartAPISession"

    response = requests.get(BASE_URL, params=session_params)
    response.raise_for_status()  # Ensure the API call was successful
    data = response.json()

    if "SessionInformation" not in data:
        raise ValueError(f"Unexpected API response: {data}")

    # Return the session information part of the response
    return data["SessionInformation"]


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


def make_api_call(method: str, config: dict, start_date: str, end_date: str) -> dict:
    """
    Make a generic API call, using only the required fields from the configuration.

    Parameters:
    - method: The API method to call.
    - config: Configuration dictionary with all configuration details.
    - start_date: Start date for the data request.
    - end_date: End date for the data request.

    Returns:
    - The JSON response from the API call.
    """
    # Prepare the parameters for the API call
    # Filter the config to include only required fields for the API call, plus any method-specific parameters
    api_params = {key: config[key] for key in REQUIRED_FIELDS if key in config}

    # Add method-specific parameters
    api_params.update({"Method": method, "StartTime": start_date, "EndTime": end_date})

    # Include session-specific parameters if available
    if "SessionID" in config and "SessionPassword" in config:
        api_params.update(
            {"SessionID": config["SessionID"], "SP": config["SessionPassword"]}
        )

    response = requests.get(BASE_URL, params=api_params)
    response.raise_for_status()
    return response.json()


def get_data(start_date: str, end_date: str, config_file: str) -> list:
    """
    Fetch and format dispatch data for a specified date range.

    Parameters:
    - start_date: Start date for the dispatch data request.
    - end_date: End date for the dispatch data request.
    - config_file: Path to the YAML configuration file.

    Returns:
    - A list of dictionaries containing formatted dispatch data.
    """
    session_config = get_or_refresh_session(config_file)
    data = make_api_call("getDispatchInfo", session_config, start_date, end_date)
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
    lineitems_attributes = {"phase": [], "phasedesc": [], "qty": [], "notes": []}
    for item in dispatch.get("lineitems", []):
        for key in lineitems_attributes.keys():
            if key in item and item[key] is not None:
                lineitems_attributes[key].append(str(item[key]))

    # Combine values for each attribute from all lineitems and assign to reformatted
    for key, values in lineitems_attributes.items():
        reformatted[key] = "; ".join(values)

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
