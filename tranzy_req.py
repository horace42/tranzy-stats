"""
Functions to get data from Tranzy API
https://api.tranzy.dev/v1/opendata/docs#/
This API partially implements the GTFS specification.

Get your API key here (use Edge if Chrome doesn't work):
https://tranzy.dev/accounts/my-apps
"""

from datetime import datetime
import requests
import json

from config import AGENCY_ID, TRANZY_KEY, TRANZY_URL, \
    AGENCY, VEHICLES, ROUTES, TRIPS, STOPS, STOP_TIMES

# calls to other endpoints than agency must have "X-Agency-Id" in headers
headers = {
    "Content-Type": "application/json",
    "X-API-KEY": TRANZY_KEY,
    "X-Agency-Id": AGENCY_ID
}


def explain_error(s: str) -> str:
    if "403" in s:
        return "Invalid API Key or invalid X-Agency-Id"
    elif "429" in s:
        return "Your API key has exceeded its request quota"
    elif "500" in s:
        return "Internal server error"
    else:
        return "Unknown error"


def get_agency_name(agency_id: str):
    """
    Get agency name
    :param agency_id: Tranzy agency ID
    :return: Agency name
    """
    headers_ag = {k: headers[k] for k in headers if k != "X-Agency-Id"}
    try:
        response = requests.get(url=f"{TRANZY_URL}{AGENCY}", headers=headers_ag)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(explain_error(str(err)))
        return "Agency name error"
    else:
        return next((a['agency_name'] for a in response.json() if a["agency_id"] == int(agency_id)), None)


def get_route(line_number: str):
    """
    Get route information for specific line number.
    :param line_number: A valid line number of chosen agency
    :return: List of json data for the route. Normally should have only 1 element.
    """
    try:
        response = requests.get(url=f"{TRANZY_URL}{ROUTES}", headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(explain_error(str(err)))
        raise SystemExit(err)
    else:
        return [r for r in response.json()
                if r["route_short_name"] in (line_number, line_number.upper(), line_number.lower())]


def get_trips(route_id: int):
    """
    Get trips (way to and back) information for chosen route.
    :param route_id: Route ID obtain from get_route return
    :return: List of json data for the trips. Normally should have only 2 elements.
    """
    try:
        response = requests.get(url=f"{TRANZY_URL}{TRIPS}", headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(explain_error(str(err)))
        raise SystemExit(err)
    else:
        return [t for t in response.json() if t["route_id"] == route_id]


def get_vehicles(trip_id: list[str], raw_log: bool):
    """
    Get vehicles positions.
    :param raw_log: Enable raw logging of JSON data
    :param trip_id: Trip ID obtain from get_trips return, used to filter output
    :return: List of json data for the positions of vehicles linked to the respective trip
    """
    try:
        response = requests.get(url=f"{TRANZY_URL}{VEHICLES}", headers=headers)
    except requests.exceptions.HTTPError as err:
        print(explain_error(str(err)))
        raise SystemExit(err)
    except requests.exceptions.ConnectionError as err:
        print(err)
        return []
    except requests.exceptions.Timeout as err:
        print(err)
        return []
    else:
        data = response.json()
        if raw_log:
            with open(f"vehicles_{datetime.now().astimezone().strftime('%Y%m%d')}.json", "a", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        if type(data) == list and len(data) != 0 and type(data[0]) == dict and "trip_id" in data[0]:
            return [v for v in response.json() if v["trip_id"] in trip_id]
        else:
            print(f"{datetime.now().astimezone().strftime('%H:%M:%S')} Invalid data for vehicles: {data}")
            return []


def get_stop_order(trip_id: str):
    """
    Get stops order for a specific trip.
    :param trip_id: Trip ID obtain from get_trips return, used to filter output
    :return: List of json data for the stops on the trip
    """
    try:
        response = requests.get(url=f"{TRANZY_URL}{STOP_TIMES}", headers=headers)
    except requests.exceptions.HTTPError as err:
        print(explain_error(str(err)))
        raise SystemExit(err)
    else:
        data = response.json()
        if type(data) == list and len(data) != 0 and type(data[0]) == dict and "stop_sequence" in data[0]:
            return [s for s in response.json() if s["trip_id"] == trip_id]
        else:
            print(f"{datetime.now().astimezone().strftime('%H:%M:%S')} Invalid data for stop_times: {data}")
            return []


def get_stops(stops_list: list[int] = None):
    """
    Get all available stops.
    :param stops_list: None, or specific stops IDs obtained from get_stop_order()
    :return: List of json data for all stops, or for the specified IDs
    """
    try:
        response = requests.get(url=f"{TRANZY_URL}{STOPS}", headers=headers)
    except requests.exceptions.HTTPError as err:
        print(explain_error(str(err)))
        raise SystemExit(err)
    else:
        data = response.json()
        if type(data) == list and len(data) != 0 and type(data[0]) == dict and "stop_id" in data[0]:
            if stops_list:
                # list of stop IDs was provided
                return [s for s in response.json() if s["stop_id"] in stops_list]
            else:
                return response.json()
        else:
            print(f"{datetime.now().astimezone().strftime('%H:%M:%S')} Invalid data for stops: {data}")
            return None
