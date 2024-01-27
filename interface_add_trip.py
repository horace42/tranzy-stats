"""
Interface to add new trip to be monitored
"""

from tkinter import *
from tkinter import ttk, messagebox

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from config import AGENCY_ID
from interface import MainWindow
from tranzy_db import Trip, StopOrder, MonitoredStops
from tranzy_db_tools import update_stops, get_route_stops
from tranzy_req import get_route, get_trips, get_stop_order


class AddTripWindow:
    def __init__(self, r: Tk, s: Session, w: MainWindow):
        self.root = r
        self.session = s
        self.main_window = w
        self.trip = Trip()
        self.start_stop = 0  # stop order to start logging from
        self.end_stop = 0  # stop order to end monitoring
        self.stops_order_object_list = []
        self.route_trips = []

        self.add_trip_window = Toplevel(self.root)
        self.add_trip_window.title("Add trip")
        add_trip_frame = ttk.Frame(self.add_trip_window, width=500, height=400)
        add_trip_frame.grid_propagate(False)
        add_trip_frame.grid(column=0, row=0)

        line_number_label = ttk.Label(add_trip_frame, text="Line number:")
        line_number_label.grid(column=0, row=0)

        self.line_number_var = StringVar(value="")
        self.line_number_var.trace_add("write", lambda *args: self.search_trips_button.configure(state=NORMAL))
        self.line_number_entry = ttk.Entry(add_trip_frame, width=10, textvariable=self.line_number_var,
                                           name="line_number")
        self.line_number_entry.grid(column=1, row=0, sticky="W")

        self.search_trips_button = ttk.Button(add_trip_frame, width=30, text="Search trips", state=DISABLED,
                                              command=self.search_trips, name="search_trips_button")
        self.search_trips_button.grid(column=2, row=0)

        self.trips_var = StringVar(value="0")  # var for radio buttons
        self.trip0_radio = ttk.Radiobutton(add_trip_frame, text="Trip 0", width=10, variable=self.trips_var, value="0",
                                           state=DISABLED, command=self.select_trip_dir)
        self.trip0_radio.grid(column=0, row=1)

        self.trip0_var = StringVar(value="")
        trip0_label = ttk.Label(add_trip_frame, width=30, textvariable=self.trip0_var)
        trip0_label.grid(column=1, row=1)

        self.trip1_radio = ttk.Radiobutton(add_trip_frame, text="Trip 1", width=10, variable=self.trips_var, value="1",
                                           state=DISABLED, command=self.select_trip_dir)
        self.trip1_radio.grid(column=0, row=2)

        self.trip1_var = StringVar(value="")
        trip1_label = ttk.Label(add_trip_frame, width=30, textvariable=self.trip1_var)
        trip1_label.grid(column=1, row=2)

        self.search_stops_button = ttk.Button(add_trip_frame, width=30, text="Search stops", state=DISABLED,
                                              command=self.search_stops)
        self.search_stops_button.grid(column=2, row=1, rowspan=2)

        self.stops_label = ttk.Label(add_trip_frame, text="Stops:", state=DISABLED)
        self.stops_label.grid(column=0, row=3)

        self.stops_choices = []
        self.stops_choices_var = StringVar(value=self.stops_choices)
        self.stops_list = Listbox(add_trip_frame, width=30, height=15, state=DISABLED, selectmode=EXTENDED,
                                  listvariable=self.stops_choices_var)
        self.stops_list.grid(column=1, row=3)
        self.stops_list.bind('<<ListboxSelect>>', self.stops_selected)

        self.add_trip_button = ttk.Button(add_trip_frame, width=30, text="Add trip", state=DISABLED,
                                          command=self.commit_trip)
        self.add_trip_button.grid(column=2, row=3)

        for child in add_trip_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        self.line_number_entry.focus()
        self.add_trip_window.protocol("WM_DELETE_WINDOW", self.window_close)
        self.add_trip_window.bind("<Return>", self.cr_pressed)
        update_stops(self.session)

    def search_trips(self):
        """
        Search route and corresponding trips and create the Trip object. Command for search_trips_button.
        :return: None
        """
        route = get_route(self.line_number_var.get())
        if route:
            self.route_trips = get_trips(route[0]["route_id"])
            self.trips_var.set(value="0")
            self.trip0_var.set(value=f"{route[0]['route_short_name']} to {self.route_trips[0]['trip_headsign']}")
            self.trip1_var.set(value=f"{route[0]['route_short_name']} to {self.route_trips[1]['trip_headsign']}")
            self.trip0_radio.configure(state=NORMAL)
            self.trip1_radio.configure(state=NORMAL)
            self.search_stops_button.configure(state=NORMAL)
            self.stops_choices = []
            self.stops_choices_var.set(self.stops_choices)
            self.stops_list.configure(state=DISABLED)
            self.stops_label.configure(state=DISABLED)
            self.add_trip_button.configure(state=DISABLED)
            self.trip = Trip(
                agency_id=AGENCY_ID,
                route_id=route[0]["route_id"],
                trip_id=self.route_trips[0]["trip_id"],
                shape_id=self.route_trips[0]["shape_id"],
                route_short_name=route[0]["route_short_name"],
                route_long_name=route[0]["route_long_name"],
                trip_headsign=self.route_trips[0]["trip_headsign"],
                monitored=True
            )
        else:
            messagebox.showerror(title="Error", message="Route not found!", parent=self.add_trip_window)
            self.line_number_var.set(value="")
            self.trip0_var.set(value="")
            self.trip1_var.set(value="")
            self.trip0_radio.configure(state=DISABLED)
            self.trip1_radio.configure(state=DISABLED)
            self.search_stops_button.configure(state=DISABLED)

    def select_trip_dir(self):
        """
        Modify Trip object when selection changes. Command for trip0_radio and trip1_radio.
        :return: None
        """
        self.trip.trip_id = self.route_trips[int(self.trips_var.get())]["trip_id"]
        self.trip.shape_id = self.route_trips[int(self.trips_var.get())]["shape_id"]
        self.trip.trip_headsign = self.route_trips[int(self.trips_var.get())]["trip_headsign"]
        self.stops_choices = []
        self.stops_choices_var.set(self.stops_choices)
        self.stops_list.configure(state=DISABLED)
        self.stops_label.configure(state=DISABLED)
        self.add_trip_button.configure(state=DISABLED)

    def search_stops(self):
        """
        Get stops order for specific route trip. Create StopOrder objects linked to created Trip
        and Stop object retrieve from db. Command for search_stops_button.
        :return: None
        """
        # retrieve stops order for selected trip from API
        stops_order = get_stop_order(self.route_trips[int(self.trips_var.get())]["trip_id"])
        if stops_order:
            stop_id_list = [s_o["stop_id"] for s_o in stops_order]
            # retrieve Stop objects from db
            stop_object_list = get_route_stops(self.session, stop_id_list)
            # create objects for stops order
            self.stops_order_object_list = []
            self.stops_choices = []
            for s_o in stops_order:
                # enumerate all trip's stops
                try:
                    stop_idx, stop_name = next(
                        (item.idx, item.stop_name) for item in stop_object_list if item.stop_id == s_o["stop_id"])
                except StopIteration:
                    print(f"Stop {s_o['stop_id']} not found in db!")
                else:
                    # corresponding stop object found in db
                    # create StopOrder object linked to Trip and Stop objects
                    self.stops_order_object_list.append(StopOrder(
                        stop_order=s_o["stop_sequence"],
                        trip=self.trip,
                        stop_idx=stop_idx
                    ))
                    self.stops_choices.append(f"{s_o['stop_sequence']} - {stop_name}")

            # update stops_list widget
            self.stops_choices_var.set(self.stops_choices)
            self.stops_list.configure(state=NORMAL)
            self.stops_label.configure(state=NORMAL)

    def commit_trip(self):
        """
        Create MonitoredStops from stops_list selection. Commit all new objects to db. Command for add_trip_button.
        :return: None
        """
        # create object for monitored stops
        m = MonitoredStops(
            start_stop=self.start_stop,
            end_stop=self.end_stop,
            trip=self.trip
        )
        # commit objects to db
        self.session.add(self.trip)
        self.session.add_all(self.stops_order_object_list)
        self.session.add(m)
        self.session.commit()
        messagebox.showinfo("Information", "Trip added to database", parent=self.add_trip_window)
        self.window_close()

    def stops_selected(self, event):
        """
        Update start_stop and end_stop based on stops_list selection. Handler for stops_list <<ListboxSelect>>.
        :param event: Bind event
        :return: None
        """
        idx_tuple = self.stops_list.curselection()
        if len(idx_tuple) > 1:
            self.add_trip_button.configure(state=NORMAL)
            self.start_stop = min(idx_tuple)
            self.end_stop = max(idx_tuple)
        else:
            self.add_trip_button.configure(state=DISABLED)
            self.start_stop = 0
            self.end_stop = 0

    def window_close(self):
        """
        On exit main window widgets states and refresh configured_trips
        :return: None
        """
        # expunge objects
        if inspect(self.trip).has_identity:
            self.session.expunge(self.trip)
        if self.stops_order_object_list:
            for item in self.stops_order_object_list:
                if inspect(item).has_identity:
                    self.session.expunge(item)
        # enable widgets from main window
        self.main_window.set_widget_state("idle_no_trip")
        # refresh configured_trips
        self.main_window.deselect_config_trips()
        self.add_trip_window.destroy()

    def cr_pressed(self, event):
        """
        Search for trips if Enter pressed while focus is on line_number_entry or search_trips_button.
        Handler for add_trip_window <Return>.
        :param event: Event
        :return: None
        """
        if self.add_trip_window.focus_get().winfo_name() in ("line_number", "search_trips_button"):
            self.search_trips()
