# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError
from django.contrib import admin
from django import forms
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required

from topfuns.models import VkGroup, VkModerator, VkAccount, Prize, Top, Blocked
from lib.vk.api import API, APIError
import re

class VkGroupAdminForm(forms.ModelForm):
    class Meta:
        model = VkGroup
        
    gid = forms.IntegerField(widget=forms.TextInput(attrs={'disabled': 'true'}), required=False, 
            label=_("GID"))
    name = forms.CharField(widget=forms.TextInput(attrs={'disabled': 'true'}), required=False, label=_("Name"))
    rules = forms.CharField(widget=forms.Textarea(), required=False, label=_("Rules"))
    
    group_data = {}
    
    def clean_url(self):
        if 'url' not in self.cleaned_data:
            self.cleaned_data['url'] = ''
            
        matches = re.findall(r'^http://(vk\.com|vkontakte\.ru)/(.*)', self.cleaned_data['url'])
        if len(matches) == 0:
            raise ValidationError, _("URL must be within Vkontakte domain")
        screen_name = matches[0][1]
        
        api = API('')
        try:
            answer = api.groups.getById(gids=screen_name)
        except APIError, e:
            raise ValidationError, "APIError: %s" % e
        
        try:
            self.group_data['gid'] = answer[0]['gid']
            self.group_data['name'] = answer[0]['name'] 
        except (KeyError, IndexError):
            raise ValidationError, _('This is not group URL')
            
        return self.cleaned_data['url']

    def save(self, force_insert=False, force_update=False, commit=True):
        group = super(VkGroupAdminForm, self).save(commit=False)
    
        group.url = self.cleaned_data['url']
        group.name = self.group_data['name']
        group.gid = self.group_data['gid']
        
        if commit:
            group.save()
        
        return group

class VkModeratorAdminForm(forms.ModelForm):
    class Meta:
        model = VkModerator
    
    mid = forms.IntegerField(widget=forms.TextInput(attrs={'disabled': 'true'}), required=False, label=_("ID"))
    name = forms.CharField(widget=forms.TextInput(attrs={'disabled': 'true'}), required=False, label=_("Name"))
    
    personal_data = {}
    
    def clean_url(self):
        #import pdb;pdb.set_trace()
        if 'url' not in self.cleaned_data:
            self.cleaned_data['url'] = ''
            
        matches = re.findall(r'^http://(vk\.com|vkontakte\.ru)/(.*)', 
                    self.cleaned_data['url'])
        if len(matches) == 0:
            raise ValidationError, _("URL must be within Vkontakte domain")
        screen_name = matches[0][1]
        
        api = API('')
        try:
            answer = api.getProfiles(uids=screen_name)
        except APIError, e:
            raise ValidationError, "APIError: %s" % e
        
        try:
            self.personal_data['mid'] = int(answer[0]['uid'])
            self.personal_data['name'] = answer[0]['first_name'] + ' ' + answer[0]['last_name']
        except (KeyError, IndexError):
            raise ValidationError, _('This is not profile URL')
            
        return self.cleaned_data['url']    
        
    def save(self, force_insert=False, force_update=False, commit=True):
        moderator = super(VkModeratorAdminForm, self).save(commit=False)
    
        moderator.url = self.cleaned_data['url']
        moderator.name = self.personal_data['name']
        moderator.mid = self.personal_data['mid']
        
        if commit:
            moderator.save()
        
        return moderator
        
class BlockedAdminForm(forms.ModelForm):
    class Meta:
        model = VkModerator
    
    who = forms.IntegerField(widget=forms.TextInput(attrs={'disabled': 'true'}), required=False, label=_("ID"))
    url = forms.CharField(required=True, label=_("Profile URL"), help_text=_("You should specify only profile URL"))
    
    personal_data = 0
    
    def clean_url(self):
        if 'url' not in self.cleaned_data:
            self.cleaned_data['url'] = ''
            return
            
        matches = re.findall(r'^http://(vk\.com|vkontakte\.ru)/(.*)', 
                    self.cleaned_data['url'])
        if len(matches) == 0:
            raise ValidationError, _("URL must be within Vkontakte domain")
        screen_name = matches[0][1]
        
        api = API('')
        try:
            answer = api.getProfiles(uids=screen_name)
        except APIError, e:
            raise ValidationError, "APIError: %s" % e
        
        try:
            self.who = int(answer[0]['uid'])
        except (KeyError, IndexError):
            raise ValidationError, _('This is not profile URL')
            
        return self.cleaned_data['url']    
        
    def save(self, force_insert=False, force_update=False, commit=True):
        blocked = super(BlockedAdminForm, self).save(commit=False)
        blocked.who = self.who
        
        if commit:
            blocked.save()
        
        return blocked        

class PrizeAdminForm(forms.ModelForm):
    class Meta:
        model = Prize
    
    rank = forms.ChoiceField(widget=forms.RadioSelect, choices=Prize.RANK_CHOICES, required=True, label=_("Rank"))
    description = forms.CharField(widget=forms.Textarea(), required=False, label=_("Description"))
        
class VkGroupAdmin(admin.ModelAdmin):
    form = VkGroupAdminForm
    
    list_display = ('gid', 'name', 'url')
    search_fields = ['gid', 'url', 'name']

class VkModeratorAdmin(admin.ModelAdmin):
    form = VkModeratorAdminForm

    exclude = ['group']
    list_display = ('mid', 'name', 'url')
    search_fields = ['group', 'mid', 'name', 'url', 'group__name', 'group__url']


class VkAccountAdmin(admin.ModelAdmin):
    list_display = ('login', 'password', 'access_token')
    search_fields = ['login']

class PrizeAdmin(admin.ModelAdmin):
    form = PrizeAdminForm

    exclude = ['group']
    list_display = ('name', 'rank')
    search_fields = ['group__name', 'group__gid', 'name', 'rank']
    
class TopAdmin(admin.ModelAdmin):
    list_display = ('who', 'rank', 'rating', 'change')
    search_fields = ('group__name', 'group__gid', 'who')
    actions = ['block_users', 'update_top']
    exclude = ['group']
    
    #@permission_required('top.recalc_top')
    def admin_recalc(self, request):
        '''
        Произвести пересчет рейтинга
        '''
        if not request.user.has_perm('topfuns.recalc_top'):
            raise Http404        

        from topfuns.management.commands.runcrawler import StatUpdater
        updater = StatUpdater(2611)
        updater.update()
        
        return HttpResponseRedirect(
            reverse("admin:topfuns_top_changelist")
        )
    
    def block_users(self, request, queryset):
        '''
        Заблокировать пользователя
        '''
        if not request.user.has_perm('topfuns.add_blocked'):
            raise Http404
            
        for entry in queryset:
            blocked = Blocked(group=entry.group, who=entry.who)
            blocked.save()
    block_users.short_description = _("Block users")
    
    def get_urls(self):
        from django.conf.urls.defaults import *
        urls = super(TopAdmin, self).get_urls()
        my_urls = patterns('', 
            url(
                r'recalc',
                self.admin_site.admin_view(self.admin_recalc),
                name='admin_recalc'
            )
        )  
        return my_urls + urls 
    
class BlockedAdmin(admin.ModelAdmin):
    form = BlockedAdminForm
    
    exclude = ['group']
    list_display = ('who', )
    search_fields = ('group__name', 'group__gid', 'who')
        
admin.site.register(VkGroup, VkGroupAdmin)
admin.site.register(VkModerator, VkModeratorAdmin)
admin.site.register(VkAccount, VkAccountAdmin)
admin.site.register(Prize, PrizeAdmin)
admin.site.register(Top, TopAdmin)
admin.site.register(Blocked, BlockedAdmin)
