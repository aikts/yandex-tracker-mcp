from dataclasses import dataclass

from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol


@dataclass
class AppContext:
    queues: QueuesProtocol
    issues: IssueProtocol
    fields: GlobalDataProtocol
    users: UsersProtocol
