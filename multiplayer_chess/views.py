
from urllib.request import Request
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from matplotlib.style import use

from multiplayer_chess.models import Friend_Request, Player
from .forms import NewUserForm, LoginForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

# Create your views here.


def index(request):
    if request.user.is_authenticated:
        return redirect('multiplayer_chess:home')
    return redirect('multiplayer_chess:login')


def loginView(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("multiplayer_chess:home")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = LoginForm()
    return render(request=request, template_name="multiplayer_chess/login.html", context={"login_form": form})


def logoutView(request):
    logout(request)
    return redirect("multiplayer_chess:login")


def registerView(request):
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        try:
            user = form.save()
            Player.objects.create(user=user)
            login(request, user)
            messages.success(request, "Registration successful")
            return redirect("multiplayer_chess:home")
        except Exception as e:
            messages.error(request, str(e))
    form = NewUserForm()
    return render(request=request, template_name="multiplayer_chess/register.html", context={"form": form})


@login_required(login_url='/login')
def home(request):
    return render(request=request, template_name='multiplayer_chess/home.html')


@login_required(login_url='/login')
def gameroom(request):
    return render(request=request, template_name="multiplayer_chess/gameroom.html", context={
        "game_type": 0
    })


@login_required(login_url='/login')
def play_with_friend(request, friend_name):
    return render(request=request, template_name="multiplayer_chess/gameroom.html", context={
        "game_type": 1,
        "friend_name": friend_name
    })


@login_required(login_url='/login')
def friends(request):

    player = Player.objects.get(user=request.user)
    friend_requests = []
    friends_list = []
    friends_list = player.friends.all().order_by('-is_online')
    friend_requests = Friend_Request.objects.filter(to_user=player)
    return render(request=request, template_name="multiplayer_chess/friends.html", context={
        'friend_requests': friend_requests,
        'friends_list': friends_list
    })


@login_required(login_url='/login')
def accept_friend_request(request, friend_name):
    player = Player.objects.get(user=request.user)
    friend = Player.objects.get(user=User.objects.get(username=friend_name))
    player.friends.add(friend)
    friend.friends.add(player)

    Friend_Request.objects.filter(from_user=friend, to_user=player).delete()
    return redirect('multiplayer_chess:friends')


@login_required(login_url='/login')
def reject_friend_request(request, friend_name):
    player = Player.objects.get(user=request.user)
    friend = Player.objects.get(user=User.objects.get(username=friend_name))
    Friend_Request.objects.filter(from_user=friend, to_user=player).delete()
    return redirect('multiplayer_chess:friends')


@login_required(login_url='/login')
def player_exists(request, friend_name):
    msg = "User found"
    exists = True
    if not User.objects.filter(username=friend_name).exists():
        msg = "User not found"
        exists = False
    elif request.user.username == friend_name:
        msg = "You"
        exists = False
    return JsonResponse({
        "exists": exists,
        "msg": msg
    })


@login_required(login_url='/login')
def send_request(request, friend_name):
    msg = ""
    from_user = Player.objects.get(user=request.user)
    to_user = Player.objects.get(user=User.objects.get(username=friend_name))
    print(from_user, to_user)
    if(Friend_Request.objects.filter(to_user=to_user, from_user=from_user).exists()):
        msg = "Request already sent"
    elif to_user in from_user.friends.all():
        msg = "Already a friend"
    else:
        Friend_Request.objects.create(from_user=from_user, to_user=to_user)
        msg = "Request sent"
    return JsonResponse({"msg": msg})


@login_required(login_url='/login')
def player_info(request):
    p = Player.objects.get(user=request.user)
    rating = 0
    total_games = p.played_in.all().count()
    games_won = p.winner.all().count()
    win_percent = games_won/total_games * 100
    context = {
        'rating': rating,
        'total_games': total_games,
        'win_percent': str(round(win_percent, 2))
    }
    return render(request=request, template_name='multiplayer_chess/profile.html', context=context)
