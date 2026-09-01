def is_active_authenticated(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.pk is not None
    )


def is_room_member(user, room):
    if not is_active_authenticated(user):
        return False
    return room.host_id == user.pk or room.participants.filter(pk=user.pk).exists()


def is_room_muted(user, room):
    if not is_active_authenticated(user):
        return False
    return room.muted_users.filter(pk=user.pk).exists()


def can_send_room_message(user, room):
    return is_room_member(user, room) and not is_room_muted(user, room)


def can_direct_message(user, other_user):
    return bool(
        is_active_authenticated(user)
        and is_active_authenticated(other_user)
        and user.pk != other_user.pk
    )
