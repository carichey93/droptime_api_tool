Droptime API Documentation
==========================

The Droptime API Documentation provides an in-depth guide on interacting with the Droptime API, focusing on configuration, running scripts, and understanding key functions. It's designed to help developers integrate Droptime's functionalities into their applications seamlessly.

Table of Contents
-----------------

1.  [Overview](#overview)
2.  [Prerequisites](#prerequisites)
3.  [Configuration File (YAML Format)](#configuration-file-yaml-format)
4.  [Running the Script](#running-the-script)
5.  [Functions](#functions)
    *   [fetch\_new\_session()](#1-fetch_new_session)
    *   [get\_or\_update\_session()](#2-get_or_update_session)
    *   [make\_api\_call()](#3-make_api_call)
    *   [reformat\_dispatch()](#4-reformat_dispatch)
    *   [get\_data()](#5-get_data)
    *   [summarize\_results()](#6-summarize_results)
6.  [Additional Documentation](#additional-documentation)

Overview
--------

This documentation details the processes for setting up, configuring, and utilizing the Droptime API Interaction Module. It covers essential steps from installation prerequisites to executing the module and understanding its core functionalities.

Prerequisites
-------------

Before starting, ensure you have the following prerequisites installed:

*   **Python 3.6 or later**: The primary programming language used.
*   **`requests` library**: Enables HTTP requests to the API.
*   **`PyYAML` library**: For YAML file parsing.
*   **`ruamel.yaml` library**: Provides YAML parsing with preservation of comments and structure.

These dependencies can be installed using the following pip command:

```
pip install requests PyYAML ruamel.yaml
```

Configuration File (YAML Format)
--------------------------------

The module uses a YAML configuration file for setting API credentials and session details. Below is the required structure with descriptions for each field:

- **CompanyID**: 'YourCompanyID'
- **Manager**: 'YourManagerCode'
- **Passcode**: 'YourPasscode'
- **SessionID**: 'OptionalInitialSessionID'
- **SessionPassword**: 'OptionalInitialSessionPassword'
- **UserName**: 'YourUsername'`

Replace placeholder values with your actual Droptime API credentials.

Running the Script
------------------

To execute the module, use the following command pattern:

```
python script_name.py [start_date] [end_date] [config_file_path]
```

*   `start_date` and `end_date`: Specify the date range for data retrieval (format: MM-DD-YYYY).
*   `config_file_path`: Path to your YAML configuration file.

Example:

```
python droptime_api_module.py 10-2-2023 10-7-2023 /path/to/config.yaml
```

Functions
---------

### 1\. fetch\_new\_session()

#### Purpose

Fetches a new session from the Droptime API using the provided configuration.

#### Parameters

*   `config`: A dictionary containing the necessary configuration for the API call. It must include `CompanyID`, `Manager`, `Passcode`, and `UserName`.

#### Returns

*   A dictionary containing the new session information, including `SessionID` and `SessionPassword`.

#### Example Usage

```config = load_config("path/to/config.yml") session_info = fetch_new_session(config) print(session_info)```

### 2\. get\_or\_refresh\_session()

#### Purpose

Retrieves the current session details from the configuration file or fetches a new session if the current one is invalid or not present.

#### Parameters

*   `config_file`: Path to the YAML configuration file.

#### Returns

*   A dictionary containing the current or new session information.

#### Example Usage

```
session_config = get_or_refresh_session("path/to/config.yml") print(session_config)
```

### 3\. make\_api\_call()

#### Purpose

Makes a generic API call to the Droptime API with specified method and parameters, handling session management automatically.

#### Parameters

*   `method`: The API method to be called as a string.
*   `config`: Configuration dictionary with session details and other necessary information.
*   `start_date`: Start date for the data request in 'YYYY-MM-DD' format.
*   `end_date`: End date for the data request in 'YYYY-MM-DD' format.

#### Returns

*   A dictionary with the API response data.

#### Example Usage

```
api_response = make_api_call("getDispatchInfo", session_config, "2023-01-01", "2023-01-31") print(api_response)
```

### 4\. reformat\_dispatch()

#### Purpose

Reformats a single dispatch entry, extracting details from `fields` and `lineitems` and converting them into a more readable and structured format.

#### Parameters

*   `dispatch`: A dictionary containing a single dispatch entry.

#### Returns

*   A dictionary with the reformatted dispatch entry, including key details and aggregated line item information.

#### Example Usage

```
for dispatch in dispatches:
   reformatted_dispatch = reformat_dispatch(dispatch)
   print(reformatted_dispatch)
```

### 5\. get\_data()

#### Purpose

Fetches and formats dispatch data for a specified date range from the Droptime API.

#### Parameters

*   `start_date`: Start date for the data request in 'YYYY-MM-DD' format.
*   `end_date`: End date for the data request in 'YYYY-MM-DD' format.
*   `config_file`: Path to the YAML configuration file.

#### Returns

*   A list of dictionaries, each containing formatted dispatch data.

#### Example Usage

```
formatted_data = get_data("2023-01-01", "2023-01-31", "path/to/config.yml")
for item in formatted_data:
   print(item)
```

### 6\. summarize\_results()

#### Purpose

Prints a summarized version of the formatted dispatch results to the console for easy reading and analysis.

#### Parameters

*   `results`: A list of dictionaries, each representing a formatted dispatch entry.

#### Example Usage

```
summarize_results(formatted_data)
```

* * *
