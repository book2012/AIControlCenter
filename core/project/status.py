class ProjectStatusService:
    def sprint_status(self):
        return {
            "current": "Sprint 22",
            "current_name": "Memory Manager",
            "remaining_sprints": [
                "Sprint 23 Knowledge Layer",
                "Sprint 24 Planner Agent",
                "Sprint 25 Automation Engine",
                "Sprint 26 Homepage Dashboard",
                "Sprint 27 Production Hardening",
            ],
            "remaining_count": 5,
        }

    def agent_status(self):
        return {
            "completed": [
                "BrainAgent",
                "StatusAction",
            ],
            "remaining": [
                "PlannerAgent",
                "KnowledgeAgent",
                "AutomationAgent",
                "BackupAgent",
                "ShoppingAgent",
                "WordPressAgent",
                "NotionAgent",
                "GitHubAgent",
                "HomepageAgent",
            ],
            "remaining_count": 9,
        }

    def format_sprint(self):
        data = self.sprint_status()
        lines = [
            "🏁 Sprint Status",
            "",
            f"Current: {data['current']} - {data['current_name']}",
            f"Remaining: {data['remaining_count']}",
            "",
            "Next:",
        ]
        lines.extend([f"- {item}" for item in data["remaining_sprints"]])
        return "\n".join(lines)

    def format_agents(self):
        data = self.agent_status()
        lines = [
            "🤖 Agent Status",
            "",
            f"Completed: {len(data['completed'])}",
            f"Remaining: {data['remaining_count']}",
            "",
            "Completed:",
        ]
        lines.extend([f"- {item}" for item in data["completed"]])
        lines.append("")
        lines.append("Remaining:")
        lines.extend([f"- {item}" for item in data["remaining"]])
        return "\n".join(lines)

    def format_project(self):
        return "\n\n".join([
            "🧠 AIControlCenter Project",
            self.format_sprint(),
            self.format_agents(),
        ])
