"""Constants for i9 Schedule integration."""

from datetime import timedelta

DOMAIN = "i9_schedule"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
MIN_SCAN_INTERVAL = timedelta(seconds=300)
MAX_SCAN_INTERVAL = timedelta(hours=24)

# API
I9_BASE_URL = "https://be.i9sports.com"
I9_API_TIMEOUT = 30

# Entity naming
ATTR_CHILD_ID = "child_id"
ATTR_TEAM_ID = "team_id"
ATTR_MEMBER_PERSON_ID = "member_person_id"
ATTR_CHILD_NAME = "child_name"
ATTR_TEAM_NAME = "team_name"
ATTR_SPORT = "sport"

# Game attributes
ATTR_GAME_TIME = "game_time"
ATTR_LOCATION = "location"
ATTR_OPPONENT = "opponent"
ATTR_JERSEY_COLOR = "jersey_color"
ATTR_ARRIVAL_TIME = "arrival_time"
ATTR_HOME_AWAY = "home_away"
ATTR_CANCELLED = "cancelled"
ATTR_MINUTES_UNTIL = "minutes_until"
ATTR_GAME_DATE = "game_date"

# Sensor platforms
PLATFORMS = ["sensor", "binary_sensor"]
