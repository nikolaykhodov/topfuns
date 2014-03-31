# -* -coding: utf-8 -*-

from django.db import models
from topfuns.fields import BaseDictField
import json
from django.utils.translation import ugettext_lazy as _
from south.modelsinspector import add_introspection_rules

class Item(models.Model):
    class Meta:
        db_table = 'topfuns_item'
        
    TYPES = {
        'post': 1,
        'video': 2,
        'photo': 3,
        'topic': 4 
    }
    
    REVERSE_TYPES = [
        '',
        'post',
        'video',
        'photo',
        'topic'
    ]
    
    POST = 1
    VIDEO = 2
    PHOTO = 3
    TOPIC = 4

    type = models.IntegerField()
    name = models.CharField(max_length=128)
    owner = models.IntegerField()

    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    
    data = BaseDictField(default={})
    
class Action(models.Model):
    class Meta:
        db_table = 'topfuns_action'

    TYPES = {
        'added': 1,
        'like': 2,
        'share': 3,
        'comment': 4
    }
    
    REVERSE_TYPES = [
        '',
        'added',
        'like',
        'share',
        'comment'
    ]
    
    ADDED = 1
    LIKE = 2
    SHARE = 3
    COMMENT = 4

    type = models.IntegerField()
    who = models.IntegerField()
    item = models.ForeignKey(Item)
    date = models.DateField(blank=True)
    
    data = BaseDictField(default={})    

class VkGroup(models.Model):
    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')

    gid = models.PositiveIntegerField(verbose_name=_('GID'))
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    url = models.CharField(max_length=256, verbose_name=_('URL'))
    
    rules = models.CharField(max_length=10000, verbose_name=_('Rules'))
    
    wall_max = models.PositiveIntegerField(default=0, verbose_name=_('Wall Scanning Depth'))
    photo_max = models.PositiveIntegerField(default=0, verbose_name=_('Photos Scanning Depth'))
    board_max = models.PositiveIntegerField(default=0, verbose_name=_('Board Scanning Depth'))
    video_max = models.PositiveIntegerField(default=0, verbose_name=_('Videos Scanning Depth'))
    
    wall_count = models.PositiveIntegerField(default=0, verbose_name=_('Wall Posts Count'))
    photos_count = models.PositiveIntegerField(default=0, verbose_name=_('Photos Count'))
    videos_count = models.PositiveIntegerField(default=0, verbose_name=_('Videos Count'))
    board_count = models.PositiveIntegerField(default=0, verbose_name=_('Topics Count'))
    
    def __unicode__(self):
        return u'%s (club%s)' % (self.name, self.gid)
       
    
class VkModerator(models.Model):
    class Meta:
        verbose_name = _('Moderator')
        verbose_name_plural = _('Moderators')

    group = models.ForeignKey(VkGroup, verbose_name=_('Group'))
    mid = models.IntegerField(verbose_name=_('ID'))
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    url = models.CharField(max_length=256, verbose_name=_('URL'))
    
    def __unicode__(self):
        return u'%s@%s' % (self.group, self.name)
        
class VkAccount(models.Model):
    class Meta:
        verbose_name = _('VK Account')
        verbose_name_plural = _('VK Accounts')


    login = models.CharField(max_length=128, verbose_name=_('Login'))
    password = models.CharField(max_length=128, verbose_name=_('Password'))
    access_token = models.CharField(max_length=128, blank=True, verbose_name=_('Access Token'))
    
    def __string__(self):
        return self.login
        
    def __unicode__(self):
        return unicode(self.__string__())
        
class Prize(models.Model):
    class Meta:
        verbose_name = _('Prize')
        verbose_name_plural = _('Prizes')
        db_table = 'topfuns_prize'


    RANK_CHOICES = (
        (1, u'1 место'),
        (2, u'2 место'),
        (3, u'3 место'),                
    )
        
    group = models.ForeignKey(VkGroup, verbose_name=_('Group'))
    rank = models.IntegerField(verbose_name=_('Rank'))
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    description = models.CharField(max_length=4096, verbose_name=_('Description'))
    img = models.URLField(verbose_name=_("Image"))
    
    def __unicode__(self):
        return u'%s@%s' % (self.group, self.name)
    

class Top(models.Model):
    class Meta:
        db_table = 'topfuns_top'
        unique_together = (('group', 'rank'), )
        verbose_name = _("Top")
        verbose_name_plural = _("Top")
        permissions = (
            ('recalc_top', "Recalculate Top"),
        )
            
    group = models.ForeignKey(VkGroup, verbose_name=_("Group"))
    who = models.IntegerField(verbose_name=_("ID"))
    rating = models.IntegerField(verbose_name=_("Rating"))
    rank = models.IntegerField(verbose_name=_("Rank"))
    change = models.IntegerField(verbose_name=_("Rank Change"))    
    
class TopHistory(models.Model):
    class Meta:
        db_table = 'topfuns_tophistory'

    group = models.ForeignKey(VkGroup, verbose_name=_("Group"))
    timestamp = models.DateTimeField()
    who = models.IntegerField(verbose_name=_("ID"))
    rating = models.IntegerField(verbose_name=_("Rating"))
    rank = models.IntegerField(verbose_name=_("Rank"))
    change = models.IntegerField(verbose_name=_("Rank Change"))  
    
class Blocked(models.Model):
    class Meta:
        verbose_name = _("Blocked User")
        verbose_name_plural = _("Blocked Users")
    
    group = models.ForeignKey(VkGroup, verbose_name=_("Group"))
    who = models.IntegerField(verbose_name=_("ID"))

class UserStat(models.Model):
    class Meta:
        db_table = 'user_stat'
        unique_together = (('group', 'who'), )
        permissions = (
            ('download_report', 'Download Report'),
        )
        
    who = models.IntegerField()
    group = models.ForeignKey(VkGroup)    
    
    likes = models.IntegerField()
    shares = models.IntegerField()
    comments = models.IntegerField()
    added = models.IntegerField()
    
class Report(models.Model):

    group = models.ForeignKey(VkGroup)
    start = models.DateField()
    end = models.DateField()
    
    stuff = models.CharField(max_length=10000)
    
add_introspection_rules([], ["^topfuns\.fields\.BaseDictField"])
