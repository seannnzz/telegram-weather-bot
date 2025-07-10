"""
Telegram bot handlers for Singapore weather commands
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from weather_api import WeatherAPI
from config import (
    STATION_ALIASES, get_wind_direction_text, 
    MAX_MESSAGE_LENGTH, STATIONS_PER_PAGE
)

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = """
🌤️ **Singapore Weather Bot**

Welcome! I provide real-time weather data from Singapore's government APIs.

**Quick Start:**
/menu - Interactive menu with all options 🎯

**Available Commands:**
/weather - Get complete weather overview
/rainfall [station|all] - Get rainfall data
/windspeed [station|all] - Get wind speed data  
/winddirection [station|all] - Get wind direction data
/wind [station|all] - Get complete wind data
/stations - List all available stations
/help - Show detailed help message

**Examples:**
• `/weather` - Overall weather summary
• `/rainfall marina` - Rainfall at Marina area
• `/rainfall all` - All stations with rainfall data
• `/windspeed S108` - Wind speed at station S108
• `/wind marina` - Complete wind data for Marina area
• `/wind all` - Complete wind data from all stations

Type /menu for an interactive interface or /help for detailed instructions.
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command and unknown commands"""
    help_message = """
🌤️ **Singapore Weather Bot Help**

**Quick Access:**
🎯 `/menu` - Interactive menu with buttons for all commands

**Commands:**

🌦️ `/weather` - Complete weather overview
• Shows rainfall, wind speed, and wind direction summary
• Displays data from all active stations

🌧️ `/rainfall [station|all]` - Rainfall information
• Without station: Shows overall rainfall summary
• With station: Shows specific station rainfall
• With `all`: Shows all stations with rainfall data
• Unit: millimeters (mm)

💨 `/windspeed [station|all]` - Wind speed information  
• Without station: Shows overall wind speed summary
• With station: Shows specific station wind speed
• With `all`: Shows all stations with wind speed data
• Unit: knots

🧭 `/winddirection [station|all]` - Wind direction information
• Without station: Shows overall wind direction summary  
• With station: Shows specific station wind direction
• With `all`: Shows all stations with wind direction data
• Unit: degrees (with compass direction)

🌬️ `/wind [station|all]` - Complete wind data  
• Without station: Shows overall wind summary
• With station: Shows specific station wind speed and direction
• With `all`: Shows all stations with complete wind data
• Combined view of wind speed and direction

📍 `/stations` - List all monitoring stations
• Shows station IDs, names, and locations
• Use station ID or name in other commands

**Station Examples:**
• Use station ID: `S108`, `S60`, `S107`
• Use station name: `marina`, `sentosa`, `changi`
• Use partial name: `jurong`, `woodlands`, `clementi`
• Use `all` to see all stations: `/rainfall all`

**Tips:**
• Station names are case-insensitive
• Partial matches work (e.g., "marina" finds "Marina Gardens Drive")
• Data is updated every few minutes
• All times shown in Singapore Time (SGT)

Need help? Just type /help anytime!
"""
    
    await update.message.reply_text(
        help_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command - show interactive menu"""
    menu_text = """
🌤️ **Singapore Weather Bot Menu**

Choose an option below to get weather data:
    """
    
    # Create inline keyboard with menu options
    keyboard = [
        [InlineKeyboardButton("🌦️ Complete Weather", callback_data="weather")],
        [InlineKeyboardButton("🌧️ Rainfall Summary", callback_data="rainfall"),
         InlineKeyboardButton("🌧️ All Rainfall", callback_data="rainfall_all")],
        [InlineKeyboardButton("💨 Wind Speed Summary", callback_data="windspeed"),
         InlineKeyboardButton("💨 All Wind Speed", callback_data="windspeed_all")],
        [InlineKeyboardButton("🧭 Wind Direction Summary", callback_data="winddirection"),
         InlineKeyboardButton("🧭 All Wind Direction", callback_data="winddirection_all")],
        [InlineKeyboardButton("🌬️ Complete Wind Data", callback_data="wind")],
        [InlineKeyboardButton("📍 All Stations", callback_data="stations")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        menu_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def weather_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /weather command - complete weather overview"""
    await update.message.reply_text("🔄 Fetching complete weather data...")
    
    try:
        async with WeatherAPI() as api:
            rainfall_data, wind_speed_data, wind_direction_data = await api.get_all_weather_data()
            
            if not any([rainfall_data, wind_speed_data, wind_direction_data]):
                await update.message.reply_text(
                    "❌ **Error**: Unable to fetch weather data. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message_parts = ["🌤️ **Singapore Weather Overview**\n"]
            
            # Rainfall summary
            if rainfall_data:
                rainfall_stats = api.get_summary_stats(rainfall_data['data']['readings'])
                timestamp = api.format_timestamp(rainfall_data['data']['readings'][0]['timestamp'])
                
                message_parts.append(f"🌧️ **Rainfall** (as of {timestamp})")
                message_parts.append(f"• Average: {rainfall_stats['avg']:.1f} mm")
                message_parts.append(f"• Range: {rainfall_stats['min']:.1f} - {rainfall_stats['max']:.1f} mm")
                message_parts.append(f"• Active stations: {rainfall_stats['count']}")
                
                if rainfall_stats['max'] > 0:
                    # Find station with highest rainfall
                    max_station = None
                    max_value = 0
                    latest_reading = rainfall_data['data']['readings'][0]
                    
                    for data_point in latest_reading['data']:
                        if data_point['value'] > max_value:
                            max_value = data_point['value']
                            station = api.find_station_by_id(rainfall_data['data']['stations'], data_point['stationId'])
                            if station:
                                max_station = station['name']
                    
                    if max_station:
                        message_parts.append(f"• Highest: {max_value:.1f} mm at {max_station}")
                
                message_parts.append("")
            
            # Wind speed summary
            if wind_speed_data:
                wind_stats = api.get_summary_stats(wind_speed_data['data']['readings'])
                timestamp = api.format_timestamp(wind_speed_data['data']['readings'][0]['timestamp'])
                
                message_parts.append(f"💨 **Wind Speed** (as of {timestamp})")
                message_parts.append(f"• Average: {wind_stats['avg']:.1f} knots")
                message_parts.append(f"• Range: {wind_stats['min']:.1f} - {wind_stats['max']:.1f} knots")
                message_parts.append(f"• Active stations: {wind_stats['count']}")
                message_parts.append("")
            
            # Wind direction summary
            if wind_direction_data:
                timestamp = api.format_timestamp(wind_direction_data['data']['readings'][0]['timestamp'])
                message_parts.append(f"🧭 **Wind Direction** (as of {timestamp})")
                message_parts.append(f"• Data available from {len(wind_direction_data['data']['stations'])} stations")
                message_parts.append("")
            
            message_parts.append("💡 *Use /rainfall, /windspeed, or /winddirection with a station name for specific data*")
            
            message = "\n".join(message_parts)
            
            # Split message if too long
            if len(message) > MAX_MESSAGE_LENGTH:
                parts = message.split("\n\n")
                current_message = parts[0]
                
                for part in parts[1:]:
                    if len(current_message + "\n\n" + part) > MAX_MESSAGE_LENGTH:
                        await update.message.reply_text(current_message, parse_mode=ParseMode.MARKDOWN)
                        current_message = part
                    else:
                        current_message += "\n\n" + part
                
                if current_message:
                    await update.message.reply_text(current_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"Error in weather_handler: {e}")
        await update.message.reply_text(
            "❌ **Error**: Failed to fetch weather data. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )

async def rainfall_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rainfall command"""
    await update.message.reply_text("🔄 Fetching rainfall data...")
    
    try:
        async with WeatherAPI() as api:
            rainfall_data = await api.get_rainfall_data()
            
            if not rainfall_data:
                await update.message.reply_text(
                    "❌ **Error**: Unable to fetch rainfall data. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            stations = rainfall_data['data']['stations']
            readings = rainfall_data['data']['readings']
            
            # Check if user specified a station or "all"
            station_query = ' '.join(context.args).strip() if context.args else None
            
            if station_query and station_query.lower() == "all":
                # Show all stations data
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                message = f"🌧️ **All Rainfall Stations**\n\n"
                message += f"📅 **Time**: {timestamp}\n\n"
                
                # Get all station readings
                station_readings = []
                latest_reading = readings[0]
                
                for data_point in latest_reading['data']:
                    station = api.find_station_by_id(stations, data_point['stationId'])
                    if station:
                        station_readings.append((station['name'], station['id'], data_point['value']))
                
                # Sort by rainfall amount (descending)
                station_readings.sort(key=lambda x: x[2] if x[2] is not None else 0, reverse=True)
                
                # Build message with all stations
                for name, station_id, value in station_readings:
                    if value is not None:
                        message += f"📍 **{name}** ({station_id}): {value:.1f} mm\n"
                    else:
                        message += f"📍 **{name}** ({station_id}): No data\n"
                
                message += f"\n💡 *Use `/rainfall [station]` for specific station details*"
                
            elif station_query:
                # Find specific station
                station_id = STATION_ALIASES.get(station_query.lower())
                if station_id:
                    station = api.find_station_by_id(stations, station_id)
                else:
                    station = api.find_station_by_name(stations, station_query)
                    if not station:
                        station = api.find_station_by_id(stations, station_query)
                
                if not station:
                    await update.message.reply_text(
                        f"❌ **Station not found**: '{station_query}'\n\n"
                        "Use /stations to see available stations, or try:\n"
                        "• Station ID (e.g., S108)\n"
                        "• Station name (e.g., Marina)\n"
                        "• Partial name (e.g., jurong)\n"
                        "• Use `all` to see all stations",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # Get reading for specific station
                reading = api.get_station_reading(readings, station['id'])
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                
                message = f"🌧️ **Rainfall Data**\n\n"
                message += f"📍 **Station**: {station['name']} ({station['id']})\n"
                message += f"📅 **Time**: {timestamp}\n"
                message += f"🌧️ **Rainfall**: {reading if reading is not None else 'No data'} mm\n\n"
                
                if reading is not None:
                    if reading == 0:
                        message += "☀️ *No rainfall detected*"
                    elif reading < 2.5:
                        message += "🌦️ *Light rainfall*"
                    elif reading < 10:
                        message += "🌧️ *Moderate rainfall*"
                    elif reading < 50:
                        message += "⛈️ *Heavy rainfall*"
                    else:
                        message += "🌩️ *Very heavy rainfall*"
                
            else:
                # Show overall summary
                stats = api.get_summary_stats(readings)
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                
                message = f"🌧️ **Rainfall Summary**\n\n"
                message += f"📅 **Time**: {timestamp}\n"
                message += f"📊 **Statistics**:\n"
                message += f"• Average: {stats['avg']:.1f} mm\n"
                message += f"• Minimum: {stats['min']:.1f} mm\n"
                message += f"• Maximum: {stats['max']:.1f} mm\n"
                message += f"• Active stations: {stats['count']}\n\n"
                
                if stats['max'] > 0:
                    # Show top 3 stations with highest rainfall
                    station_values = []
                    latest_reading = readings[0]
                    
                    for data_point in latest_reading['data']:
                        if data_point['value'] > 0:
                            station = api.find_station_by_id(stations, data_point['stationId'])
                            if station:
                                station_values.append((station['name'], data_point['value']))
                    
                    if station_values:
                        station_values.sort(key=lambda x: x[1], reverse=True)
                        message += "🏆 **Top Rainfall Locations**:\n"
                        for i, (name, value) in enumerate(station_values[:3], 1):
                            message += f"{i}. {name}: {value:.1f} mm\n"
                else:
                    message += "☀️ *No rainfall detected across all stations*"
                
                message += f"\n\n💡 *Use `/rainfall [station]` for specific station data*"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"Error in rainfall_handler: {e}")
        await update.message.reply_text(
            "❌ **Error**: Failed to fetch rainfall data. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )

async def wind_speed_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /windspeed command"""
    await update.message.reply_text("🔄 Fetching wind speed data...")
    
    try:
        async with WeatherAPI() as api:
            wind_data = await api.get_wind_speed_data()
            
            if not wind_data:
                await update.message.reply_text(
                    "❌ **Error**: Unable to fetch wind speed data. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            stations = wind_data['data']['stations']
            readings = wind_data['data']['readings']
            
            # Check if user specified a station or "all"
            station_query = ' '.join(context.args).strip() if context.args else None
            
            if station_query and station_query.lower() == "all":
                # Show all stations data
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                message = f"💨 **All Wind Speed Stations**\n\n"
                message += f"📅 **Time**: {timestamp}\n\n"
                
                # Get all station readings
                station_readings = []
                latest_reading = readings[0]
                
                for data_point in latest_reading['data']:
                    station = api.find_station_by_id(stations, data_point['stationId'])
                    if station:
                        station_readings.append((station['name'], station['id'], data_point['value']))
                
                # Sort by wind speed (descending)
                station_readings.sort(key=lambda x: x[2] if x[2] is not None else 0, reverse=True)
                
                # Build message with all stations
                for name, station_id, value in station_readings:
                    if value is not None:
                        message += f"📍 **{name}** ({station_id}): {value:.1f} knots\n"
                    else:
                        message += f"📍 **{name}** ({station_id}): No data\n"
                
                message += f"\n💡 *Use `/windspeed [station]` for specific station details*"
                
            elif station_query:
                # Find specific station
                station_id = STATION_ALIASES.get(station_query.lower())
                if station_id:
                    station = api.find_station_by_id(stations, station_id)
                else:
                    station = api.find_station_by_name(stations, station_query)
                    if not station:
                        station = api.find_station_by_id(stations, station_query)
                
                if not station:
                    await update.message.reply_text(
                        f"❌ **Station not found**: '{station_query}'\n\n"
                        "Wind speed data is only available at selected stations.\n"
                        "Use /stations to see available stations or try `all` to see all stations.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # Get reading for specific station
                reading = api.get_station_reading(readings, station['id'])
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                
                message = f"💨 **Wind Speed Data**\n\n"
                message += f"📍 **Station**: {station['name']} ({station['id']})\n"
                message += f"📅 **Time**: {timestamp}\n"
                message += f"💨 **Wind Speed**: {reading if reading is not None else 'No data'} knots\n\n"
                
                if reading is not None:
                    # Wind speed categories (Beaufort scale approximation)
                    if reading < 1:
                        message += "🌬️ *Calm*"
                    elif reading < 7:
                        message += "🍃 *Light breeze*"
                    elif reading < 17:
                        message += "💨 *Moderate breeze*"
                    elif reading < 28:
                        message += "🌪️ *Strong breeze*"
                    else:
                        message += "⛈️ *Very strong wind*"
                
            else:
                # Show overall summary
                stats = api.get_summary_stats(readings)
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                
                message = f"💨 **Wind Speed Summary**\n\n"
                message += f"📅 **Time**: {timestamp}\n"
                message += f"📊 **Statistics**:\n"
                message += f"• Average: {stats['avg']:.1f} knots\n"
                message += f"• Minimum: {stats['min']:.1f} knots\n"
                message += f"• Maximum: {stats['max']:.1f} knots\n"
                message += f"• Active stations: {stats['count']}\n\n"
                
                # Show top 3 stations with highest wind speed
                station_values = []
                latest_reading = readings[0]
                
                for data_point in latest_reading['data']:
                    if data_point['value'] is not None:
                        station = api.find_station_by_id(stations, data_point['stationId'])
                        if station:
                            station_values.append((station['name'], data_point['value']))
                
                if station_values:
                    station_values.sort(key=lambda x: x[1], reverse=True)
                    message += "🏆 **Highest Wind Speed Locations**:\n"
                    for i, (name, value) in enumerate(station_values[:3], 1):
                        message += f"{i}. {name}: {value:.1f} knots\n"
                
                message += f"\n\n💡 *Use `/windspeed [station]` for specific station data*"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"Error in wind_speed_handler: {e}")
        await update.message.reply_text(
            "❌ **Error**: Failed to fetch wind speed data. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )

async def wind_direction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /winddirection command"""
    await update.message.reply_text("🔄 Fetching wind direction data...")
    
    try:
        async with WeatherAPI() as api:
            wind_data = await api.get_wind_direction_data()
            
            if not wind_data:
                await update.message.reply_text(
                    "❌ **Error**: Unable to fetch wind direction data. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            stations = wind_data['data']['stations']
            readings = wind_data['data']['readings']
            
            # Check if user specified a station or "all"
            station_query = ' '.join(context.args).strip() if context.args else None
            
            if station_query and station_query.lower() == "all":
                # Show all stations data
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                message = f"🧭 **All Wind Direction Stations**\n\n"
                message += f"📅 **Time**: {timestamp}\n\n"
                
                # Get all station readings
                station_readings = []
                latest_reading = readings[0]
                
                for data_point in latest_reading['data']:
                    station = api.find_station_by_id(stations, data_point['stationId'])
                    if station:
                        station_readings.append((station['name'], station['id'], data_point['value']))
                
                # Sort by station name
                station_readings.sort(key=lambda x: x[0])
                
                # Build message with all stations
                for name, station_id, value in station_readings:
                    if value is not None:
                        direction_text = get_wind_direction_text(value)
                        message += f"📍 **{name}** ({station_id}): {value}° ({direction_text})\n"
                    else:
                        message += f"📍 **{name}** ({station_id}): No data\n"
                
                message += f"\n💡 *Use `/winddirection [station]` for specific station details*"
                
            elif station_query:
                # Find specific station
                station_id = STATION_ALIASES.get(station_query.lower())
                if station_id:
                    station = api.find_station_by_id(stations, station_id)
                else:
                    station = api.find_station_by_name(stations, station_query)
                    if not station:
                        station = api.find_station_by_id(stations, station_query)
                
                if not station:
                    await update.message.reply_text(
                        f"❌ **Station not found**: '{station_query}'\n\n"
                        "Wind direction data is only available at selected stations.\n"
                        "Use /stations to see available stations or try `all` to see all stations.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # Get reading for specific station
                reading = api.get_station_reading(readings, station['id'])
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                
                message = f"🧭 **Wind Direction Data**\n\n"
                message += f"📍 **Station**: {station['name']} ({station['id']})\n"
                message += f"📅 **Time**: {timestamp}\n"
                
                if reading is not None:
                    direction_text = get_wind_direction_text(reading)
                    message += f"🧭 **Direction**: {reading}° ({direction_text})\n\n"
                    
                    # Add compass emoji based on direction
                    if 337.5 <= reading or reading < 22.5:
                        message += "⬆️ *Wind from North*"
                    elif 22.5 <= reading < 67.5:
                        message += "↗️ *Wind from Northeast*"
                    elif 67.5 <= reading < 112.5:
                        message += "➡️ *Wind from East*"
                    elif 112.5 <= reading < 157.5:
                        message += "↘️ *Wind from Southeast*"
                    elif 157.5 <= reading < 202.5:
                        message += "⬇️ *Wind from South*"
                    elif 202.5 <= reading < 247.5:
                        message += "↙️ *Wind from Southwest*"
                    elif 247.5 <= reading < 292.5:
                        message += "⬅️ *Wind from West*"
                    elif 292.5 <= reading < 337.5:
                        message += "↖️ *Wind from Northwest*"
                else:
                    message += f"🧭 **Direction**: No data\n"
                
            else:
                # Show overall summary
                timestamp = api.format_timestamp(readings[0]['timestamp'])
                
                message = f"🧭 **Wind Direction Summary**\n\n"
                message += f"📅 **Time**: {timestamp}\n"
                message += f"📊 **Available from {len(stations)} stations**\n\n"
                
                # Show all station directions
                station_directions = []
                latest_reading = readings[0]
                
                for data_point in latest_reading['data']:
                    if data_point['value'] is not None:
                        station = api.find_station_by_id(stations, data_point['stationId'])
                        if station:
                            direction_text = get_wind_direction_text(data_point['value'])
                            station_directions.append((station['name'], data_point['value'], direction_text))
                
                if station_directions:
                    station_directions.sort(key=lambda x: x[0])  # Sort by station name
                    message += "🏆 **Wind Directions by Station**:\n"
                    for name, degrees, direction in station_directions:
                        message += f"• {name}: {degrees}° ({direction})\n"
                
                message += f"\n\n💡 *Use `/winddirection [station]` for specific station data*"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"Error in wind_direction_handler: {e}")
        await update.message.reply_text(
            "❌ **Error**: Failed to fetch wind direction data. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )

async def stations_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stations command"""
    await update.message.reply_text("🔄 Fetching station information...")
    
    try:
        async with WeatherAPI() as api:
            # Get data from all APIs to show which stations support which data types
            rainfall_data, wind_speed_data, wind_direction_data = await api.get_all_weather_data()
            
            all_stations = {}
            
            # Collect all stations and their data types
            if rainfall_data:
                for station in rainfall_data['data']['stations']:
                    all_stations[station['id']] = {
                        'name': station['name'],
                        'location': station['location'],
                        'data_types': ['rainfall']
                    }
            
            if wind_speed_data:
                for station in wind_speed_data['data']['stations']:
                    if station['id'] in all_stations:
                        all_stations[station['id']]['data_types'].append('wind_speed')
                    else:
                        all_stations[station['id']] = {
                            'name': station['name'],
                            'location': station['location'],
                            'data_types': ['wind_speed']
                        }
            
            if wind_direction_data:
                for station in wind_direction_data['data']['stations']:
                    if station['id'] in all_stations:
                        all_stations[station['id']]['data_types'].append('wind_direction')
                    else:
                        all_stations[station['id']] = {
                            'name': station['name'],
                            'location': station['location'],
                            'data_types': ['wind_direction']
                        }
            
            if not all_stations:
                await update.message.reply_text(
                    "❌ **Error**: Unable to fetch station data. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Sort stations by name
            sorted_stations = sorted(all_stations.items(), key=lambda x: x[1]['name'])
            
            # Create station list message
            message_parts = ["📍 **Available Weather Stations**\n"]
            
            for station_id, station_info in sorted_stations:
                data_types = station_info['data_types']
                
                # Create data type indicators
                indicators = []
                if 'rainfall' in data_types:
                    indicators.append("🌧️")
                if 'wind_speed' in data_types:
                    indicators.append("💨")
                if 'wind_direction' in data_types:
                    indicators.append("🧭")
                
                indicators_str = "".join(indicators)
                
                station_line = f"• **{station_info['name']}** ({station_id}) {indicators_str}"
                message_parts.append(station_line)
            
            message_parts.append("\n**Legend:**")
            message_parts.append("🌧️ Rainfall data available")
            message_parts.append("💨 Wind speed data available")
            message_parts.append("🧭 Wind direction data available")
            
            message_parts.append("\n**Usage Examples:**")
            message_parts.append("• `/rainfall S108` - Get rainfall at Marina Gardens")
            message_parts.append("• `/windspeed marina` - Get wind speed at Marina area")
            message_parts.append("• `/winddirection sentosa` - Get wind direction at Sentosa")
            
            message = "\n".join(message_parts)
            
            # Split message if too long
            if len(message) > MAX_MESSAGE_LENGTH:
                # Split at logical points
                legend_start = message.find("\n**Legend:**")
                if legend_start > 0:
                    stations_message = message[:legend_start]
                    legend_message = message[legend_start:]
                    
                    await update.message.reply_text(stations_message, parse_mode=ParseMode.MARKDOWN)
                    await update.message.reply_text(legend_message, parse_mode=ParseMode.MARKDOWN)
                else:
                    # Split by number of stations
                    lines = message.split('\n')
                    current_message = lines[0] + '\n'
                    
                    for line in lines[1:]:
                        if len(current_message + line + '\n') > MAX_MESSAGE_LENGTH:
                            await update.message.reply_text(current_message, parse_mode=ParseMode.MARKDOWN)
                            current_message = line + '\n'
                        else:
                            current_message += line + '\n'
                    
                    if current_message.strip():
                        await update.message.reply_text(current_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"Error in stations_handler: {e}")
        await update.message.reply_text(
            "❌ **Error**: Failed to fetch station information. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )

async def wind_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /wind command - shows both windspeed and winddirection from all stations or specific station"""
    # Check if user specified a station or "all"
    station_query = ' '.join(context.args).strip() if context.args else None
    
    if station_query:
        await update.message.reply_text(f"🔄 Fetching wind data for '{station_query}'...")
    else:
        await update.message.reply_text("🔄 Fetching wind data from all stations...")
    
    try:
        async with WeatherAPI() as api:
            wind_speed_data, wind_direction_data = await asyncio.gather(
                api.get_wind_speed_data(),
                api.get_wind_direction_data()
            )
            
            if not wind_speed_data and not wind_direction_data:
                await update.message.reply_text(
                    "❌ **Error**: Unable to fetch wind data. Please try again later.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Collect all wind station data
            wind_stations = {}
            
            # Add wind speed data
            if wind_speed_data:
                for station in wind_speed_data['data']['stations']:
                    wind_stations[station['id']] = {
                        'name': station['name'],
                        'speed': api.get_station_reading(wind_speed_data['data']['readings'], station['id']),
                        'direction': None,
                        'direction_text': None
                    }
            
            # Add wind direction data
            if wind_direction_data:
                for station in wind_direction_data['data']['stations']:
                    if station['id'] in wind_stations:
                        direction = api.get_station_reading(wind_direction_data['data']['readings'], station['id'])
                        wind_stations[station['id']]['direction'] = direction
                        wind_stations[station['id']]['direction_text'] = get_wind_direction_text(direction) if direction is not None else None
                    else:
                        direction = api.get_station_reading(wind_direction_data['data']['readings'], station['id'])
                        wind_stations[station['id']] = {
                            'name': station['name'],
                            'speed': None,
                            'direction': direction,
                            'direction_text': get_wind_direction_text(direction) if direction is not None else None
                        }
            
            # Get timestamp from available data
            timestamp = None
            if wind_speed_data:
                timestamp = api.format_timestamp(wind_speed_data['data']['readings'][0]['timestamp'])
            elif wind_direction_data:
                timestamp = api.format_timestamp(wind_direction_data['data']['readings'][0]['timestamp'])
            
            if station_query and station_query.lower() == "all":
                # Show all stations data
                message = "🌬️ **Complete Wind Data (All Stations)**\n\n"
                if timestamp:
                    message += f"📅 **Time**: {timestamp}\n\n"
                
                # Sort stations by name
                sorted_stations = sorted(wind_stations.items(), key=lambda x: x[1]['name'])
                
                # Build message with all wind data
                for station_id, data in sorted_stations:
                    message += f"📍 **{data['name']}** ({station_id})\n"
                    
                    # Wind speed
                    if data['speed'] is not None:
                        message += f"💨 Speed: {data['speed']:.1f} knots"
                    else:
                        message += "💨 Speed: No data"
                    
                    # Wind direction
                    if data['direction'] is not None:
                        message += f" | 🧭 Direction: {data['direction']}° ({data['direction_text']})\n"
                    else:
                        message += " | 🧭 Direction: No data\n"
                    
                    message += "\n"
                
                message += "💡 *Use `/wind [station]` for specific station details*"
                
            elif station_query:
                # Find specific station
                station_id = STATION_ALIASES.get(station_query.lower())
                target_station = None
                target_station_id = None
                
                if station_id and station_id in wind_stations:
                    target_station = wind_stations[station_id]
                    target_station_id = station_id
                else:
                    # Search by name or ID
                    for sid, station_data in wind_stations.items():
                        if (station_query.lower() in station_data['name'].lower() or 
                            station_query.upper() == sid):
                            target_station = station_data
                            target_station_id = sid
                            break
                
                if not target_station:
                    await update.message.reply_text(
                        f"❌ **Station not found**: '{station_query}'\n\n"
                        "Wind data is only available at selected stations.\n"
                        "Use /stations to see available stations or try `all` to see all stations.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # Build message for specific station
                message = f"🌬️ **Wind Data - {target_station['name']}**\n\n"
                message += f"📍 **Station**: {target_station['name']} ({target_station_id})\n"
                if timestamp:
                    message += f"📅 **Time**: {timestamp}\n\n"
                
                # Wind speed details
                if target_station['speed'] is not None:
                    message += f"💨 **Wind Speed**: {target_station['speed']:.1f} knots\n"
                    
                    # Wind speed categories (Beaufort scale approximation)
                    if target_station['speed'] < 1:
                        message += "🌬️ *Calm*\n"
                    elif target_station['speed'] < 7:
                        message += "🍃 *Light breeze*\n"
                    elif target_station['speed'] < 17:
                        message += "💨 *Moderate breeze*\n"
                    elif target_station['speed'] < 28:
                        message += "🌪️ *Strong breeze*\n"
                    else:
                        message += "⛈️ *Very strong wind*\n"
                else:
                    message += "💨 **Wind Speed**: No data\n"
                
                # Wind direction details
                if target_station['direction'] is not None:
                    message += f"🧭 **Wind Direction**: {target_station['direction']}° ({target_station['direction_text']})\n"
                    
                    # Add compass emoji based on direction
                    direction = target_station['direction']
                    if 337.5 <= direction or direction < 22.5:
                        message += "⬆️ *Wind from North*\n"
                    elif 22.5 <= direction < 67.5:
                        message += "↗️ *Wind from Northeast*\n"
                    elif 67.5 <= direction < 112.5:
                        message += "➡️ *Wind from East*\n"
                    elif 112.5 <= direction < 157.5:
                        message += "↘️ *Wind from Southeast*\n"
                    elif 157.5 <= direction < 202.5:
                        message += "⬇️ *Wind from South*\n"
                    elif 202.5 <= direction < 247.5:
                        message += "↙️ *Wind from Southwest*\n"
                    elif 247.5 <= direction < 292.5:
                        message += "⬅️ *Wind from West*\n"
                    elif 292.5 <= direction < 337.5:
                        message += "↖️ *Wind from Northwest*\n"
                else:
                    message += "🧭 **Wind Direction**: No data\n"
                
                message += "\n💡 *Use `/wind all` to see all stations or `/wind [station]` for other stations*"
                
            else:
                # Show overall summary
                message = "🌬️ **Wind Data Summary**\n\n"
                if timestamp:
                    message += f"📅 **Time**: {timestamp}\n\n"
                
                # Calculate summary statistics
                speed_values = [data['speed'] for data in wind_stations.values() if data['speed'] is not None]
                direction_values = [data['direction'] for data in wind_stations.values() if data['direction'] is not None]
                
                if speed_values:
                    avg_speed = sum(speed_values) / len(speed_values)
                    max_speed = max(speed_values)
                    min_speed = min(speed_values)
                    
                    message += f"💨 **Wind Speed Statistics**:\n"
                    message += f"• Average: {avg_speed:.1f} knots\n"
                    message += f"• Range: {min_speed:.1f} - {max_speed:.1f} knots\n"
                    message += f"• Active stations: {len(speed_values)}\n\n"
                    
                    # Show top 3 stations with highest wind speed
                    station_speeds = [(data['name'], data['speed']) for data in wind_stations.values() if data['speed'] is not None]
                    station_speeds.sort(key=lambda x: x[1], reverse=True)
                    
                    if station_speeds:
                        message += "🏆 **Highest Wind Speed Locations**:\n"
                        for i, (name, speed) in enumerate(station_speeds[:3], 1):
                            message += f"{i}. {name}: {speed:.1f} knots\n"
                        message += "\n"
                
                if direction_values:
                    message += f"🧭 **Wind Direction Data**: Available from {len(direction_values)} stations\n\n"
                
                message += "💡 *Use `/wind [station]` for specific station data or `/wind all` to see all stations*"
            
            # Split message if too long
            if len(message) > MAX_MESSAGE_LENGTH:
                # Split at station boundaries
                lines = message.split('\n')
                current_message = lines[0] + '\n' + lines[1] + '\n\n'  # Include header
                
                for line in lines[2:]:
                    if len(current_message + line + '\n') > MAX_MESSAGE_LENGTH:
                        await update.message.reply_text(current_message, parse_mode=ParseMode.MARKDOWN)
                        current_message = line + '\n'
                    else:
                        current_message += line + '\n'
                
                if current_message.strip():
                    await update.message.reply_text(current_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"Error in wind_handler: {e}")
        await update.message.reply_text(
            "❌ **Error**: Failed to fetch wind data. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboard buttons"""
    query = update.callback_query
    await query.answer()
    
    # Extract the callback data
    data = query.data
    
    # Create a modified update object for callback queries
    # This allows us to reuse existing handlers
    callback_update = Update(
        update_id=update.update_id,
        message=query.message,
        callback_query=query
    )
    
    # Map callback data to appropriate handlers
    if data == "weather":
        await weather_handler(callback_update, context)
    elif data == "rainfall":
        await rainfall_handler(callback_update, context)
    elif data == "rainfall_all":
        # Create a new context with "all" argument
        context.args = ["all"]
        await rainfall_handler(callback_update, context)
    elif data == "windspeed":
        await wind_speed_handler(callback_update, context)
    elif data == "windspeed_all":
        # Create a new context with "all" argument
        context.args = ["all"]
        await wind_speed_handler(callback_update, context)
    elif data == "winddirection":
        await wind_direction_handler(callback_update, context)
    elif data == "winddirection_all":
        # Create a new context with "all" argument
        context.args = ["all"]
        await wind_direction_handler(callback_update, context)
    elif data == "wind":
        await wind_handler(callback_update, context)
    elif data == "stations":
        await stations_handler(callback_update, context)
    else:
        await query.edit_message_text(
            text="❌ **Error**: Unknown option selected.",
            parse_mode=ParseMode.MARKDOWN
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ **Error**: Something went wrong. Please try again later.\n\n"
            "If the problem persists, use /help for available commands.",
            parse_mode=ParseMode.MARKDOWN
        )
