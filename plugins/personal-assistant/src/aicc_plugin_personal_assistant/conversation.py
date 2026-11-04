"""Bounded local conversation domain. No tools or resource authority."""
from threading import Lock

class ConversationError(RuntimeError):
    pass

class ConversationBusy(ConversationError):
    pass

def validate_messages(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 8:
        raise ConversationError("invalid_messages")
    output = []
    total = 0
    for index, item in enumerate(value):
        if (not isinstance(item, dict) or set(item) != {"role", "content"}
                or item["role"] not in {"user", "assistant"}
                or item["role"] != ("user" if index % 2 == 0 else "assistant")
                or not isinstance(item["content"], str) or not item["content"].strip()
                or len(item["content"]) > 4000):
            raise ConversationError("invalid_messages")
        total += len(item["content"])
        if total > 12000:
            raise ConversationError("history_too_large")
        output.append(dict(item))
    if output[-1]["role"] != "user":
        raise ConversationError("invalid_messages")
    return output

class ConversationService:
    def __init__(self, port, *, lock=None):
        self._port = port
        self._lock = lock if lock is not None else Lock()

    def chat(self, messages):
        approved = validate_messages(messages)
        if not self._lock.acquire(blocking=False):
            raise ConversationBusy("assistant_busy")
        try:
            try:
                result = self._port.chat(approved)
            except Exception:
                raise ConversationError("model_unavailable") from None
            if not isinstance(result, str) or not result.strip() or len(result) > 16000:
                raise ConversationError("invalid_model_response")
            return result
        finally:
            self._lock.release()


    def stream(self, messages):
        approved = validate_messages(messages)
        def generate():
            if not self._lock.acquire(blocking=False):
                raise ConversationBusy("assistant_busy")
            size = 0
            try:
                for part in self._port.stream(approved):
                    if not isinstance(part, str):
                        raise ConversationError("invalid_model_response")
                    size += len(part)
                    if size > 8000:
                        raise ConversationError("invalid_model_response")
                    if part:
                        yield part
                if not size:
                    raise ConversationError("invalid_model_response")
            except ConversationError:
                raise
            except Exception:
                raise ConversationError("model_unavailable") from None
            finally:
                self._lock.release()
        return generate()
