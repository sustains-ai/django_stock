# Minimal views for testing
from django.http import HttpResponse

def test_view(request):
    return HttpResponse("Test view works!")

def custom_login(request):
    print("🔍 Login view called")
    return HttpResponse("Login view is working!")
