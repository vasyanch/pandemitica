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

    #path('ask/', views.QuestionAddView.as_view(), name='ask'),
    #path('question/<int:id>/', views.QuestionDetailsView.as_view(), name='question'),
    #path('search/', views.SearchView.as_view(), name='search'),
    #path('search/<str:tag>/', views.SearchTagView.as_view(), name='search_tag'),
    #path('profile/<int:id_user>/edit_data/', views.EditProfileView.as_view(), name='edit_profile'),
]