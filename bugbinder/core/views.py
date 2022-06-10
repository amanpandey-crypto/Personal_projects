from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Project, Task
from django.db.models import Q
from _auth.models import User
from _profile.models import Profile
from django.http import JsonResponse


@login_required
def dashboard(request):
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        project = Project(owner=request.user)
        project.title = title
        project.description = description
        project.save()
        project.dev.add(request.user)
        return redirect("project", id=project.id)
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(dev__in=[request.user])
    ).distinct()

    context = {
        'projects': projects, 'task_count': count_task(request)
    }
    return render(request, 'core/dashboard.html', context)


def projectView(request, id):
    try:
        project = Project.objects.get(id=id)
    except:
        project = None

    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        project.title = title
        project.description = description
        project.save()
    return render(request, 'core/project.html', {"project": project, 'task_count': count_task(request)})


@login_required
@csrf_exempt
def assign(request):
    if request.method == "POST":
        id = request.POST.get('id')
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            task = Task.objects.get(id=id)
            project = Project.objects.get(task__in=[task])
            if request.user == project.owner or request.user == user:
                task.dev = user
                task.assigned = True
                task.save()
                project.save()
                cout_update(project, assigend=True)
                return JsonResponse({'status': 200})
            raise ValueError

        except:
            return JsonResponse({'status': 403})


@login_required
@csrf_exempt
def delete_task(request):
    if request.method == "POST":
        try:
            id = request.POST.get('id')
            task = Task.objects.get(id=id)
            project = task.project
            if request.user == project.owner:
                task.delete()
                project.bugs = project.bugs - 1
                project.save()
                return JsonResponse({'status': 200})
            return JsonResponse({'status': 403})
        except:
            return JsonResponse({'status': 403})


@login_required
@csrf_exempt
def delete_project(request):
    if request.method == "POST":
        try:
            id = request.POST.get('id')
            project = Project.objects.get(id=id)
            if request.user == project.owner:
                project.delete()
                return JsonResponse({'status': 200})
            return JsonResponse({'status': 400})
        except:
            return JsonResponse({'status': 400})


@login_required
@csrf_exempt
def edit_project(request):
    if request.method == "POST":
        try:
            id = request.POST.get('id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            project = Project.objects.get(id=id)
            if request.user == project.owner:
                project.title = title
                project.description = description
                project.save()
                return JsonResponse({'status': 200})
            return JsonResponse({'status': 403})
        except:
            return JsonResponse({'status': 400})


@login_required
@csrf_exempt
def search_dev(request):
    if request.method == "POST":
        try:
            # if True:
            email = request.POST.get('email')
            user = User.objects.get(
                Q(email=email) | Q(username=email)
            )
            profile = Profile.objects.get(user=user)
            return JsonResponse({'name': profile.name, 'github': profile.github, 'username': user.username, 'status': 200})
        except:
            return JsonResponse({'status': 400})


@login_required
@csrf_exempt
def save_dev(request):
    if request.method == "POST":
        # try:
        if True:
            project_id = request.POST.get('project_id')
            dev_username = request.POST.get('dev_username')

            user = User.objects.get(username=dev_username)
            project = Project.objects.get(id=project_id)
            if project.owner == request.user:
                if user in project.dev.all():
                    return JsonResponse({'status': 403})
                project.dev.add(user)
                return JsonResponse({'user_id': user.id, 'status': 200})
            raise ValueError
        # except:
        #     return JsonResponse({'status': 400})


@login_required
@csrf_exempt
def remove_dev(request):
    if request.method == "POST":
        project_id = request.POST.get('project_id')
        dev_id = request.POST.get('dev_id')

        try:
            user = User.objects.get(id=dev_id)
            project = Project.objects.get(id=project_id)
            if project.owner == request.user:
                project.dev.remove(user)
                return JsonResponse({'status': 200})
            raise ValueError
        except:
            return JsonResponse({'status': 400})


@login_required
@csrf_exempt
def issueView(request):
    if request.method == "POST":
        project_id = request.POST.get("project_id")
        title = request.POST.get("title")
        reproduce = request.POST.get("reproduce")
        environment = request.POST.get("environment")
        comment = request.POST.get("comment")

        project = Project.objects.get(id=project_id)
        task = Task()
        task.title = title
        task.reproduce = reproduce
        task.environment = environment
        task.comment = comment
        task.project = project
        task.save()
        project.task.add(task)
        cout_update(project, bug=True)
        return JsonResponse({"status": 200})

    projects = Project.objects.filter(
        Q(owner=request.user) | Q(dev__in=[request.user])
    ).distinct()
    return render(request, 'core/bug-issue.html', {'task_count': count_task(request), 'projects': projects})


@csrf_exempt
def publicissueView(request, id):
    project = get_object_or_404(Project, id=id)
    if request.method == "POST":
        try:
            email = request.POST.get("email")
            title = request.POST.get("title")
            reproduce = request.POST.get("reproduce")
            environment = request.POST.get("environment")
            comment = request.POST.get("comment")

            task = Task()
            task.title = title
            task.reproduce = reproduce
            task.environment = environment
            task.comment = comment
            task.project = project
            task.email = email
            task.save()
            project.task.add(task)
            cout_update(project, bug=True)
            return JsonResponse({"status": 200})
        except:
            return JsonResponse({"status": 400})

    return render(request, 'core/bug-issue-public.html', {"project": project, 'task_count': count_task(request)})


@csrf_exempt
@login_required
def taskView(request):
    tasks = Task.objects.filter(dev=request.user)
    profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        task_id = request.POST.get('task_id')
        solution = request.POST.get('solution')
        task = Task.objects.get(id=task_id)
        task.solution = solution
        task.assigned = False
        task.done = True
        task.save()
        profile.fixed = profile.fixed + 1
        profile.save()
        cout_update(task.project, fixed=True)
        return JsonResponse({"status": 200})

    return render(request, 'core/task.html', {"tasks": tasks, 'task_count': count_task(request), "fixed_task": profile.fixed})


def count_task(request):
    if request.user.is_authenticated:
        tasks = Task.objects.filter(Q(dev=request.user), Q(done=False))
        return tasks.count()
    return None


def cout_update(project, bug=False, assigend=False, fixed=False):
    if bug:
        project.bugs = project.bugs+1
    elif assigend:
        project.bugs = project.bugs - 1
        project.assigned = project.assigned + 1
    elif fixed:
        project.assigned = project.assigned - 1
        project.fixed = project.fixed + 1
    project.save()
