"""
Configuration of constants
"""
# statistics collection duration
TIME_TO_RUN = 95  # minutes
# polling interval
POLLING_INTERVAL = 30  # seconds

# API key and endpoints
# Get your API key here (use Edge if Chrome doesn't work):
# https://tranzy.dev/accounts/my-apps
# agency (token is created for a single agency)
AGENCY_ID = "2"
TRANZY_KEY = "YWTSVcSGyx2DNvX9zSO0o4qdcNwset6l8E9WDg0c"
TRANZY_URL = "https://api.tranzy.dev/v1/opendata/"

AGENCY = "agency"
VEHICLES = "vehicles"
ROUTES = "routes"
TRIPS = "trips"
SHAPES = "shapes"  # not used (route GPS coordinates)
STOPS = "stops"
STOP_TIMES = "stop_times"

# maximum distance from a vehicle to a stop to log the position
# a smaller value could filter out some positions between stops
# a bigger value will log positions outside the monitored segment
MAX_DIST_TO_STOP = 300
# tolerance in seconds (+/-) for vehicle datetime
TIME_TOLERANCE = 60
