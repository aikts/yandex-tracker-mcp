"""Probe the live Tracker checklist API for the things mocked tests cannot answer.

The docs for `PATCH /v3/issues/{id}/checklistItems/{itemId}` contradict
themselves - the path names one item, the example body is an array of all of
them - so only a real request settles what the endpoint takes. This script also
checks the cases the fixtures hard-code by hand: a numeric uid `assignee`, a
`quarter` deadline, and whether `text` really is required on every edit.

It writes to a real issue: every item it creates is deleted again in a `finally`,
and the issue's pre-existing checklist is printed first so a leftover is visible.
Point it at a scratch issue, not at anything that matters.

Credentials come from the environment or from a `.env` file in the repo root
(which is gitignored). Only one of the org ids is needed - whichever is set is
used, and if both are, the one Tracker accepts is picked by a probe request.

    TRACKER_TOKEN=... TRACKER_CLOUD_ORG_ID=... \
        uv run python scripts/verify_checklist_api.py TEST-123

Pass no issue key to only run the credential preflight.
"""

import asyncio
import json
import os
import pathlib
import sys
from typing import Any

import aiohttp

BASE_URL = "https://api.tracker.yandex.net"
ENV_FILE = pathlib.Path(__file__).resolve().parent.parent / ".env"


def load_env_file(path: pathlib.Path) -> None:
    """Load `KEY=VALUE` lines into `os.environ`, without pulling in a dependency
    for the two variables this script reads from a gitignored `.env`."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def auth_header() -> dict[str, str]:
    load_env_file(ENV_FILE)
    token = os.environ.get("TRACKER_TOKEN")
    iam_token = os.environ.get("TRACKER_IAM_TOKEN")
    if token:
        return {"Authorization": f"OAuth {token}"}
    if iam_token:
        return {"Authorization": f"Bearer {iam_token}"}
    sys.exit(
        f"Set TRACKER_TOKEN (OAuth) or TRACKER_IAM_TOKEN - in the environment "
        f"or in {ENV_FILE}."
    )


def org_headers() -> list[tuple[str, str]]:
    """The org headers worth trying, most specific first.

    Which one an organization answers to is not derivable from the id itself,
    so when both are configured the caller probes rather than guesses.
    """
    candidates = [
        ("X-Cloud-Org-ID", os.environ.get("TRACKER_CLOUD_ORG_ID")),
        ("X-Org-ID", os.environ.get("TRACKER_ORG_ID")),
    ]
    found = [(name, value) for name, value in candidates if value]
    if not found:
        sys.exit(
            f"Set TRACKER_CLOUD_ORG_ID (Yandex Cloud) or TRACKER_ORG_ID "
            f"(Yandex 360) - in the environment or in {ENV_FILE}."
        )
    return found


async def preflight(headers: dict[str, str]) -> dict[str, str] | None:
    """Resolve which org header works and report who the token belongs to."""
    for name, value in org_headers():
        candidate = {**headers, name: value}
        async with aiohttp.ClientSession(
            base_url=BASE_URL, headers=candidate
        ) as session:
            async with session.get("/v3/myself") as response:
                body = await response.text()
            if response.status == 200:
                me = json.loads(body)
                print(
                    f"Authenticated as {me.get('display')} "
                    f"({me.get('login')}, uid={me.get('uid')}) via {name}"
                )
                return candidate
            print(f"  {name}: HTTP {response.status} - {body[:200]}")
    return None


class Probe:
    def __init__(self, session: aiohttp.ClientSession, issue_id: str) -> None:
        self._session = session
        self._issue = issue_id
        self.failures: list[str] = []

    async def request(
        self, method: str, path: str, body: Any = None
    ) -> tuple[int, Any]:
        kwargs: dict[str, Any] = {"json": body} if body is not None else {}
        async with self._session.request(method, path, **kwargs) as response:
            text = await response.text()
        try:
            return response.status, json.loads(text)
        except json.JSONDecodeError:
            return response.status, text

    def check(self, name: str, ok: bool, detail: str) -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
        if not ok:
            self.failures.append(name)

    async def checklist(self) -> list[dict[str, Any]]:
        status, body = await self.request(
            "GET", f"/v3/issues/{self._issue}/checklistItems"
        )
        return body if status == 200 and isinstance(body, list) else []

    async def add_item(self, **fields: Any) -> tuple[int, Any]:
        return await self.request(
            "POST",
            f"/v3/issues/{self._issue}/checklistItems",
            {"text": "probe", **fields},
        )

    async def delete_item(self, item_id: str) -> None:
        await self.request(
            "DELETE", f"/v3/issues/{self._issue}/checklistItems/{item_id}"
        )

    @staticmethod
    def items_of(body: Any) -> list[dict[str, Any]]:
        if isinstance(body, dict):
            return body.get("checklistItems", [])
        return body if isinstance(body, list) else []

    async def run(self) -> None:
        created: list[str] = []
        try:
            print(f"\nExisting checklist on {self._issue}:")
            for item in await self.checklist():
                print(f"  - {item.get('id')} {item.get('text')!r}")

            # POST: one item per request, and what the response looks like.
            print("\n[1] POST one item")
            status, body = await self.add_item()
            self.check("POST accepts a single object", status == 200, f"HTTP {status}")
            if status != 200:
                print(f"       {body}")
                return
            items = self.items_of(body)
            self.check(
                "POST answers with the issue object carrying checklistItems",
                isinstance(body, dict) and "checklistItems" in body,
                f"top-level type {type(body).__name__}",
            )
            item_id = items[-1]["id"]
            created.append(item_id)
            item_path = f"/v3/issues/{self._issue}/checklistItems/{item_id}"

            # The question the docs cannot answer: object body or array body.
            print("\n[2] PATCH body shape")
            status, body = await self.request(
                "PATCH", item_path, {"text": "probe object", "checked": True}
            )
            self.check(
                "PATCH accepts an OBJECT body (what the client sends)",
                status == 200,
                f"HTTP {status}"
                + (
                    ""
                    if status == 200
                    else f" - {json.dumps(body, ensure_ascii=False)}"
                ),
            )
            status, body = await self.request(
                "PATCH", item_path, [{"text": "probe array", "checked": False}]
            )
            print(
                f"  INFO  PATCH with an ARRAY body (what the docs show): HTTP {status}"
            )

            # text really required?
            print("\n[3] Is `text` required on PATCH?")
            status, body = await self.request("PATCH", item_path, {"checked": True})
            self.check(
                "PATCH without `text` is accepted (no refill needed)",
                status == 200,
                f"HTTP {status}"
                + (
                    ""
                    if status == 200
                    else " - rejected, `text` is required again, bring the refill back"
                ),
            )

            # deadlineType: quarter, and isExceeded in the response.
            print("\n[4] deadline")
            status, body = await self.request(
                "PATCH",
                item_path,
                {
                    "text": "probe",
                    "deadline": {
                        "date": "2026-08-20T00:00:00.000000+0000",
                        "deadlineType": "quarter",
                    },
                },
            )
            self.check(
                "deadlineType 'quarter' is accepted",
                status == 200,
                f"HTTP {status}"
                + (
                    ""
                    if status == 200
                    else f" - {json.dumps(body, ensure_ascii=False)}"
                ),
            )
            if status == 200:
                deadline = next(
                    (
                        i.get("deadline")
                        for i in self.items_of(body)
                        if i["id"] == item_id
                    ),
                    None,
                )
                print(f"       deadline echoed back: {deadline}")
                self.check(
                    "response deadline carries isExceeded (required by our model)",
                    isinstance(deadline, dict) and "isExceeded" in deadline,
                    f"keys {sorted(deadline)}"
                    if isinstance(deadline, dict)
                    else "absent",
                )

            # 6-digit vs 3-digit fractional seconds.
            print("\n[5] datetime precision")
            for label, stamp in (
                (
                    "6 digits (what _tracker_datetime emits)",
                    "2026-08-21T00:00:00.000000+0000",
                ),
                ("3 digits (what the docs show)", "2026-08-21T00:00:00.000+0000"),
            ):
                status, _ = await self.request(
                    "PATCH",
                    item_path,
                    {
                        "text": "probe",
                        "deadline": {"date": stamp, "deadlineType": "date"},
                    },
                )
                self.check(
                    f"deadline date with {label}", status == 200, f"HTTP {status}"
                )

            # assignee as a numeric uid.
            print("\n[6] assignee as a numeric uid")
            status, body = await self.request("GET", "/v3/myself")
            uid = body.get("uid") if isinstance(body, dict) else None
            print(f"       current user uid={uid!r}")
            if uid is not None:
                for label, value in (("int", int(uid)), ("string", str(uid))):
                    status, body = await self.request(
                        "PATCH", item_path, {"text": "probe", "assignee": value}
                    )
                    self.check(
                        f"assignee as a {label}",
                        status == 200,
                        f"HTTP {status}"
                        + (
                            ""
                            if status == 200
                            else f" - {json.dumps(body, ensure_ascii=False)}"
                        ),
                    )

            # Can a field be cleared, or only overwritten?
            print("\n[7] clearing assignee and deadline")

            async def set_both() -> bool:
                status, _ = await self.request(
                    "PATCH",
                    item_path,
                    {
                        "assignee": uid,
                        "deadline": {
                            "date": "2026-08-22T00:00:00.000000+0000",
                            "deadlineType": "date",
                        },
                    },
                )
                return status == 200

            for field, empty, label in (
                ("assignee", None, "null"),
                ("assignee", "", "empty string"),
                ("assignee", {}, "empty object"),
                ("assignee", 0, "0"),
                ("assignee", "0", '"0"'),
                ("deadline", None, "null"),
                ("deadline", {}, "empty object"),
            ):
                if not await set_both():
                    print(f"       skipped {field} = {label}: could not set it first")
                    continue
                status, body = await self.request("PATCH", item_path, {field: empty})
                item = next((i for i in self.items_of(body) if i["id"] == item_id), {})
                value = item.get(field, "<absent>")
                cleared = status == 200 and value in (None, "<absent>")
                print(
                    f"  {'CLEARED' if cleared else 'kept   '}  {field} = {label}: "
                    f"HTTP {status}"
                    + (
                        f", {field} is now "
                        f"{json.dumps(value, ensure_ascii=False, default=str)}"
                        if status == 200
                        else f" - {json.dumps(body, ensure_ascii=False)[:160]}"
                    )
                )

            # 404 on an item-scoped path: unknown item vs unknown issue.
            print("\n[8] 404 shape on item-scoped paths")
            status, _ = await self.request(
                "PATCH",
                f"/v3/issues/{self._issue}/checklistItems/000000000000000000000000",
                {"text": "probe"},
            )
            self.check(
                "unknown item id answers 404 (drives ChecklistItemNotFound)",
                status == 404,
                f"HTTP {status}",
            )

            # Deleting the last item: is checklistItems absent or empty?
            print("\n[9] response after deleting the last item")
            before = await self.checklist()
            if len(before) == len(created):
                status, body = await self.request("DELETE", item_path)
                created.remove(item_id)
                self.check(
                    "DELETE of the last item answers 200",
                    status == 200,
                    f"HTTP {status}",
                )
                if isinstance(body, dict):
                    print(
                        "       checklistItems key "
                        f"{'present' if 'checklistItems' in body else 'ABSENT'} "
                        "(our model defaults it to [])"
                    )
            else:
                print("       skipped: the issue has other checklist items")
        finally:
            for item_id in created:
                await self.delete_item(item_id)
            if created:
                print(f"\nCleaned up {len(created)} probe item(s).")


async def main() -> None:
    if len(sys.argv) > 2:
        sys.exit(f"usage: {sys.argv[0]} [ISSUE-KEY]")

    headers = await preflight(auth_header())
    if headers is None:
        sys.exit("\nNo org header was accepted - check the token and the org id.")

    if len(sys.argv) == 1:
        print("\nPreflight only - pass an issue key to run the checklist probes.")
        return
    issue_id = sys.argv[1]

    async with aiohttp.ClientSession(base_url=BASE_URL, headers=headers) as session:
        probe = Probe(session, issue_id)
        await probe.run()
        print()
        if probe.failures:
            print(f"{len(probe.failures)} check(s) failed: {', '.join(probe.failures)}")
            sys.exit(1)
        print("All checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
