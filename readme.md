# Tranzy Stats
Collect statistics for specific transit routes. Designed and tested on CTP Cluj-Napoca using _Tranzy_ API.<br>
This was born out of necessity to find the best time to leave during rush hours to a new school location.<br>
Then it grew to exercise my Python beginner skills.
## Features
### Simple Tkinter GUI
* Main window
* Add new trip
* Modify trip
* Show statistics
### Statistics collection
* Multiple trips monitoring at once
* Collect statistics only between specific stops
* Start immediately for a specific period in minutes
  * or run between specific times (deferred start)
* Configurable polling interval in seconds
* Real-time logs highlighting saved vehicles
### Config file
Configure API endpoints, default values, tolerable distance and time, CSV file encoding.

**!!!!! Export your API key to TRANZY_KEY environment variable !!!!!**
### Export
Export trip statistics to csv (encoding configurable, default UTF-8 BOM)
### Raw logging
Option to enable saving of full JSON response for vehicles polling (could create huge files)
## Database
SQLite managed with SQLAlchemy ORM

![Database schema](/images/tranzy.db.png)
## User guide
The program uses Tkinter to display interfaces that allows the user to perform various actions. It uses following external libraries:
* SQLAlchemy - to create and access the database
* requests - to call endpoints of Tranzy API
* geopy - to calculate vehicle distances from stops
### Main window
The main windows offers on the left side configuration options, buttons to run actions or open additional windows. 
On the right side the selected trip(s) is displayed, a text box for real-time messages, time to next poll and end of monitoring, as well as a button to open the stats window.

![Main window](/images/main_window_idle.jpg)
* Options:
  * Polling interval - number of seconds between calls to the vehicles API
  * List of configured trips - select one or multiple trips to monitor. Select just one trip for: modify, export, delete and show statistics
  * Duration / Timeframe - the type of interval you want to set for monitoring
    * Run for - minutes for monitoring - starts as soon as Start monitoring button is pressed
    * Start time - desired start time. If in the past monitoring will start as soon as Start monitoring button is pressed for the default period.
    * End time - desired end time. Ignored if start time is in the past, or end time is before start time.
  * Raw logging - enables saving of all JSON responses from the vehicles API. Could generate big files as all vehicles on route are included in the response.

![JSON log](/images/raw_json_log.jpg)
* Buttons:
  * Add trip - opens dedicated window to configure a new trip.
  * Modify trip - opens dedicated window to display/change the monitored stops of the selected trip.
  * Export - exports selected trip data to a CSV file.
  * Delete - deletes the selected trip and all related data. Opens dialog to export to CSV before deletion.
  * Start monitoring - starts the monitoring of the selected trip(s).
  * Stop monitoring - stops the ongoing or scheduled monitoring.
  * Show stats - opens dedicated window to show the statistics for the selected trip.

**Scheduled start using 'Timeframe' option**

![Deferred start](/images/main_window_deferred_start.jpg)

**Ongoing monitoring (single trip)**

![Monitoring](/images/main_window_monitoring.jpg)

**Multiple trips selected (previous polling stopped)**

![Multiple trips](/images/main_window_multiple.jpg)

**Ongoing monitoring (multiple trips)**

![Monitoring](/images/main_window_monitoring_multiple.jpg)
### Add new trip
The window allows to:
* Input a line number and search the correspondent trips

![Add trip](/images/add_trip.jpg)
* Select the desired trip (way or return) and search the correspondent stops
* Select desired start/end stops to be monitored and add the trip to the database

![Add trip - stops selected](/images/add_trip_selected.jpg)
* The list of configured trips from the main window will be updated after the new trip is added

![Trip added](/images/add_trip_main_window.jpg)
### Modify trip
The window shows all the stops for the selected trip and selects in the list the currently configured stops for monitoring.

![Modify trip](/images/modify_trip.jpg)

Select new stops and press Apply changes to save the new configuration.

![New monitored stops](/images/modify_trip_new_selection.jpg)
### Export
With a single trip selected, press the Export button to save the trip's data to a CSV file in the 'exports' folder. File name contains route number, trip id and timestamp of the export.
### Delete
With a single trip selected, press the Delete button to delete all trip's data from the database, including its configuration. A prompt is made to offer possibility of export before deletion, or to cancel the operation.
### Real-time messages
The text box on the right side of the main window display various messages during monitoring:
* blue - information about the execution (waiting until start time, start polling, end polling)
* gray - information about vehicles not logged in the database because bad datetime or because they are outside monitored segment (distance to monitored stops is bigger than the value configured)
* green - information about vehicles saved in the database: trip id, vehicle label, timestamp, the closest stop and distance to it
### Show statistics
The window shows the monitored stops of the selected trip.

![Show stats](/images/show_stats.jpg)

Select start/end stops to display statistics and press Show stats button. On the right side a list will be displayed with timestamps a vehicle was in the start and end stops.

![Statistics](/images/show_stats_results.jpg)
## Tranzy OpenData API
https://api.tranzy.dev/v1/opendata/docs#/ <br>
This API partially implements the GTFS specification.<br>
More details can be found at: https://gtfs.org/.

Warning: This API is currently in its BETA version and is subject to change without notice.<br>
Please report any bugs or issues using the contact form at: https://tranzy.dev/accounts/contact

Terms and conditions: https://tranzy.dev/accounts/terms-and-conditions
### API token
Create an account and application per agency:
https://tranzy.dev/accounts/my-apps
### API agencies
* SCTP Iasi
* CTP Cluj
* RTEC&PUA Chisinau
* Eltrans Botosani
