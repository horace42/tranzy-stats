import os
from time import sleep
from datetime import timedelta
from tkinter import Tk, INSERT, NORMAL, DISABLED

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from interface import MainWindow
from tranzy_db_tools import *
from config import TIME_TO_RUN, POLLING_INTERVAL


def main():

    # connect to db
    engine = create_engine("sqlite+pysqlite:///tranzy.db", echo=False)
    # uncomment to rewrite the db
    # if os.path.isfile("tranzy.db"):
    #     os.remove("tranzy.db")
    Base.metadata.create_all(engine)

    session = Session(engine)

    # populate configured_trips widget with the trips already stored in db
    # TODO move to interface (to be call also after configuring new trip
    configured_trips_list = get_monitored_trip(session)
    if configured_trips_list:
        for t in configured_trips_list:
            line = f"{t.trip_id} - line {t.route_short_name} ({t.route_long_name}) to {t.trip_headsign}"
            w.trips_choices.append(line)
            w.trips_choices_var.set(w.trips_choices)

    # start monitoring
    start_monitoring = "n"  # input("Start monitoring? (y/n) ")
    if start_monitoring.lower() == "y":
        # TODO: add support for multiple trips

        # get trip to monitor from trips configured in the db
        monitored_trip_id = select_monitored_trip(session)
        if monitored_trip_id:
            trip, stops_object_list = get_monitor_config(session, monitored_trip_id)
            print(f"\nMonitoring line {trip.route_short_name} ({trip.route_long_name}) to {trip.trip_headsign}\n")

            end_dt = datetime.now() + timedelta(minutes=TIME_TO_RUN)
            while datetime.now() < end_dt:
                vehicles = get_vehicles(monitored_trip_id)
                if not vehicles or len(vehicles) == 0:
                    print(f"{datetime.now().astimezone().strftime('%H:%M:%S')} No vehicles on route")
                else:
                    for v in vehicles:
                        insert_position(session, trip, v, stops_object_list)

                sleep(POLLING_INTERVAL)
    session.close()


if __name__ == '__main__':
    root = Tk()
    root.title("Tranzy Stats")
    w = MainWindow(root)
    w.agency_name_var.set(get_agency_name(AGENCY_ID))
    main()
    root.mainloop()
