from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('new_game/<int:game_num>', views.newGame, name='new_game'),
    path('new_game/', views.newGame, name='new_game'),
    path('play_game/<int:game_num>', views.playGame, name='play_game'),
    path('play_game/', views.newGame, name='new_game'),
     #path('<int:gameID>/', views.index, name='index')
]
