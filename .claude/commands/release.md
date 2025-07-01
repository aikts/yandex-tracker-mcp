---
allowed-tools: Bash(mkdir:*), Bash(grep:*), Bash(make:*), Bash(find:*), Bash(sed:*), Bash(git add:*), Bash(git commit:*), Bash(git tag:*), Bash(git describe:*), Bash(git branch:*), Bash(git log:*), Bash(git status:*), Bash(git diff:*)
description: make a new release of the project
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`
- Linters status: !`make`

# Task
Prepare a new release of the project. You may spin parallel tasks if you need as long as changed files don't overlap.

# Instructions
1. Make sure to fix all linter problems with `make` command.
2. Make sure that @README.md is up to date with current code structure, specification, architecture, features, environment variables. Make sure to also update the translated version at @README_ru.md. Also if there are new tools added to the project - make sure they are documented in @README.md, @README_ru.md, @manifest.json
3. If it is a minor change or a patch, update the version in @pyproject.toml accordingly. While major version is still 0.x, any minor changes should be reflected at increase of patch part, and any big changes - in the minor part of the version.
4. Always make sure that the version in @manifest.json is the same as in @pyproject.toml.
5. Make sure @CHANGELOG.md is up to date with the latest changes. Changes may be collected through git history since last git tag or current unstaged changes. Always add a new version to the @CHANGELOG.md, even if it is a patch release. Never edit previous versions.
6. Make a git commit reflecting changes currently made.
