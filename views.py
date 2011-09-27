from django.http import HttpResponseRedirect
from django.contrib.auth import logout

def logout_user(request):
    
    redirect_to = request.REQUEST.get('next', '')
    logout(request)
    
    return HttpResponseRedirect(redirect_to)
