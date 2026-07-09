from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConversationSession:
    id: str
    messages: list[Message] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.utcnow)

    def add(self, role: str, content: str):
        message = Message(role=role, content=content)
        self.messages.append(message)
        return message

    def to_dict(self):
        return {
            "id": self.id,
            "created": self.created.isoformat(),
            "messages": [m.to_dict() for m in self.messages],
        }


class ConversationMemory:
    def __init__(self):
        self.sessions = {}

    def create(self):
        session = ConversationSession(id=str(uuid4()))
        self.sessions[session.id] = session
        return session

    def get(self, session_id: str):
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        return self.get(session_id).add(role, content)

    def list(self):
        return [
            session.to_dict()
            for session in self.sessions.values()
        ]
