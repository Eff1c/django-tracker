from django.contrib import admin

from .models import Project, TaskType, TaskPriority, Task, Comment

admin.site.register(Project)
admin.site.register(TaskType)
admin.site.register(TaskPriority)
admin.site.register(Task)
admin.site.register(Comment)
