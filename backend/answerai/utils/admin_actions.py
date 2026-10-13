import time
from uuid import uuid4

from answerai.models.admin_actions import AdminAction
from answerai.utils.secret_redaction import redact_value


def record_action(db, actor_id, action, target_id=None, details=None):
    db.add(
        AdminAction(
            id=str(uuid4()),
            actor_id=actor_id,
            target_id=target_id,
            action=action,
            details=redact_value(details or {}),
            created_at=int(time.time()),
        )
    )
