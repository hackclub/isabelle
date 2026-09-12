from isabelle.utils.env import env


def is_reviewer(slack_id) -> bool:
    return bool(slack_id) and slack_id in env.authorised_users


def is_leader(slack_id, event) -> bool:
    if not slack_id or not event:
        return False
    return event.get("LeaderSlackID") == slack_id


def can_edit_event(slack_id, event) -> bool:
    return is_reviewer(slack_id) or is_leader(slack_id, event)


def can_reassign_leader(slack_id) -> bool:
    return is_reviewer(slack_id)


def has_allowed_email(email) -> bool:
    if not email or "@" not in str(email):
        return False
    domain = str(email).rsplit("@", 1)[-1].strip().lower()
    return domain in env.submitter_email_domains


def can_submit(email, slack_id, allowlisted_ids) -> bool:
    if is_reviewer(slack_id):
        return True
    if has_allowed_email(email):
        return True
    return bool(slack_id) and slack_id in set(allowlisted_ids or [])
