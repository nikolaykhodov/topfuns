# -*- coding: utf-8 -*-

'''
Юнит-тесты для прототипа TopFuns
'''

import unittest
from lib.vk.api import API, Account, Board, GroupSnapshoter

LOGIN = 'khodov@gmail.com'
PASSWORD = '67u8k1ZWdK4pQp3Dqo'
APP_ID = 2688740 # http://vk.com/app2688740
PERMISSIONS = 'friends,photos,video,wall,groups,offline'
GID = 2611 # http://vk.com/club2611
TOPIC_ID = 25498694 # http://vk.com/topic-2611_25498694


class AccountTest(unittest.TestCase):
    '''
    Базовый класс для кейсов, требующих авторизации во ВКонтакте
    '''
    def __init__(self, *args, **kwargs):
        super(AccountTest, self).__init__(*args, **kwargs)
        self.account = Account(LOGIN, PASSWORD)        

class AuthTest(AccountTest):
    '''
    Тестирование авторизации пользователя
    '''
    def runTest(self):
        self.assertTrue(self.account.auth())    
        
class OAuthTest(AccountTest):
    '''
    Тестирование получения прав по протоколу OAuth и токена для доступа
    '''

    def setUp(self):
        self.account.auth()

    def runTest(self):
        self.assertNotEqual(self.account.oauth(APP_ID, PERMISSIONS), None)            

class APITest(unittest.TestCase):
    '''
    Тестирование работоспособности класса для работы с API
    '''
    
    def setUp(self):
        self.api = API('')

    def runTest(self):
        answer = self.api.getProfiles(uids='durov,andrew')

        self.assertEqual(answer[0]['uid'], 1)
        self.assertEqual(answer[1]['uid'], 6492)      
        self.assertEqual(self.api.isAppUser(), "0")  
        
class BoardTest(unittest.TestCase):
    '''
    Тестирование класса для парсинга топиков и комментариев к ним
    '''
    
    def setUp(self):
        self.board = Board(GID)

    def test_get(self):
        topics = self.board.get_topics()


        topics_count = len(topics)

        self.assertTrue(topics_count > 0)
        self.assertTrue(len(filter(lambda x: x['count'] > 0, topics)) == topics_count)     
        
    def test_getComments(self):
        comments = self.board.get_comments(TOPIC_ID)
        self.assertTrue(len(comments) > 0)   
        self.assertTrue(len(filter(lambda x: x.date is not None, comments)) > 0)
        
    def test_count(self):
        count = self.board.get_count()
        self.assertNotEqual(count, None)
        self.assertGreater(count, 0)

class SnapshoterTest(unittest.TestCase):
    '''
    Тестирование класса для создания снимка
    '''        
    
    def setUp(self):
        self.account = Account(LOGIN, PASSWORD)
        self.account.auth()
        self.snapshoter = GroupSnapshoter(GID, API(self.account.oauth(APP_ID, PERMISSIONS)))
        
    def test_count(self):
        self.assertGreater(self.snapshoter.get_wall_count(), 0)
        self.assertGreater(self.snapshoter.get_videos_count(), 0)        
        self.assertGreater(self.snapshoter.get_photos_count(), 0)
        
