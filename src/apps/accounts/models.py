from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )


class Manager(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="manager",
        verbose_name="пользователь",
    )
    enterprises = models.ManyToManyField(
        "enterprises.Enterprise",
        related_name="managers",
        verbose_name="предприятия",
    )

    class Meta:
        indexes = [
            models.Index(fields=["id"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            self.user.is_staff = True
            group = Group.objects.get(name="managers")
            self.user.groups.add(group)
            self.user.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}"
