# -*- coding: utf-8 -*-

'''
Различные утилиты для облегчения жизни
'''
from django.db import connection, transaction
import logging
import settings

def run_sql(script):
    '''
    Исполняет скрипт по командам
    '''
    dirty_commands = script.split(';')
    commands = [command for command in dirty_commands if command.strip() != '']
    try:
        for command in commands:
            cursor = connection.cursor()
            cursor.execute(command)
            cursor.close()
    except Exception, ex:
        logging.exception(ex)
        transaction.rollback_unless_managed()
        return False
    else:
        transaction.commit_unless_managed()  
        return True
        
def setup_crawler_logging():
    '''
    Setup Logging
    '''
    try:
        if setup_crawler_logging.init is True:
            return
    except AttributeError:
        pass
            
    log = logging.getLogger("")
    log.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    sth = logging.StreamHandler()
    sth.setLevel(logging.INFO)
    log.addHandler(sth)
    fhnd = logging.FileHandler(settings.CRAWLER_LOG)
    fhnd.setLevel(logging.DEBUG)
    log.addHandler(fhnd)    
    
    setup_crawler_logging.init = True
