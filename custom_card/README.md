# i9 Schedule Custom Lovelace Card

A beautiful, responsive Home Assistant Lovelace card for displaying your child's next i9 Sports game with all key information at a glance.

## Features

- ⚽ **Next Game at a Glance**: Date, time, location, opponent, and jersey color
- 🎨 **Jersey Color Styling**: Card accent automatically matches the jersey color
- ⏱ **Countdown Timer**: Shows days/hours until game starts
- 🎯 **Clean Design**: Matches Home Assistant's theme system
- 📱 **Responsive**: Works on mobile and desktop displays
- 🔄 **Refresh Button**: Manually trigger an update from i9 Sports API
- 🔌 **Integrates with i9_schedule**: Works seamlessly with the Home Assistant integration

## Installation

### Option A: HACS Installation (Recommended)

1. Go to **HACS** > **Frontend** > **Explore & Add Repositories**
2. Search for **i9 Schedule** and add it
3. Install the repository
4. Restart Home Assistant

### Option B: Manual Installation

1. Navigate to your Home Assistant config directory:
   ```bash
   cd ~/.homeassistant/
   ```

2. Create directories if they don't exist:
   ```bash
   mkdir -p www/community/i9-schedule-card
   ```

3. Download the card files to that folder:
   ```bash
   cd www/community/i9-schedule-card
   wget https://raw.githubusercontent.com/bendavis/i9-schedule-ha/main/custom_card/i9-schedule-card.js
   wget https://raw.githubusercontent.com/bendavis/i9-schedule-ha/main/custom_card/manifest.json
   ```

4. Add to your `configuration.yaml` or UI card resources:
   ```yaml
   lovelace:
     mode: yaml
     resources:
       - url: /local/community/i9-schedule-card/i9-schedule-card.js
         type: module
   ```

   **OR** through the UI:
   - Settings > Dashboards > Edit Dashboard (⋯ menu)
   - Click the ⋯ menu → Manage Resources
   - Create new resource: `/local/community/i9-schedule-card/i9-schedule-card.js`


5. Restart Home Assistant (not required with browser cache clear)

## Adding the Card to Your Dashboard

### YAML Mode

Edit your dashboard YAML and add:

```yaml
type: custom:i9-schedule-card
child_id: child_1
```

### UI Mode (Lovelace Visual Editor)

1. Edit your dashboard
2. Click **+ Add card** (bottom right)
3. Select **Custom card** at the bottom of the card picker
4. Find and select **i9 Schedule Card**
5. Configure with your `child_id`

## Configuration

### Basic Configuration

```yaml
type: custom:i9-schedule-card
child_id: child_1
```

### Finding Your Child ID

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click on **i9 Schedule**
3. View the entities
4. Find the entity names like: `sensor.i9_CHILD_ID_next_game_time`
5. Extract the `CHILD_ID` portion

Examples:
- Entity: `sensor.i9_child_1_next_game_time` → use `child_id: child_1`
- Entity: `sensor.i9_child_2_next_game_time` → use `child_id: child_2`

## What the Card Shows

### When There's an Upcoming Game

- **Game Date & Time**: When the game is scheduled
- **Team Name**: Your child's team
- **Opponent**: Who they're playing against
- **Location**: Venue name and field/court
- **Jersey Color**: What color to wear (with matching card accent)
- **Arrival Time**: When to be there
- **Home/Away**: Whether it's a home or away game
- **Countdown**: Days and hours until game time
- **Refresh Button**: Manually trigger data update

### When No Games Are Scheduled

Shows a friendly message: "No Upcoming Games"

## Jersey Colors

The card accent color automatically matches your child's jersey:

| Jersey Color | Card Theme |
|---|---|
| Red | 🔴 Red accent |
| Blue | 🔵 Blue accent |
| Green | 🟢 Green accent |
| Orange | 🟠 Orange accent |
| Purple | 🟣 Purple accent |
| Yellow | 🟡 Gold accent |
| Pink | 💗 Pink accent |
| Cyan | 🔷 Cyan accent |

## Troubleshooting

### Card Doesn't Load

1. **Check browser console**: Press F12, look for JavaScript errors
2. **Verify resource URL**: Ensure it matches your installation path
3. **Hard refresh**: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
4. **Restart Home Assistant**: Full restart if needed
5. **Check integration status**: Ensure i9_schedule is loaded without errors

### No Entity Data Shows

1. Verify `child_id` matches your entity names (check in Developer Tools)
2. Check i9 Schedule integration is set up and working
3. Ensure child has upcoming games in i9 Sports schedule

### Mobile Display Issues

The card is fully responsive. If sizing looks wrong:
- Check dashboard grid settings
- Try adjusting column count in dashboard settings
- Device may need a full refresh

## Using with Automations

The card works with i9_schedule services for advanced automations:

```yaml
alias: "Game reminder"
trigger:
  - platform: numeric_state
    entity_id: sensor.i9_child_1_minutes_until_next_game
    below: 60
    above: 55
action:
  - service: notify.notify
    data:
      message: "The next i9 game starts in about 1 hour!"
```

## Advanced Configuration

The card supports additional optional configuration:

```yaml
type: custom:i9-schedule-card
child_id: child_1
theme: default          # Optional: default theme
show_countdown: true    # Optional: show countdown timer
```

## Performance

- **Card Size**: ~5 KB (minified)
- **Update Frequency**: Synced with i9_schedule integration updates (default: every 48 hours + pre-event polling)
- **Real-time Updates**: Automatically refreshes when Home Assistant receives new data
- **Service Integration**: Refresh button calls `i9_schedule.force_update` service

## Related

- [i9 Schedule Integration](../README.md) - Main integration documentation
- [Home Assistant](https://www.home-assistant.io/) - Home automation platform
- [Lovelace UI](https://www.home-assistant.io/lovelace/) - Dashboard system

Found a bug or have a feature request? Open an issue on the [GitHub repository](https://github.com/bendavis/i9-schedule-ha/issues).

## License

MIT License - See LICENSE file for details
