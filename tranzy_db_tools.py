"""
Functions for interaction with the database
"""

from sqlalchemy import select, and_, delete, update, func, extract
from sqlalchemy.orm import Session

from datetime import timedelta, timezone

from geopy import distance

import csv

from config import MAX_DIST_TO_STOP, TIME_TOLERANCE, CSV_ENC
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


def get_route_stops(session: Session, stop_id_list):
    """
    Retrieve stops from the db based on their Tranzy ID.
    :param session: Session
    :param stop_id_list: List of Tranzy stop IDs
    :return: List of Stop objects
    """
    stmt = select(Stop).where(Stop.stop_id.in_(stop_id_list))
    result = session.execute(stmt)
    return result.scalars().all()


def get_monitored_trips(session: Session):
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
    :return: Trip object, list of Stop object, monitored start and end
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
    return row.Trip, stops_object_list, start_stop, end_stop


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
        distance_list = [distance.distance((vehicle['latitude'], vehicle['longitude']),
                                           (s.stop_lat, s.stop_lon)).m for s in stops_object_list]
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
            return f"{vehicle['trip_id']}-{vehicle['label']}, {dt.astimezone().strftime('%H:%M:%S')}, " \
                   f"{closest_stop.stop_name} at {min_distance} meters", 1
        else:
            return f"{vehicle['trip_id']}-{vehicle['label']} outside monitored segment", 2
    else:
        return f"{vehicle['trip_id']}-{vehicle['label']} skipped - bad datetime: " \
               f"{dt.astimezone().strftime('%Y-%m-%d %H:%M:%S')}", 2


def export_csv(session: Session, trip_id):
    """
    Export trip statistics to csv
    :param session: Session
    :param trip_id: Trip id
    :return: File name
    """
    # select statement
    stmt = select(Trip.idx, Trip.agency_id, Trip.trip_id,
                  Trip.route_short_name, Trip.route_long_name, Trip.trip_headsign,
                  Position.vehicle_no, Position.latitude, Position.longitude,
                  Position.timestamp, Position.speed, Position.stop_distance,
                  Stop.stop_name)\
        .join_from(Trip, Position)\
        .join_from(Position, Stop)\
        .where(Trip.trip_id == trip_id)
    # get data as list of Result objects (named tuple)
    results = session.execute(stmt).all()
    if results:
        file_name = f"exports/tranzy_{results[0].route_short_name}_{trip_id}" \
                    f"_{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(file_name, "w", newline='', encoding=CSV_ENC) as f:
            writer = csv.writer(f, delimiter=",", dialect="excel")
            writer.writerow(results[0]._fields)
            writer.writerows(results)
        return file_name
    else:
        return None


def delete_trip_data(session: Session, trip_id):
    """
    Delete all trip data
    :param session: Session
    :param trip_id: Trip id
    :return: None
    """
    stmt = select(Trip.idx).where(Trip.trip_id == trip_id)
    trip_idx = session.execute(stmt).first()[0]
    if trip_idx:
        trip_idx = int(trip_idx)
        # delete statements
        del_monitored_stops_stmt = delete(MonitoredStops).where(MonitoredStops.trip_idx == trip_idx)
        del_stop_order_stmt = delete(StopOrder).where(StopOrder.trip_idx == trip_idx)
        del_position_stmt = delete(Position).where(Position.trip_idx == trip_idx)
        del_trip_stmt = delete(Trip).where(Trip.idx == trip_idx)
        session.execute(del_monitored_stops_stmt)
        session.execute(del_stop_order_stmt)
        session.execute(del_position_stmt)
        session.execute(del_trip_stmt)
        session.commit()
    else:
        print("Something went wrong...")


def update_monitored_stops(session: Session, trip: Trip, s_stop: int, e_stop: int):
    """
    Re-configure a saved trip by updating the start and end stop
    :param session: Session
    :param trip: Trip object to re-configure
    :param s_stop: Start stop order
    :param e_stop: End stop order
    :return: None
    """
    upd_monitored_stops_stmt = update(MonitoredStops).where(MonitoredStops.trip_idx == trip.idx)\
        .values(start_stop=s_stop, end_stop=e_stop)
    session.execute(upd_monitored_stops_stmt)
    session.commit()


def get_trip_stats(session: Session, trip_idx, start_stop_idx, end_stop_idx):
    """
    Retrieve two list of Positions closest to the stops.
    :param session: Session
    :param trip_idx: DB trip idx
    :param start_stop_idx: DB stop idx of the stop from where to display stats
    :param end_stop_idx: DB stop idx of the stop to where to display stats
    :return: List of positions for each given stop
    """
    stmt = select(Position, func.min(Position.stop_distance))\
        .where(and_(Position.trip_idx == trip_idx, Position.stop_idx == start_stop_idx))\
        .group_by(extract('year', Position.timestamp),
                  extract('month', Position.timestamp),
                  extract('day', Position.timestamp),
                  extract('hour', Position.timestamp),
                  Position.vehicle_no,
                  Position.stop_idx)\
        .order_by(Position.timestamp)
    positions_start = session.execute(stmt).scalars()
    stmt = select(Position, func.min(Position.stop_distance))\
        .where(and_(Position.trip_idx == trip_idx, Position.stop_idx == end_stop_idx))\
        .group_by(extract('year', Position.timestamp),
                  extract('month', Position.timestamp),
                  extract('day', Position.timestamp),
                  extract('hour', Position.timestamp),
                  Position.vehicle_no,
                  Position.stop_idx)\
        .order_by(Position.timestamp)
    positions_end = session.execute(stmt).scalars()
    return positions_start.all(), positions_end.all()
