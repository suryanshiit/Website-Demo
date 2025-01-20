from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
   # path('manifest.json', manifest, name='manifest'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/logout/', views.signout, name='logout'),
    path('download-csv/', views.download_csv, name='download_csv'),
    path('get_data', views.get_data, name='get_data'),
    path("download_data", views.download_data, name="download_data"),
    path('chatbot_query', views.chatbot_query, name='chatbot_query'),
]
