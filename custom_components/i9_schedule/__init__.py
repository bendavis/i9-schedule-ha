"""i9 Schedule integration for Home Assistant."""

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_PASSWORD,
    CONF_PRE_EVENT_MINUTES,
    CONF_PRE_EVENT_UPDATE,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .i9_client import I9API, InvalidAuth

_LOGGER: logging.Logger = logging.getLogger(__name__)


class I9DataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching i9 Sports data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.config_entry = config_entry
        self.api: I9API | None = None
        self._last_known_children: set[str] = set()
        self._next_pre_event_update: float | None = None

        scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        if isinstance(scan_interval, int):
            scan_interval = timedelta(seconds=scan_interval)

        super().__init__(
            hass,
            _LOGGER,
            name="i9 Schedule",
            update_interval=scan_interval,
            always_update=False,
        )

    async def _async_update_data(self):
        """Fetch data from i9 API."""
        try:
            if self.api is None:
                session = async_get_clientsession(self.hass)
                self.api = I9API(
                    self.config_entry.data[CONF_USERNAME],
                    self.config_entry.data[CONF_PASSWORD],
                    session=session,
                )
                await self.api.authenticate()

            # Fetch teams and schedules
            teams = await self.api.get_teams()

            # Build consolidated data structure
            data = {}
            for team in teams:
                member_person_id = team["memberPersonId"]
                team_id = team["teamId"]
                child_name = team["memberPersonName"]

                if member_person_id not in data:
                    data[member_person_id] = {
                        "child_name": child_name,
                        "teams": [],
                    }

                # Fetch schedule for this team
                schedule = await self.api.get_schedule(member_person_id, team_id)

                team_data = {
                    "team_id": team_id,
                    "team_name": team["teamName"],
                    "sport": team.get("sportName", "Unknown"),
                    "schedule": schedule,
                    "next_game": self.api.get_next_game(schedule),
                }
                data[member_person_id]["teams"].append(team_data)

            # Detect new children and trigger entity discovery
            self._check_for_new_children(data)

            # Update next pre-event check time
            self._schedule_pre_event_update(data)

            return data

        except InvalidAuth as err:
            raise ConfigEntryAuthFailed(f"Invalid i9 credentials: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error connecting to i9 API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error fetching i9 schedule data: {err}") from err

    def _schedule_pre_event_update(self, data: dict) -> None:
        """Schedule a pre-event update if enabled."""
        from datetime import datetime

        pre_event_enabled = self.config_entry.options.get(CONF_PRE_EVENT_UPDATE, True)
        if not pre_event_enabled:
            return

        pre_event_minutes = self.config_entry.options.get(CONF_PRE_EVENT_MINUTES, 120)

        # Find the next game across all children
        next_game_time = None
        for child_data in data.values():
            for team_data in child_data.get("teams", []):
                next_game = team_data.get("next_game")
                if next_game:
                    game_dt = I9API._parse_datetime(next_game.get("startTime"))
                    if game_dt:
                        if next_game_time is None or game_dt < next_game_time:
                            next_game_time = game_dt

        if next_game_time:
            # Calculate pre-event update time
            pre_event_time = next_game_time - timedelta(minutes=pre_event_minutes)
            now = datetime.now()

            if pre_event_time > now:
                self._next_pre_event_update = pre_event_time.timestamp()
                time_until = int((pre_event_time - now).total_seconds() / 60)
                _LOGGER.debug("Next pre-event update scheduled in %d minutes", time_until)

    def _check_for_new_children(self, new_data: dict) -> None:
        """Check if new children were discovered and trigger entity addition."""
        new_child_ids = set(new_data.keys())

        # If new children found, signal to coordinator listeners
        if new_child_ids != self._last_known_children:
            new_children = new_child_ids - self._last_known_children
            if new_children:
                new_child_names = [new_data[cid]["child_name"] for cid in new_children]
                _LOGGER.info(
                    "New children discovered: %s. Entities will be created automatically.",
                    new_child_names,
                )

            # Update tracking
            self._last_known_children = new_child_ids


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up i9 Schedule from config entry."""
    coordinator = I9DataUpdateCoordinator(hass, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Set up service handlers
    async def handle_get_next_game(call):
        """Handle get_next_game service call."""
        child_id = call.data.get("child_id")
        data = coordinator.data

        if child_id not in data:
            _LOGGER.error("Child ID %s not found", child_id)
            return

        # Get next game from first team with one
        for team_data in data[child_id]["teams"]:
            if team_data["next_game"]:
                return {"result": [team_data["next_game"]]}

        return {"result": []}

    async def handle_get_games_filtered(call):
        """Handle get_games_filtered service call."""
        child_id = call.data.get("child_id")
        start_date = call.data.get("start_date")
        end_date = call.data.get("end_date")
        team_id = call.data.get("team_id")

        data = coordinator.data
        if child_id not in data:
            _LOGGER.error("Child ID %s not found", child_id)
            return {"result": []}

        all_games = []
        for team_data in data[child_id]["teams"]:
            if team_id and team_data["team_id"] != team_id:
                continue

            filtered = coordinator.api.filter_games(team_data["schedule"], start_date=start_date, end_date=end_date)
            all_games.extend(filtered)

        return {"result": all_games}

    async def handle_force_update(call):
        """Handle force_update service call."""
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "get_next_game_details", handle_get_next_game)
    hass.services.async_register(DOMAIN, "get_games_filtered", handle_get_games_filtered)
    hass.services.async_register(DOMAIN, "force_update", handle_force_update)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

        # Unregister services
        hass.services.async_remove(DOMAIN, "get_next_game_details")
        hass.services.async_remove(DOMAIN, "get_games_filtered")
        hass.services.async_remove(DOMAIN, "force_update")

    return unload_ok
