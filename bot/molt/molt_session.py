from common.expired_dict import ExpiredDict
from config import conf


class MoltSession:
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.conversation_id = ""

    def reset(self):
        self.conversation_id = ""


class MoltSessionManager:
    def __init__(self):
        expires = conf().get("molt_session_expires", 0)
        if expires > 0:
            self.sessions = ExpiredDict(expires)
        else:
            self.sessions = {}

    def get_or_create(self, context) -> MoltSession:
        session_id = context.get("session_id", "default") if context else "default"
        if session_id not in self.sessions:
            msg = context.get("msg") if context else None
            user_id = None
            if msg is not None:
                if context.get("isgroup", False):
                    user_id = getattr(msg, "actual_user_id", None) or getattr(msg, "from_user_id", None)
                else:
                    user_id = getattr(msg, "other_user_id", None) or getattr(msg, "from_user_id", None)
            self.sessions[session_id] = MoltSession(session_id, user_id or session_id)
        return self.sessions[session_id]

    def clear(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def clear_all(self):
        self.sessions.clear()
