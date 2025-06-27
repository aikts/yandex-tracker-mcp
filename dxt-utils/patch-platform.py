import json
import sys

gh_os = sys.argv[1]

platform = {
    "Linux": "linux",
    "Windows": "win32",
    "macOS": "darwin",
}[gh_os]

with open("manifest.json", "r") as f:
    manifest = json.load(f)

manifest["compatibility"]["platforms"] = [platform]
print(json.dumps(manifest, indent=2))  # noqa: T201
