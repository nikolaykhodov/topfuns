# -*- encoding: utf-8 -*-
'''
Модуль для доступа к API ВКонтакте
'''

import re
import urllib2
from urllib import urlencode
from urllib2 import HTTPError
from base64 import b64encode
import json
from BeautifulSoup import BeautifulSoup
from basedict import BaseDict
from django.conf import settings
from datetime import date, timedelta
import time
import logging

__author__ = 'Nikolay Khodov <nkhodov@gmail.com>'
__version__ = '1.0'

class TokenHandler(urllib2.HTTPRedirectHandler):     

    def __init__(self, account_obj=None):
        self.account = account_obj

    def http_error_302(self, req, fp, code, msg, headers):
        if self.account and len(re.findall(r'blank\.html', headers['Location'])) > 0:
            matches = re.findall(r'access_token=([a-z0-9]+)', headers['Location'])
            setattr(self.account, 'vk_token', matches[0] if len(matches) > 0 else '')

        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)              

        status = code                                
        return result 

class AccountError(Exception):
    '''
    Исключения, связанные с аккаунтом
    '''
    pass

class Account(object):
    '''
    Класс пользователя ВКонтакте
    '''    
    
    def __init__(self, login, password):
        '''
        Конструктор
        login    -- имя или почта пользователя
        password -- пароль
        '''
        self.login = login
        self.password = password
        self.is_loginned = False
        
        http_debug_handler = urllib2.HTTPHandler()
        https_debug_handler = urllib2.HTTPSHandler()

        if settings.DEBUG:
            http_debug_handler.set_http_debuglevel(1)
            https_debug_handler.set_http_debuglevel(1)
            
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(), 
            http_debug_handler,
            https_debug_handler,
            TokenHandler(account_obj=self)
        )        
        # Парсинг даты в обсуждениях поддерживает только английский язык
        self.opener.addheaders.append(('Cookie', 'remixlang=3'))
        
    def auth(self):
        '''
        Аутентификация аккаунта ВКонтакте
        '''
        
        content = self.opener.open('http://vk.com/login.php').read()

        matches = re.findall(r'name="ip_h" value="([^"]+)"', content)

        if len(matches) == 0:
            raise AccountError, "Not valid ip_h"

        self.ip_h = matches[0]
        
        data = urlencode({'act': 'login', 
                          'email': self.login, 
                          'pass': self.password, 
                          'expire': '', 
                          'vk': '1', 
                          'q': 1,
                          'al_frame': 1,
                          'to': b64encode('http://vk.com/feed2.php'),
                          'act': 'login',
                          'from_host': 'vk.com',
                          'from_protocol': 'http',
                          'ip_h': matches[0]
                          })
        response = self.opener.open('https://login.vk.com/', data).read()        

        if response.find('javascript: quick_login()') >= 0:           
            raise AccountError, "Invalid email or password"        

        # Проверка по 4 последним цифрам номера телефона
        if response.find('security_check') >= 0:
            matches = re.findall(r'\+?\d+(\d{4})', self.login)
            if len(matches) == 0:
                raise AccountError, 'Account needs security check'
            code = matches[0]

            matches = re.findall(r'\{act:\s*[\'"]security_check.*?hash:\s*[\'"]([0-9a-z]+)', response)
            if len(matches) == 0:
                raise AccountError, 'Can\'t find hash for security check'
            hash = matches[0]

            data = urlencode(dict(
                act='security_check',
                al=1,
                al_page=3,
                code=code,
                hash=hash,
                to=''
            ))
            self.opener.open('http://vk.com/login.php', data)

        self.is_loginned = True

        return True

    def oauth(self, app_id, scope):
        '''
        Авторизация пользователя в приложении. Возвращает offline-токен
        app_id -- номер приложения
        scope  -- список запрашиваемых прав, перечисленных через запятую
        '''

        if not self.is_loginned:
            raise Exception, 'Account must be loginned'
        
        url = 'http://oauth.vk.com/authorize?'+urlencode(dict(
            client_id=app_id,
            scope=scope,
            redirect_uri='blank.html',
            display='page',
            response_type='token'
        ))

        '''login_url = 'https://login.vk.com/?'+urlencode(dict(
            from_host='oauth.vk.com',
            from_protocol='http',
            ip_h=self.ip_h,
            soft=1,
            to=b64encode(url).replace('=', '-')
        ))'''

        response = self.opener.open(url)
        
        token = getattr(self, 'vk_token', None)
        setattr(self, 'vk_token', None)
        
        if token is not None:
            return  token

        # Может мы на странице получения прав доступа???
        matches = re.findall(r'hash=([0-9a-z]+)&client_id=\d+&settings=([0-9]+)', response.read())
        if len(matches) == 0: 
            return None            
        
        # Предоставление доступа
        url = 'https://oauth.vk.com/grant_access?hash=%s&client_id=%s&settings=%s&redirect_uri=blank.html&response_type=token&state=&token_type=0' % (
            matches[0][0],
            app_id,
            matches[0][1]
        )
        self.opener.open(url)

        token = getattr(self, 'vk_token', None)                
        setattr(self, 'vk_token', None)

        return token

    def make_request(self, *args, **kwargs):
        '''
        Выполнение запроса от лица аккаунта
        '''
        if not self.is_loginned:
            raise AccountError, 'Account must be loginned'
                
        return self.opener.open(self, *args, **kwargs)                

class APIError(Exception):
    '''
    Исключение при работе c API
    '''
    
    class CaptchaNeeded(Exception):
        """
        Требуется капча для продолжения
        
        Параметры:
            -- sid - номер сессии для капчи
            -- img - ссылка на изображение капчи
        """
        def __init__(self, sid, img):
            self.sid = sid
            self.img = img
    CaptchaNeeded = CaptchaNeeded
    
class APIProxy(object):
    '''
    Класс-посредник, позволяющий вызывать методы API ВКонтакте, не описывая их 
    в коде
    '''
    def __init__(self, api, prefix=''):
        '''
        api    -- объект класса API
        prefix -- префикс перед названиями методов. Если не пустая строка, то 
                  имя метода формируется как <prefix>.<method>, иначе <method>.
        '''
        self.api = api
        self.prefix = prefix
        self.methods = {}
        
    def get_method_name(self, name):
        '''
        Возвращает имя непосредственное имя метода для запроса к API ВКонтакте
        '''
        return ('' if self.prefix == '' else self.prefix + '.') + name
    
    def __getattr__(self, name):
        '''
        Метод-заглушка для формирования запросов к API с динамическими 
        названиями методов
        '''
        def method(*args, **kwargs):
            '''
            Метод, непосредственно выполняющий запрос
            '''
            args = kwargs
            args['access_token'] = self.api.access_token
            url = 'https://api.vk.com/method/' + self.get_method_name(name) + '?' 
            
            logging.debug('https://api.vk.com/method/' + self.get_method_name(name) + '?' + urlencode(dict(args)))
            
            response = urllib2.urlopen(url, urlencode(dict(args)), 5).read()

            answer = json.loads(response)
            try:
                return answer['response']
            except (KeyError):
                if answer['error']['error_code'] == 14:
                    raise APIError.CaptchaNeeded(answer['error']['captcha_sid'], answer['error']['captcha_img'])
                else:
                    raise APIError, "%s (code %s)" % (answer['error']['error_msg'], answer['error']['error_code'])
            except (HTTPError):
                raise APIError, "API is down"
        
        if name not in self.methods:
            self.methods[name] = method

        return self.methods[name]

class API(object):
    '''
    Класс для запросов к API ВКонтакте
    '''
    def __init__(self, access_token):
        '''
        access_token -- токен
        '''
        self.access_token = access_token

        # обертка для простых методов        
        self.methods = APIProxy(self)
        prefixes = ['likes', 'friends', 'groups', 'photos', 'wall', 'newsfeed', 
                    'audio', 'video', 'docs', 'places', 'secure', 'storage', 
                    'notes', 'pages', 'offers', 'questions', 
                    'subscriptions', 'messages']
        # обертка для вложенные методов
        for prefix in prefixes:
            setattr(self, prefix, APIProxy(self, prefix))
            
        self.cached_names = {}
            
    def __getattr__(self, name):
        '''
        Позволяет обращаться к методам без префикса
        '''
        return self.methods.__getattr__(name)          
        
    def resolve_names(self, ids):
        '''
        Выполняет резолвинг имен, которые не в формате 
        id<номер пользователя ВКонтакте>
        
        ids -- список идентификаторов пользователей
        '''
        ids_map = dict([[mid, mid] for mid in ids])
        
        to_resolve = []
        for mid in ids:
            if mid in self.cached_names:
                ids_map[mid] = self.cached_names[mid]
            elif len(re.findall(r'^id\d+$', mid)) > 0:
                ids_map[mid] = int(mid.replace('id', ''))
                self.cached_names[mid] = ids_map[mid]
            else:
                to_resolve.append(mid)
                
        if len(to_resolve) > 0:
            sequence = GroupSnapshoter.create_requests_sequence(1, len(to_resolve), 400)
            for start, count in sequence:
                part = to_resolve[start:start+count]
                
                answer = self.getProfiles(
                    uids=",".join(part),
                    fields='uid'
                )
                for i in xrange(len(part)):
                    ids_map[part[i]] = answer[i]['uid']
                    self.cached_names[part[i]] = answer[i]['uid']
                
        return ids_map
class Board(object):
    '''
    Класс для парсинга обсуждений: топики и комментарии
    '''
    def __init__(self, gid, account=None, api=None, resolve_names=True):
        '''
        Конструктор
        
        gid     -- номер группы
        account -- залогиненный аккаунт (нужен для парсинга закрытых групп)
        api     -- объект класса API для резолвинга имен
        resolve_names -- следует ли возращать имена пользователей или их номера
        '''
        self.gid = gid
        self.account = account
        self.api = api
        self.resolve_names = resolve_names
        
        if account is None:
            debug_handler = urllib2.HTTPHandler()

            if settings.DEBUG:
                debug_handler.set_http_debuglevel(1)

            self.opener = urllib2.build_opener(
                debug_handler
            )         
            # Парсинг даты поддерживает только английский язык    
            self.opener.addheaders.append(('Cookie', 'remixlang=3'))
        
    def make_request(self, *args, **kwargs):
        '''
        Выполняет запрос
        '''
        try:
            if self.account is not None:
                return self.account.make_request(*args, **kwargs)
            else:
                return self.opener.open(*args, **kwargs)
        except HTTPError:
            raise APIError, "API is down"
                
    @staticmethod
    def clear(content):
        '''
        Очистка строки от служебной информации
        '''
        return re.sub(r'.*<!>', '', content)
            
    def get_topics(self, offset=0, count=40, order='by_update'):
        '''
        Возвращает список тем в формате [{id: ..., count: ...}], где:
            id    - идентификатор топика
            count - количество сообщений
        Размер массива обычно составляет 40 элементов.
            
        offset -- смещение от начала списка
        order  -- сортировка топиков: by_update (по дате обновления), by_date (по дате создания)
        '''
        if count < 0:
            count = 0
            
        query = urlencode(dict(
            al=1,
            offset=offset,
            part=1,
            order=2 if order == 'by_date' else 2 #by_update
        ))
        response = self.make_request('http://vk.com/board%s' % self.gid,  query).read()

        topics = []
        soup = BeautifulSoup(self.clear(response))        
        for info in soup.findAll((), {'class': 'blst_info'}):
            try:
                topic_id = re.findall(r'/topic-\d+_(\d+)', str(info))[0]
                count_msgs = int(re.findall(r'(\d+)', str(info.find((), {'class': 'blst_msgs'})))[0])
            except (IndexError, ValueError):
                continue
                
            topics.append(BaseDict({
                'id':    topic_id,
                'count': count_msgs
            }))

        return topics[:count]
    
    def get_topic_info(self, topic_id):
        '''
        Возвращает идентификатор создателя топика. Основано на 
        предположении, что владелец первого комментария и есть создатель.
        '''
        comments = self.get_comments(topic_id, offset=0)
        return BaseDict({
            'from_id': comments[0].from_id,
            'date':    comments[0].date
        })
    
    @staticmethod
    def parse_date(txt):
        '''
        Возвращает дату на основе текстового представления.
        Поддерживается только английская версия
        '''
        if not isinstance(txt, basestring):
            return None

        if txt.find('Today') >= 0:
            return date.today()
        elif txt.find('Yesterday') >= 0:
            return date.today() + timedelta(-1)
        else:
            try:
                time_struct = time.strptime(txt, "%b %d, %Y at %I:%M %p")
                return date(time_struct.tm_year, time_struct.tm_mon, time_struct.tm_mday)
            except ValueError:
                return None    
    
    def get_comments(self, topic_id, offset=0, count=20):
        '''
        Возвращает список комментариев к топику в формате [{id: ..., from_id: ..., text: '...', date: ...}], где:
            id      - идентификатор комментария
            from_id - идентификатор человека, написавшего пост (необязательно числовой идентификатор)
            text    - текст поста
            date    - дата создания комментария
        
        topic_id      -- идентификатор топика
        offset        -- смещение от начала топика
        '''
        if count < 0:
            count = 0
                    
        query = urlencode(dict(
            al=1,
            offset=offset,
            part=1
        ))
        response = self.make_request('http://vk.com/topic-%s_%s' % (self.gid, topic_id), query).read()
        soup = BeautifulSoup(self.clear(response))
        comments = []
        for comment in soup.findAll((), {'class': 'bp_info'}):
            try:
                comment_id = re.findall(r'id="bp_data-\d+_(\d+)', str(comment))[0]
                from_id = re.findall(r'href="/([^"]+)"', str(comment.find((), {'class': 'bp_author'})))[0]
                text = str(comment.find((), {'class': 'bp_text'}))
                
                comment_date = str(comment.find((), {'class': 'bp_date'})) 
                comment_date = re.sub(r'<.*?>', '', comment_date)               
                comment_date = self.parse_date(comment_date)
            except (IndexError, ValueError):
                continue
            
            comments.append(BaseDict({
                'id':      comment_id,
                'from_id': from_id,
                'date':    comment_date,
                'text':    text
            }))
    
        # Резолвинг имен
        if self.api and self.resolve_names:
            ids = list(set([comment.from_id for comment in comments]))
            ids_map = self.api.resolve_names(ids)
            
            for comment in comments:
                comment.from_id = ids_map[comment.from_id]
                
            
        return comments[:count]
        
    def get_count(self):
        '''
        Возвращает количество тем в группе
        '''
        response = self.make_request('http://vk.com/board%s' % (self.gid)).read()
        matches = re.findall(r'id="board_summary"><a.*?</a>.*?(\d+).*?</div>', response)
        return int(matches[0]) if len(matches) > 0 else None

class GroupSnapshoter(object):
    '''
    Создание снимка текущего состояния группы
    '''

    WALL_COUNT = 100
    BOARD_COUNT = 40
    VIDEOS_COUNT = 200
    PHOTOS_COUNT = 100
    LIKES_COUNT = 1000
    BOARD_COMMENT_COUNT = 20
    
    def __init__(self, gid, api, account=None, resolve_names=True):
        '''
        gid     -- номер группы
        api     -- API
        account -- аккаунт для выполнения запросов
        resolve_names -- следует ли возращать имена пользователей или их номера
        '''
        self.account = account
        self.gid = int(gid)
        self.resolve_names = resolve_names        
        
        self.api = api
        self.board = Board(gid, account, resolve_names=False)
        
    @staticmethod
    def create_requests_sequence(start, end, count):
        '''
        Возвращает последовательность пар (смещение, кол-во запрашиваемых
        элементов) для получения элементов со start по end
        
        count -- разме выборки
        '''
        if start > end: 
            raise Exception, "start must be greater than end"
        if end - start  <= count:
            return [(start-1, end - start + 1)]    
            
        sequence = [(i*count+start-1, count) for i in xrange(0, (end-start)/count)]
        if end % count > 0:
            sequence.append(((end-start)/count * count, end % count))
        else:
            sequence.append(((end-start)/count * count, count))
            
        return sequence
        
    def get_wall_count(self):
        '''
        Возвращает количество постов на стене
        '''
        return self.api.wall.get(owner_id=-self.gid)[0]
        
    def get_photos_count(self):
        '''
        Возвращает количество фотографий в группе
        '''
        return self.api.photos.getAll(owner_id=-self.gid)[0]        
        
    def get_videos_count(self):
        '''
        Возвращает количество видео в группе
        '''
        return self.api.video.get(owner_id=-self.gid)[0]
        
    def make_for_wall(self, size=100):
        '''
        Возвращает снимок для стены
        
        size -- максимальный размер выборки
        '''

        if size < 1:
            return []
                    
        offset = 0
        posts = []
        
        for offset, count in self.create_requests_sequence(1, size, self.WALL_COUNT):
            answer = self.api.wall.get(owner_id=-self.gid, offset=offset, count=count)
            if len(answer) < 2:
                break
            posts[len(posts):] = answer[1:]

        snapshot = []
        
        for post in posts:
            try:
                post_date = date.fromtimestamp(int(post['date']))
            except (ValueError, KeyError):
                post_date = None
                 
            snapshot.append(BaseDict({
                'name':    'wall%s_%s' % (post['to_id'], post['id']),
                'type':    'post',
                'owner':   -self.gid,
                'from_id':  post['from_id'],
                'likes':    post['likes']['count'],
                'comments': post['comments']['count'],
                'shares':   post['reposts']['count'],
                'date':     post_date,
                'data': BaseDict({
                    'internal_id': post['id'],
                })
            }))
        
        return snapshot
    
    def make_for_board(self, size=100):
        '''
        Возвращает снимок для топиков
        
        size -- максимальный размер выборки
        '''
        
        if size < 1:
            return []        
   
        offset = 0
        topics = []
        
        for offset, count in self.create_requests_sequence(1, size, self.BOARD_COUNT):
            answer = self.board.get_topics(offset=offset, count=count)
            if len(answer) == 0:
                break
            topics[len(topics):] = answer
        
        snapshot = []
        
        for topic in topics:
            snapshot.append(BaseDict({
                'name':     'topic-%s_%s' % (self.gid, topic['id']),
                'type':     'topic',
                'owner':    -self.gid,
                'from_id':  0,
                'comments': topic['count'],
                'likes':    0,
                'shares':   0, 
                'date':     None,
                'data': BaseDict({
                    'internal_id': topic['id']
                })
            }))
        
        return snapshot    
        
    def make_for_videos(self, size=100):
        '''
        Возвращает снимок для видео
        
        size -- максимальный размер выборки
        '''
        if size < 1:
            return []
    
        offset = 0
        videos = []
        
        for offset, count in self.create_requests_sequence(1, size, self.VIDEOS_COUNT):
            answer = self.api.video.get(gid=self.gid, offset=offset, count=count)
            if len(answer) < 2:
                break
            videos[len(videos):] = answer[1:]
        
        snapshot = []
        
        for video in videos:
            execute = self.api.execute(code='''
                return {
                        comments: API.video.getComments({
                            owner_id: %(owner)s, 
                            vid: %(id)s,
                            count: 1
                        }), 
                        likes:API.likes.getList({
                            type: "video", 
                            owner_id: %(owner)s, 
                            item_id: %(id)s,
                            count: 1
                        })
                    };''' % {'id': video['vid'], 'owner': video['owner_id']} 
            )
            
            try:
                video_date = date.fromtimestamp(int(video['date']))
            except (ValueError, KeyError):
                video_date = None
                
            snapshot.append(BaseDict({
                'name':    'video%s_%s' % (video['owner_id'], video['vid']),
                'type':    'video',
                'owner':   -self.gid,
                'from_id':  video['owner_id'],
                'likes':    execute['likes']['count'],
                'comments': execute['comments'][0],
                'shares':   0,
                'date':     video_date,
                'data': BaseDict({
                    'internal_id': video['vid']
                })
            }))
        
        return snapshot
        
    def make_for_photos(self, size=100):
        '''
        Возвращает снимок для фотографий
        
        size -- максимальный размер выборки
        '''
        
        if size < 1:
            return []        
    
        offset = 0
        photos = []
        
        for offset, count in self.create_requests_sequence(1, size, self.PHOTOS_COUNT):
            answer = self.api.photos.getAll(owner_id=-self.gid, offset=offset, count=count, extended=1)
            if len(answer) < 2:
                break
            photos[len(photos):] = answer[1:]
        
        snapshot = []
        
        for photo in photos:
            comments = self.api.photos.getComments(owner_id=-self.gid, pid=photo['pid'])
            if comments is None:
                continue
            comments = comments[0]
            
            try:
                photo_date = date.fromtimestamp(int(photo['created']))
            except (ValueError, KeyError):
                photo_date = None            
            
            snapshot.append(BaseDict({
                'name':    'photo-%s_%s' % (self.gid, photo['pid']),
                'type':    'photo',
                'owner':   -self.gid,
                'from_id':  photo['owner_id'],
                'likes':    photo['likes']['count'],
                'comments': comments,
                'shares':   0,
                'date':     photo_date,
                'data': BaseDict({
                    'internal_id': photo['pid']
                })
            }))
        
        return snapshot    
