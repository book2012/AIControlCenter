# Automation

## Status

✅ AutomationExecutor
✅ PlannerAutomationRunner
✅ SafeExecutionPolicy
✅ AutomationQueue
✅ Automation API
✅ Telegram /automation
✅ Scheduler Runner Integration

## Safety

Automation only executes allowed read-only commands.

Allowed:
- /status
- /doctor
- /scheduler
- /memory
- /knowledge
- /backup verify

Blocked:
- /backup run
- unknown commands
- unsafe commands

## API

GET /automation
POST /automation
GET /automation/{item_id}

## Commands

/automation
/automation run <command>
