from django.urls import path

from . import views

app_name = 'main'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('project/', views.Projects.as_view(), name='projects'),
    path('edit_project/<str:project_name>/', views.EditProject.as_view(), name='edit_project'),
    path('project/<str:project_name>/', views.project, name='project'),
    path(
        'project/<str:project_name>/task/<int:task_id>/',
        views.task,
        name='task'
    ),
    path(
        'project/<str:project_name>/task/<int:task_id>/edit_task/',
        views.edit_task,
        name='edit_task'
    ),
    path(
        'project/<str:project_name>/task/<int:task_id>/time_loging/',
        views.time_loging,
        name='time_loging'
    ),
    path(
        'project/<str:project_name>/task/<int:task_id>/log_edit/<int:log_id>/',
        views.LogEdit.as_view(),
        name='log_edit'
    ),
]
