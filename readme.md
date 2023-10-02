# DROPTIME API DOCUMENTATION

---

## Overview
The documentation provides details on interacting with the Droptime API, including configuration, running scripts, and key functions.

## Table of Contents
1. [Configuration File (YAML format)](#configuration-file-yaml-format)
2. [Running the Script](#running-the-script)
3. [Functions](#functions)
    - [fetch_new_session()](#1-fetch_new_session)
    - [get_or_update_session()](#2-get_or_update_session)
    - [make_api_call()](#3-make_api_call)
    - [reformat_dispatch()](#4-reformat_dispatch)
    - [fetch_and_reformat()](#5-fetch_and_reformat)
    - [summarize_results()](#6-summarize_results)
 

### Additional Documentation
[Link to Additional Documentation](https://droptime.net/api/detail.php?token=eWFtbC9NaXNjL2ltcG9ydFZpZXdwb2ludEl0ZW1zLnlhbWw=)

<a id="configuration-file-yaml-format"></a>
## Configuration File (YAML format)

The configuration file is crucial for the Droptime API. Structure it in the YAML format as follows:

**Fields:**
- **CompanyID**: Your company's ID on Droptime.
- **Manager**: Manager code (e.g., single letter).
- **Passcode**: Your Droptime account passcode.
- **SessionID**: Unique session ID. Might be auto-updated by the script.
- **SessionPassword**: Password for the session. Might be auto-updated by the script.
- **UserName**: Droptime account username.

**Example Configuration:**
```yaml
CompanyID: '123999'
Manager: M
Passcode: Password1!
SessionID: 6576189
SessionPassword: '9062278468'
UserName: omrichey
```

<a id="running-the-script"></a>
## Running the Script

Execute the script with the following command:

```
python script_name.py [start_date] [end_date] [config_file_path]
```

**Arguments:**
- `start_date`: Start date ('MM-DD-YYYY'). Defaults to "10-2-2023".
- `end_date`: End date ('MM-DD-YYYY'). Defaults to "10-7-2023".
- `config_file_path`: (Optional) Path to the API credentials and session details. Defaults to "config.yaml".

**Usage Example:**
```
python script_name.py 10-2-2023 10-7-2023 /path/to/your/config.yaml
```

<a id="functions"></a>
## Functions

<a id="1-fetch_new_session"></a>
### 1.  fetch_new_session() -> dict
**Purpose:** Fetch a new session from the Droptime API using the provided configuration.
**Returns:** Dictionary with session details.

<a id="2-get_or_update_session"></a>
### 2. get_or_update_session() -> dict
**Purpose:** Retrieve session details from the config. If invalid, fetch a new one.
**Returns:** Dictionary with session details.

<a id="3-make_api_call"></a>
### 3. make_api_call(method: str, params: dict) -> dict
**Parameters:** 
1. `method`: API method (string).
2. `params`: Parameters dictionary.
**Purpose:** Make an API call with a given method and parameters, handling session expiration.
**Returns:** Dictionary with API response data.

<a id="4-reformat_dispatch"></a>
### 4. reformat_dispatch(dispatch: dict) -> dict
**Parameters:** 
1. `dispatch`: Dispatch data dictionary.
**Purpose:** Reformat a single dispatch data for improved readability.
**Returns:** Dictionary with reformatted dispatch data.

<a id="5-fetch_and_reformat"></a>
### 5. fetch_and_reformat(start_date: str, end_date: str) -> list
**Parameters:** 
1. `start_date`: Start date string.
2. `end_date`: End date string.
**Purpose:** Fetch and reformat dispatch information for a date range.
**Returns:** List of dictionaries with dispatch data.

```json
[
    {
        'Plant': 'Huntsville Asphalt',
        'Time of Day': 'Day',
        'Customer': 'S&W Construction',
        'Paver': '62.101114 - Weiler',
        'Job Scope': 'Non Main Line',
        ...
        'lineitems': [
            {
                'phase': '50.40102.2',
                'phasedesc': 'Superpave Base Layer 1`` Max Agg C/D',
                'qty': 263.0,
                'notes': ''
            },
            ...
        ]
    },
    ...
]
```

<a id="6-summarize_results"></a>
### 6. summarize_results(results: list)
**Parameters:** 
1. `results`: List of job task dictionaries. 
**Purpose:** Print a summarized version of the data in a tabular format.

**Example Usage:**
```python
results = [
    {'Job Number': '403251.', ...}
]
summarize_results(results)
```
**Example Output:**
```
Project: 403251. - Racetrac #2625 Huntsville
Crew: James Minyard
Load Out Time: 08:00:00
Paving Start Time: 08:30:00

Phase                Description                          Quantity   Notes                         
------------------------------------------------------------------------------------------------------------------------
50.40102.2           Superpave Base Layer                 263.0      N/A                          

------------------------------------------------------------------------------------------------------------------------

```