from django.urls import path
from query.views import execute_query


app_name = 'query'
urlpatterns = [
    path('execute/', execute_query, name='execute_query'),
]
