from core.agent.plan_review import PlanReviewService
from core.agent.planner_agent import PlannerAgent
from core.automation.queue import AutomationQueue
from core.backup.confirm import BackupConfirmService
from core.backup.plan import BackupPlanService
from core.backup.run import BackupRunService
from core.backup.verify import BackupVerifyService
from core.dashboard.api import DashboardAPI
from core.datacenter.backup_registry import BackupRegistry
from core.datacenter.storage_registry import StorageRegistry
from core.doctor.service import DoctorService
from core.knowledge.search import KnowledgeSearch
from core.homepage.status import HomepageStatusService
from core.logs.service import LogsService
from core.memory.manager import MemoryManager
from core.project.status import ProjectStatusService
from core.runtime.service_health import ServiceHealth
from core.scheduler.status import SchedulerStatusService
from core.task.registry import TaskRegistry
from core.worker_status.service import WorkerStatusService


class CommandRouter:
    def __init__(
        self,
        memory=None,
        automation=None,
    ):
        self.dashboard = DashboardAPI()
        self.storage = StorageRegistry()
        self.backup = BackupRegistry()
        self.registry = TaskRegistry()
        self.doctor = DoctorService()
        self.logs = LogsService()
        self.backup_verify = BackupVerifyService()
        self.worker_status = WorkerStatusService()
        self.backup_plan = BackupPlanService()
        self.backup_confirm = BackupConfirmService()
        self.backup_run = BackupRunService(self.backup_confirm)
        self.scheduler_status = SchedulerStatusService()
        self.memory = memory or MemoryManager()
        self.project = ProjectStatusService()
        self.service_health = ServiceHealth()
        self.knowledge = KnowledgeSearch()
        self.homepage = HomepageStatusService()
        self.planner = PlannerAgent()
        self.plan_reviewer = PlanReviewService()
        self.automation = automation or AutomationQueue()

    def route(self, text: str) -> str:
        command = text.strip()
        lowered = command.lower()

        if lowered == "/status":
            return self.status()
        if lowered == "/storage":
            return self.storage_status()
        if lowered == "/backup":
            return self.backup_status()
        if lowered == "/backup plan":
            return self.backup_plan.format_text()
        if lowered == "/backup confirm":
            return self.backup_confirm.format_text()
        if lowered.startswith("/backup run "):
            token = command.split(" ", 2)[2].strip()
            return self.backup_run.format_text(token)
        if lowered == "/backup verify":
            return self.backup_verify.format_text()
        if lowered == "/tasks":
            return self.tasks_status()
        if lowered == "/worker":
            return self.worker_status.format_text()
        if lowered == "/doctor":
            return self.doctor.format_text()
        if lowered == "/logs":
            return self.logs.format_text()
        if lowered == "/scheduler":
            return self.scheduler_status.format_text()

        if lowered == "/service-health":
            return self.service_health.format_text()
        if lowered == "/memory":
            return self.memory_status()
        if lowered.startswith("/memory search "):
            query = command.split(" ", 2)[2].strip()
            return self.memory_search(query)
        if lowered == "/sprint":
            return self.project.format_sprint()
        if lowered == "/agents":
            return self.project.format_agents()
        if lowered == "/project":
            return self.project.format_project()
        if lowered == "/knowledge":
            return self.knowledge_status()

        if lowered == "/homepage":
            return self.homepage_status()
        if lowered.startswith("/knowledge search "):
            query = command.split(" ", 2)[2].strip()
            return self.knowledge_search(query)
        if lowered.startswith("/plan "):
            goal = command.split(" ", 1)[1].strip()
            return self.plan(goal)
        if lowered == "/automation":
            return self.automation_status()
        if lowered.startswith("/automation run "):
            action = command.split(" ", 2)[2].strip()
            return self.automation_run(action)
        if lowered == "/help":
            return self.help()

        return self.help()

    def status(self) -> str:
        data = self.dashboard.status()
        brain = data["brain"]
        integrations = brain["integrations"]["integrations"]

        return "\n".join([
            "🧠 AIControlCenter",
            f"State: {brain['state']}",
            f"Standalone: {brain['standalone']}",
            "",
            "Integrations:",
            f"- OpenAI: {'OK' if integrations['openai']['configured'] else 'NO'}",
            f"- Google: {'OK' if integrations['google']['configured'] else 'NO'}",
            f"- Notion: {'OK' if integrations['notion']['configured'] else 'NO'}",
            f"- GitHub: {'OK' if integrations['github']['configured'] else 'NO'}",
            "",
            f"Storage: {'OK' if data['storage']['exists'] else 'NO'}",
            f"Backup: {'OK' if data['backup']['exists'] else 'NO'}",
            f"Workers queried: {len(data['workers'])}",
        ])

    def storage_status(self) -> str:
        summary = self.storage.summary()
        lines = ["📦 Storage", f"Root: {summary['root']}", f"Exists: {'OK' if summary['exists'] else 'NO'}", "", "Categories:"]
        for name, item in summary["categories"].items():
            lines.append(f"- {name}: {item['directory_count']} dirs, {item['file_count']} files")
        return "\n".join(lines)

    def backup_status(self) -> str:
        summary = self.backup.summary()
        lines = ["💾 Backup", f"Root: {summary['root']}", f"Exists: {'OK' if summary['exists'] else 'NO'}", "", "Read-only mode."]
        return "\n".join(lines)

    def tasks_status(self) -> str:
        running = self.registry.running()
        if not running:
            return "🧾 Tasks\nRunning: none"
        return "\n".join(["🧾 Tasks"] + [f"- {t.worker}: {t.command} ({t.status})" for t in running])

    def memory_status(self) -> str:
        s = self.memory.status()
        return "\n".join([
            "🧠 Memory",
            f"Type: {s['type']}",
            f"Sessions: {s['sessions']}",
            f"Working items: {s['working_items']}",
            f"Long-term items: {s['long_term_items']}",
            f"Ready: {s['ready']}",
        ])

    def memory_search(self, query: str) -> str:
        results = self.memory.search_long_term(query)
        lines = ["🧠 Memory Search", f"Query: {query}", f"Results: {len(results)}", ""]
        lines.extend([f"- {item['content']}" for item in results[:5]])
        return "\n".join(lines)

    def knowledge_status(self) -> str:
        s = self.knowledge.status()
        return "\n".join(["📚 Knowledge", f"Documents: {s['documents']}", f"Ready: {s['ready']}"])

    def knowledge_search(self, query: str) -> str:
        results = self.knowledge.search(query)
        lines = ["📚 Knowledge Search", f"Query: {query}", f"Results: {len(results)}", ""]
        lines.extend([f"- {item['name']} score={item['score']}" for item in results[:5]])
        return "\n".join(lines)

    def plan(self, goal: str) -> str:
        plan = self.planner.create_plan(goal)
        lines = ["🧭 Plan", f"Goal: {plan['goal']}", f"Status: {plan['status']}", f"Executable: {plan['executable']}", "", "Steps:"]
        lines.extend([f"{s['order']}. {s['name']} [{s['action']}]" for s in plan["steps"]])
        return "\n".join(lines)

    def automation_status(self) -> str:
        return "\n".join(["⚙️ Automation", f"Items: {len(self.automation.list())}"])

    def automation_run(self, action: str) -> str:
        item = self.automation.submit(action)
        result = self.automation.run(item["id"])
        return "\n".join([
            "⚙️ Automation Run",
            f"Action: {result['action']}",
            f"Status: {result['status']}",
            f"Executed: {result['result'].get('executed')}",
            f"Blocked: {result['result'].get('blocked')}",
        ])

    def homepage_status(self) -> str:
        data = self.homepage.status()
        brain = data["brain"]

        return "\n".join([
            "🏠 Homepage",
            f"Brain: {brain['state']}",
            f"Storage: {'OK' if data['storage']['exists'] else 'NO'}",
            f"Backup: {'OK' if data['backup']['exists'] else 'NO'}",
            f"Scheduler Jobs: {len(data['scheduler']['jobs'])}",
            f"Memory Ready: {data['memory']['ready']}",
            f"Knowledge Docs: {data['knowledge']['documents']}",
            f"Workers: {len(data['workers'])}",
        ])

    def help(self) -> str:
        return "\n".join([
            "AIControlCenter Commands",
            "/status",
            "/storage",
            "/backup",
            "/backup plan",
            "/backup confirm",
            "/backup run <token>",
            "/backup verify",
            "/tasks",
            "/worker",
            "/doctor",
            "/logs",
            "/scheduler",
            "/service-health",
            "/memory",
            "/memory search <query>",
            "/sprint",
            "/agents",
            "/project",
            "/knowledge",
            "/homepage",
            "/knowledge search <query>",
            "/plan <goal>",
            "/automation",
            "/automation run <command>",
            "/ask <message>",
        ])
