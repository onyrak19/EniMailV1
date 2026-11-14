from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Level, Parcours, Role
class MyUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("ENI", {"fields": ("role", "level", "parcours", "phone", "avatar", "is_approved", "notify_by_email")}),)
    list_display = ("username", "email", "first_name", "role", "level", "parcours", "is_approved")
admin.site.register(User, MyUserAdmin)
admin.site.register(Level)
admin.site.register(Parcours)
admin.site.register(Role)
