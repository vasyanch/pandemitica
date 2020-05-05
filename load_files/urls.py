from django.urls import path

from . import views

app_name = 'load_files'
urlpatterns = [
    path('load_file/<str:file_type>/', views.LoadFileView.as_view(), name='load_file'),
    path('select_file_type/', views.SelectFileTypeView.as_view(), name='select_file_type'),
    path('file_processing/', views.FileProcessingView.as_view(), name='file_processing'),
    path('profile/<int:id_user>/', views.ProfileView.as_view(), name='profile'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LogInView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
]