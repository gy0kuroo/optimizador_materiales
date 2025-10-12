from django.urls import path
from . import views

app_name = "opticut"

urlpatterns = [
    path("", views.index, name="index"),
]
