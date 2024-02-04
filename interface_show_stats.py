"""
Interface to show statistics for selected trip at specific start/end stops
"""
from datetime import timezone, timedelta

from tkinter import *
from tkinter import ttk, messagebox

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from interface import MainWindow
from tranzy_db import Trip
from tranzy_db_tools import get_monitor_config, get_route_stops, get_trip_stats
from tranzy_req import get_stop_order


class ShowStatsWindow:
    def __init__(self, r: Tk, s: Session, w: MainWindow):
        self.root = r
        self.session = s
        self.main_window = w
        self.trip = Trip()
        self.start_stop = 0  # stop order to start logging from
        self.end_stop = 0  # stop order to end monitoring
        self.stop_idx_list = []

        self.show_stats_window = Toplevel(self.root)
        self.show_stats_window.title("Show stats")

        trip_desc_label = ttk.Label(self.show_stats_window, text=self.main_window.monitored_trip_var.get())
        trip_desc_label.grid(column=0, columnspan=2, row=0)
        trip_desc_label.grid_configure(padx=5, pady=10)

        left_frame = ttk.Frame(self.show_stats_window, width=250, height=450)
        left_frame.grid_propagate(False)
        left_frame.grid(column=0, row=1)
        right_frame = ttk.Frame(self.show_stats_window, width=420, height=450)
        right_frame.grid_propagate(False)
        right_frame.grid(column=1, row=1)

        stops_label = ttk.Label(left_frame, text="Stops:")
        stops_label.grid(column=0, row=0)

        self.stops_choices = []
        self.stops_choices_var = StringVar(value=self.stops_choices)
        self.stops_list = Listbox(left_frame, width=30, height=15, selectmode=EXTENDED,
                                  listvariable=self.stops_choices_var)
        self.stops_list.grid(column=0, row=1)
        self.stops_list.bind('<<ListboxSelect>>', self.stops_selected)

        self.show_stats_button = ttk.Button(left_frame, width=30, text="Show stats",
                                            state=DISABLED, command=self.show_stats)
        self.show_stats_button.grid(column=0, row=2)

        for child in left_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        self.start_label_var = StringVar(value="Start")
        start_label = ttk.Label(right_frame, textvariable=self.start_label_var, width=20, anchor="e")
        start_label.grid(column=0, row=0)

        arrow_label = ttk.Label(right_frame, text=">>>", width=4)
        arrow_label.grid(column=1, row=0)

        self.end_label_var = StringVar(value="End")
        end_label = ttk.Label(right_frame, textvariable=self.end_label_var, width=20, anchor="w")
        end_label.grid(column=2, row=0)

        stats_frame = ttk.Frame(right_frame, width=40, height=20)
        stats_frame.grid(column=0, columnspan=3, row=1)

        self.stats_text = Text(stats_frame, width=47, height=20, state=DISABLED, wrap=NONE,
                               background="white", padx=10, pady=10)
        self.stats_text.grid(column=0, row=0, sticky="NWES")

        self.stats_scroll_y = ttk.Scrollbar(stats_frame, orient=VERTICAL, command=self.stats_text.yview)
        self.stats_scroll_y.grid(column=1, row=0, sticky="NS")
        self.stats_text.configure(yscrollcommand=self.stats_scroll_y.set)

        for child in right_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        self.show_stats_window.protocol("WM_DELETE_WINDOW", self.window_close)
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
            self.stop_idx_list = []
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
                    self.stop_idx_list.append(stop_idx)

            # update stops_list widget with just the monitored stops
            self.stops_choices = self.stops_choices[self.start_stop: self.end_stop + 1]
            self.stops_choices_var.set(self.stops_choices)
            self.stop_idx_list = self.stop_idx_list[self.start_stop: self.end_stop + 1]

    def stops_selected(self, event):
        """
        Update start_stop and end_stop based on stops_list selection. Handler for stops_list <<ListboxSelect>>.
        :param event: Bind event
        :return: None
        """
        idx_tuple = self.stops_list.curselection()
        if len(idx_tuple) > 1:
            self.show_stats_button.configure(state=NORMAL)
            self.start_stop = min(idx_tuple)
            self.end_stop = max(idx_tuple)
            self.start_label_var.set(value=self.stops_choices[self.start_stop].split(" - ")[1])
            self.end_label_var.set(value=self.stops_choices[self.end_stop].split(" - ")[1])
        else:
            self.show_stats_button.configure(state=DISABLED)
            self.start_stop = 0
            self.end_stop = 0

    def show_stats(self):
        """
        Retrieve db data and insert in Text widget
        :return: None
        """
        positions_start, positions_end = get_trip_stats(self.session, self.trip.idx,
                                                        self.stop_idx_list[self.start_stop],
                                                        self.stop_idx_list[self.end_stop])
        self.stats_text.configure(state=NORMAL)
        if positions_start and positions_end:
            self.stats_text.delete("1.0", END)
            for i in range(len(positions_start)):
                row = f"{positions_start[i].vehicle_no} : "
                row += f"{positions_start[i].timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%d.%m.%Y %H:%M:%S')}"
                row += " >>> no data\n"
                # find the correspondent vehicle in positions_end
                for j in range(max(0, i - 10), min(len(positions_end), i + 10)):
                    if positions_start[i].vehicle_no == positions_end[j].vehicle_no \
                            and timedelta(0) < (positions_end[j].timestamp - positions_start[i].timestamp) < timedelta(60):
                        travel_time = str(positions_end[j].timestamp - positions_start[i].timestamp)
                        row = row.replace("no data", f"{positions_end[j].timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%H:%M:%S')} in {travel_time[travel_time.find(':') + 1:]}")
                        break
                self.stats_text.insert(END, row)
            self.stats_text.see(END)
        else:
            messagebox.showerror(title="Trip stats", message="No entries found for selected stop!",
                                 parent=self.show_stats_window)
            self.stats_text.delete("1.0", END)
        self.stats_text.configure(state=DISABLED)

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
        self.show_stats_window.destroy()
