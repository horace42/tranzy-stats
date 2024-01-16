import os
from time import sleep
from datetime import timedelta
from tkinter import Tk

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

    # configure a trip to monitor (can be skipped by user input
    session = Session(engine)

    # TODO: GUI
    config_monitored_trip(session)

    # start monitoring
    start_monitoring = input("Start monitoring? (y/n) ")
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
    MainWindow(root)
    root.mainloop()
    # main()
