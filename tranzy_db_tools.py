"""
Functions for interaction with the database
"""

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from datetime import timedelta, timezone

from geopy import distance

from config import MAX_DIST_TO_STOP, TIME_TOLERANCE
from tranzy_db import *
from tranzy_req import *


def update_stops(session: Session):
    """
    Refresh stops from API
    :param session: db session
    :return: None
    """
    stops = get_stops()
    stop_id_list = []
    for s in stops:
        stop_id_list.append(s["stop_id"])

    # retrieve all stops already saved in db
    stmt = select(Stop.stop_id).where(Stop.stop_id.in_(stop_id_list))
    result = session.execute(stmt)
    existing_stop_id_list = result.scalars().all()

    # create objects if stop_id doesn't already exist
    stop_object_list = []
    for s in stops:
        if s["stop_id"] not in existing_stop_id_list:
            stop_object_list.append(Stop(
                            stop_id=s["stop_id"],
                            stop_name=s["stop_name"],
                            stop_lat=s["stop_lat"],
                            stop_lon=s["stop_lon"]))
            # print(f"Stop {s['stop_id']} added.")
        else:
            # print(f"Stop {s['stop_id']} already in db.")
            pass
    # commit to db
    if stop_object_list:
        session.add_all(stop_object_list)
        session.commit()
        print("Stops updated!")
    else:
        print("No stops to update.")


def config_monitored_trip(session: Session):
    """
    Configure a new monitored trip - non GUI
    :param session: db session
    :return: None
    """
    # update stops
    update_stops(session)

    # get user input for line number and trip direction
    line_number = ""
    while line_number == "":
        line_number = input("Input the desired line number (0 to skip): ")

    if line_number != "0":
        route = get_route(line_number)
        if route:
            print(f"Route found: {route[0]['route_short_name']} - {route[0]['route_long_name']}")
            route_trips = get_trips(route[0]["route_id"])
            print("with following trips:")
            print(f"     {route_trips[0]['direction_id']} - {route[0]['route_short_name']} "
                  f"towards {route_trips[0]['trip_headsign']}")
            print(f"     {route_trips[1]['direction_id']} - {route[0]['route_short_name']} "
                  f"towards {route_trips[1]['trip_headsign']}")
            direction = -1
            while direction not in [0, 1]:
                direction = int(input("Input the desired direction (0 / 1): "))
            if route_trips[0]["direction_id"] == direction:
                route_trip = route_trips[0]
            else:
                route_trip = route_trips[1]

            # create Trip object for user's choice
            # TODO: check if already imported
            t = Trip(
                agency_id=AGENCY_ID,
                route_id=route[0]["route_id"],
                trip_id=route_trip["trip_id"],
                shape_id=route_trip["shape_id"],
                route_short_name=route[0]["route_short_name"],
                route_long_name=route[0]["route_long_name"],
                trip_headsign=route_trip["trip_headsign"],
                monitored=True
            )

            # retrieve stops order for selected trip
            stops_order = get_stop_order(route_trip["trip_id"])
            stop_id_list = [s_o["stop_id"] for s_o in stops_order]

            # retrieve corresponding stops from db
            stmt = select(Stop).where(Stop.stop_id.in_(stop_id_list))
            result = session.execute(stmt)
            stop_object_list = result.scalars().all()

            # create objects for stops order
            stops_order_object_list = []
            print(f"List of stops for {route[0]['route_short_name']} to {route_trip['trip_headsign']}:")
            stop_order_numbers = []  # stop order list to be used for input validation
            for s_o in stops_order:
                # enumerate all trip's stops
                try:
                    stop_idx, stop_name = next((item.idx, item.stop_name) for item in stop_object_list if item.stop_id == s_o["stop_id"])
                except StopIteration:
                    print(f"Stop {s_o['stop_id']} not found in db!")
                else:
                    # corresponding stop object found in db
                    # create StopOrder object linked to Stop object
                    stops_order_object_list.append(StopOrder(
                        stop_order=s_o["stop_sequence"],
                        trip=t,
                        stop_idx=stop_idx
                    ))
                    stop_order_numbers.append(s_o["stop_sequence"])
                    print(f"     {s_o['stop_sequence']} - {stop_name}")
            s_start = -1
            s_end = -1
            while s_start not in stop_order_numbers \
                    or s_end not in stop_order_numbers \
                    or s_start >= s_end:
                s_start = int(input("Input first stop: "))
                s_end = int(input("Input last stop: "))

            # create object for monitored stops
            m = MonitoredStops(
                start_stop=s_start,
                end_stop=s_end,
                trip=t
            )

            # commit objects to db
            session.add(t)
            session.add_all(stops_order_object_list)
            session.add(m)
            session.commit()
            print("Trip configured for monitoring")
        else:
            # route not found
            print(f"Route for '{line_number}' not found!")
    else:
        pass


def get_monitored_trip(session: Session):
    """
    Retrieve trips configured for monitoring
    :param session:
    :return: List of Trip objects
    """
    stmt = select(Trip).order_by(Trip.route_short_name)
    trip_obj_list = session.execute(stmt).scalars().all()
    if trip_obj_list:
        return trip_obj_list
    else:
        return None


def get_monitor_config(session: Session, trip_id) -> (Trip, list[Stop]):
    """
    Get the necessary details for monitoring
    :param session: The open Session to the db
    :param trip_id: The ID of the monitored trip.
    :return: Trip object and list of Stop object
    """
    # retrieve trip record from db
    stmt = select(Trip, MonitoredStops.start_stop, MonitoredStops.end_stop) \
        .join_from(Trip, MonitoredStops)\
        .where(Trip.trip_id == trip_id)
    row = session.execute(stmt).first()
    # monitored_trip_obj = row.Trip
    start_stop = row.start_stop
    end_stop = row.end_stop

    # retrieve monitored stops from db
    stmt = select(Stop).join_from(Trip, StopOrder)\
        .join_from(StopOrder, Stop)\
        .where(and_(Trip.trip_id == trip_id,
                    start_stop <= StopOrder.stop_order,
                    StopOrder.stop_order <= end_stop))
    stops_object_list = [row[0] for row in session.execute(stmt).all()]
    return row.Trip, stops_object_list


def insert_position(session: Session, trip, vehicle, stops_object_list: list[Stop]) -> (str, int):
    """
    Insert new position into db if it's close to the monitored stops
    :param session: The open Session to the db
    :param trip: Trip object
    :param vehicle: JSON from Tranzy API containing the position of a specific vehicle
    :param stops_object_list: Stop objects that must be closed to vehicle position
    :return: Message to log, message type
    """
    dt = datetime.fromisoformat(vehicle['timestamp'])
    dt_now = datetime.now(timezone.utc)
    if dt_now - timedelta(seconds=TIME_TOLERANCE) < dt < dt_now + timedelta(seconds=TIME_TOLERANCE):
        # calculate distance to each monitored stop and get the closest stop
        distance_list = [distance.distance((vehicle['latitude'], vehicle['longitude']), (s.stop_lat, s.stop_lon)).m for s in stops_object_list]
        min_distance = min(distance_list)
        closest_stop = stops_object_list[distance_list.index(min_distance)]
        min_distance = int(round(min_distance, 0))

        # check if closest stop is within a tolerable distance
        if min_distance <= MAX_DIST_TO_STOP:
            new_position = Position(
                vehicle_no=vehicle['label'],
                latitude=vehicle['latitude'],
                longitude=vehicle['longitude'],
                timestamp=dt,
                speed=vehicle['speed'],
                stop_distance=min_distance,
                trip_idx=trip.idx,
                stop_idx=closest_stop.idx
            )
            session.add(new_position)
            session.commit()
            return f"{vehicle['label']}, {dt.astimezone().strftime('%H:%M:%S')}, {closest_stop.stop_name} at {min_distance} meters", 1
        else:
            return f"{vehicle['label']} outside monitored segment", 2
    else:
        return f"{vehicle['label']} skipped - bad datetime: {dt.astimezone().strftime('%Y-%m-%d %H:%M:%S')}", 2


# TODO: results output - select distinct stops with smallest stop_distance from position?
