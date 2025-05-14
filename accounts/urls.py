from django.urls import path
from accounts import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register/', views.register, name="register"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('userprofile/<str:username>/', views.userprofile, name="userprofile"),
    path('search/', views.search_view, name="search"),
    path('create-chat/<str:username>/', views.create_or_get_chatroom, name="create_chat"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()