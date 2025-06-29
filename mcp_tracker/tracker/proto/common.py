from dataclasses import dataclass


@dataclass
class YandexAuth:
    token: str | None = None
    cloud_org_id: str | None = None
    org_id: str | None = None
