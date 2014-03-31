# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Item'
        db.create_table('topfuns_item', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('owner', self.gf('django.db.models.fields.IntegerField')()),
            ('likes', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('comments', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('shares', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('data', self.gf('topfuns.fields.BaseDictField')(default={})),
        ))
        db.send_create_signal('topfuns', ['Item'])

        # Adding model 'Action'
        db.create_table('topfuns_action', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('who', self.gf('django.db.models.fields.IntegerField')()),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['topfuns.Item'])),
            ('date', self.gf('django.db.models.fields.DateField')(blank=True)),
            ('data', self.gf('topfuns.fields.BaseDictField')(default={})),
        ))
        db.send_create_signal('topfuns', ['Action'])

        # Adding model 'VkGroup'
        db.create_table('topfuns_vkgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gid', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('rules', self.gf('django.db.models.fields.CharField')(max_length=10000)),
            ('wall_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('photo_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('board_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('video_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('topfuns', ['VkGroup'])

        # Adding model 'VkModerator'
        db.create_table('topfuns_vkmoderator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['topfuns.VkGroup'])),
            ('mid', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('topfuns', ['VkModerator'])

        # Adding model 'VkAccount'
        db.create_table('topfuns_vkaccount', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('login', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('access_token', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
        ))
        db.send_create_signal('topfuns', ['VkAccount'])

        # Adding model 'Prize'
        db.create_table('topfuns_prize', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['topfuns.VkGroup'])),
            ('rank', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('img', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('topfuns', ['Prize'])

        # Adding model 'Top'
        db.create_table('topfuns_top', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['topfuns.VkGroup'])),
            ('who', self.gf('django.db.models.fields.IntegerField')()),
            ('rating', self.gf('django.db.models.fields.IntegerField')()),
            ('rank', self.gf('django.db.models.fields.IntegerField')()),
            ('change', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('topfuns', ['Top'])

        # Adding unique constraint on 'Top', fields ['group', 'rank']
        db.create_unique('topfuns_top', ['group_id', 'rank'])

        # Adding model 'TopHistory'
        db.create_table('topfuns_tophistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['topfuns.VkGroup'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('who', self.gf('django.db.models.fields.IntegerField')()),
            ('rating', self.gf('django.db.models.fields.IntegerField')()),
            ('rank', self.gf('django.db.models.fields.IntegerField')()),
            ('change', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('topfuns', ['TopHistory'])

        # Adding model 'Blocked'
        db.create_table('topfuns_blocked', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['topfuns.VkGroup'])),
            ('who', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('topfuns', ['Blocked'])

        # Adding model 'UserStat'
        db.create_table('user_stat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('who', self.gf('django.db.models.fields.IntegerField')()),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['topfuns.VkGroup'])),
            ('likes', self.gf('django.db.models.fields.IntegerField')()),
            ('shares', self.gf('django.db.models.fields.IntegerField')()),
            ('comments', self.gf('django.db.models.fields.IntegerField')()),
            ('added', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('topfuns', ['UserStat'])

        # Adding unique constraint on 'UserStat', fields ['group', 'who']
        db.create_unique('user_stat', ['group_id', 'who'])

        # Adding model 'Report'
        db.create_table('topfuns_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['topfuns.VkGroup'])),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')()),
            ('stuff', self.gf('django.db.models.fields.CharField')(max_length=10000)),
        ))
        db.send_create_signal('topfuns', ['Report'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'UserStat', fields ['group', 'who']
        db.delete_unique('user_stat', ['group_id', 'who'])

        # Removing unique constraint on 'Top', fields ['group', 'rank']
        db.delete_unique('topfuns_top', ['group_id', 'rank'])

        # Deleting model 'Item'
        db.delete_table('topfuns_item')

        # Deleting model 'Action'
        db.delete_table('topfuns_action')

        # Deleting model 'VkGroup'
        db.delete_table('topfuns_vkgroup')

        # Deleting model 'VkModerator'
        db.delete_table('topfuns_vkmoderator')

        # Deleting model 'VkAccount'
        db.delete_table('topfuns_vkaccount')

        # Deleting model 'Prize'
        db.delete_table('topfuns_prize')

        # Deleting model 'Top'
        db.delete_table('topfuns_top')

        # Deleting model 'TopHistory'
        db.delete_table('topfuns_tophistory')

        # Deleting model 'Blocked'
        db.delete_table('topfuns_blocked')

        # Deleting model 'UserStat'
        db.delete_table('user_stat')

        # Deleting model 'Report'
        db.delete_table('topfuns_report')


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
            'board_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'gid': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'photo_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'rules': ('django.db.models.fields.CharField', [], {'max_length': '10000'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'video_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
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
