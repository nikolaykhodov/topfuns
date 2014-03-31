# -*- encoding: utf-8 -*-
'''
Команда для генерирования отчета по расписанию
'''
from django.db import connection
from datetime import date, timedelta
from topfuns.models import Report, VkGroup
from topfuns.helpers import run_sql
from django.core.management.base import BaseCommand
from time import strptime 
from settings import p
import re
import logging
from django import forms



class Command(BaseCommand):
    '''
    Command
    '''
    
    args = '   '
    help = 'Generating report for the week period'            
    
    @staticmethod
    def gen_report(beginWith=None, endWith=None):
        '''
        Процедура непосредственного формирования отчета
        '''
        if beginWith is None or endWith is None:
            beginWith = date.today() - timedelta(8)
            endWith = date.today() - timedelta(1)
        
        gid = 2611
        
        sql = open(p('app/topfuns/sql/gen_report.mysql.sql')).read().decode('utf8') % {
            'gid': gid,
            'start_with': beginWith.strftime('%Y-%m-%d'),
            'end_with':   endWith.strftime('%Y-%m-%d')
        }
        variables = re.findall(r'/\*(.*?)\*/.*?SELECT @([a-z_]+)', sql.replace('\r', '').replace('\n', ''))

        data = []
        if len(variables) > 0 and run_sql(sql):
            cursor = connection.cursor()
            cursor.execute("SELECT " + ",".join(["@" + var[1] + " as " + var[1] for var in variables]) + ";")

            row = cursor.fetchall()

            for i in xrange(len(row[0])):
                data.append({
                    'description':  variables[i][0], 
                    'value': row[0][i]
                })
            content = ''
        
        content = ''
        for entry in data:
            content += '"%(description)s";"%(value)s"\n' %  {
                'description': entry['description'],
                'value': entry['value']
            }
            
        
        group = VkGroup.objects.get(gid=2611)    
        Report.objects.create(group=group, start=beginWith, end=endWith, stuff=content)
    
    def handle(self, *args, **kwargs):
        '''
        Handle
        '''
        beginWith = None
        endWith = None
        
        if len(args) >= 2:
            try:
                time_struct = strptime(args[0], '%Y-%m-%d')
                beginWith = date(time_struct.tm_year, time_struct.tm_mon, time_struct.tm_mday)
                
                time_struct = strptime(args[1], '%Y-%m-%d')
                endWith = date(time_struct.tm_year, time_struct.tm_mon, time_struct.tm_mday)
            except ValueError:
                pass
                            
        self.gen_report(beginWith, endWith)
            
        
