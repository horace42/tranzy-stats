# Tranzy Stats
Collect statistics for specific transit routes. Designed and tested on CTP Cluj-Napoca using _Tranzy_ API.<br>
This was born out of necessity to find the best time to leave during rush hours to a new school location.<br>
Then it grew to exercise my Python beginner skills.
## Features
### Simple Tkinter GUI
![Main window](tbd)<br>
![Add trip](tbd)
### Statistics collection
* Single trip monitoring at once
* Collect statistics only between specific stops
* Start immediately for a specific period in minutes
* Run between specific times (deferred start)
* Configurable polling interval in seconds
* Configure and save multiple trips for monitoring
* Realtime logs highlighting saved statistics
* Display seconds until next poll
### Config file
Configure API endpoints, default values and tolerable distance and time.
## Database
SQLite using SQLAlchemy ORM
![Database schema](/images/tranzy.db.png)
## Tranzy OpenData API
https://api.tranzy.dev/v1/opendata/docs#/ <br>
This API partially implements the GTFS specification.<br>
More details can be found at: https://gtfs.org/.

Warning: This API is currently in its BETA version and is subject to change without notice.<br>
Please report any bugs or issues using the contact form at: https://tranzy.dev/accounts/contact

Terms and conditions: https://tranzy.dev/accounts/terms-and-conditions
### API token
Create an account and tokens per agency:
https://tranzy.dev/accounts/my-apps
### API agencies
* SCTP Iasi
* CTP Cluj
* RTEC&PUA Chisinau
* Eltrans Botosani
