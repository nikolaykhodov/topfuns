# -*- coding: utf-8 -*- 
'''
Модуль создания снимка группы и фиксации изменений
'''

from django.core.management.base import BaseCommand
import logging

from topfuns.models import Item, Action, VkGroup, VkAccount
from lib.vk.basedict import BaseDict
from lib.vk.api import API, GroupSnapshoter, Account, Board, APIError, AccountError
from topfuns.helpers import run_sql, setup_crawler_logging

from settings import APP_ID
from settings import APP_PERMISSION_SCOPE
from settings import p
from settings import CREATE_ACTIONS_WHEN_EMPTY
from datetime import date
from urllib2 import HTTPError

class Crawler(object):
    '''
    Класс создания снимка группы
    '''    
    
    def __init__(self, gid):
        self.vk_accounts = VkAccount.objects.all()
        self.gid = str(gid)
        
        self.board = None
        self.account = None
        self.api = None
        self.save_actions = True
    
    def choose_account(self):
        '''
        Возвращает первый аккаунт с валидным токеном доступа
        '''
        vk_account = None
        for vk_acc in self.vk_accounts:
            try:
                if not self.test_token(vk_acc):
                    if not self.refresh_token(vk_acc):
                        continue
                vk_account = vk_acc
            except (AccountError, HTTPError):
                continue 
                            
        return vk_account
    
    @staticmethod
    def test_token(vk_account):
        '''
        Возвращает True, если токен аккаунта account валиден
        '''
        api = API(vk_account.access_token)
        try:
            return (api.friends.get(uid=1) is not None)
        except APIError:
            return False
            
    @staticmethod
    def refresh_token(vk_account):
        '''
        Возвращает True, если удалось обновить токен для аккаунта account
        '''
        account = Account(vk_account.login, vk_account.password)
        account.auth()
        access_token = account.oauth(APP_ID, APP_PERMISSION_SCOPE)
        
        # Нифига! Ну, что ж, придется ответить отказом
        if access_token is None:
            return False
        else:
            # Получили свеженький как цветущая девственница токен :)
            # Не забудим его сохранить в базу данных.
            vk_account.access_token = access_token
            vk_account.save()
            return True
    
    @staticmethod
    def find(item):
        '''
        Возвращает объект Item из базы данных с таким же идентификатором, 
        как у и item из снимка
        '''
        try:
            return Item.objects.get(name=item.name)
        except Item.DoesNotExist:
            return None
            
    def create_update_task(self, snapshot):
        '''
        Возвращает задание для обновления базы данных
        
        snapshot -- свежий снимок группы
        '''
        tasks = []
        for new_item in snapshot:
            old_item = Crawler.find(new_item)
            
            # Новый объект надо добавить в базу данных
            if old_item is None:
                task = BaseDict(
                    action='add',
                    item=new_item,
                )

                if new_item.likes > 0 and self.save_actions:
                    task.likes_change = [1, new_item.likes]
                else:
                    task.likes_change = None
                    
                if new_item.comments > 0 and self.save_actions:
                    task.comments_change = [1, new_item.comments]     
                else:
                    task.comments_change = None
                    
                if new_item.shares > 0 and self.save_actions:
                    task.shares_change = [1, new_item.shares]
                else:
                    task.shares_change = None
            else:
                # Для старого объекта обновить информацию и 
                # составить список действий с ним
                task = BaseDict(
                    action='update',
                    item=new_item
                )
                
                # измененилось количество лайков
                if new_item.likes > old_item.likes:
                    task.likes_change = [1, new_item.likes-old_item.likes]
                else:
                    task.likes_change = None

                # измененилось количество комментариев
                if new_item.comments > old_item.comments:
                    task.comments_change = [
                        old_item.comments+1, 
                        new_item.comments
                    ]
                else:
                    task.comments_change = None

                # измененилось количество репостов                    
                if new_item.shares > old_item.shares:
                    task.shares_change = [old_item.shares+1, new_item.shares]
                else:
                    task.shares_change = None
            
            tasks.append(task)
        
        return tasks
    
    
    def fetch_likes(self, item, change, shares=False):
        '''
        Возвращает список пользователей, совершивших действие 
        "поставил лайк" пользователей для item.
        
        change -- [<начало списка лайков>, <конец списка лайков>]
        shares -- если True, то обрабатывает пользователей, которые сделали 
                  репост объекта
        '''
        sequence = GroupSnapshoter.create_requests_sequence(
                    change[0], 
                    change[1], 
                    GroupSnapshoter.LIKES_COUNT
        )
        
        retval = []
        for offset, count in sequence:
            try:
                likes = self.api.likes.getList(
                    type=item.type, 
                    owner_id=item.owner, 
                    item_id=item.data.internal_id,
                    offset=offset, 
                    count=count,
                    filter='likes' if not shares else 'copies'
                )
                
                retval.extend(likes['users'])
            except APIError:
                continue
            
        return retval
            
    def fetch_comments(self, item, change):
        '''
        Возвращает список комментариев для item.
        
        change -- [<начало списка лайков>, <конец списка лайков>]
        '''            
        if item.type == 'post':
            sequence = GroupSnapshoter.create_requests_sequence(
                change[0], 
                change[1],
                GroupSnapshoter.WALL_COUNT
            )
            get = lambda offset, count: self.api.wall.getComments(
                    owner_id=item.owner,
                    post_id=item.data.internal_id, 
                    offset=offset, 
                    count=count
                )[1:]
        elif item.type == 'topic':
            sequence = GroupSnapshoter.create_requests_sequence(
                change[0], 
                change[1],
                GroupSnapshoter.BOARD_COMMENT_COUNT
            )
            get = lambda offset, count: self.board.get_comments(
                    topic_id=item.data.internal_id, 
                    offset=offset,
            )
        elif item.type == 'photo':
            sequence = GroupSnapshoter.create_requests_sequence(
                change[0], 
                change[1],
                GroupSnapshoter.PHOTOS_COUNT
            )
            get = lambda offset, count: self.api.photos.getComments(
                    owner_id=item.owner,
                    pid=item.data.internal_id, 
                    offset=offset, 
                    count=count
                )[1:]
        elif item.type == 'video':
            sequence = GroupSnapshoter.create_requests_sequence(
                change[0], 
                change[1],
                GroupSnapshoter.VIDEOS_COUNT
            )
            get = lambda offset, count: self.api.video.getComments(
                    owner_id=item.owner,
                    vid=item.data.internal_id, 
                    offset=offset, 
                    count=count
                )[1:]
        
        retval = []
        for offset, count in sequence: 
            try:
                comments = get(offset, count)
            except APIError:
                continue
            
            for comment in comments:
                if 'uid' in comment: 
                    comment['from_id'] = comment['uid']
                    
                if 'message' in comment: 
                    comment['text'] = comment['message']
                    
                if isinstance(comment['date'], basestring) or isinstance(comment['date'], int):
                    try:
                        comment['date'] = date.fromtimestamp(int(comment['date']))
                    except (ValueError, KeyError):
                        comment['date'] = None          
                        
            retval.extend(comments)

                        
        return retval
                    
    def fetch_updates(self, tasks):
        '''
        Выполняет обновление базы объектов и действий пользователей
        '''
        # Получает список новых комментариев, лайков и репостов для объекта
        for task in tasks:
        
            # Узнать номер создателя топика
            if task.action == 'add' and task.item.type == 'topic':
                try:
                    info = self.board.get_topic_info(task.item.data.internal_id)
                    task.item.from_id = info.from_id
                    task.item.date = info.date
                except APIError:
                    task.item.from_id = None

            if task.likes_change:
                logging.info("Fetching likes for %s from %s to %s", task.item.name, task.likes_change[0], task.likes_change[1])
            
                task.likes = self.fetch_likes(task.item, task.likes_change, False)
                
                logging.info("%s likes are fetched for %s", len(task.likes), task.item.name)

            if task.shares_change:
                logging.info("Fetching shares for %s from %s to %s", task.item.name, task.shares_change[0], task.shares_change[1])
            
                task.shares = self.fetch_likes(task.item, task.shares_change, True)
                
                logging.info("%s shares are fetched for %s", len(task.shares), task.item.name)
            
            if task.comments_change:
                logging.info('Fetching comments for %s from %s to %s', task.item.name, task.comments_change[0], task.comments_change[1])
                
                task.comments = self.fetch_comments(task.item, 
                                  task.comments_change)
                                  
                logging.info('%s comments are fetched for %s', len(task.comments), task.item.name)
        
        

        # Резолвинг номеров пользователей для топиков и комментариев к ним
        logging.info("Start resolving names for topics and its comments") 

        ids = []
        for task in tasks:
            if task.item.type == 'topic': 
                if task.action == 'add':
                    ids.append(task.item.from_id)
                if task.comments_change:
                    ids.extend([comment.from_id for comment in task.comments])

        ids = list(set(ids))
        ids_map = self.api.resolve_names(ids)
   
        for task in tasks:
            if task.item.type == 'topic':    
                if task.action == 'add':
                    task.item.from_id = ids_map[task.item.from_id]
                if task.comments_change:                
                    for comment in task.comments:
                        comment.from_id = ids_map[comment.from_id]
        
        logging.info("Completed resolving names for topics and its comments")        
        
        return tasks
    
    def fix_updates(self, tasks):
        '''
        Фиксирует обновления в базе данных 
        '''            
        for task in tasks:
            if task.action == 'add':
                item = Item.objects.create(
                    type=Item.TYPES[task.item.type], name=task.item.name, 
                    owner=task.item.owner, likes=task.item.likes,
                    comments=task.item.comments, shares=task.item.shares, 
                    data=task.item.data)


                if task.item.from_id:
                    Action.objects.create(
                        type=Action.TYPES['added'], item=item, who=task.item.from_id,date=task.item.date
                    )

            elif task.action == 'update' and (task.likes_change or task.shares_change or task.comments_change):
                item = Item.objects.get(name=task.item.name)

                item.likes = task.item.likes
                item.comments = task.item.comments
                item.shares = task.item.shares
                item.data = task.item.data

                item.save()
                
            if task.likes_change:
                for user in task.likes:
                    Action.objects.create(
                        who=user,
                        type=Action.TYPES['like'], 
                        item=item,
                        date=date.today()
                    )

            if task.shares_change:
                for user in task.shares:
                    Action.objects.create(
                        who=user,
                        type=Action.TYPES['share'], 
                        item=item,
                        date=date.today()
                    )

            if task.comments_change:
                for comment in task.comments:
                    Action.objects.create(
                        who=comment['from_id'],
                        type=Action.TYPES['comment'], 
                        item=item, 
                        date=comment['date'],
                        data = {'text': comment['text']}
                    )

    def run(self):
        '''
        Запускает работу кроулера
        '''
        self.account = self.choose_account()
        if self.account is None:
            raise Exception, "No valid account for parsing"

        
        self.api = API(self.account.access_token)
        self.board = Board(self.gid, api=self.api, resolve_names=False)
        
        # Если True, то для для всех (новых и обновленных) объектов будут
        # записываться действия пользователей, иначе только для 
        # обновленных
        self.save_actions = len(Item.objects.all()) != 0 or CREATE_ACTIONS_WHEN_EMPTY
        vk_group = VkGroup.objects.get(gid=self.gid)        
        
        logging.info("Start crawling for group %s", self.gid)
        logging.info("Save actions = %s", self.save_actions)
        logging.info("Wall Scanning Depth = %s", vk_group.wall_max)
        logging.info("Video Scanning Depth = %s", vk_group.video_max)
        logging.info("Photo Scanning Depth = %s", vk_group.photo_max)
        logging.info("Board Scanning Depth = %s", vk_group.board_max)
        
                
        snapshoter = GroupSnapshoter(self.gid, self.api)

        logging.info("Old Wall Posts Count = %s", vk_group.wall_count)
        logging.info("Old Photos Count = %s", vk_group.photos_count)
        logging.info("Old Videos Count = %s", vk_group.videos_count)
        logging.info("Old Board Topics Count = %s", vk_group.board_count)
        
        wall_count = snapshoter.get_wall_count()
        photos_count = snapshoter.get_photos_count()
        videos_count = snapshoter.get_videos_count()
        board_count = self.board.get_count()
        
        '''
        Рассчитываем разницу в количестве объектов, на которую надо
        увеличить глубину сканирования, чтобы собрать все новые объекты и 
        обновить старые
        '''
        new_posts = max(wall_count - vk_group.wall_count, 0)
        new_videos = max(videos_count - vk_group.videos_count, 0)
        new_photos = max(photos_count - vk_group.photos_count, 0)
        new_topics = max(board_count - vk_group.board_count, 0)
        
        '''
        '''
        vk_group.wall_count = wall_count
        vk_group.photos_count = photos_count
        vk_group.videos_count = videos_count
        vk_group.board_count = board_count

        
        logging.info("New Wall Posts Count = %s", wall_count)
        logging.info("New Photos Count = %s", photos_count)
        logging.info("New Videos Count = %s", videos_count)
        logging.info("New Board Topics Count = %s", board_count)        

        snapshot = []
        snapshot =      snapshoter.make_for_wall(size=vk_group.wall_max + new_posts)
        snapshot.extend(snapshoter.make_for_videos(size=vk_group.video_max + new_videos))
        snapshot.extend(snapshoter.make_for_photos(size=vk_group.photo_max + new_photos))
        snapshot.extend(snapshoter.make_for_board(size=vk_group.board_max + new_topics))
       
        logging.info("Crawling finished")
        logging.info("%s items are at snapshot", len(snapshot))
        
        logging.info("Creating tasks for updating")
        
        tasks = self.create_update_task(snapshot)  
        
        logging.info("Created tasks for updating")       
        logging.info("%s items are to be added", len(filter(lambda task: task.action=='add', tasks)))
        logging.info("%s items are to be updated", len(filter(lambda task: task.action=='update', tasks)))
        
        new_comments, new_likes, new_shares = 0, 0, 0
        for task in tasks:
            if task.comments_change:
                new_comments += task.comments_change[1] - task.comments_change[0] + 1
            if task.likes_change:
                new_likes += task.likes_change[1] - task.likes_change[0] + 1
            if task.shares_change:
                new_shares += task.shares_change[1] - task.shares_change[0] + 1

        logging.info("New comments: %s", new_comments)
        logging.info("New likes: %s", new_likes)
        logging.info("New shares: %s", new_shares)
        
        logging.info("Start fetching updates")
        
        tasks = self.fetch_updates(tasks)
        
        logging.info("Completed fetching updates")
        
        new_comments, new_likes, new_shares = 0, 0, 0
        for task in tasks:
            if task.comments_change:
                new_comments += len(task.comments)
            if task.likes_change:
                new_likes += len(task.likes)
            if task.shares_change:
                new_shares += len(task.shares)

        logging.info("New comments are fetched: %s", new_comments)
        logging.info("New likes are fetched: %s", new_likes)
        logging.info("New shares are fetched: %s", new_shares)
        
        logging.info("Start fixing updates")
        
        self.fix_updates(tasks)
        
        logging.info("Completed fixing updates")


class StatUpdater(object):
    '''
    Класс для обновления статистики
    '''         
    
    def __init__(self, gid):
        '''
        gid -- номер группы
        '''
        self.gid = int(gid)
        setup_crawler_logging()
        
    def update(self):
        '''
        Запускает обновление
        '''
        
        logging.info("Update top for group %s", self.gid)
        
        sql_script = open(p('app/topfuns/sql/processing.mysql.sql'), 'U')
        sql = sql_script.read().decode('utf-8') % {'gid': self.gid}
        run_sql(sql) 
        sql_script.close()
        
        logging.info("Updating for group %s completed", self.gid)
            
class Command(BaseCommand):
    '''
    Command
    '''
    
    args = '   '
    help = 'Run crawler'
    
    def handle(self, *args, **kwargs):
        '''
        handle
        '''
        setup_crawler_logging()
        
        groups = VkGroup.objects.all()
        for group in groups:
            crawler = Crawler(group.gid)
            updater = StatUpdater(group.gid)
            try:
                crawler.run()
                updater.update()
            except Exception, ex:
                logging.exception(ex)
                

