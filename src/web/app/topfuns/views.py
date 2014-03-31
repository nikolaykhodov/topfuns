# -*- coding: utf-8 -*-

from django.http import HttpResponse, Http404
from django.http import HttpResponsePermanentRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django import forms


from datetime import date
from datetime import datetime
from datetime import timedelta


from topfuns.models import *
from topfuns.helpers import run_sql
from topfuns.forms import DownloadReportForm

from random import randint
import hashlib
import json
import re
from settings import p
import re

def print_sql_queries(func):
    def view(*args, **kwargs):
        result = func(*args, **kwargs)

        from django.db import connection
        for q in connection.queries:
            print q['sql']
        
        return result
            
    return view

def top(request):
    top =  Top.objects.all().filter(group__gid=2611).order_by('rank')[:10]
    if len(top) > 0:
        max_rating = top[0].rating
    
        for user in top:
            setattr(user, 'relative_rating', int(float(user.rating) / max_rating * 100))
    
    return HttpResponse(render_to_response('top.html',{
        'top': top,
        'needs_loader': True
    }))

def actions(request, uid=None):
    user = stat = None
    if uid is not None:
        try:
            user = Top.objects.get(group__gid=2611, who=uid)
            stat = UserStat.objects.get(group__gid=2611, who=uid)
        except (Top.DoesNotExist, UserStat.DoesNotExist):
            user = {'who': uid, 'rating': -1}
            stat = {'added': 0, 'likes': 0, 'comments': 0}

    actions = Action.objects.filter(item__owner=-2611).filter(who__gte=0).exclude(item__type=4)
    if uid is not None:
        actions = actions.filter(who=uid)
    actions = actions.order_by('-date')[:20]
    
    feed = []
    for action in actions:
        feed.append(dict(
            id=action.id,
            who=action.who,
            item=action.item.name,
            type=Action.REVERSE_TYPES[action.type],
            item_type = Item.REVERSE_TYPES[action.item.type],
            data=action.data,
            owner=-2611,
            internal_id=action.item.data.internal_id
        ))
    
    return HttpResponse(render_to_response('actions.html',{
        'user': user,
        'stat': stat,
        'actions': actions,
        'needs_loader': True,
        'feed': json.dumps(feed)
    }))    

def prizes(request):
    return HttpResponse(render_to_response('prizes.html',{
        'prizes': Prize.objects.all().filter(group__gid=2611)[:3]
    }))      

def rules(request):
    try:
        rules = VkGroup.objects.get(gid=2611).rules
    except VkGroup.DoesNotExist:
        raise Http404
    
    return HttpResponse(render_to_response('rules.html',{
        'rules': rules.replace('\n', '').replace('\r', '')
    })) 

@permission_required('topfuns.download_report')    
def admin_download_report(request):
    '''
    Страница формирование отчета об активности пользователей за промежуток времени
    '''
    form = DownloadReportForm(request.POST, reports=Report.objects.all())
    
    if request.POST.get('post', '') == 'yes':
        if form.is_valid():
            report = form.get_report()
        
            response = HttpResponse(content=report.stuff, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="stat-for-%s__%s-%s.csv"' % (
                report.group.gid,
                report.start.strftime('%d.%m.%Y'),
                report.end.strftime('%d.%m.%Y')
            )
            
            return response
        
    return render_to_response('admin/topfuns/userstat/download_report.html',{
        'form': DownloadReportForm(reports=Report.objects.all())
    }, context_instance=RequestContext(request))
