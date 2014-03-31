# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'VkGroup.wall_count'
        db.add_column('topfuns_vkgroup', 'wall_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0), keep_default=False)

        # Adding field 'VkGroup.photos_count'
        db.add_column('topfuns_vkgroup', 'photos_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0), keep_default=False)

        # Adding field 'VkGroup.videos_count'
        db.add_column('topfuns_vkgroup', 'videos_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0), keep_default=False)

        # Adding field 'VkGroup.board_count'
        db.add_column('topfuns_vkgroup', 'board_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'VkGroup.wall_count'
        db.delete_column('topfuns_vkgroup', 'wall_count')

        # Deleting field 'VkGroup.photos_count'
        db.delete_column('topfuns_vkgroup', 'photos_count')

        # Deleting field 'VkGroup.videos_count'
        db.delete_column('topfuns_vkgroup', 'videos_count')

        # Deleting field 'VkGroup.board_count'
        db.delete_column('topfuns_vkgroup', 'board_count')


    models = {
        'topfuns.action': {
            'Meta': {'object_name': 'Action'},
            'data': ('topfuns.fields.BaseDictField', [], {'default': '{}'}),
            'date': ('django.db.models.fields.DateField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['topfuns.Item']"}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'who': ('django.db.models.fields.IntegerField', [], {})
        },
        'topfuns.blocked': {
            'Meta': {'object_name': 'Blocked'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['topfuns.VkGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'who': ('django.db.models.fields.IntegerField', [], {})
        },
        'topfuns.item': {
            'Meta': {'object_name': 'Item'},
            'comments': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'data': ('topfuns.fields.BaseDictField', [], {'default': '{}'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'likes': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'owner': ('django.db.models.fields.IntegerField', [], {}),
            'shares': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'topfuns.prize': {
            'Meta': {'object_name': 'Prize'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['topfuns.VkGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'img': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'rank': ('django.db.models.fields.IntegerField', [], {})
        },
        'topfuns.report': {
            'Meta': {'object_name': 'Report'},
            'end': ('django.db.models.fields.DateField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['topfuns.VkGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {}),
            'stuff': ('django.db.models.fields.CharField', [], {'max_length': '10000'})
        },
        'topfuns.top': {
            'Meta': {'unique_together': "(('group', 'rank'),)", 'object_name': 'Top'},
            'change': ('django.db.models.fields.IntegerField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['topfuns.VkGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.IntegerField', [], {}),
            'rating': ('django.db.models.fields.IntegerField', [], {}),
            'who': ('django.db.models.fields.IntegerField', [], {})
        },
        'topfuns.tophistory': {
            'Meta': {'object_name': 'TopHistory'},
            'change': ('django.db.models.fields.IntegerField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['topfuns.VkGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.IntegerField', [], {}),
            'rating': ('django.db.models.fields.IntegerField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'who': ('django.db.models.fields.IntegerField', [], {})
        },
        'topfuns.userstat': {
            'Meta': {'unique_together': "(('group', 'who'),)", 'object_name': 'UserStat', 'db_table': "'user_stat'"},
            'added': ('django.db.models.fields.IntegerField', [], {}),
            'comments': ('django.db.models.fields.IntegerField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['topfuns.VkGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'likes': ('django.db.models.fields.IntegerField', [], {}),
            'shares': ('django.db.models.fields.IntegerField', [], {}),
            'who': ('django.db.models.fields.IntegerField', [], {})
        },
        'topfuns.vkaccount': {
            'Meta': {'object_name': 'VkAccount'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'topfuns.vkgroup': {
            'Meta': {'object_name': 'VkGroup'},
            'board_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'board_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'gid': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'photo_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'photos_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'rules': ('django.db.models.fields.CharField', [], {'max_length': '10000'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'video_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'videos_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'wall_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'wall_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'topfuns.vkmoderator': {
            'Meta': {'object_name': 'VkModerator'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['topfuns.VkGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mid': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        }
    }

    complete_apps = ['topfuns']
