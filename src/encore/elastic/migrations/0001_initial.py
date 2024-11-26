# Generated by Django 5.1.1 on 2024-11-04 06:58

import model_utils.fields

import django.core.serializers.json
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("launchpad", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "status",
                    model_utils.fields.StatusField(
                        choices=[
                            ("new", "New"),
                            ("in_progress", "In Progress"),
                            ("failed", "Failed"),
                            ("completed", "Completed"),
                        ],
                        default="new",
                        max_length=100,
                        no_check_for_status=True,
                        verbose_name="status",
                    ),
                ),
                (
                    "status_changed",
                    model_utils.fields.MonitorField(
                        default=django.utils.timezone.now, monitor="status", verbose_name="status changed"
                    ),
                ),
                ("remote_ip", models.GenericIPAddressField(db_index=True, protocol="IPv4")),
                (
                    "method",
                    models.TextField(
                        choices=[("get", "Get"), ("post", "Post"), ("put", "Put"), ("snmp", "Snmp")],
                        db_index=True,
                        default="get",
                    ),
                ),
                (
                    "task",
                    models.TextField(
                        choices=[("event", "Event"), ("resolve", "Resolve")], db_index=True, default="event"
                    ),
                ),
                ("task_data", models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ("failure_reason", models.TextField(blank=True, default="")),
            ],
            options={
                "verbose_name": "Api Log",
                "verbose_name_plural": "Api Logs",
                "indexes": [models.Index(fields=["status"], name="elastic_api_status_e74e73_idx")],
            },
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "status",
                    model_utils.fields.StatusField(
                        choices=[
                            ("new", "New"),
                            ("suppressed", "Suppressed"),
                            ("creating_ticket", "Creating Ticket"),
                            ("alerted", "Alerted"),
                            ("resolving", "Resolving"),
                            ("resolved", "Resolved"),
                            ("deduped", "Deduped"),
                            ("error", "Error"),
                        ],
                        default="new",
                        max_length=100,
                        no_check_for_status=True,
                        verbose_name="status",
                    ),
                ),
                (
                    "status_changed",
                    model_utils.fields.MonitorField(
                        default=django.utils.timezone.now, monitor="status", verbose_name="status changed"
                    ),
                ),
                ("doc_id", models.TextField()),
                ("doc_index", models.TextField()),
                ("level", models.TextField(blank=True, null=True)),
                ("title", models.TextField(blank=True, null=True)),
                ("event_ts", models.DateTimeField()),
                (
                    "event_type",
                    models.TextField(
                        choices=[
                            ("up", "Up"),
                            ("down", "Down"),
                            ("neutral", "Neutral"),
                            ("<<missing>>", "Error: Field Not Found"),
                        ],
                        db_index=True,
                    ),
                ),
                ("asset_unique_id", models.TextField(blank=True, null=True)),
                ("asset_type", models.TextField(blank=True, null=True)),
                ("retry_count", models.PositiveIntegerField()),
                ("extras", models.JSONField(default=dict)),
                ("api_log", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to="elastic.apilog")),
                (
                    "monitor_tool_ip",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="events",
                        related_query_name="event",
                        to="launchpad.monitortoolip",
                    ),
                ),
            ],
            options={
                "verbose_name": "Event",
                "verbose_name_plural": "Events",
            },
        ),
        migrations.CreateModel(
            name="ErrorLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "event_status",
                    model_utils.fields.StatusField(
                        choices=[
                            ("new", "New"),
                            ("suppressed", "Suppressed"),
                            ("creating_ticket", "Creating Ticket"),
                            ("alerted", "Alerted"),
                            ("resolving", "Resolving"),
                            ("resolved", "Resolved"),
                            ("deduped", "Deduped"),
                            ("error", "Error"),
                        ],
                        default="new",
                        max_length=100,
                        no_check_for_status=True,
                    ),
                ),
                ("error_desc", models.TextField()),
                ("repeat_count", models.PositiveIntegerField(default=1)),
                ("resolved", models.BooleanField(default=False)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="errors",
                        related_query_name="error",
                        to="elastic.event",
                    ),
                ),
            ],
            options={
                "verbose_name": "Error Log",
                "verbose_name_plural": "Error Logs",
            },
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["status"], name="elastic_eve_status_c2eaf0_idx"),
        ),
        migrations.AddConstraint(
            model_name="errorlog",
            constraint=models.UniqueConstraint(fields=("event", "event_status", "error_desc"), name="unique_error_log"),
        ),
    ]
