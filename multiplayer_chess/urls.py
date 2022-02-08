from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'multiplayer_chess'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.loginView, name='login'),
    path('logout/', views.logoutView, name='logout'),
    path('register/', views.registerView, name='register'),
    path('home/', views.home, name='home'),
    path('gameroom/', views.gameroom, name='gameroom'),
    path('friends/', views.friends, name='friends'),
    path('play_with_friend/<str:friend_name>/',
         views.play_with_friend, name='play_with_friend'),
    path('accept_friend_request/<str:friend_name>/',
         views.accept_friend_request, name='accept_friend_request'),
    path('reject_friend_request/<str:friend_name>/',
         views.reject_friend_request, name='reject_friend_request'),
    path('player_exists/<str:friend_name>/',
         views.player_exists, name='player_exists'),
    path('send_request/<str:friend_name>/',
         views.send_request, name="send_request"),
    path('player_info/', views.player_info, name='player_info')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
