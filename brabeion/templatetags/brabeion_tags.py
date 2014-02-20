from django import template

from ..models import BadgeAward


register = template.Library()


class BadgeCountNode(template.Node):
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        if len(bits) == 2:
            return cls(bits[1])
        elif len(bits) == 4:
            if bits[2] != "as":
                raise template.TemplateSyntaxError("Second argument to %r must "
                    "be 'as'" % bits[0])
            return cls(bits[1], bits[3])
        raise template.TemplateSyntaxError("%r takes either 1 or 3 arguments." % bits[0])
    
    def __init__(self, user, context_var=None):
        self.user = template.Variable(user)
        self.context_var = context_var
    
    def render(self, context):
        user = self.user.resolve(context)
        badge_count = BadgeAward.objects.filter(user=user).count()
        if self.context_var is not None:
            context[self.context_var] = badge_count
            return ""
        return unicode(badge_count)

@register.tag
def badge_count(parser, token):
    """
    Returns badge count for a user, valid usage is::

        {% badge_count user %}
    
    or
    
        {% badge_count user as badges %}
    """
    return BadgeCountNode.handle_token(parser, token)


class BadgesForUserNode(template.Node):
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        if len(bits) != 5:
            raise template.TemplateSyntaxError("%r takes exactly 4 arguments." % bits[0])
        if not (bits[2][0] in ('"', "'") and bits[2][-1] == bits[2][0]):
            raise template.TemplateSyntaxError("%r expects 2nd argument format to be '\"string\"'" % bits[0])
        if bits[3] != "as":
            raise template.TemplateSyntaxError("The 3rd argument to %r should "
                "be 'as'" % bits[0])
        return cls(bits[1], bits[2][1:-1], bits[4])
    
    def __init__(self, user, slug, context_var):
        self.user = template.Variable(user)
        self.slug = slug
        self.context_var = context_var
    
    def render(self, context):
        user = self.user.resolve(context)
        slug = self.slug

        filters = {'user': user}
        excludes = {}
        if not slug == '':
            if slug.startswith('not_'):
                excludes.update({'slug': slug.replace('not_', '')})
            else:
                filters.update({'slug': slug})
        context[self.context_var] = BadgeAward.objects.filter(**filters).exclude(**excludes).order_by("-awarded_at")
        return ""
        

@register.tag
def badges_for_user(parser, token):
    """
    Sets the badges for a given user to a context var.  Usage:
        
        {% badges_for_user user as badges %}
    """
    return BadgesForUserNode.handle_token(parser, token)
