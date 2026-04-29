class YandexTrackerError(Exception):
    pass


class IssueNotFound(YandexTrackerError):
    def __init__(self, issue_id: str):
        super().__init__(f"Issue with ID '{issue_id}' not found.")
        self.issue_id = issue_id


class GoalNotFound(YandexTrackerError):
    def __init__(self, goal_id: str):
        super().__init__(f"Goal with ID '{goal_id}' not found.")
        self.goal_id = goal_id
