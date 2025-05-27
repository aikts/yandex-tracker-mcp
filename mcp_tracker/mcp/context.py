from dataclasses import dataclass

from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol


@dataclass
class AppContext:
    queues: QueuesProtocol
    issues: IssueProtocol
