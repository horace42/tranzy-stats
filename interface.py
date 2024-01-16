from tkinter import *
from tkinter import ttk
from tkinter.font import Font
from tkinter import messagebox

from datetime import datetime, timedelta

from config import POLLING_INTERVAL


class MainWindow:
    def __init__(self, r: Tk):
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
        polling_interval_spin = ttk.Spinbox(left_frame, width=4, from_=10, to=90, increment=10, textvariable=self.polling_interval_var)
        polling_interval_spin.grid(column=3, row=0)

        self.configured_trips = Text(left_frame, width=45, height=10, state=DISABLED, wrap=WORD, background="white", padx=10, pady=10)
        self.configured_trips.grid(column=0, columnspan=4, row=1, rowspan=5)

        add_trip_button = ttk.Button(left_frame, width=30, text="Configure new trip")
        add_trip_button.grid(column=0, columnspan=4, row=6)

        self.interval_type_var = StringVar(value="duration")
        duration_radio = ttk.Radiobutton(left_frame, text="Duration", width=15, variable=self.interval_type_var, value="duration")
        duration_radio.grid(column=0, columnspan=2, row=7)

        timeframe_radio = ttk.Radiobutton(left_frame, text="Timeframe", width=15, variable=self.interval_type_var, value="timeframe")
        timeframe_radio.grid(column=2, columnspan=2, row=7)

        # TODO: visibility depending on the radio button selected
        minutes_to_run_label = ttk.Label(left_frame, text="Run for (m):", width=15)
        minutes_to_run_label.grid(column=0, row=8)

        self.minutes_var = StringVar(value="30")
        minutes_spin = ttk.Spinbox(left_frame, width=5, from_=10, to=90, increment=10, textvariable=self.minutes_var)
        minutes_spin.grid(column=1, row=8)

        start_time_label = ttk.Label(left_frame, text="Start time:", width=15)
        start_time_label.grid(column=2, row=8)

        now = datetime.now()
        self.start_hour_var = StringVar(value=str(now.hour))
        self.start_minute_var = StringVar(value=str((now.minute // 10) * 10))
        start_frame = ttk.Frame(left_frame, width=100, height=20)
        start_frame.grid_propagate(False)
        start_frame.grid(column=3, row=8)
        start_hour_spin = ttk.Spinbox(start_frame, width=4, from_=0, to=23, increment=1, textvariable=self.start_hour_var)
        start_minute_spin = ttk.Spinbox(start_frame, width=4, from_=0, to=50, increment=10, textvariable=self.start_minute_var)
        start_hour_spin.grid(column=0, row=0)
        start_minute_spin.grid(column=1, row=0)

        end_time_label = ttk.Label(left_frame, text="End time:", width=15)
        end_time_label.grid(column=2, row=9)

        now_30 = now + timedelta(minutes=30)
        self.end_hour_var = StringVar(value=str(now_30.hour))
        self.end_minute_var = StringVar(value=str((now_30.minute // 10) * 10))
        end_frame = ttk.Frame(left_frame, width=100, height=20)
        end_frame.grid_propagate(False)
        end_frame.grid(column=3, row=9)
        end_hour_spin = ttk.Spinbox(end_frame, width=4, from_=0, to=23, increment=1, textvariable=self.end_hour_var)
        end_minute_spin = ttk.Spinbox(end_frame, width=4, from_=0, to=50, increment=10, textvariable=self.end_minute_var)
        end_hour_spin.grid(column=0, row=0)
        end_minute_spin.grid(column=1, row=0)

        start_monitoring_button = ttk.Button(left_frame, width=30, text="Start monitoring")
        start_monitoring_button.grid(column=0, columnspan=4, row=10)

        stop_monitoring_button = ttk.Button(left_frame, width=30, text="Stop monitoring")
        stop_monitoring_button.grid(column=0, columnspan=4, row=11)

        for child in left_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)

        self.monitored_trip_var = StringVar(value="monitored trip...")
        monitored_trip_label = ttk.Label(right_frame, textvariable=self.monitored_trip_var)
        monitored_trip_label.grid(column=0, columnspan=2, row=0)

        self.monitor_log = Text(right_frame, width=64, height=20, state=DISABLED, wrap=WORD, background="white", padx=10, pady=10)
        self.monitor_log.grid(column=0, columnspan=2, row=1, rowspan=10)

        next_poll_label = ttk.Label(right_frame, text="Next poll in (s):", width=30)
        next_poll_label.grid(column=0, row=11)

        self.timer = StringVar(value="30")
        timer_label = ttk.Label(right_frame, textvariable=self.timer, width=10)
        timer_label.grid(column=1, row=11)

        for child in right_frame.winfo_children():
            child.grid_configure(padx=5, pady=10)
