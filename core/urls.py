from django.contrib import admin
from django.urls import path
from games import views  # замени myapp на название своего приложения

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('games.urls')),
]