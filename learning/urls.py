from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('hiragana_lessons/', views.hiragana_lessons, name='hiragana_lessons'),
    path('katakana_lessons/', views.katakana_lessons, name='katakana_lessons'),
    path('kanji_intro_lessons/', views.kanji_intro_lessons, name='kanji_intro_lessons'),
    path('grammar_lessons/', views.grammar_lessons, name='grammar_lessons'),
    path('update-stage/', views.update_stage, name='update_stage'),
    path('update-streak/', views.update_streak, name='update_streak'),
]