---
allowed-tools: Bash(git push:*), mcp__github__list_workflow_runs
description: push changes and validate GitHub Actions
---

# Task
You need to publish changes to the git remote repository and validate that GitHub Actions are passing.

# Instructions
1. Make sure `make` command passes without errors.
2. Make sure there are any commits not pushed yet to the remote repository.
3. Run `git push` command to push the changes if there are any.
4. If nothing to push - follow next steps.
5. Retrieve all GitHub workflows started by this push using github mcp server tools.
6. Wait until all GitHub Actions are passing.
7. Report status of the workflows and their URLs.
