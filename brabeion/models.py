from django.db import models

from django.conf import settings

from django.utils import timezone

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

class BadgeAward(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name="badges_earned")
    awarded_at = models.DateTimeField(default=timezone.now)
    slug = models.CharField(max_length=255)
    level = models.IntegerField()
    
    def __unicode__(self):
        return u'%s (%s) awarded to %s' % (self.slug, self.level, self.user)

    def __getattr__(self, attr):
        return getattr(self._badge, attr)
    
    @property
    def badge(self):
        return self
    
    @property
    def _badge(self):
        from brabeion import badges
        return badges._registry[self.slug]
    
    @property
    def name(self):
        return self._badge.levels[self.level - 1].name
    
    @property
    def description(self):
        return self._badge.levels[self.level - 1].description
    
    @property
    def progress(self):
        return self._badge.progress(self.user, self.level)
