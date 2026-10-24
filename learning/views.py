import json
from functools import wraps
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

UserModel = get_user_model()

# Keys match the database values (User.Stage values)
STAGE_RANKING = {
    'HIRAGANA': 1,
    'KATAKANA': 2,
    'KANJI': 3,
    'GRAMMAR': 4,
}


def stage_required(required_stage_name):
    """Decorator to gate views based on STAGE_RANKING."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user_rank = STAGE_RANKING.get(request.user.highest_unlocked_stage, 1)
            required_rank = STAGE_RANKING.get(required_stage_name, 1)

            if user_rank < required_rank:
                return redirect('index')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = UserModel
        fields = (UserModel.USERNAME_FIELD, *UserModel.REQUIRED_FIELDS)


@require_http_methods(["GET", "POST"])
def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'learning/index.html')


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = CustomUserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('index')
    return render(request, 'learning/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    error = None
    if request.method == 'POST':
        input_value = request.POST.get('username', '').strip()
        password_value = request.POST.get('password', '')

        auth_credentials = {
            UserModel.USERNAME_FIELD: input_value,
            'password': password_value,
        }
        user = authenticate(request, **auth_credentials)

        if user is not None:
            login(request, user)
            return redirect('index')
        error = 'Invalid username or password.'

    return render(request, 'learning/login.html', {'error': error})


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return redirect('login')


@stage_required('HIRAGANA')
def hiragana_lessons(request):
    return render(request, 'learning/hiragana_lessons.html')


@stage_required('KATAKANA')
def katakana_lessons(request):
    return render(request, 'learning/katakana.html')


@stage_required('KANJI')
def kanji_intro_lessons(request):
    return render(request, 'learning/kanji.html')


@stage_required('GRAMMAR')
def grammar_lessons(request):
    return render(request, 'learning/grammar.html')


@login_required
@require_http_methods(["POST"])
def update_stage(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    new_stage = data.get('new_stage')
    stage_choices = UserModel._meta.get_field('highest_unlocked_stage').choices
    valid_stages = {value for value, _label in stage_choices}

    if new_stage not in valid_stages or new_stage not in STAGE_RANKING:
        return JsonResponse({'error': 'Invalid stage'}, status=400)

    current_rank = STAGE_RANKING.get(request.user.highest_unlocked_stage, 1)
    new_rank = STAGE_RANKING[new_stage]

    # Only advance progress, do not allow downgrading
    if new_rank > current_rank:
        request.user.highest_unlocked_stage = new_stage
        request.user.save(update_fields=['highest_unlocked_stage'])

    return JsonResponse({'status': 'ok', 'current_stage': request.user.highest_unlocked_stage})


@login_required
@require_http_methods(["POST"])
def update_streak(request):
    """Record streak activity, respecting the model's 24-hour cooldown."""
    incremented = request.user.append_to_streak()
    return JsonResponse({
        'status': 'ok',
        'incremented': incremented,
        'streak': request.user.streak,
    })