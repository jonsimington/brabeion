from .models import BadgeAward
from .signals import badge_awarded



class BadgeAwarded(object):
    def __init__(self, level=None, user=None):
        self.level = level
        self.user = user


class BadgeDetail(object):
    def __init__(self, name=None, description=None):
        self.name = name
        self.description = description

    def __repr__(self):
        return unicode(self.name)


class Badge(object):
    async = False
    
    def __init__(self):
        assert not (self.multiple and len(self.levels) > 1)
        for i, level in enumerate(self.levels):
            if not isinstance(level, BadgeDetail):
                self.levels[i] = BadgeDetail(level)
    
    def possibly_award(self, **state):
        """
        Will see if the user should be awarded a badge.  If this badge is
        asynchronous it just queues up the badge awarding.
        """
        assert "user" in state

        try:
            user_id = state['user'].pk
        except AttributeError:
            user_id = state['user']

        state['user_id'] = user_id
        del state['user']

        if self.async:
            from .tasks import AsyncBadgeAward
            state = self.freeze(**state)
            AsyncBadgeAward.delay(self, state)
            return
        self.actually_possibly_award(**state)
    
    def actually_possibly_award(self, **state):
        """
        Does the actual work of possibly awarding a badge.
        """
        user_id = state["user_id"]
        force_timestamp = state.pop("force_timestamp", None)
        awarded = self.award(**state)
        if awarded is None:
            return
        if awarded.user is not None:
            user_id = awarded.user.pk
        if awarded.level is None:
            assert len(self.levels) == 1
            awarded.level = 1
        if (not self.multiple and
            BadgeAward.objects.filter(user__pk=user_id, slug=self.slug, level=awarded.level)):
            return
        extra_kwargs = {}
        if force_timestamp is not None:
            extra_kwargs["awarded_at"] = force_timestamp
        badge = BadgeAward.objects.create(user_id=user_id, slug=self.slug,
            level=awarded.level, **extra_kwargs)
        badge_awarded.send(sender=self, badge_award=badge)
    
    def freeze(self, **state):
        return state


def send_badge_messages(badge_award, **kwargs):
    """
    If the Badge class defines a message, send it to the user who was just
    awarded the badge.
    """
    user_message = getattr(badge_award.badge, "user_message", None)
    if callable(user_message):
        message = user_message(badge_award)
    else:
        message = user_message
    if message is not None:
        badge_award.user.message_set.create(message=message)
badge_awarded.connect(send_badge_messages)
