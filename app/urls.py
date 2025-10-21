from django.urls import path
from . import views

urlpatterns = [
    # path('strings/', views.list_strings, name='strings_collection'),  # GET returns list; POST -> use create_string via separate route if desired
    path('strings', views.handle_create_and_list, name='create_string'),  # keep POST separate for clarity
    path('strings/filter-by-natural-language', views.filter_by_nl, name='filter_by_nl'),
    # GET/DELETE on same path -> RESTful resource
    path('strings/<path:string_value>', views.string_detail, name='string_detail'),
]
