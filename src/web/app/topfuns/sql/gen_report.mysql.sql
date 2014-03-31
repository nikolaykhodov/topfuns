SELECT @group:=%(gid)s;
SELECT @start_with:='%(start_with)s';
SELECT @end_with:='%(end_with)s';

SELECT @group_id:=(SELECT id FROM topfuns_vkgroup WHERE gid=@group);

CREATE TEMPORARY TABLE moderators (`mid` int(11), PRIMARY KEY(`mid`)) 
  SELECT mid FROM topfuns_vkmoderator WHERE group_id=@group_id;

CREATE TEMPORARY TABLE  `user_actions` (
  `id` int(11) NOT NULL,
  `who` int(11) NOT NULL,
  `action_type` int(11) NOT NULL,
  `date` date NOT NULL,
  `item_type` int(11) NOT NULL,  
  `item_id` int(11) NOT NULL,
  `admin` TINYINT(1) NOT NULL DEFAULT 0,

  PRIMARY KEY(`id`),
  KEY `atype_itype_admin_itemid`(`action_type`, `item_type`, `admin`, `item_id`) USING BTREE
) ENGINE=MyISAM;


INSERT INTO `user_actions` (id, who, action_type, date, item_type, item_id) 
  SELECT action.id, action.who, action.type as action_type, action.date, item.type as item_type, item.id as item_id
  FROM `topfuns_action` as action 
  LEFT JOIN `topfuns_item` as item ON (action.item_id=item.id and item.owner=-@group)  
  WHERE action.date >= @start_with AND action.date <= @end_with;

UPDATE user_actions,moderators SET admin=1 WHERE user_actions.who = moderators.mid OR user_actions.who=-@group;

CREATE TEMPORARY TABLE `admin_content` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND admin=1;	
  
CREATE TEMPORARY TABLE `admin_post` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND item_type=1 AND admin=1;	
	
CREATE TEMPORARY TABLE `admin_video` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND item_type=2 AND admin=1;		
	
CREATE TEMPORARY TABLE `admin_photo` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND item_type=3 AND admin=1;	
	
CREATE TEMPORARY TABLE `admin_topic` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND item_type=4 AND admin=1;		

CREATE TEMPORARY TABLE `fan_content` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND admin=0;	
  
CREATE TEMPORARY TABLE `fan_post` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND item_type=1 AND admin=0;	
	
CREATE TEMPORARY TABLE `fan_video` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND item_type=2 AND admin=0;		
	
CREATE TEMPORARY TABLE `fan_photo` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND item_type=3 AND admin=0;	
	
CREATE TEMPORARY TABLE `fan_topic` (`item_id` int(11), PRIMARY KEY(`item_id`))
    SELECT item_id FROM user_actions as a
	WHERE action_type=1 AND item_type=4 AND admin=0;	
	
CREATE TEMPORARY TABLE `admin_shared_post` (`item_id` int(11), PRIMARY KEY(`item_id`))
	SELECT item_id FROM user_actions
	WHERE action_type=3 AND item_type=1
	GROUP BY item_id;	

/* admin wall posts */
SELECT @admin_posts:=(SELECT COUNT(*) FROM admin_post);

/* fan wall posts */
SELECT @fan_posts:=(SELECT COUNT(*) FROM fan_post);

/* total wall posts */
SELECT @total_posts:=@admin_posts + @fan_posts;

/* admin wall post comments by fans */
SELECT @adm_post__fan_comments:=(SELECT COUNT(*) FROM user_actions AS a 
    INNER JOIN admin_post AS b ON (a.item_id=b.item_id) 
    WHERE action_type=4 and item_type=1 and admin=0
);

/* admin wall post comments by admins */
SELECT @adm_post__admin_comments:=(SELECT COUNT(*) FROM user_actions AS a 
    INNER JOIN admin_post AS b ON (a.item_id=b.item_id) 
    WHERE action_type=4 and item_type=1 and admin=1
);

/* admin wall post fan commentators */
SELECT @adm_post__commentators:=(SELECT COUNT(distinct who) FROM user_actions AS a 
    INNER JOIN admin_post AS b ON (a.item_id=b.item_id) 
    WHERE action_type=4 and item_type=1 and admin=0
);

/* average comments per admin post */
SELECT @adm_post__comments_per_post:=ROUND((@adm_post__admin_comments+@adm_post__fan_comments)/@admin_posts);

/* average comments per commentator */
SELECT @adm_post__comments_per_commentator:=ROUND((@adm_post__admin_comments+@adm_post__fan_comments)/@adm_post__commentators);

/* admin posts likes */
SELECT @adm_post__likes:=(SELECT COUNT(*) FROM user_actions AS a 
    INNER JOIN admin_post AS b ON (a.item_id=b.item_id) 
    WHERE action_type=2 and item_type=1 and admin=0
); 

/* average likes per admin post */
SELECT @adm_post__likes_per_post:=ROUND(@adm_post__likes/@admin_posts);

/* admin wall post fan likers */
SELECT @adm_post__likers:=(SELECT COUNT(distinct who) FROM user_actions AS a 
    INNER JOIN admin_post AS b ON (a.item_id=b.item_id) 
    WHERE action_type=2 and item_type=1 and admin=0
);

/* admin shared posts */
SELECT @adm_post__shares:=(SELECT COUNT(*) FROM admin_shared_post);

/* admin posts sharings */
SELECT @adm_post__sharings:=(SELECT COUNT(distinct who) FROM user_actions AS a 
    INNER JOIN admin_shared_post AS b ON (a.item_id=b.item_id) 
    WHERE action_type=3 and item_type=1 and admin=0
);

/* average shares per admin post */
SELECT @adm_post__shares_per_post:=ROUND(@adm_post__shares/@admin_posts);

/* average likes per shared post */
SELECT @adm_post__likes_per_share:=(ROUND((
        SELECT COUNT(*) FROM user_actions AS a 
            INNER JOIN admin_shared_post AS b ON (a.item_id=b.item_id) 
            WHERE action_type=2 and item_type=1 and admin=0
	) / @adm_post__shares)
);

/* average comments per shared post  */
SELECT @adm_post__comments_per_share:=(ROUND((
    SELECT COUNT(*) FROM user_actions as a
        INNER JOIN admin_shared_post AS b ON (a.item_id=b.item_id) 
	    WHERE action_type=4 AND item_type=1 
	)/@adm_post__shares)
);


/* fan wall posts comments by fans  */
SELECT @fan_post__fan_comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_post AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=1 AND admin=0
);

/* fan wall posts comments by admins */
SELECT @fan_post__admin_comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_post AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=1 and admin=1
);

/* fan wall posts fans commented */
SELECT @fan_post__commentators:=(SELECT COUNT(distinct who) FROM user_actions as a
    INNER JOIN fan_post AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=1 AND admin=0
);

/* average comments per fan post */
SELECT @fan_post__comments_per_post:=ROUND((@fan_post__admin_comments+@fan_post__fan_comments)/@fan_posts);


/* average fans commented per fan post */
SELECT @fan_post__commentators_per_post:=ROUND(@fan_post__commentators/@fan_posts);

/* fan posts likes */
SELECT @fan_post__likes:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_post AS b ON (a.item_id=b.item_id) 
	WHERE action_type=2 AND item_type=1 
); 

/* average likes per fan post */
SELECT @fan_post__likes_per_post:=ROUND(@fan_post__likes / @fan_posts); 

/* fan wall post likers */
SELECT @fan_post__likers:=(SELECT COUNT(distinct who) FROM user_actions as a
    INNER JOIN fan_post AS b ON (a.item_id=b.item_id) 
	WHERE action_type=2 AND item_type=1 
);

/* admin topics */
SELECT @admin_topics:=(SELECT COUNT(*) FROM admin_topic);

/* admin topic comments by fans */
SELECT @adm_topic__fan_comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN admin_topic AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=4 AND admin=0
);

/* admin topic comments by admins */
SELECT @adm_topic__admin_comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN admin_topic AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=4 AND admin=1
);

/* admin topic comments */
SELECT @adm_topic__comments:=@adm_topic__fan_comments + @adm_topic__admin_comments;

/* admin topics fan commentators */
SELECT @adm_topic__commentators:=(SELECT COUNT(distinct who) FROM user_actions as a
    INNER JOIN admin_topic AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=4 AND admin=0
);


/* users generated discussion topics */
SELECT @fan_topics:=(SELECT COUNT(*) FROM fan_topic);

/* fans generated discussion topics comments by fans */
SELECT @fan_topic__fan_comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_topic AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=4 AND admin=0
);

/* fans generated discussion topics comments by admins */
SELECT @fan_topic__admin_comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_topic AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=4 AND admin=1
);

/* fan generated discussion topics comments */
SELECT @fan_topic__comments:=@fan_topic__fan_comments + @fan_topic__admin_comments;

/* fan generated discussion topics users commented */
SELECT @fan_topic__commentators:=(SELECT COUNT(distinct who) FROM user_actions as a
    INNER JOIN fan_topic AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=4 AND admin=0
);

/* all videos */
SELECT @new_videos:=(SELECT COUNT(*) FROM admin_video);

/* video likes */
SELECT @video__likes:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN admin_video AS b ON (a.item_id=b.item_id) 
	WHERE action_type=2 AND item_type=2 
);

/* video comments */
SELECT @video__comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN admin_video AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=2
);

/* new admin photos */
SELECT @admin_photos:=(SELECT COUNT(*) FROM admin_photo);

/* admin photo likes */
SELECT @adm_photos__likes:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN admin_photo AS b ON (a.item_id=b.item_id) 
	WHERE action_type=2 AND item_type=3 
);

/* admin photo comments */
SELECT @adm_photos__comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN admin_photo AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=3 
);


/* new fan photos */
SELECT @fan_photos:=(SELECT COUNT(*) FROM fan_photo);

/* fan photo likes */
SELECT @fan_photos__likes:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_photo AS b ON (a.item_id=b.item_id) 
	WHERE action_type=2 AND item_type=3 
);

/* fan photo comments */
SELECT @fan_photos__comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_photo AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 AND item_type=3 
);

/* total likes to admin content */
SELECT @adm_content__likes:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN admin_content AS b ON (a.item_id=b.item_id) 
	WHERE action_type=2
);

/* total comments to admin content */
SELECT @adm_content__comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN admin_content AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 
);

/* total admin content users interacted */
SELECT @adm_content__interacted_users:=(SELECT COUNT(distinct who) FROM user_actions as a
    INNER JOIN admin_content AS b ON (a.item_id=b.item_id) 
	WHERE action_type>1 AND admin=0
);

/* total likes to fan content */
SELECT @fan_content__likes:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_content AS b ON (a.item_id=b.item_id) 
	WHERE action_type=2
);

/* total comments to fan content */
SELECT @fan_content__comments:=(SELECT COUNT(*) FROM user_actions as a
    INNER JOIN fan_content AS b ON (a.item_id=b.item_id) 
	WHERE action_type=4 
);

/* total fan content users interacted */
SELECT @fan_content__interacted_users:=(SELECT COUNT(distinct who) FROM user_actions as a
    INNER JOIN fan_content AS b ON (a.item_id=b.item_id) 
	WHERE action_type>1 AND admin=0
);

/* total likes */
SELECT @total__likes:=(SELECT COUNT(*) FROM user_actions as a
	WHERE action_type=2
);

/* total comments */
SELECT @total__shares:=(SELECT COUNT(*) FROM user_actions as a
	WHERE action_type=4
);

/* total shares */
SELECT @total_content__comments:=(SELECT COUNT(*) FROM user_actions as a
	WHERE action_type=3
);

/* total user content interactions */
SELECT @total_content__interactions:=(SELECT COUNT(*) FROM user_actions as a
	WHERE action_type > 1
);

