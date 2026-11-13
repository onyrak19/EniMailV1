from django.urls import path
from . import views as v
urlpatterns = [
    path("box/<str:name>/", v.box), path("send/", v.send), path("bulk/", v.bulk), path("action/<int:pk>/", v.action),
    path("delete/<int:pk>/", v.msg_delete), path("trash/empty/", v.empty_trash),
    path("attachment/<int:pk>/", v.download), path("stats/", v.stats),
]
