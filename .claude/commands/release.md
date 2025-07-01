Prepare a new release of the project.

Call /docs command to update documentation before releasing.

If it is a minor change or a patch, update the version in @pyproject.toml accordingly. While major version is still 0.x, any minor changes should be reflected at increase of patch part, and any big changes - in the minor part of the version.

Always make sure that the version in @manifest.json is the same as in @pyproject.toml.

Make sure @CHANGELOG.md is up to date with the latest changes.
Changes may be collected through git history since last git tag or current unstaged changes.
Always add a new version to the @CHANGELOG.md, even if it is a patch release. Never edit previous versions.
