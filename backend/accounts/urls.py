from django.urls import path
from . import views as v
urlpatterns = [
    path("login/", v.LoginView.as_view()), path("register/code/", v.request_code), path("register/", v.register),
    path("password/code/", v.password_code), path("password/reset/", v.password_reset),
    path("me/", v.me), path("me/password/", v.me_password), path("me/avatar/", v.me_avatar), path("users/", v.users), path("users/resolve/", v.resolve),
    path("admin/pending/", v.pending), path("admin/approve/<int:pk>/", v.approve), path("admin/reject/<int:pk>/", v.reject),
    path("admin/users/", v.admin_users), path("admin/users/<int:pk>/", v.admin_user),
]
