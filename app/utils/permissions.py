def require_role(user, role):
    if not user or user.role != role:
        return False
    return True