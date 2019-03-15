from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

# Create your views here.
def login_user(request):
    err = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', '/'))
        else:
            err = 'Invalid credentials, please try again'

    context = {
        'err': err,
    }
    return render(request, 'accounts/login.html', context)

def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return render(request, 'accounts/logout.html')
