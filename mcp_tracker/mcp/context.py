from dataclasses import dataclass

from mcp_tracker.tracker.custom.client import TrackerClient


@dataclass
class AppContext:
    tracker: TrackerClient
