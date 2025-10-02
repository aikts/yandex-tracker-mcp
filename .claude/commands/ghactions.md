---
allowed-tools: Bash(git push:*), mcp__github__list_workflow_runs
description: validate GitHub Actions workflows
---

# Task
You need to validate that GitHub Actions workflows of latest push are passing.

# Instructions
1. Retrieve all GitHub workflows started by latest push using github mcp server tools.
2. Wait until all GitHub Actions are passing.
3. Report status of the workflows and their URLs.
