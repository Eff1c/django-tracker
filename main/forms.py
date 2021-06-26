import datetime

from django import forms
from django.forms import ValidationError
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from tinymce.widgets import TinyMCE

from .models import Project, TaskType, TaskPriority

TASK_TYPE_CHOICES = [
    (type.id, type.name) for type in TaskType.objects.all()
]

TASK_PRIORITY_CHOICES = [
    (priority.id, priority.name) for priority in TaskPriority.objects.all()
]

ALL_USERS_CHOICES = [
    (user.id, user.username) for user in User.objects.exclude(username="AnonymousUser").filter(is_superuser=False)
]


class ProjectForm(forms.Form):
    title = forms.CharField(max_length=200, label=_('Title'))
    description = forms.CharField(label=_('Description'), widget=TinyMCE)
    unique_name = forms.CharField(max_length=100, label=_('Unique name (for url)'))
    workers = forms.MultipleChoiceField(
        label=_('Workers on the project'),
        widget=forms.CheckboxSelectMultiple,
        choices=ALL_USERS_CHOICES
    )

    def clean_project_name(self):
        unique_name = self.cleaned_data['project_name']

        project = Project.objects.filter(unique_name__iexact=unique_name).exists()
        if project:
            raise ValidationError(_('You can not use this project name.'))

        return unique_name


class ChangeProjectForm(forms.Form):
    title = forms.CharField(max_length=200, label=_('Title'))
    description = forms.CharField(label=_('Description'), widget=TinyMCE)
    workers = forms.MultipleChoiceField(
        label=_('Workers on the project'),
        widget=forms.CheckboxSelectMultiple,
        choices=ALL_USERS_CHOICES
    )


class TaskForm(forms.Form):
    topic = forms.CharField(max_length=200, min_length=1, label=_('Topic'))
    description = forms.CharField(label=_('Description'), widget=forms.Textarea)
    start_date = forms.DateField(label=_('Start date'), initial=datetime.date.today, widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    finish_date = forms.DateField(label=_('Finish date'), initial=datetime.date.today, widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    type = forms.ChoiceField(label=_('Type'), widget=forms.Select, choices=TASK_TYPE_CHOICES)
    priority = forms.ChoiceField(label=_('Priority'), widget=forms.Select, choices=TASK_PRIORITY_CHOICES)
    estimated_time = forms.IntegerField(label=_('Estimated time'))
    executor = forms.ChoiceField(label=_('Executor'), widget=forms.Select)

    def __init__(self, *args, **kwargs):
        project_name = kwargs.pop('project_name')
        project = Project.objects.get(unique_name=project_name)
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['executor'].choices = [(user.id, user.username) for user in User.objects.filter(groups__name=project.group_executors.name)]


class CommentForm(forms.Form):
    text = forms.CharField(max_length=600, label=_('Text comment'), widget=forms.Textarea)


class TimeLogingForm(forms.Form):
    comment = forms.CharField(max_length=500, label=_('Log comment'), widget=forms.Textarea)
    time_spent = forms.IntegerField(label=_("Time spent (hours)"))


class TestForm(forms.Form):
    # workers = forms.MultipleChoiceField(
    #     label=_('Workers on the project'),
    #     widget=forms.CheckboxSelectMultiple,
    #     choices=ALL_USERS_CHOICES
    # )
    image = forms.ImageField(label=_('Avatar'))
