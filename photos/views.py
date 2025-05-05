from django.shortcuts import render

def upload_photo(request):
    return render(request, "photos/index.html", {})