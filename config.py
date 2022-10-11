# General config for server

our_team = 6328
default_port = 8000  # Can override w/ command line argument
host = "0.0.0.0"
tba_key = "KDjqaOWmGYkyTSgPCQ7N0XSezbIBk1qzbuxz8s5WfdNtd6k34yL46vU73VnELIrP"
auto_schedule_min_count = 4  # Min number of submissions before next schedule
schedule_total_priority = 0.5  # Weight to apply to total when scheduling
message_expiration = 60  # Secs after sending before message expires
db_global = "global.db"  # Database for data not tied to specific games
db_games = "data_$GAME.db"  # Database for collected scouting data
image_dir = "images"  # Folder for image data
schedule_csv = "schedule.csv"  # CSV for offline scheduling
default_game = "2022"
admin_socket_port = 8001  # port for admin web socket
forward_socket_port = 8002  # port for forwarding server
bt_enable = True
bt_ports_outgoing = ["COM4", "COM5", "COM6", "COM7",
                     "COM8", "COM9"]  # current implementation
bt_showheartbeats = True
