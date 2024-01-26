"""
Interface to view/modify monitored stops
"""
from tkinter import *
from tkinter import ttk

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from interface import MainWindow
from tranzy_db import Trip


class MonitoredStopsWindow:
    def __init__(self, r: Tk, s: Session, w: MainWindow):
        self.root = r
        self.session = s
        self.main_window = w
        self.trip = Trip()
        self.start_stop = 0  # stop order to start logging from
        self.end_stop = 0  # stop order to end monitoring
        self.stops_order_object_list = []

        self.mon_stops_window = Toplevel(self.root)
        self.mon_stops_window.title("Monitored stops")
        mon_stops_frame = ttk.Frame(self.mon_stops_window, width=500, height=400)
        mon_stops_frame.grid_propagate(False)
        mon_stops_frame.grid(column=0, row=0)

        # TODO: when opening this window call set_trip_id_list and verify a single trip is selected
        print(self.main_window.trip_id_list[0])
        route_short_label = ttk.Label(mon_stops_frame, text="TODO rt short")
        route_short_label.grid(column=0, row=0)

        route_long_label = ttk.Label(mon_stops_frame, text="TODO rt long")
        route_long_label.grid(column=1, columnspan=2, row=0)

        trip_desc_label = ttk.Label(mon_stops_frame, text="TODO: trip description")
        trip_desc_label.grid(column=0, columnspan=3, row=1)

        stops_label = ttk.Label(mon_stops_frame, text="Stops:")
        stops_label.grid(column=0, row=2)

        self.stops_choices = []
        self.stops_choices_var = StringVar(value=self.stops_choices)
        self.stops_list = Listbox(mon_stops_frame, width=30, height=15, selectmode=EXTENDED,
                                  listvariable=self.stops_choices_var)
        self.stops_list.grid(column=1, row=2)
        self.stops_list.bind('<<ListboxSelect>>', self.stops_selected)

        self.mod_stops_button = ttk.Button(mon_stops_frame, width=30, text="Apply changes",
                                           command=self.commit_trip)
        self.mod_stops_button.grid(column=2, row=2)

        for child in mon_stops_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        self.mon_stops_window.protocol("WM_DELETE_WINDOW", self.window_close)
        self.search_stops()

    def search_stops(self):
        pass

    def stops_selected(self, event):
        pass

    def commit_trip(self):
        pass

    def window_close(self):
        # expunge objects
        if inspect(self.trip).has_identity:
            self.session.expunge(self.trip)
        if self.stops_order_object_list:
            for item in self.stops_order_object_list:
                self.session.expunge(item)
        # enable buttons from main window
        self.main_window.configure_trip_button.configure(state=NORMAL)
        self.main_window.configured_trips.configure(state=NORMAL)
        # refresh configured_trips
        self.main_window.deselect_config_trips()
        self.mon_stops_window.destroy()