class YandexTrackerError(Exception):
    pass


class IssueNotFound(YandexTrackerError):
    def __init__(self, issue_id: str):
        super().__init__(f"Issue with ID '{issue_id}' not found.")
        self.issue_id = issue_id


class AttachmentNotFound(YandexTrackerError):
    def __init__(self, issue_id: str, attachment_id: str, file_name: str):
        super().__init__(
            f"Attachment '{file_name}' (id={attachment_id}) "
            f"for issue '{issue_id}' not found."
        )
        self.issue_id = issue_id
        self.attachment_id = attachment_id
        self.file_name = file_name
