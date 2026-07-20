from django.shortcuts import render

def home(request):
    return render(request, "dashboard/index.html")
# Create your views here.
