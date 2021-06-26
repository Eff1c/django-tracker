from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils import timezone
from tinymce.models import HTMLField


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = HTMLField()
    unique_name = models.SlugField(max_length=100, unique=True)
    group_executors = models.OneToOneField(Group, on_delete=models.SET)

    class Meta:
        ordering = ['id']
        permissions = (
            ('work_on_project', 'Work on the project'),
        )

    def __str__(self):
        return self.title


class TaskType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class TaskPriority(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Task(models.Model):
    topic = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    finish_date = models.DateField()
    type = models.ForeignKey(TaskType, on_delete=models.PROTECT)
    priority = models.ForeignKey(TaskPriority, on_delete=models.PROTECT)
    estimated_time = models.IntegerField()
    executor = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="executor"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, editable=False, related_name="creator"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks"
    )

    def __str__(self):
        return self.topic

    class Meta:
        ordering = ['id']


class TimeLoging(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    time_spent = models.IntegerField()
    comment = models.CharField(max_length=500)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_loging")

    class Meta:
        ordering = ['id']


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=600)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    created = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['id']
