from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Team, TeamMember
from tasks.forms import TeamCreationForm

User = get_user_model()

class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    form_class = TeamCreationForm
    template_name = 'teams/create.html'
    success_url = reverse_lazy('team_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_members'] = User.objects.exclude(
            id=self.request.user.id
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        team = self.object
        TeamMember.objects.create(
            team=team,
            user=self.request.user,
            role='admin'
        )
        messages.success(self.request, 'Team created successfully!')
        return response

@login_required
def dashboard(request):
    user_teams = Team.objects.filter(members=request.user)
    context = {
        'teams': user_teams,
    }
    return render(request, 'accounts/dashboard.html', context)

class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'teams/list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        return Team.objects.filter(members=self.request.user)

class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'teams/detail.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_members'] = self.object.members.all()
        context['is_admin'] = TeamMember.objects.filter(
            team=self.object,
            user=self.request.user,
            role='admin'
        ).exists()
        return context

@login_required
def add_team_member(request, team_id):
    if request.method == 'POST' and request.is_ajax():
        team = get_object_or_404(Team, id=team_id)
        user_id = request.POST.get('user_id')
        
        if not TeamMember.objects.filter(team=team, user=request.user, role='admin').exists():
            return JsonResponse({'error': 'Permission denied'}, status=403)
            
        try:
            user = User.objects.get(id=user_id)
            TeamMember.objects.create(team=team, user=user, role='member')
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def remove_team_member(request, team_id, member_id):
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id)
        if not TeamMember.objects.filter(team=team, user=request.user, role='admin').exists():
            messages.error(request, 'Permission denied')
            return redirect('team_detail', pk=team_id)
            
        try:
            member = TeamMember.objects.get(team=team, user_id=member_id)
            member.delete()
            messages.success(request, 'Team member removed successfully')
        except TeamMember.DoesNotExist:
            messages.error(request, 'Member not found')
            
    return redirect('team_detail', pk=team_id)