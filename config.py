"""
Configuration file for the Singapore Weather Bot
"""

import os

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# API URLs
RAINFALL_API_URL = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
WIND_SPEED_API_URL = "https://api-open.data.gov.sg/v2/real-time/api/wind-speed"
WIND_DIRECTION_API_URL = "https://api-open.data.gov.sg/v2/real-time/api/wind-direction"

# API request settings
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3

# Message formatting
MAX_MESSAGE_LENGTH = 4096
STATIONS_PER_PAGE = 10

# Common station mappings for user-friendly names
STATION_ALIASES = {
    "marina": "S108",
    "sentosa": "S60",
    "changi": "S107",
    "jurong": "S33",
    "woodlands": "S104",
    "tuas": "S115",
    "clementi": "S50",
    "bishan": "S217",
    "tampines": "S84",
    "punggol": "S81",
    "yishun": "S209",
    "hougang": "S221",
    "pasir ris": "S94",
    "bukit timah": "S90",
    "toa payoh": "S88",
    "ang mo kio": "S109",
    "geylang": "S215",
    "orchard": "S79",
    "scotts": "S111"
}

# Wind direction mappings
WIND_DIRECTIONS = {
    0: "N", 45: "NE", 90: "E", 135: "SE",
    180: "S", 225: "SW", 270: "W", 315: "NW"
}

def get_wind_direction_text(degrees):
    """Convert wind direction in degrees to compass direction"""
    if degrees is None:
        return "Unknown"
    
    # Normalize to 0-360 range
    degrees = degrees % 360
    
    # Find closest direction
    closest_direction = min(WIND_DIRECTIONS.keys(), key=lambda x: abs(x - degrees))
    
    # If within 22.5 degrees, return the direction, otherwise interpolate
    if abs(degrees - closest_direction) <= 22.5:
        return WIND_DIRECTIONS[closest_direction]
    else:
        # Find the two closest directions for interpolation
        directions = sorted(WIND_DIRECTIONS.keys())
        for i in range(len(directions)):
            if degrees < directions[i]:
                if i == 0:
                    return f"{WIND_DIRECTIONS[315]}-{WIND_DIRECTIONS[directions[i]]}"
                else:
                    return f"{WIND_DIRECTIONS[directions[i-1]]}-{WIND_DIRECTIONS[directions[i]]}"
        return f"{WIND_DIRECTIONS[directions[-1]]}-{WIND_DIRECTIONS[directions[0]]}"
