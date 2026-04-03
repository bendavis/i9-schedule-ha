/**
 * i9 Schedule Card
 * A custom Lovelace card for displaying i9 Sports game schedules
 * Integrates with the i9_schedule Home Assistant integration
 */

class I9ScheduleCard extends HTMLElement {
  /**
   * Configuration element for the card editor
   */
  static getConfigElement() {
    return document.createElement("i9-schedule-card-editor");
  }

  /**
   * Default configuration for new cards
   */
  static getStubConfig() {
    return {
      child_id: "child_1",
      theme: "default",
      show_countdown: true
    };
  }

  /**
   * Initialize the custom element with shadow DOM
   */
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._unsubscribeStateUpdated = null;
  }

  /**
   * Set configuration from the Lovelace dashboard
   */
  setConfig(config) {
    if (!config.child_id) {
      throw new Error("child_id is required in card configuration");
    }
    this.config = config;
  }

  /**
   * Get the card size for Lovelace grid layout
   */
  getCardSize() {
    return 4;
  }

  /**
   * Set Home Assistant object and subscribe to state changes
   */
  set hass(hass) {
    this._hass = hass;
    this._updateCard();
  }

  /**
   * Get all entity IDs needed for this card
   */
  _getEntityIds() {
    const { child_id } = this.config;
    return [
      `sensor.i9_${child_id}_next_game_time`,
      `sensor.i9_${child_id}_next_game_location`,
      `sensor.i9_${child_id}_next_game_opponent`,
      `sensor.i9_${child_id}_next_game_jersey_color`,
      `sensor.i9_${child_id}_next_game_arrival_time`,
      `sensor.i9_${child_id}_next_game_home_away`,
      `sensor.i9_${child_id}_minutes_until_next_game`,
      `sensor.i9_${child_id}_next_game_team_name`,
      `binary_sensor.i9_${child_id}_game_today`
    ];
  }

  /**
   * Get entity state safely
   */
  _getEntityState(entityId) {
    const entity = this._hass?.states?.[entityId];
    return entity?.state || "N/A";
  }

  /**
   * Get entity attributes safely
   */
  _getEntityAttributes(entityId) {
    const entity = this._hass?.states?.[entityId];
    return entity?.attributes || {};
  }

  /**
   * Update the card rendering
   */
  _updateCard() {
    if (!this.config || !this._hass) return;

    const { child_id } = this.config;

    // Get all entity states
    const gameTime = this._getEntityState(`sensor.i9_${child_id}_next_game_time`);
    const location = this._getEntityState(`sensor.i9_${child_id}_next_game_location`);
    const opponent = this._getEntityState(`sensor.i9_${child_id}_next_game_opponent`);
    const jerseyColor = this._getEntityState(`sensor.i9_${child_id}_next_game_jersey_color`);
    const arrivalTime = this._getEntityState(`sensor.i9_${child_id}_next_game_arrival_time`);
    const homeAway = this._getEntityState(`sensor.i9_${child_id}_next_game_home_away`);
    const minutes = this._getEntityState(`sensor.i9_${child_id}_minutes_until_next_game`);
    const teamName = this._getEntityState(`sensor.i9_${child_id}_next_game_team_name`);

    // Get location attributes for court/field info
    const locationAttrs = this._getEntityAttributes(
      `sensor.i9_${child_id}_next_game_location`
    );
    const court = locationAttrs?.court || "";

    // Format countdown text
    let countdownText = "No upcoming games";
    if (minutes !== "N/A" && minutes !== "unknown") {
      const minutesNum = parseInt(minutes);
      if (!isNaN(minutesNum)) {
        const days = Math.floor(minutesNum / 1440);
        const hours = Math.floor((minutesNum % 1440) / 60);
        const mins = minutesNum % 60;

        if (days > 0) {
          countdownText = `${days}d ${hours}h away`;
        } else if (hours > 0) {
          countdownText = `${hours}h ${mins}m away`;
        } else {
          countdownText = `${mins}m away`;
        }
      }
    }

    // Render the card
    this._render(
      gameTime,
      location,
      opponent,
      jerseyColor,
      arrivalTime,
      homeAway,
      countdownText,
      teamName,
      court
    );
  }

  /**
   * Map jersey color name to hex value
   */
  _getJerseyColor(colorName) {
    const colorMap = {
      red: "#ef4444",
      blue: "#3b82f6",
      green: "#10b981",
      yellow: "#eab308",
      orange: "#f97316",
      purple: "#a855f7",
      pink: "#ec4899",
      indigo: "#6366f1",
      cyan: "#06b6d4",
      lime: "#84cc16",
      violet: "#7c3aed",
      rose: "#f43f5e"
    };
    return colorMap[colorName?.toLowerCase()] || "#3b82f6";
  }

  /**
   * Render the card UI
   */
  _render(
    gameTime,
    location,
    opponent,
    jerseyColor,
    arrivalTime,
    homeAway,
    countdown,
    teamName,
    court
  ) {
    const accentColor = this._getJerseyColor(jerseyColor);
    const noGames = gameTime === "N/A" || gameTime === "unknown";

    const html = `
      <ha-card>
        <div class="card-content">
          ${noGames ? this._renderNoGames() : this._renderGame(
            gameTime,
            location,
            opponent,
            jerseyColor,
            arrivalTime,
            homeAway,
            countdown,
            teamName,
            court,
            accentColor
          )}
        </div>
      </ha-card>
    `;

    this.shadowRoot.innerHTML = html + this._getStyles(accentColor);
    this._attachEventListeners();
  }

  /**
   * Render no games message
   */
  _renderNoGames() {
    return `
      <div class="no-games">
        <div class="emoji">⚽</div>
        <div class="title">No Upcoming Games</div>
        <div class="subtitle">Check back soon for schedule updates</div>
      </div>
    `;
  }

  /**
   * Render game details
   */
  _renderGame(
    gameTime,
    location,
    opponent,
    jerseyColor,
    arrivalTime,
    homeAway,
    countdown,
    teamName,
    court,
    accentColor
  ) {
    return `
      <div class="game-card">
        <div class="header" style="border-left: 4px solid ${accentColor}">
          <div class="header-top">
            <div class="game-date">${gameTime}</div>
            <button class="refresh-btn" title="Refresh game data">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
              </svg>
            </button>
          </div>
          <div class="team-name">${teamName}</div>
        </div>

        <div class="body">
          <div class="info-section">
            <div class="info-row">
              <span class="label">🏈 vs</span>
              <span class="value">${opponent}</span>
            </div>
            <div class="info-row">
              <span class="label">📍 Location</span>
              <span class="value">${location}</span>
            </div>
            ${court ? `<div class="info-row secondary"><span class="label">Field</span><span class="value">${court}</span></div>` : ""}
          </div>

          <div class="divider"></div>

          <div class="info-section">
            <div class="info-row">
              <span class="label">⏰ Game Time</span>
              <span class="value primary">${gameTime}</span>
            </div>
            <div class="info-row">
              <span class="label">📋 Arrive by</span>
              <span class="value">${arrivalTime}</span>
            </div>
          </div>

          <div class="divider"></div>

          <div class="info-section">
            <div class="info-row">
              <span class="label">👕 Jersey</span>
              <span class="jersey-badge" style="background-color: ${accentColor}">${jerseyColor.toUpperCase()}</span>
            </div>
            <div class="info-row">
              <span class="label">🏠 Game Type</span>
              <span class="value">${homeAway}</span>
            </div>
          </div>

          <div class="countdown">
            <span>⏱ ${countdown}</span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Get card styles
   */
  _getStyles(accentColor) {
    return `
      <style>
        :host {
          --primary-color: ${accentColor};
        }

        ha-card {
          display: block;
          height: 100%;
        }

        .card-content {
          padding: 0;
        }

        /* No Games State */
        .no-games {
          padding: 40px 20px;
          text-align: center;
          color: var(--secondary-text-color);
        }

        .no-games .emoji {
          font-size: 48px;
          margin-bottom: 12px;
        }

        .no-games .title {
          font-size: 18px;
          font-weight: 600;
          color: var(--primary-text-color);
          margin-bottom: 4px;
        }

        .no-games .subtitle {
          font-size: 13px;
        }

        /* Game Card */
        .game-card {
          display: flex;
          flex-direction: column;
          height: 100%;
        }

        .header {
          padding: 16px;
          background: linear-gradient(
            135deg,
            var(--primary-color) 0%,
            rgba(255, 255, 255, 0.05) 100%
          );
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .header-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .game-date {
          font-size: 14px;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.8);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .team-name {
          font-size: 18px;
          font-weight: 700;
          color: var(--card-background-color);
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }

        .refresh-btn {
          background: rgba(255, 255, 255, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-radius: 6px;
          padding: 6px;
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }

        .refresh-btn:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: rotate(15deg);
        }

        .refresh-btn:active {
          transform: rotate(-15deg);
        }

        .body {
          padding: 16px;
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .info-section {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .info-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 14px;
        }

        .info-row.secondary {
          margin-left: 20px;
          font-size: 13px;
          opacity: 0.85;
        }

        .label {
          color: var(--secondary-text-color);
          font-weight: 500;
          flex: 0 0 auto;
        }

        .value {
          color: var(--primary-text-color);
          font-weight: 500;
          text-align: right;
          flex: 1;
          margin-left: 12px;
          word-break: break-word;
        }

        .value.primary {
          font-size: 15px;
          font-weight: 600;
          color: var(--primary-color);
        }

        .jersey-badge {
          display: inline-block;
          padding: 6px 12px;
          border-radius: 16px;
          color: white;
          font-weight: 600;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .divider {
          height: 1px;
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.1),
            transparent
          );
          margin: 4px 0;
        }

        .countdown {
          background: linear-gradient(
            135deg,
            rgba(74, 222, 128, 0.1),
            rgba(59, 130, 246, 0.1)
          );
          border: 1px solid rgba(74, 222, 128, 0.2);
          border-radius: 8px;
          padding: 12px;
          text-align: center;
          font-weight: 600;
          color: var(--primary-color);
          margin-top: 4px;
        }
      </style>
    `;
  }

  /**
   * Attach event listeners to buttons
   */
  _attachEventListeners() {
    const refreshBtn = this.shadowRoot.querySelector(".refresh-btn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => this._handleRefresh());
    }
  }

  /**
   * Handle refresh button click
   */
  async _handleRefresh() {
    if (!this._hass) return;

    try {
      await this._hass.callService("i9_schedule", "force_update", {});
    } catch (error) {
      console.error("Error calling force_update service:", error);
    }
  }

  /**
   * Cleanup when element is disconnected
   */
  disconnectedCallback() {
    if (this._unsubscribeStateUpdated) {
      this._unsubscribeStateUpdated();
    }
  }
}

// Register the custom element
customElements.define("i9-schedule-card", I9ScheduleCard);

// HACS configuration
window.customCards = window.customCards || [];
window.customCards.push({
  type: "i9-schedule-card",
  name: "i9 Schedule Card",
  description: "Display i9 Sports game schedules",
  preview: true,
  documentationURL: "https://github.com/bendavis/i9-schedule-ha"
});
