"""
Configuration of constants / defaults
"""

import os

# API key and endpoints
# Get your API key here (use Edge if Chrome doesn't work):
# https://tranzy.dev/accounts/my-apps
# ********** EXPORT YOUR KEY AS ENVIRONMENT VARIABLE "TRANZY_KEY"

# agency (token is created for a single agency)
AGENCY_ID = "2"
TRANZY_KEY = os.environ.get("TRANZY_KEY")
TRANZY_URL = "https://api.tranzy.dev/v1/opendata/"

AGENCY = "agency"
VEHICLES = "vehicles"
ROUTES = "routes"
TRIPS = "trips"
SHAPES = "shapes"  # not used (route GPS coordinates)
STOPS = "stops"
STOP_TIMES = "stop_times"

# statistics collection default duration
TIME_TO_RUN = 30  # minutes
# default polling interval
POLLING_INTERVAL = 30  # seconds
# maximum distance from a vehicle to a stop to log the position
#  - a smaller value could filter out some positions between stops
#  - a bigger value will log positions outside the monitored segment
MAX_DIST_TO_STOP = 300
# tolerance in seconds (+/-) for vehicle datetime
TIME_TOLERANCE = 60

# encoding for csv export (use utf-8-sig for UTF-8 BOM)
CSV_ENC = "utf-8-sig"
