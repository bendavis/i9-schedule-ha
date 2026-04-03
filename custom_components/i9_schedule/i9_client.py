"""i9 Sports API client."""

import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)

I9_BASE_URL = "https://be.i9sports.com"


class InvalidAuth(Exception):
    """Raised when authentication fails."""


class I9API:
    """Client for i9 Sports API."""

    def __init__(
        self,
        username: str,
        password: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialize API client."""
        self.username = username
        self.password = password
        self.session = session or aiohttp.ClientSession()
        self.token: Optional[str] = None
        self.member_id: Optional[int] = None

    async def authenticate(self) -> bool:
        """Authenticate to i9 Sports API."""
        try:
            payload = {
                "username": self.username,
                "password": self.password,
                "userType": "member",
                "code": "",
                "mfaemail": "",
                "mfaphone": "",
            }

            async with self.session.post(
                f"{I9_BASE_URL}/api/auth/login",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuth("Invalid username or password")
                resp.raise_for_status()

                body = await resp.json()
                self.token = body.get("token")

                # Try to get member_id from response
                self.member_id = (body.get("member") or {}).get("id")

                # Fallback: decode JWT for MemberId
                if not self.member_id and self.token:
                    self.member_id = self._decode_member_id(self.token)

                if not self.token or not self.member_id:
                    raise InvalidAuth("Failed to extract token or member ID from response")

                return True

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during authentication: %s", err)
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid JSON response during authentication: %s", err)
            raise InvalidAuth("Invalid response format") from err

    @staticmethod
    def _decode_member_id(token: str) -> Optional[int]:
        """Decode MemberId from JWT token."""
        try:
            parts = token.split(".")
            if len(parts) < 3:
                return None

            payload_b64 = parts[1]
            # Add padding if needed
            payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)

            payload_json = base64.urlsafe_b64decode(payload_b64)
            claims = json.loads(payload_json)
            return claims.get("MemberId")
        except Exception as err:
            _LOGGER.warning("Failed to decode JWT token: %s", err)
            return None

    async def get_teams(self) -> list[dict[str, Any]]:
        """Get all teams for the member."""
        if not self.token or not self.member_id:
            raise InvalidAuth("Not authenticated")

        try:
            async with self.session.get(
                f"{I9_BASE_URL}/api/member/GetMemberTeams",
                params={"memberId": self.member_id},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuth("Token expired or invalid")
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error fetching teams: %s", err)
            raise

    async def get_schedule(self, member_person_id: int, team_id: int) -> list[dict[str, Any]]:
        """Get schedule for a specific team."""
        if not self.token or not self.member_id:
            raise InvalidAuth("Not authenticated")

        try:
            async with self.session.get(
                f"{I9_BASE_URL}/api/member/GetFullSchedule",
                params={
                    "memberId": self.member_id,
                    "memberPersonId": member_person_id,
                    "teamId": team_id,
                },
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuth("Token expired or invalid")
                resp.raise_for_status()

                body = await resp.json()
                return body.get("memberSchedule", [])
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error fetching schedule: %s", err)
            raise

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def get_next_game(games: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """Find the next upcoming game from a schedule."""
        now = datetime.now()
        candidates = []

        for game in games:
            if game.get("cancelled"):
                continue

            game_dt = I9API._parse_datetime(game.get("startTime") or game.get("gameDate"))
            if game_dt and game_dt >= now:
                candidates.append((game_dt, game))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]

        return None

    @staticmethod
    def filter_games(
        games: list[dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Filter games by date range."""
        start = None
        end = None

        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                _LOGGER.warning("Invalid start_date format: %s", start_date)

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                # Include entire end day
                end = end.replace(hour=23, minute=59, second=59)
            except ValueError:
                _LOGGER.warning("Invalid end_date format: %s", end_date)

        if not start:
            start = datetime.now()
        if not end:
            end = start + timedelta(days=30)

        filtered = []
        for game in games:
            if game.get("cancelled"):
                continue

            game_dt = I9API._parse_datetime(game.get("startTime") or game.get("gameDate"))
            if game_dt and start <= game_dt <= end:
                filtered.append(game)

        # Sort by date
        filtered.sort(key=lambda g: I9API._parse_datetime(g.get("startTime")) or datetime.min)
        return filtered

    @staticmethod
    def summarize_game(
        game: dict[str, Any],
        child_name: str,
        team_name: str,
    ) -> dict[str, Any]:
        """Create a summary of game information."""
        game_dt = I9API._parse_datetime(game.get("startTime"))
        now = datetime.now()
        minutes_until = None
        if game_dt:
            minutes_until = int((game_dt - now).total_seconds() / 60)

        return {
            "player": child_name,
            "team": team_name,
            "date": (game.get("gameDate") or "")[:10],
            "arrive": game.get("practiceStartTimeString"),
            "game_time": game.get("startTimeString"),
            "location": game.get("fieldName"),
            "court_field": game.get("activityAreaName"),
            "home_away": game.get("homeOrAway"),
            "opponent": game.get("opponentTeamName"),
            "jersey_color": game.get("jerseyColor"),
            "cancelled": bool(game.get("cancelled")),
            "minutes_until": minutes_until,
        }
