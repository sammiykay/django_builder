# Generated manually for ChatThread and ChatMessage updates

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ai_builder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatThread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thread_id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('context_length', models.IntegerField(default=20)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='chat_thread', to='ai_builder.project')),
            ],
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='message_type',
            field=models.CharField(choices=[('normal', 'Normal Chat'), ('error_report', 'Error Report'), ('code_request', 'Code Request'), ('fix_applied', 'Fix Applied'), ('system_notification', 'System Notification')], default='normal', max_length=20),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='is_error_report',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='error_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='error_source',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='files_modified',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='code_changes',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='thread',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='ai_builder.chatthread'),
        ),
    ]