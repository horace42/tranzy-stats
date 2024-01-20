"""
Interface implementation
"""

from tkinter import *
from tkinter import ttk
from tkinter import messagebox

from datetime import datetime, timedelta, time

from sqlalchemy.orm import Session

from config import POLLING_INTERVAL, TIME_TO_RUN, AGENCY_ID
from tranzy_db import Trip, Stop
from tranzy_db_tools import get_monitored_trip, get_monitor_config, insert_position
from tranzy_req import get_agency_name, get_vehicles


class MainWindow:
    def __init__(self, r: Tk, s: Session):
        self.after_countdown_id = None  # id to cancel scheduling of countdown (single polling)
        self.after_stop_polling_id = None  # id to cancel scheduling of stop polling (time to run)
        self.after_actual_start_id = None  # id to cancel scheduling of deferred start
        self.time_to_run = 5  # default time to run the polling (minutes)
        self.monitoring = False  # monitoring in progress
        self.trip_id = ""
        self.session = s
        self.trip: Trip  # Trip objet to retrieve monitored trip details from db
        self.stops_object_list: list[Stop]  # list of Stop objects to retrieve from db stops of monitored trip

        self.root = r
        self.root.minsize(width=1024, height=768)

        left_frame = ttk.Frame(self.root, width=462, height=768)
        left_frame.configure(borderwidth=10, relief="raised")
        left_frame.grid_propagate(False)
        left_frame.grid(column=0, row=0)

        right_frame = ttk.Frame(self.root, width=562, height=768)
        right_frame.configure(borderwidth=10, relief="raised")
        right_frame.grid_propagate(False)
        right_frame.grid(column=1, row=0)

        agency_label = ttk.Label(left_frame, text="Agency:")
        agency_label.grid(column=0, row=0)

        self.agency_name_var = StringVar(value="")
        agency_name_label = ttk.Label(left_frame, textvariable=self.agency_name_var)
        agency_name_label.grid(column=1, row=0)

        polling_label = ttk.Label(left_frame, text="Polling interval (s):")
        polling_label.grid(column=2, row=0)

        self.polling_interval_var = StringVar(value=str(POLLING_INTERVAL))
        polling_interval_spin = ttk.Spinbox(left_frame, width=4, from_=10, to=90, increment=10,
                                            textvariable=self.polling_interval_var, wrap=True)
        polling_interval_spin.grid(column=3, row=0)

        self.trips_choices = []
        self.trips_choices_var = StringVar(value=self.trips_choices)
        self.configured_trips = Listbox(left_frame, width=60, height=10,
                                        selectmode=BROWSE, listvariable=self.trips_choices_var)
        self.configured_trips.grid(column=0, columnspan=4, row=1, rowspan=5)
        # when selection changes update the monitored_trip_label var
        self.configured_trips.bind('<<ListboxSelect>>', self.update_selected_trip)

        add_trip_button = ttk.Button(left_frame, width=30, text="Configure new trip", command=self.add_trip)
        add_trip_button.grid(column=0, columnspan=4, row=6)

        self.interval_type_var = StringVar(value="duration")
        duration_radio = ttk.Radiobutton(left_frame, text="Duration", width=15,
                                         variable=self.interval_type_var, value="duration",
                                         command=self.select_interval_type)
        duration_radio.grid(column=0, columnspan=2, row=7)

        timeframe_radio = ttk.Radiobutton(left_frame, text="Timeframe", width=15,
                                          variable=self.interval_type_var, value="timeframe",
                                          command=self.select_interval_type)
        timeframe_radio.grid(column=2, columnspan=2, row=7)

        self.minutes_to_run_label = ttk.Label(left_frame, text="Run for (m):", width=15)
        self.minutes_to_run_label.grid(column=0, row=8)

        self.minutes_var = StringVar(value=TIME_TO_RUN)
        self.minutes_spin = ttk.Spinbox(left_frame, width=5, from_=10, to=90, increment=10,
                                        textvariable=self.minutes_var, wrap=True)
        self.minutes_spin.grid(column=1, row=8)

        self.start_time_label = ttk.Label(left_frame, text="Start time:", width=15, state=DISABLED)
        self.start_time_label.grid(column=2, row=8)

        now = datetime.now()
        self.start_hour_var = StringVar(value=str(now.hour))
        self.start_minute_var = StringVar(value=str((now.minute // 10) * 10))
        start_frame = ttk.Frame(left_frame, width=100, height=20)
        start_frame.grid_propagate(False)
        start_frame.grid(column=3, row=8)
        self.start_hour_spin = ttk.Spinbox(start_frame, width=4, from_=0, to=23, increment=1, wrap=True,
                                           textvariable=self.start_hour_var, state=DISABLED)
        self.start_minute_spin = ttk.Spinbox(start_frame, width=4, from_=0, to=50, increment=10, wrap=True,
                                             textvariable=self.start_minute_var, state=DISABLED)
        self.start_hour_spin.grid(column=0, row=0)
        self.start_minute_spin.grid(column=1, row=0)

        self.end_time_label = ttk.Label(left_frame, text="End time:", width=15, state=DISABLED)
        self.end_time_label.grid(column=2, row=9)

        now_30 = now + timedelta(minutes=30)
        self.end_hour_var = StringVar(value=str(now_30.hour))
        self.end_minute_var = StringVar(value=str((now_30.minute // 10) * 10))
        end_frame = ttk.Frame(left_frame, width=100, height=20)
        end_frame.grid_propagate(False)
        end_frame.grid(column=3, row=9)
        self.end_hour_spin = ttk.Spinbox(end_frame, width=4, from_=0, to=23, increment=1, wrap=True,
                                         textvariable=self.end_hour_var, state=DISABLED)
        self.end_minute_spin = ttk.Spinbox(end_frame, width=4, from_=0, to=50, increment=10, wrap=True,
                                           textvariable=self.end_minute_var, state=DISABLED)
        self.end_hour_spin.grid(column=0, row=0)
        self.end_minute_spin.grid(column=1, row=0)

        self.start_monitoring_button = ttk.Button(left_frame, width=30, text="Start monitoring",
                                                  command=self.start_monitoring)
        self.start_monitoring_button.state(["disabled"])
        self.start_monitoring_button.grid(column=0, columnspan=4, row=10)

        self.stop_monitoring_button = ttk.Button(left_frame, width=30, text="Stop monitoring",
                                                 command=self.stop_monitoring)
        self.stop_monitoring_button.state(["disabled"])
        self.stop_monitoring_button.grid(column=0, columnspan=4, row=11)

        for child in left_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        self.monitored_trip_var = StringVar(value="Choose a trip to monitor")
        monitored_trip_label = ttk.Label(right_frame, textvariable=self.monitored_trip_var)
        monitored_trip_label.grid(column=0, columnspan=2, row=0)

        log_frame = ttk.Frame(right_frame, width=64, height=20)
        log_frame.grid(column=0, columnspan=2, row=1)
        self.monitor_log = Text(log_frame, width=62, height=20, state=DISABLED, wrap=WORD,
                                background="white", padx=10, pady=10)
        self.monitor_log.grid(column=0, row=0, sticky="NWES")

        # log tags
        self.monitor_log.tag_configure("information", foreground="blue")
        self.monitor_log.tag_configure("logged_position", foreground="green")
        self.monitor_log.tag_configure("skipped_position", foreground="gray")

        self.log_scroll = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.monitor_log.yview)
        self.log_scroll.grid(column=1, row=0, sticky="NS")
        self.monitor_log.configure(yscrollcommand=self.log_scroll.set)

        next_poll_label = ttk.Label(right_frame, text="Next poll in (s):", width=30)
        next_poll_label.grid(column=0, row=2)

        self.timer_var = StringVar(value="--")
        self.timer_label = ttk.Label(right_frame, textvariable=self.timer_var, width=10)
        self.timer_label.grid(column=1, row=2)

        for child in right_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        # init widgets
        self.agency_name_var.set(get_agency_name(AGENCY_ID))
        self.fill_configured_trips()

    def update_selected_trip(self, event):
        """
        Update the monitored_trip_label var when configured_trips selection changes
        :param event: Bind event
        :return: None
        """
        idx_tuple = self.configured_trips.curselection()
        if len(idx_tuple) == 1:
            idx = int(idx_tuple[0])
            self.monitored_trip_var.set(value=self.trips_choices[idx])
            self.start_monitoring_button.configure(state="!disabled")

    def start_monitoring(self):
        """
        Start monitoring when start_monitoring_button is pressed
        :return: None
        """
        self.start_monitoring_button.configure(state="disabled")
        self.stop_monitoring_button.configure(state="!disabled")
        self.trip_id = self.monitored_trip_var.get().split("-")[0].replace(" ", "")
        self.trip, self.stops_object_list = get_monitor_config(self.session, self.trip_id)

        # compute time to run based on selected radio button
        if self.interval_type_var.get() == "duration":
            self.time_to_run = int(self.minutes_var.get())
            self.actual_start()
        else:
            # compute start time and duration
            start_time = datetime.combine(datetime.today(),
                                          time(int(self.start_hour_var.get()), int(self.start_minute_var.get())))
            end_time = datetime.combine(datetime.today(),
                                        time(int(self.end_hour_var.get()), int(self.end_minute_var.get())))
            if start_time < end_time:
                self.time_to_run = int((end_time - start_time).total_seconds() // 60)
            else:
                # fall back to default time to run in case end time is before start time
                self.time_to_run = TIME_TO_RUN
            if start_time < datetime.now():
                # fall back to default time to run in case end time is before start time
                self.time_to_run = TIME_TO_RUN
                self.write_log("start time in the past, starting now...")
                self.actual_start()
            else:
                wait_for = int((start_time - datetime.now()).total_seconds() * 1000)
                self.write_log(f"waiting until {start_time.astimezone().strftime('%H:%M:%S')}")
                self.after_actual_start_id = self.root.after(wait_for, self.actual_start)

    def actual_start(self):
        """
        Actual start of monitoring. Called with 'root.after' when timeframe radio button is selected.
        :return: None
        """
        self.after_actual_start_id = None
        self.write_log(f"polling vehicles for trip {self.trip_id} for {self.time_to_run} minutes")
        self.monitoring = True
        self.after_stop_polling_id = self.root.after(self.time_to_run * 60 * 1000, self.stop_monitoring)
        self.countdown(0)

    def stop_monitoring(self):
        """
        Stop monitoring anc cancel all pending scheduled calls
        :return: None
        """
        self.timer_var.set("--")
        # cancel polling if in progress
        if self.after_countdown_id:
            self.root.after_cancel(self.after_countdown_id)
            self.after_countdown_id = None
        # cancel total run time if in progress
        if self.after_stop_polling_id:
            self.root.after_cancel(self.after_stop_polling_id)
            self.after_stop_polling_id = None
        # cancel deferred start if in progress
        if self.after_actual_start_id:
            self.root.after_cancel(self.after_actual_start_id)
            self.after_actual_start_id = None
        self.start_monitoring_button.configure(state="!disabled")
        self.stop_monitoring_button.configure(state="disabled")
        self.monitoring = False
        self.write_log("polling stopped")

    def countdown(self, timer: int):
        """
        Countdown for set timer in seconds. Poll vehicles when reaches zero.
        :param timer: Countdown seconds
        :return: None
        """
        self.timer_var.set(value=str(timer))
        if timer > 0:
            self.after_countdown_id = self.root.after(1000, self.countdown, timer - 1)
        else:
            # poll vehicles from the API and insert in db
            self.timer_var.set("--")
            self.timer_label.update()
            if self.monitoring:
                vehicles = get_vehicles(self.trip_id)
                if not vehicles or len(vehicles) == 0:
                    self.write_log("no vehicles on route", 2)
                else:
                    for v in vehicles:
                        msg, msg_type = insert_position(self.session, self.trip, v, self.stops_object_list)
                        self.write_log(msg, msg_type)
                self.countdown(int(self.polling_interval_var.get()))

    def write_log(self, message, msg_type=0):
        """
        Writes a message at the end of monitor_log widgets, and scrolls to the end
        :param message: Message to write
        :param msg_type: 0 - information, 1 - vehicle position logged in db, 2 - skipped vehicles
        :return: None
        """
        tags = ["information", "logged_position", "skipped_position"]
        self.monitor_log["state"] = "normal"
        self.monitor_log.insert(END, f"{datetime.now().astimezone().strftime('%H:%M:%S')} - {message}\n",
                                (tags[msg_type]))
        self.monitor_log.see(END)
        self.monitor_log["state"] = "disabled"

    def select_interval_type(self):
        """
        Enable/disable widgets based on selected radio button
        :return: None
        """
        if self.interval_type_var.get() == "duration":
            self.minutes_to_run_label.configure(state=NORMAL)
            self.minutes_spin.configure(state=NORMAL)
            self.start_time_label.configure(state=DISABLED)
            self.start_hour_spin.configure(state=DISABLED)
            self.start_minute_spin.configure(state=DISABLED)
            self.end_time_label.configure(state=DISABLED)
            self.end_hour_spin.configure(state=DISABLED)
            self.end_minute_spin.configure(state=DISABLED)
        else:
            self.minutes_to_run_label.configure(state=DISABLED)
            self.minutes_spin.configure(state=DISABLED)
            self.start_time_label.configure(state=NORMAL)
            self.start_hour_spin.configure(state=NORMAL)
            self.start_minute_spin.configure(state=NORMAL)
            self.end_time_label.configure(state=NORMAL)
            self.end_hour_spin.configure(state=NORMAL)
            self.end_minute_spin.configure(state=NORMAL)

    def fill_configured_trips(self):
        """
        Populate configured_trips widget with the trips already stored in db
        :return: None
        """
        configured_trips_list = get_monitored_trip(self.session)
        if configured_trips_list:
            self.trips_choices = []
            for t in configured_trips_list:
                line = f"{t.trip_id} - line {t.route_short_name} ({t.route_long_name}) to {t.trip_headsign}"
                self.trips_choices.append(line)
                self.trips_choices_var.set(self.trips_choices)

    def add_trip(self):
        # TODO new window to add trip
        add_trip_window = Toplevel(self.root)
        add_trip_frame = ttk.Frame(add_trip_window, width=500, height=400)
        add_trip_frame.grid_propagate(False)
        add_trip_frame.grid(column=0, row=0)

        line_number_label = ttk.Label(add_trip_frame, text="Line number:")
        line_number_label.grid(column=0, row=0)

        self.line_number_var = StringVar(value="")
        self.line_number_var.trace_add("write", lambda *args: self.search_trips_button.configure(state=NORMAL))
        line_number_entry = ttk.Entry(add_trip_frame, width=10, textvariable=self.line_number_var)
        line_number_entry.grid(column=1, row=0, sticky="W")

        self.search_trips_button = ttk.Button(add_trip_frame, width=30, text="Search trips", state=DISABLED, command=self.search_trips)
        self.search_trips_button.grid(column=2, row=0)

        self.trips_var = StringVar(value="0")
        trip0_radio = ttk.Radiobutton(add_trip_frame, text="Trip 0", width=10, variable=self.trips_var, value="0", state=DISABLED, command=self.select_trip_dir)
        trip0_radio.grid(column=0, row=1)

        self.trip0_var = StringVar(value="")
        trip0_label = ttk.Label(add_trip_frame, width=30, textvariable=self.trip0_var)
        trip0_label.grid(column=1, row=1)

        trip1_radio = ttk.Radiobutton(add_trip_frame, text="Trip 1", width=10, variable=self.trips_var, value="1", state=DISABLED, command=self.select_trip_dir)
        trip1_radio.grid(column=0, row=2)

        self.trip1_var = StringVar(value="")
        trip1_label = ttk.Label(add_trip_frame, width=30, textvariable=self.trip1_var)
        trip1_label.grid(column=1, row=2)

        self.search_stops_button = ttk.Button(add_trip_frame, width=30, text="Search stops", state=DISABLED, command=self.search_stops)
        self.search_stops_button.grid(column=2, row=1, rowspan=2)

        stops_label = ttk.Label(add_trip_frame, text="Stops:", state=DISABLED)
        stops_label.grid(column=0, row=3)

        self.stops_choices = []
        self.stops_choices_var = StringVar(value=self.stops_choices)
        stops_list = Listbox(add_trip_frame, width=30, height=15, state=DISABLED, selectmode=EXTENDED, listvariable=self.stops_choices_var)
        stops_list.grid(column=1, row=3)
        stops_list.bind('<<ListboxSelect>>', self.stops_selected)

        self.add_trip_button = ttk.Button(add_trip_frame, width=30, text="Add trip", state=DISABLED, command=self.commit_trip)
        self.add_trip_button.grid(column=2, row=3)

        for child in add_trip_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        line_number_entry.focus()
        self.fill_configured_trips()

    def search_trips(self):
        # messagebox.showinfo(title="test", message=self.line_number_var.get())
        pass

    def select_trip_dir(self, event):
        pass

    def search_stops(self):
        pass

    def commit_trip(self):
        pass

    def stops_selected(self, event):
        self.add_trip_button.configure(state=NORMAL)
        pass
