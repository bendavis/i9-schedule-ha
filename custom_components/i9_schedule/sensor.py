"""Sensors for i9 Schedule integration."""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback as ha_callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .i9_client import I9API

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async def async_discover_entities():
        """Discover and add entities for all children."""
        entities = []
        
        if coordinator.data:
            for child_id, child_data in coordinator.data.items():
                child_name = child_data["child_name"]
                
                for team_data in child_data["teams"]:
                    team_id = team_data["team_id"]
                    team_name = team_data["team_name"]
                    
                    # Add sensor entities
                    entities.extend([
                        I9NextGameTimeSensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9NextGameLocationSensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9NextGameOpponentSensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9NextGameJerseyColorSensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9NextGameArrivalTimeSensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9NextGameHomeAwaySensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9MinutesUntilGameSensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9NextGameTeamNameSensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9GameTodayBinarySensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                        I9GameThisWeekBinarySensor(
                            coordinator, child_id, team_id, child_name, team_name
                        ),
                    ])
        
        if entities:
            async_add_entities(entities)
    
    # Initial discovery
    await async_discover_entities()
    
    # Set up listener for coordinator updates to discover new children
    @ha_callback
    def async_discover_new_children():
        """Discover new children on coordinator update."""
        hass.async_create_task(async_discover_entities())
    
    coordinator.async_add_listener(async_discover_new_children)


class I9BaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for i9 Schedule sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        child_id: str,
        team_id: str,
        child_name: str,
        team_name: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.child_id = child_id
        self.team_id = team_id
        self.child_name = child_name
        self.team_name = team_name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{child_id}_{team_id}")},
            name=f"{child_name} - {team_name}",
            manufacturer="i9 Sports",
            model="Game Schedule",
        )

    def _get_team_data(self) -> Optional[dict[str, Any]]:
        """Get team data from coordinator."""
        if not self.coordinator.data or self.child_id not in self.coordinator.data:
            return None
        
        child_data = self.coordinator.data[self.child_id]
        for team_data in child_data.get("teams", []):
            if team_data["team_id"] == self.team_id:
                return team_data
        return None

    def _get_next_game(self) -> Optional[dict[str, Any]]:
        """Get next game from team data."""
        team_data = self._get_team_data()
        if team_data:
            return team_data.get("next_game")
        return None


class I9NextGameTimeSensor(I9BaseSensor):
    """Sensor for next game time."""

    _attr_unique_id_suffix = "next_game_time"
    _attr_name = "Next Game Time"
    _attr_icon = "mdi:clock"

    @property
    def native_value(self) -> Optional[str]:
        """Return the next game start time."""
        game = self._get_next_game()
        if game:
            return game.get("startTimeString")
        return None


class I9NextGameLocationSensor(I9BaseSensor):
    """Sensor for next game location."""

    _attr_unique_id_suffix = "next_game_location"
    _attr_name = "Next Game Location"
    _attr_icon = "mdi:map-marker"

    @property
    def native_value(self) -> Optional[str]:
        """Return the next game location."""
        game = self._get_next_game()
        if game:
            return game.get("fieldName")
        return None


class I9NextGameOpponentSensor(I9BaseSensor):
    """Sensor for next game opponent."""

    _attr_unique_id_suffix = "next_game_opponent"
    _attr_name = "Next Game Opponent"
    _attr_icon = "mdi:trophy"

    @property
    def native_value(self) -> Optional[str]:
        """Return the next game opponent."""
        game = self._get_next_game()
        if game:
            return game.get("opponentTeamName")
        return None


class I9NextGameJerseyColorSensor(I9BaseSensor):
    """Sensor for next game jersey color."""

    _attr_unique_id_suffix = "next_game_jersey_color"
    _attr_name = "Next Game Jersey Color"
    _attr_icon = "mdi:shirt"

    @property
    def native_value(self) -> Optional[str]:
        """Return the next game jersey color."""
        game = self._get_next_game()
        if game:
            color = game.get("jerseyColor")
            return color if color else None
        return None


class I9NextGameArrivalTimeSensor(I9BaseSensor):
    """Sensor for next game arrival/warmup time."""

    _attr_unique_id_suffix = "next_game_arrival_time"
    _attr_name = "Next Game Arrival Time"
    _attr_icon = "mdi:car"

    @property
    def native_value(self) -> Optional[str]:
        """Return the next game arrival/warmup time."""
        game = self._get_next_game()
        if game:
            return game.get("practiceStartTimeString")
        return None


class I9NextGameHomeAwaySensor(I9BaseSensor):
    """Sensor for next game home/away."""

    _attr_unique_id_suffix = "next_game_home_away"
    _attr_name = "Next Game Home Away"
    _attr_icon = "mdi:home-variant"

    @property
    def native_value(self) -> Optional[str]:
        """Return home or away."""
        game = self._get_next_game()
        if game:
            return game.get("homeOrAway")
        return None


class I9MinutesUntilGameSensor(I9BaseSensor):
    """Sensor for minutes until next game."""

    _attr_unique_id_suffix = "minutes_until_next_game"
    _attr_name = "Minutes Until Next Game"
    _attr_icon = "mdi:hourglass-end"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    @property
    def native_value(self) -> Optional[int]:
        """Return minutes until next game."""
        game = self._get_next_game()
        if game:
            try:
                game_dt = I9API._parse_datetime(game.get("startTime"))
                if game_dt:
                    now = datetime.now()
                    minutes = int((game_dt - now).total_seconds() / 60)
                    return max(0, minutes)
            except Exception as err:
                _LOGGER.warning("Error calculating minutes until game: %s", err)
        return None


class I9NextGameTeamNameSensor(I9BaseSensor):
    """Sensor for next game team name."""

    _attr_unique_id_suffix = "next_game_team_name"
    _attr_name = "Next Game Team Name"
    _attr_icon = "mdi:badge-account"

    @property
    def native_value(self) -> Optional[str]:
        """Return the team name."""
        return self.team_name


class I9GameTodayBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for whether child has game today."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        child_id: str,
        team_id: str,
        child_name: str,
        team_name: str,
    ) -> None:
        """Initialize binary sensor."""
        super().__init__(coordinator)
        self.child_id = child_id
        self.team_id = team_id
        self.child_name = child_name
        self.team_name = team_name
        self._attr_unique_id = f"{DOMAIN}_{child_id}_{team_id}_game_today"
        self._attr_name = "Game Today"
        self._attr_icon = "mdi:calendar-check"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{child_id}_{team_id}")},
            name=f"{child_name} - {team_name}",
            manufacturer="i9 Sports",
            model="Game Schedule",
        )

    @property
    def is_on(self) -> bool:
        """Return True if child has a game today."""
        if not self.coordinator.data or self.child_id not in self.coordinator.data:
            return False
        
        child_data = self.coordinator.data[self.child_id]
        today = datetime.now().date()
        
        for team_data in child_data.get("teams", []):
            if team_data["team_id"] != self.team_id:
                continue
            
            for game in team_data.get("schedule", []):
                if game.get("cancelled"):
                    continue
                
                game_dt = I9API._parse_datetime(game.get("gameDate"))
                if game_dt and game_dt.date() == today:
                    return True
        
        return False


class I9GameThisWeekBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for whether child has game this week."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        child_id: str,
        team_id: str,
        child_name: str,
        team_name: str,
    ) -> None:
        """Initialize binary sensor."""
        super().__init__(coordinator)
        self.child_id = child_id
        self.team_id = team_id
        self.child_name = child_name
        self.team_name = team_name
        self._attr_unique_id = f"{DOMAIN}_{child_id}_{team_id}_game_this_week"
        self._attr_name = "Game This Week"
        self._attr_icon = "mdi:calendar-week"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{child_id}_{team_id}")},
            name=f"{child_name} - {team_name}",
            manufacturer="i9 Sports",
            model="Game Schedule",
        )

    @property
    def is_on(self) -> bool:
        """Return True if child has a game this week."""
        if not self.coordinator.data or self.child_id not in self.coordinator.data:
            return False
        
        child_data = self.coordinator.data[self.child_id]
        now = datetime.now()
        week_end = now + timedelta(days=7)
        
        for team_data in child_data.get("teams", []):
            if team_data["team_id"] != self.team_id:
                continue
            
            for game in team_data.get("schedule", []):
                if game.get("cancelled"):
                    continue
                
                game_dt = I9API._parse_datetime(
                    game.get("startTime") or game.get("gameDate")
                )
                if game_dt and now <= game_dt <= week_end:
                    return True
        
        return False
