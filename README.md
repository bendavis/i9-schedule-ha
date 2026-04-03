# i9 Schedule Integration

A Home Assistant custom integration for retrieving sports schedules from i9 Sports for your children.

## Features

- **Multi-child support**: Automatically creates separate entities for each child enrolled in i9 Sports
- **Game information**: Displays next game time, location, opponent, jersey color, arrival time, and more
- **Configurable polling**: Set your own update frequency (5 minutes to 24 hours)
- **Smart pre-event polling**: Automatically increases update frequency before games to ensure you get the latest info
- **Automation-friendly**: Exposes sensors, binary sensors, and services for creating automations
- **Example automations**: Includes templates for game reminders, notifications, and status updates

## Installation

### Via HACS (Recommended)

**Integration**

1. Open Home Assistant and go to **HACS**
2. Click **Integrations** in the sidebar
3. Click the **⋯ menu** → **Custom repositories**
4. Paste: `https://github.com/bendavis/i9-schedule-ha`
5. Select category: **Integration**
6. Click **Create**
7. Find **i9 Schedule** in the list and click it
8. Click **Install** → **Install**
9. Restart Home Assistant (Settings → System → Restart)

The integration is now installed! To display your games, you'll want the companion card:

**Custom Lovelace Card**

The custom card is now maintained in a separate repository:
- Repository: `https://github.com/bendavis/i9-schedule-card`
- See the [card repository](https://github.com/bendavis/i9-schedule-card) for installation instructions.

### Manual Installation

For a fully manual setup without HACS:

1. Download this repository: `https://github.com/bendavis/i9-schedule-ha/archive/refs/heads/main.zip`
2. Extract `custom_components/i9_schedule/` to `~/.homeassistant/custom_components/`
3. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Create Integration**
2. Search for and select "i9 Schedule"
3. Enter your i9 Sports login credentials (email and password)
4. Set your preferred update interval (default: 30 minutes)
5. Complete setup

## Entities

### Sensors (per child/team)

- `sensor.i9_<child>_next_game_time` - Start time of next upcoming game
- `sensor.i9_<child>_next_game_location` - Venue/field name
- `sensor.i9_<child>_next_game_opponent` - Opponent team name
- `sensor.i9_<child>_next_game_jersey_color` - Jersey color to wear
- `sensor.i9_<child>_next_game_arrival_time` - Recommended arrival/warm-up time
- `sensor.i9_<child>_next_game_home_away` - "Home" or "Away"
- `sensor.i9_<child>_minutes_until_next_game` - Minutes remaining until game
- `sensor.i9_<child>_next_game_team_name` - Team name

### Binary Sensors (per child)

- `binary_sensor.i9_<child>_game_today` - True if child has a game today
- `binary_sensor.i9_<child>_game_this_week` - True if child has a game this week

## Services

### `i9_schedule.get_next_game_details`

Returns detailed information about the next upcoming game for a child.

**Parameters:**
- `child_id` (string, required): The child's identifier

**Response:** Full game object with all available details

**Example automation:**
```yaml
service: i9_schedule.get_next_game_details
data:
  child_id: "child_1"
response_variable: game_details
```

### `i9_schedule.get_games_filtered`

Retrieves games within a specified date range, optionally filtered by team.

**Parameters:**
- `child_id` (string, required): The child's identifier
- `start_date` (string, optional): Start date (YYYY-MM-DD), default: today
- `end_date` (string, optional): End date (YYYY-MM-DD), default: 30 days from start
- `team_id` (string, optional): Specific team ID if child is on multiple teams

**Response:** Array of game objects

### `i9_schedule.force_update`

Manually trigger an immediate update from the i9 Sports API.

**Example:**
```yaml
service: i9_schedule.force_update
```

## Automation Examples

See `examples/automations.yaml` for complete automation templates including:

- Game reminder notifications (1 hour before)
- Daily game summary
- Jersey color change alerts
- Game cancellation notifications
- Multi-child game coordination

## Troubleshooting

### "Invalid username or password"
- Verify your i9 Sports login credentials
- Ensure your account has active children enrolled
- Check that your account isn't locked

### "No games found"
- Confirm children are enrolled in current season
- Check the i9 Sports website directly to verify schedule data exists
- Verify you're in the correct timezone

### Entities not updating
- Check Home Assistant logs for errors
- Try "Force Update" service call
- Verify integration is running (Settings → Devices & Services)

## Support

For issues, questions, or feature requests, please [open an issue on GitHub](https://github.com/bendavis/i9-schedule-ha/issues).

## License

MIT License - See LICENSE file for details
