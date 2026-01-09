import re
import copy
import logging

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class ActronAdvanceState:
    _state: dict = field(default_factory=dict)
    _timestamp: datetime = None
    _event_id: str = None

    @property
    def is_on(self) -> bool:
        return self._state["UserAirconSettings"]["isOn"]

    @property
    def turbo_mode(self) -> dict:
        return {
            "Supported": self._state["UserAirconSettings"]["TurboMode"]["Supported"],
            "Enabled": self._state["UserAirconSettings"]["TurboMode"]["Enabled"],
        }

    @property
    def quiet_mode(self) -> dict:
        return {
            "Supported": self._state["UserAirconSettings"]["QuietMode"],
            "Enabled": self._state["UserAirconSettings"]["QuietModeEnabled"],
            "Active": self._state["UserAirconSettings"]["QuietModeActive"],
        }

    @property
    def mode(self) -> str:
        return self._state["UserAirconSettings"]["Mode"]

    @property
    def fan_mode(self) -> dict:
        return {
            "Mode": self._state["UserAirconSettings"]["FanMode"],
            "Continuous": self._state["UserAirconSettings"]["FanMode"].endswith(
                "+CONT"
            ),
        }

    @property
    def vft(self) -> dict:
        return self._state["UserAirconSettings"]["VFT"]

    @property
    def zones(self) -> List[dict]:
        return self._state["RemoteZoneInfo"]

    @property
    def enabled_zones(self) -> List[bool]:
        return self._state["UserAirconSettings"]["EnabledZones"]

    @property
    def peripherals(self) -> List[dict]:
        return self._state["AirconSystem"]["Peripherals"]

    @property
    def servicing(self) -> dict:
        return self._state["Servicing"]

    def update_from_status(self, status: dict):
        # keys ['isOnline', 'timeSinceLastContact', 'lastStatusUpdate', 'lastKnownState']

        # event['timestamp'] example 2025-03-07T16:35:07.3687629+00:00
        aedt_zone = ZoneInfo("Australia/Sydney")
        # remove all microseconds as the server can seemingly sometimes send timestamps
        # with varying levels of precision and given we don't really care about
        # that it's easier to just strip it off
        self._timestamp = (
            datetime.fromisoformat(status["lastStatusUpdate"][:19])
            .replace(tzinfo=timezone.utc)
            .astimezone(aedt_zone)
        )
        self._state = copy.deepcopy(status["lastKnownState"])

    def update_from_event(self, event: dict):
        if event["type"] not in ["full-status-broadcast", "status-change-broadcast"]:
            return

        # we need at least one full-status-broadcast
        if event["type"] != "full-status-broadcast" and len(self._state) == 0:
            return

        changes = []

        # event['timestamp'] example 2025-03-07T16:35:07.3687629+00:00
        aedt_zone = ZoneInfo("Australia/Sydney")
        # remove all microseconds as the server can seemingly sometimes send timestamps
        # with varying levels of precision and given we don't really care about
        # that it's easier to just strip it off
        self._timestamp = (
            datetime.fromisoformat(event["timestamp"][:19])
            .replace(tzinfo=timezone.utc)
            .astimezone(aedt_zone)
        )
        self._event_id = event["id"]

        if event["type"] == "full-status-broadcast":
            logger.debug(
                f"Found full status broadcast from {self.event_timestamp(event)} which was {self.event_time_ago(event)} ago"
            )
            self._state = event["data"]
            return

        logger.debug(
            f"Merging status-change-broadcast from {self.event_timestamp(event)} which was {self.event_time_ago(event)} ago"
        )

        def recursive_merge(state, keys, value, full_key):
            # if at the final key, set the value
            if len(keys) == 1:
                # record changes - path, before, after
                # state could be a dict or a list here
                before = state[keys[0]]
                after = value
                if before != after:
                    changes.append((full_key, state[keys[0]], value))
                # keys[0] will be the final remaining key, so set the value
                state[keys[0]] = value
                return state

            # get the next key
            key = keys.pop(0)
            # merge the value
            state[key] = recursive_merge(state[key], keys, value, full_key)

            return state

        new_state = copy.deepcopy(self._state)
        for key, value in event["data"].items():
            # keys that start with @ are metadata - skip as not required
            if key.startswith("@"):
                continue

            # Split the key into parts
            parts = re.split(r"\.|\[|\]", key)
            # convert index numbers to integers
            parts = [int(part) if part.isdigit() else part for part in parts if part]

            new_state = recursive_merge(new_state, parts, value, key)

        self._state = new_state

        return changes

    @staticmethod
    def event_timestamp(event):
        # event['timestamp'] example 2025-03-07T16:35:07.3687629+00:00
        aedt_zone = ZoneInfo("Australia/Sydney")
        # remove all microseconds as the server can seemingly sometimes send timestamps
        # with varying levels of precision and given we don't really care about
        # that it's easier to just strip it off
        return (
            datetime.fromisoformat(event["timestamp"][:19])
            .replace(tzinfo=timezone.utc)
            .astimezone(aedt_zone)
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )

    @staticmethod
    def event_time_ago(event):
        # strip the microseconds from the timestamp to make parsing easier
        event_time = datetime.fromisoformat(event["timestamp"][:19]).replace(
            tzinfo=timezone.utc
        )
        now = datetime.now(timezone.utc).replace(microsecond=0)
        time_diff = now - event_time
        # sometimes the server returns timestamps in the future, so return 0 if that's the case
        return max(time_diff, timedelta(0))
