CREATE TEMPORARY TABLE IF NOT EXISTS `user_actions` (
  `who` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `date` date NOT NULL,
  `type` int(11) NOT NULL,

  KEY `by_type` (`type`) USING BTREE,
  KEY `by_who_and_type` (`who`,`type`) USING BTREE,
  KEY `by_who` (`who`) USING BTREE,
  KEY `by_type_and_who` (`type`,`who`) USING BTREE
) ENGINE=InnoDB;

SELECT @group:=%(gid)s;
SELECT @group_id:=(SELECT id FROM topfuns_vkgroup WHERE gid=@group);

/*--------- Сохранить старую версию рейтинга пользователей*/
CREATE TEMPORARY TABLE `top_copy` (
  `who` int(11) NOT NULL,
  `rating` int(11) NOT NULL,
  `rank` int(11) NOT NULL,
  `change` int(11) NOT NULL,
  PRIMARY KEY (`who`)
) ENGINE=MEMORY;


SELECT @curtime:=NOW();
INSERT INTO `topfuns_tophistory`(group_id, timestamp, who, rating, rank, `change`)
  SELECT @group_id, @curtime, who, rating, rank, `change` FROM `topfuns_top` WHERE group_id=@group_id;


INSERT INTO `top_copy` 
  SELECT who, rating, rank, `change` FROM `topfuns_top` WHERE @group_id;

DELETE FROM `topfuns_top` WHERE group_id=@group_id;

/*------- Собрать статистику о действиях пользователей за заданный промежуток времени*/
INSERT INTO `user_actions` (`who`, `type`, `name`, `date`) 
  SELECT action.who, action.type, item.name, action.date 
  FROM `topfuns_action` as action 
  LEFT JOIN `topfuns_item` as item ON (action.item_id=item.id and item.owner=-@group)  
  WHERE action.who > 0 AND action.who NOT IN (SELECT mid FROM topfuns_vkmoderator WHERE group_id=@group_id)
    AND action.who NOT IN (SELECT who FROM topfuns_blocked WHERE group_id=@group_id)
    AND action.date >= '2011-12-02';

/*-------------- Подсчитать статистику каждого пользователя*/
DELETE FROM `user_stat` WHERE group_id=@group_id;


CREATE TEMPORARY TABLE `stat_added` (
  `who` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  
    PRIMARY KEY (`who`)    
) ENGINE=MEMORY;

CREATE TEMPORARY TABLE `stat_shares` (
  `who` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  
    PRIMARY KEY (`who`)    
) ENGINE=MEMORY;

CREATE TEMPORARY TABLE `stat_comments` (
  `who` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  
    PRIMARY KEY (`who`)    
) ENGINE=MEMORY;

CREATE TEMPORARY TABLE `stat_likes` (
  `who` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  
   PRIMARY KEY (`who`)    
) ENGINE=MEMORY;

INSERT INTO `user_stat` (who, group_id, likes, shares, comments, added) 
  SELECT DISTINCT who, @group_id as group_id, 0, 0, 0, 0 FROM `user_actions`; 

INSERT INTO `stat_added`(quantity, who) 
  SELECT count(who) as quantity, who FROM `user_actions` WHERE type=1 GROUP BY who;
UPDATE user_stat,stat_added SET user_stat.added=stat_added.quantity WHERE user_stat.who=stat_added.who AND group_id=@group_id;

INSERT INTO `stat_likes`(quantity, who) 
  SELECT count(who) as quantity, who FROM `user_actions` WHERE type=2 GROUP BY who;
UPDATE user_stat,stat_likes SET user_stat.likes=stat_likes.quantity WHERE user_stat.who=stat_likes.who AND group_id=@group_id;  

INSERT INTO `stat_shares`(quantity, who) 
  SELECT count(who) as quantity, who FROM `user_actions` WHERE type=3 GROUP BY who;
UPDATE user_stat,stat_shares SET user_stat.shares=stat_shares.quantity WHERE user_stat.who=stat_shares.who AND group_id=@group_id;

INSERT INTO `stat_comments`(quantity, who) 
  SELECT count(who) as quantity, who FROM `user_actions` WHERE type=4 GROUP BY who;
UPDATE user_stat,stat_comments SET user_stat.comments=stat_comments.quantity WHERE user_stat.who=stat_comments.who AND group_id=@group_id;
    
/*--------- Обновить рейтинг*/
SET @last:=(SELECT COUNT(*) FROM `user_stat` WHERE group_id=@group_id);

CREATE TEMPORARY TABLE calculated_rating 
  SELECT stat.who, 2*(likes+shares) + comments + added*3 as rating, IFNULL(top.rank, @last) as prev_rank
  FROM `user_stat` as stat 
  LEFT JOIN `top_copy` as top ON (stat.who=top.who and stat.group_id=@group_id)
  ORDER BY rating,who;

SELECT @new_rank:=(SELECT COUNT(*) FROM `user_stat`)+1;

INSERT INTO `topfuns_top` (who, rating, rank, `change`, group_id)
  SELECT who, rating, @new_rank:=@new_rank-1 as new_rank, prev_rank - @new_rank as `change`, @group_id as group_id 
  FROM calculated_rating; 
