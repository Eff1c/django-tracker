from main.models import Project
from django.db import models
from django.contrib.auth.models import User


class Activation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)


class Position(models.Model):
    name = models.CharField(max_length=100)
    administrator_rights = models.BooleanField()

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthday = models.DateField()
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    avatar = models.ImageField(null=True, upload_to="avatars/")
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        related_name="employees"
    )

    def __str__(self):
        return self.user.username
