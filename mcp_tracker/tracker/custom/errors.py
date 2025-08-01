class YandexTrackerError(Exception):
    pass


class IssueNotFound(YandexTrackerError):
    def __init__(self, issue_id: str):
        super().__init__(f"Issue with ID '{issue_id}' not found.")
        self.issue_id = issue_id
