---
name: observability-workflow-optimizer
description: Suggest improvements to skills, agents, and workflows based on usage analysis
allowed-tools:
  - Bash
  - Read
  - Task
---

# Workflow Optimizer Pipeline

This command orchestrates the full analysis pipeline. Follow these steps IN ORDER:

## Step 1: Collect Data

Run IMMEDIATELY (do not explore or read files first):

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 20 > /tmp/usage-data.json
```

## Step 2: Interpret Data

After the script completes, use the Task tool to spawn the usage-insights-agent:

```
Task(subagent_type="observability:usage-insights-agent", prompt="Analyze the usage data in /tmp/usage-data.json. Identify missed opportunities, configuration issues, and provide specific recommendations.")
```

## Step 3: Generate Fixes

After receiving insights from the agent, use the Skill tool to load the workflow-optimizer skill:

```
Skill(skill="observability:observability-workflow-optimizer")
```

Then follow that skill to generate minimal, targeted fixes based on the insights.

## Important

- Do NOT manually explore for session files
- Do NOT read JSONL files directly
- The script handles all data collection
- Wait for each step to complete before proceeding
