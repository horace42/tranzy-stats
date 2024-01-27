"""
Interface to view/modify monitored stops
"""

from tkinter import *
from tkinter import ttk, messagebox

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from interface import MainWindow
from tranzy_db import Trip
from tranzy_db_tools import get_monitor_config, get_route_stops, update_monitored_stops
from tranzy_req import get_stop_order


class ModTripWindow:
    def __init__(self, r: Tk, s: Session, w: MainWindow):
        self.root = r
        self.session = s
        self.main_window = w
        self.trip = Trip()
        self.start_stop = 0  # stop order to start logging from
        self.end_stop = 0  # stop order to end monitoring

        self.mon_stops_window = Toplevel(self.root)
        self.mon_stops_window.title("Monitored stops")
        mon_stops_frame = ttk.Frame(self.mon_stops_window, width=460, height=400)
        mon_stops_frame.grid_propagate(False)
        mon_stops_frame.grid(column=0, row=0)

        trip_desc_label = ttk.Label(mon_stops_frame, text=self.main_window.monitored_trip_var.get())
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
                                           state=DISABLED, command=self.commit_trip)
        self.mod_stops_button.grid(column=2, row=2)

        for child in mon_stops_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        self.mon_stops_window.protocol("WM_DELETE_WINDOW", self.window_close)
        self.stops_list.focus()
        self.search_stops()

    def search_stops(self):
        """
        Get stops order for the selected trip.
        :return: None
        """
        self.trip, stops_list, self.start_stop, self.end_stop = get_monitor_config(self.session,
                                                                                   self.main_window.trip_id_list[0])
        stops_order = get_stop_order(self.trip.trip_id)
        if stops_order:
            stop_id_list = [s_o["stop_id"] for s_o in stops_order]
            # retrieve Stop objects from db
            stop_object_list = get_route_stops(self.session, stop_id_list)
            # create objects for stops order
            self.stops_choices = []
            for s_o in stops_order:
                # enumerate all trip's stops
                try:
                    stop_idx, stop_name = next(
                        (item.idx, item.stop_name) for item in stop_object_list if item.stop_id == s_o["stop_id"])
                except StopIteration:
                    print(f"Stop {s_o['stop_id']} not found in db!")
                else:
                    # corresponding stop object found in db - append to list var
                    self.stops_choices.append(f"{s_o['stop_sequence']} - {stop_name}")

            # update stops_list widget
            self.stops_choices_var.set(self.stops_choices)
            # Listbox select currently monitored stops
            self.stops_list.selection_set(self.start_stop, self.end_stop)

    def stops_selected(self, event):
        """
        Update start_stop and end_stop based on stops_list selection. Handler for stops_list <<ListboxSelect>>.
        :param event: Bind event
        :return: None
        """
        idx_tuple = self.stops_list.curselection()
        if len(idx_tuple) > 1:
            self.mod_stops_button.configure(state=NORMAL)
            self.start_stop = min(idx_tuple)
            self.end_stop = max(idx_tuple)
        else:
            self.mod_stops_button.configure(state=DISABLED)
            self.start_stop = 0
            self.end_stop = 0

    def commit_trip(self):
        """
        Update monitored stops in db
        :return: None
        """
        update_monitored_stops(self.session, self.trip, self.start_stop, self.end_stop)
        messagebox.showinfo("Information", "Trip modified", parent=self.mon_stops_window)
        self.window_close()

    def window_close(self):
        """
        On exit main window widgets states and refresh configured_trips
        :return: None
        """
        # expunge objects
        if inspect(self.trip).has_identity:
            self.session.expunge(self.trip)
        # enable widgets from main window
        self.main_window.set_widget_state("idle_no_trip")
        # refresh configured_trips
        self.main_window.deselect_config_trips()
        self.mon_stops_window.destroy()
