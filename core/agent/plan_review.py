class PlanReviewService:
    def review(self, plan):
        issues = []

        if not plan.get("goal"):
            issues.append("missing_goal")

        if not plan.get("steps"):
            issues.append("missing_steps")

        executable = len(issues) == 0

        return {
            "plan_id": plan.get("id"),
            "goal": plan.get("goal"),
            "status": "approved" if executable else "needs_revision",
            "executable": executable,
            "issues": issues,
        }

    def format_text(self, plan):
        review = self.review(plan)

        lines = [
            "🧭 Plan Review",
            f"Plan: {review['plan_id']}",
            f"Goal: {review['goal']}",
            f"Status: {review['status']}",
            f"Executable: {review['executable']}",
        ]

        if review["issues"]:
            lines.append("")
            lines.append("Issues:")
            for issue in review["issues"]:
                lines.append(f"- {issue}")

        return "\n".join(lines)
