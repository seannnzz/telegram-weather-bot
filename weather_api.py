"""
Weather API client for Singapore government weather data
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config import (
    RAINFALL_API_URL, WIND_SPEED_API_URL, WIND_DIRECTION_API_URL,
    REQUEST_TIMEOUT, MAX_RETRIES
)

logger = logging.getLogger(__name__)

class WeatherAPI:
    """Client for Singapore weather APIs"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, url: str) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return data
                        else:
                            logger.error(f"API returned error code: {data.get('code')}")
                            return None
                    else:
                        logger.warning(f"HTTP {response.status} for {url}, attempt {attempt + 1}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {url}, attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error requesting {url}: {e}, attempt {attempt + 1}")
            
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    async def get_rainfall_data(self) -> Optional[Dict]:
        """Get rainfall data from API"""
        logger.info("Fetching rainfall data...")
        return await self._make_request(RAINFALL_API_URL)
    
    async def get_wind_speed_data(self) -> Optional[Dict]:
        """Get wind speed data from API"""
        logger.info("Fetching wind speed data...")
        return await self._make_request(WIND_SPEED_API_URL)
    
    async def get_wind_direction_data(self) -> Optional[Dict]:
        """Get wind direction data from API"""
        logger.info("Fetching wind direction data...")
        return await self._make_request(WIND_DIRECTION_API_URL)
    
    async def get_all_weather_data(self) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
        """Get all weather data concurrently"""
        logger.info("Fetching all weather data...")
        
        tasks = [
            self.get_rainfall_data(),
            self.get_wind_speed_data(),
            self.get_wind_direction_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in concurrent request: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return tuple(processed_results)
    
    def find_station_by_name(self, stations: List[Dict], search_name: str) -> Optional[Dict]:
        """Find station by name (case-insensitive partial match)"""
        search_name = search_name.lower()
        
        for station in stations:
            if search_name in station['name'].lower():
                return station
        
        return None
    
    def find_station_by_id(self, stations: List[Dict], station_id: str) -> Optional[Dict]:
        """Find station by ID"""
        for station in stations:
            if station['id'].upper() == station_id.upper():
                return station
        
        return None
    
    def format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            # Parse the timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            # Convert to Singapore time and format
            return dt.strftime("%d %b %Y, %I:%M %p SGT")
        except Exception as e:
            logger.error(f"Error formatting timestamp {timestamp_str}: {e}")
            return timestamp_str
    
    def get_station_reading(self, readings: List[Dict], station_id: str) -> Optional[float]:
        """Get reading value for a specific station"""
        if not readings:
            return None
        
        # Get the latest reading
        latest_reading = readings[0]
        
        for data_point in latest_reading.get('data', []):
            if data_point['stationId'] == station_id:
                return data_point['value']
        
        return None
    
    def get_summary_stats(self, readings: List[Dict]) -> Dict:
        """Get summary statistics from readings"""
        if not readings:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}
        
        values = []
        latest_reading = readings[0]
        
        for data_point in latest_reading.get('data', []):
            if data_point['value'] is not None:
                values.append(data_point['value'])
        
        if not values:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}
        
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values)
        }
