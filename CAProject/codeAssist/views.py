from urllib import request
from django.shortcuts import render

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import Upload
from django.http import HttpResponse
from django.http import HttpRequest


class UploadView(CreateView):
    model = Upload
    fields = ['upload_file', ]
    success_url = reverse_lazy('fileupload')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Upload.objects.all()
        return context

def run_file(request):
    if request.method == "post":
        return "Hello world"
