"""
URL configuration for chatwme project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from chat import views

urlpatterns = [
    path('', views.index_view, name="index"),
    path('home/', views.home, name="home"),
    path('chatroom/<slug:slug>/', views.chat_view, name="chatroom"),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<slug:slug>/', views.group_chat, name='group_chat'),
    path('groups/<slug:slug>/invite/', views.invite_to_group, name='invite_to_group'),
    path('groups/<slug:slug>/leave/', views.leave_group, name='leave_group'),
    path('groups/<slug:slug>/make-admin/<int:user_id>/', views.make_admin, name='make_admin'),
    path('groups/<slug:slug>/remove/<int:user_id>/', views.remove_from_group, name='remove_from_group'),
]

