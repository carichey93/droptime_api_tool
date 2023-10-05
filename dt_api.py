import sys
import requests
import yaml

"""
Droptime API

This module provides a set of functions to interact with the Droptime API, offering functionalities like:
1. Establishing a new API session or retrieving an existing one.
2. Generic API calls with session management.
3. Fetching dispatch data for a specified date range.
4. Reformating the fetched dispatch data for enhanced readability.
"""

BASE_URL = "https://api.droptime.net/API.aspx"


def fetch_new_session(config_file: str) -> dict:
    """
    Fetch a new session from the Droptime API using the provided config file.
    """
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    params = {"Method": "StartAPISession", **config}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if "SessionInformation" not in data:
        raise ValueError(f"Unexpected API response: {data}")
    config.update(data["SessionInformation"])

    # Save the updated configuration with the new session information back to the file
    with open(config_file, "w") as file:
        yaml.dump(config, file)

    return config


def get_or_update_session(config_file: str) -> dict:
    """
    Retrieve or refresh session details using the config file.
    """
    try:
        with open(config_file, "r") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        data = None

    if not data or "SessionID" not in data or "SessionPassword" not in data:
        data = fetch_new_session(config_file)
        with open(config_file, "w") as file:
            yaml.dump(data, file)

    return data


def make_api_call(method: str, params: dict, config_file: str) -> dict:
    """
    Make an API call, and handle session expiration by refreshing the session if needed.
    """
    session_data = get_or_update_session(config_file)
    params.update(
        {
            "Method": method,
            "SessionID": session_data["SessionID"],
            "SP": session_data["SessionPassword"],
        }
    )

    response = requests.get(BASE_URL, params=params)
    response_data = response.json()

    # Check for session expiration
    if (
            response_data.get("ErrorCode") == '1'
            and response_data.get("ErrorMessage") == "Your session has expired. Please login again."
    ):
        print("Session has expired, refreshing...")
        new_session_data = fetch_new_session(config_file)

        # Update the parameters with new session details and make the API call again
        params.update({
            "SessionID": new_session_data["SessionID"],
            "SP": new_session_data["SessionPassword"],
        })
        response = requests.get(BASE_URL, params=params)
        response_data = response.json()

    response.raise_for_status()
    return response_data

def reformat_dispatch(dispatch: dict) -> dict:
    """Applies formatting to a dispatch so that the results are more usable"""
    # Safely extract relevant field data
    reformatted = {}
    for field in dispatch.get("fields", []):
        if "catname" in field:
            value = (
                field.get("itemdesc") or field.get("itemvalue") or field.get("items")
            )
            reformatted[field["catname"]] = value

    # Extract crew name if present
    crew_data = dispatch.get("crew", {})
    if (
        isinstance(crew_data, dict)
        and "firstname" in crew_data
        and "lastname" in crew_data
    ):
        crew_name = f"{crew_data['firstname']} {crew_data['lastname']}".strip()
        reformatted["crew"] = crew_name

    # Adjust job name fields
    if "Job Number" in reformatted:
        reformatted["Job Name"] = reformatted.pop("Job Number")
    if "job" in reformatted:
        reformatted["Job Number"] = reformatted.pop("job")

    # Process line items, moving 'job' to the root level if present
    updated_lineitems = []
    for lineitem in dispatch.get("lineitems", []):
        if isinstance(lineitem, dict) and "job" in lineitem:
            reformatted["Job Number"] = lineitem["job"]
        else:
            updated_lineitems.append(lineitem)
    reformatted["lineitems"] = updated_lineitems

    # Merge reformatting results with original data, excluding 'fields' and already processed keys
    dispatch_updated = {
        k: v for k, v in dispatch.items() if k not in ["fields", "crew"]
    }
    reformatted.update(dispatch_updated)

    # Filter lineitems for the desired keys
    if "lineitems" in reformatted:
        reformatted["lineitems"] = [
            {
                key: lineitem[key]
                for key in ["phase", "phasedesc", "qty", "notes"]
                if key in lineitem
            }
            for lineitem in reformatted["lineitems"]
        ]

    # If 'lineitems' is present, move it to the end
    if "lineitems" in reformatted:
        lineitems = reformatted.pop("lineitems")
        reformatted["lineitems"] = lineitems

    return reformatted


def get_data(start_date: str, end_date: str, config_file) -> list:
    """Fetch dispatch info for the given date range and reformat the data."""
    params = {"StartTime": start_date, "EndTime": end_date}
    data = make_api_call("getDispatchInfo", params, config_file)
    return [reformat_dispatch(dispatch) for dispatch in data["Items"]]


def summarize_results(results: list):
    """Prints a summarized view of the dispatches to the terminal"""
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
                    phase_value,
                    phase_desc_value,
                    qty_value,
                    notes_value
                )
            )

        # Separator for different projects
        print("\n" + "-" * 120 + "\n")


if __name__ == "__main__":
    # Check for command line arguments. The format is: script.py start_date end_date config_file_path
    if len(sys.argv) == 4:
        start, end, config_input = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        print(
            "Error: Please provide start_date, end_date, and config_file_path as arguments."
        )
        sys.exit(1)

    result = get_data(start, end, config_input)
    summarize_results(result)
