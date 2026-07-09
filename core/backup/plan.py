class BackupPlanService:
    def plan(self):
        return {
            "mode": "read-only planning",
            "worker": "ubuntu-main",
            "actions": [
                "compose backup",
                "configs backup",
                "logs snapshot",
                "database backup check",
            ],
            "execution": "not_started",
        }

    def format_text(self):
        plan = self.plan()

        lines = [
            "💾 Backup Plan",
            "",
            f"Mode: {plan['mode']}",
            f"Target Worker: {plan['worker']}",
            "",
            "Estimated Actions:",
        ]

        for action in plan["actions"]:
            lines.append(f"- {action}")

        lines.append("")
        lines.append("Execution: not started")
        lines.append("No backup was executed.")

        return "\n".join(lines)
