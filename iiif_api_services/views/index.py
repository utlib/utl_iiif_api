from django.shortcuts import render


def index(request, path=''):
  """
  Renders the Angular2 SPA
  """
  return render(request, 'index.html')