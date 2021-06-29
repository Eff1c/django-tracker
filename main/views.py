from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.forms import fields
from guardian.decorators import permission_required_or_403
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, View, ListView
from django.views.generic.edit import FormView
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm

from accounts.utils import send_change_notification
from .models import Project, TaskType, TaskPriority, Task, Comment, TimeLoging
from .forms import ProjectForm, ChangeProjectForm, TaskForm, CommentForm, TimeLogingForm, TestForm


def check_user_group(user):
    return user.is_superuser or user 


class AdminOnlyView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('main:index')

        return super().dispatch(request, *args, **kwargs)


class Index(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        current_user = request.user
        if current_user.is_superuser:
            return redirect('main:projects')

        elif current_user.employee.project:
            return redirect('main:project', project_name=current_user.employee.project.unique_name)
        
        else:
            messages.warning(
                request, _('You do not have access to any projects. Wait for the administrator to add you to any-one.'))
            return redirect('accounts:profile')


class Projects(AdminOnlyView, FormView, ListView):
    model = Project
    form_class = ProjectForm
    paginate_by = 1
    template_name = 'main/projects.html'

    def form_valid(self, form):
        request = self.request
        unique_name_arg = form.cleaned_data['unique_name']

        # check on unique
        if Project.objects.filter(
            unique_name = unique_name_arg
        ).exists():
            messages.warning(request, _("Don't unique url name!"))


        else:
            # create group for user, how will worked on this project
            group_executors = Group.objects.create(name=unique_name_arg)

            new_project = Project()
            new_project.title = form.cleaned_data['title']
            new_project.description = form.cleaned_data['description']
            new_project.unique_name = unique_name_arg
            new_project.group_executors = group_executors
            new_project.save()

            # add workers to group
            for user_id in form.cleaned_data['workers']:
                executor = User.objects.get(pk=user_id)
                group_executors.user_set.add(executor)
                # set user project foreign key
                executor.employee.project = new_project

            # assign permissions for group executors
            assign_perm('work_on_project', group_executors, new_project)

            messages.success(request, _('You are successfully add new project!'))

        return HttpResponseRedirect(request.path_info)


class EditProject(AdminOnlyView, FormView):
    template_name = 'main/edit_project.html'
    form_class = ChangeProjectForm

    def get_initial(self):
        project = Project.objects.get(
            unique_name=self.kwargs["project_name"]
        )
        initial = super().get_initial()
        initial['title'] = project.title
        initial['description'] = project.description
        initial['workers'] = [executor.id for executor in User.objects.filter(groups__name=project.group_executors.name)]
        return initial

    def form_valid(self, form):
        request = self.request
        project = Project.objects.get(
            unique_name=self.kwargs["project_name"]
        )

        project.title = form.cleaned_data['title']
        project.description = form.cleaned_data['description']
        project.save()

        # change group_executors
        group_executors = project.group_executors 
        workers = form.cleaned_data['workers']
        all_users = [user for user in User.objects.exclude(username="AnonymousUser").filter(is_superuser=False)]
        for user in all_users:
            if str(user.id) in workers:
                group_executors.user_set.add(user)
                # change user project foreign key
                user.employee.project = project
            else:
                group_executors.user_set.remove(user)
                # delete user project foreign key
                if user.employee.project == project:
                    user.employee.project = None
            
            user.employee.save()

        messages.success(request, _('You are successfully edit this project!'))

        return redirect('main:projects')


@login_required
@permission_required_or_403('main.work_on_project', (Project, 'unique_name', 'project_name'))
def project(request, project_name):
    current_user = request.user
    project = Project.objects.get(unique_name=project_name)
    tasks = project.tasks.all()
    paginate_by = 1
    dict_for_template = {
        "project": project,
        "query": tasks,
    }
    template_name = 'main/project.html'

    form = TaskForm(request.POST, project_name=project_name)
    if request.method == 'POST' and current_user.is_superuser:
        if form.is_valid():
            new_task = Task()
            new_task.topic = form.cleaned_data['topic']
            new_task.description = form.cleaned_data['description']
            new_task.start_date = form.cleaned_data['start_date']
            new_task.finish_date = form.cleaned_data['finish_date']
            new_task.type = TaskType.objects.get(
                pk=int(form.cleaned_data['type'])
            )
            new_task.priority = TaskPriority.objects.get(
                pk=int(form.cleaned_data['priority'])
            )
            new_task.estimated_time = form.cleaned_data['estimated_time']
            new_task.executor = User.objects.get(
                pk=int(form.cleaned_data['executor'])
            )
            new_task.author = current_user
            new_task.project = project
            new_task.save()

            messages.success(request, _('You are successfully add new task!'))

            return HttpResponseRedirect(request.path_info)

    paginator = Paginator(tasks, paginate_by)

    page_number = request.GET.get('page')
    dict_for_template["page_obj"] = paginator.get_page(page_number)

    if current_user.is_superuser:
        dict_for_template["form"] = TaskForm(project_name=project_name)

    return render(request, template_name, dict_for_template)


@login_required
@permission_required_or_403('main.work_on_project', (Project, 'unique_name', 'project_name'))
def task(request, project_name, task_id):
    current_user = request.user
    current_task = Task.objects.get(pk=task_id)
    comments = current_task.comments.order_by('created').all()
    paginate_by = 1
    dict_for_template = {
        "project_name": project_name,
        "task": current_task,
    }
    template_name = 'main/task.html'

    dict_for_template["spend_time"] = current_task.time_loging.aggregate(Sum('time_spent'))['time_spent__sum'] or 0

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = Comment()
            new_comment.author = current_user
            new_comment.comment = form.cleaned_data['text']
            new_comment.task = current_task
            new_comment.save()

            messages.success(request, _('You are successfully add new comment!'))

            return HttpResponseRedirect(request.path_info)

    paginator = Paginator(comments, paginate_by)

    page_number = request.GET.get('page')
    dict_for_template["page_obj"] = paginator.get_page(page_number)

    dict_for_template["form"] = CommentForm()

    return render(request, template_name, dict_for_template)


def add_to_list_change(list_change, name_field, field, new_value):
    change_text = "Field: {name_field}. Old value: {old_value}; new value: {new_value}."

    if field != new_value:
        list_change.append(
            change_text.format(
                name_field = name_field,
                old_value = field,
                new_value = new_value
            )
        )
        field = new_value

    return list_change, field


@login_required
@permission_required_or_403('main.work_on_project', (Project, 'unique_name', 'project_name'))
def edit_task(request, project_name, task_id):
    current_user = request.user
    current_task = Task.objects.get(pk=task_id)
    dict_for_template = {
        "project_name": project_name,
        "task": current_task,
    }
    template_name = 'main/edit_task.html'

    if request.method == 'POST':
        form = TaskForm(request.POST, project_name=project_name)
        if form.is_valid():
            list_change = []

            list_change, current_task.topic = add_to_list_change(
                list_change,
                "topic",
                current_task.topic,
                form.cleaned_data['topic'],
            )

            list_change, current_task.description = add_to_list_change(
                list_change,
                "description",
                current_task.description,
                form.cleaned_data['description'],
            )

            list_change, current_task.start_date = add_to_list_change(
                list_change,
                "start_date",
                current_task.start_date,
                form.cleaned_data['start_date'],
            )

            list_change, current_task.finish_date = add_to_list_change(
                list_change,
                "finish_date",
                current_task.finish_date,
                form.cleaned_data['finish_date'],
            )

            list_change, current_task.type = add_to_list_change(
                list_change,
                "type",
                current_task.type,
                TaskType.objects.get(
                    pk=int(form.cleaned_data['type'])
                ),
            )

            list_change, current_task.priority = add_to_list_change(
                list_change,
                "priority",
                current_task.priority,
                TaskPriority.objects.get(
                    pk=int(form.cleaned_data['priority'])
                ),
            )

            list_change, current_task.estimated_time = add_to_list_change(
                list_change,
                "estimated_time",
                current_task.estimated_time,
                form.cleaned_data['estimated_time'],
            )

            list_change, current_task.executor = add_to_list_change(
                list_change,
                "executor",
                current_task.executor,
                User.objects.get(
                    pk=int(form.cleaned_data['executor'])
                ),
            )

            if len(list_change) != 0:
                current_task.save()
                text_list_change = f"Editor: {current_user}.\n" + "\n".join(list_change)
                # send email
                send_change_notification(text_list_change, current_task)
                print(text_list_change)

                messages.success(request, _('You are successfully edit task!'))
            else:
                messages.warning(request, _('Not found change in task fields!'))

            return redirect('main:task', project_name=project_name, task_id=current_task.id)

    dict_for_template["form"] = TaskForm(
        initial={
            "topic": current_task.topic,
            "description": current_task.description,
            "start_date": current_task.start_date,
            "finish_date": current_task.finish_date,
            "type": current_task.type.id,
            "priority": current_task.priority.id,
            "estimated_time": current_task.estimated_time,
            "executor": current_task.executor.id,
        },
        project_name=project_name,
    )

    return render(request, template_name, dict_for_template)


@login_required
@permission_required_or_403('main.work_on_project', (Project, 'unique_name', 'project_name'))
def time_loging(request, project_name, task_id):
    current_user = request.user
    current_task = Task.objects.get(pk=task_id)
    time_loging = current_task.time_loging.all()
    paginate_by = 1
    dict_for_template = {
        "project_name": project_name,
        "task": current_task,
    }
    template_name = 'main/time_loging.html'

    if request.method == 'POST':
        form = TimeLogingForm(request.POST)
        if form.is_valid():
            new_log = TimeLoging()
            new_log.author = current_user
            new_log.time_spent = form.cleaned_data['time_spent']
            new_log.comment = form.cleaned_data['comment']
            new_log.task = current_task
            new_log.save()

            messages.success(request, _('You are successfully add new log!'))

            return HttpResponseRedirect(request.path_info)

    paginator = Paginator(time_loging, paginate_by)

    page_number = request.GET.get('page')
    dict_for_template["page_obj"] = paginator.get_page(page_number)

    dict_for_template["form"] = TimeLogingForm()

    return render(request, template_name, dict_for_template)


class LogEdit(AdminOnlyView, FormView):
    template_name = 'main/edit_log.html'
    form_class = TimeLogingForm

    def get_initial(self):
        log = TimeLoging.objects.get(
            pk=self.kwargs["log_id"]
        )
        initial = super().get_initial()
        initial['comment'] = log.comment
        initial['time_spent'] = log.time_spent
        return initial

    def form_valid(self, form):
        request = self.request
        log = TimeLoging.objects.get(
            pk=self.kwargs["log_id"]
        )

        log.comment = form.cleaned_data['comment']
        log.time_spent = form.cleaned_data['time_spent']
        log.save()

        messages.success(request, _('You are successfully edit this log!'))

        return redirect(
            'main:time_loging',
            project_name=self.kwargs["project_name"],
            task_id=self.kwargs["task_id"]
        )


class ChangeLanguageView(TemplateView):
    template_name = 'main/change_language.html'