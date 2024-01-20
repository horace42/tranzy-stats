from tkinter import *
from tkinter import ttk
from tkinter.font import Font
from tkinter import messagebox

from datetime import datetime, timedelta

from config import POLLING_INTERVAL, TIME_TO_RUN


class MainWindow:
    def __init__(self, r: Tk):
        self.after_countdown_id = None  # id to cancel scheduling of countdown (single polling)
        self.after_stop_polling_id = None  # id to cancel scheduling of stop polling (time to run)
        self.time_to_run = 5  # default time to run the polling (minutes)
        self.monitoring = False  # monitoring in progress
        self.trip_id = ""

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
                                            textvariable=self.polling_interval_var)
        polling_interval_spin.grid(column=3, row=0)

        self.trips_choices = []
        self.trips_choices_var = StringVar(value=self.trips_choices)
        self.configured_trips = Listbox(left_frame, width=60, height=10,
                                        selectmode=BROWSE, listvariable=self.trips_choices_var)
        self.configured_trips.grid(column=0, columnspan=4, row=1, rowspan=5)
        # when selection changes update the monitored_trip_label var
        self.configured_trips.bind('<<ListboxSelect>>', self.update_selected_trip)

        add_trip_button = ttk.Button(left_frame, width=30, text="Configure new trip")
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
                                        textvariable=self.minutes_var)
        self.minutes_spin.grid(column=1, row=8)

        self.start_time_label = ttk.Label(left_frame, text="Start time:", width=15, state=DISABLED)
        self.start_time_label.grid(column=2, row=8)

        now = datetime.now()
        self.start_hour_var = StringVar(value=str(now.hour))
        self.start_minute_var = StringVar(value=str((now.minute // 10) * 10))
        start_frame = ttk.Frame(left_frame, width=100, height=20)
        start_frame.grid_propagate(False)
        start_frame.grid(column=3, row=8)
        # TODO: implement check in start_monitoring > default time if end time not valid
        self.start_hour_spin = ttk.Spinbox(start_frame, width=4, from_=0, to=23, increment=1,
                                           textvariable=self.start_hour_var, state=DISABLED)
        self.start_minute_spin = ttk.Spinbox(start_frame, width=4, from_=0, to=50, increment=10,
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
        self.end_hour_spin = ttk.Spinbox(end_frame, width=4, from_=0, to=23, increment=1,
                                         textvariable=self.end_hour_var, state=DISABLED)
        self.end_minute_spin = ttk.Spinbox(end_frame, width=4, from_=0, to=50, increment=10,
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

        self.log_scroll = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.monitor_log.yview)
        self.log_scroll.grid(column=1, row=0, sticky="NS")
        self.monitor_log.configure(yscrollcommand=self.log_scroll.set)

        next_poll_label = ttk.Label(right_frame, text="Next poll in (s):", width=30)
        next_poll_label.grid(column=0, row=2)

        self.timer_var = StringVar(value="--")
        timer_label = ttk.Label(right_frame, textvariable=self.timer_var, width=10)
        timer_label.grid(column=1, row=2)

        for child in right_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        # self.monitor_log["state"] = "normal"
        # for i in range(30):
        #     self.monitor_log.insert(INSERT, chars=f"line {i}\n")

    def update_selected_trip(self, event):
        idxs = self.configured_trips.curselection()
        if len(idxs) == 1:
            idx = int(idxs[0])
            self.monitored_trip_var.set(value=self.trips_choices[idx])
            self.start_monitoring_button.configure(state="!disabled")

    def start_monitoring(self):
        self.start_monitoring_button.configure(state="disabled")
        self.stop_monitoring_button.configure(state="!disabled")
        self.trip_id = self.monitored_trip_var.get().split("-")[0].replace(" ", "")
        # call stop_monitoring after the set running time
        # TODO: compute self.time_to_run depending on chosen radiobutton
        self.write_log(f"polling vehicles for trip {self.trip_id} for {self.time_to_run} minutes")
        self.monitoring = True
        self.after_stop_polling_id = self.root.after(self.time_to_run * 60 * 1000, self.stop_monitoring)
        self.countdown(int(self.polling_interval_var.get()))

    def stop_monitoring(self):
        self.timer_var.set("--")
        if self.after_countdown_id:
            self.root.after_cancel(self.after_countdown_id)
            self.after_countdown_id = None
        if self.after_stop_polling_id:
            self.root.after_cancel(self.after_stop_polling_id)
            self.after_stop_polling_id = None
        self.start_monitoring_button.configure(state="!disabled")
        self.stop_monitoring_button.configure(state="disabled")
        self.monitoring = False
        self.write_log("polling stopped")

    def countdown(self, timer: int):
        self.timer_var.set(value=str(timer))
        if timer > 0:
            self.after_countdown_id = self.root.after(1000, self.countdown, timer - 1)
        else:
            # messagebox.showinfo(title="testing", message="Time's up!")
            # TODO: poll vehicles
            if self.monitoring:
                self.write_log("polling...")
                self.timer_var.set("--")
                self.countdown(int(self.polling_interval_var.get()))

    def write_log(self, message):
        self.monitor_log["state"] = "normal"
        self.monitor_log.insert(END, chars=f"{datetime.now().astimezone().strftime('%H:%M:%S')} - {message}\n")
        self.monitor_log.see(END)
        self.monitor_log["state"] = "disabled"
        # TODO: scroll to end

    def select_interval_type(self):
        # enable/disable widget based on selected radio button
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
