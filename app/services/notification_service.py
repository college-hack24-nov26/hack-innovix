from app.extensions import db
from app.models import Notification


def notify_role(role: str, title: str, body: str, link: str = None) -> None:
    db.session.add(Notification(role_target=role, title=title, body=body, link=link))
    db.session.commit()
