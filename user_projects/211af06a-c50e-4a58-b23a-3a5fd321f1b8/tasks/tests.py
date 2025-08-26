from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import TaskList, Task
from .forms import TaskForm
import pytest
from django.utils import timezone

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def tasklist(user):
    return TaskList.objects.create(
        title='Test List',
        description='Test Description',
        owner=user
    )

@pytest.fixture
def task(tasklist):
    return Task.objects.create(
        title='Test Task',
        description='Test Task Description',
        due_date=timezone.now(),
        priority=1,
        status='pending',
        task_list=tasklist
    )

@pytest.fixture
def client():
    return Client()

@pytest.mark.django_db
class TestTaskListModel:
    def test_tasklist_creation(self, tasklist):
        assert tasklist.title == 'Test List'
        assert tasklist.description == 'Test Description'
        assert str(tasklist) == 'Test List'

    def test_tasklist_with_tasks(self, tasklist, task):
        assert tasklist.tasks.count() == 1
        assert tasklist.tasks.first().title == 'Test Task'

@pytest.mark.django_db
class TestTaskModel:
    def test_task_creation(self, task):
        assert task.title == 'Test Task'
        assert task.status == 'pending'
        assert str(task) == 'Test Task'

    def test_task_status_choices(self, task):
        valid_statuses = ['pending', 'in_progress', 'completed']
        assert task.status in valid_statuses

@pytest.mark.django_db
class TestTaskListViews:
    def test_tasklist_list_view(self, client, user, tasklist):
        client.force_login(user)
        url = reverse('tasklist-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Test List' in str(response.content)

    def test_tasklist_detail_view(self, client, user, tasklist):
        client.force_login(user)
        url = reverse('tasklist-detail', kwargs={'pk': tasklist.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert tasklist.title in str(response.content)

    def test_task_create_view(self, client, user, tasklist):
        client.force_login(user)
        url = reverse('task-create')
        data = {
            'title': 'New Task',
            'description': 'New Description',
            'due_date': timezone.now(),
            'priority': 2,
            'status': 'pending',
            'task_list': tasklist.id
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Task.objects.filter(title='New Task').exists()

@pytest.mark.django_db
class TestTaskForm:
    def test_valid_task_form(self, tasklist):
        form_data = {
            'title': 'Form Test Task',
            'description': 'Form Test Description',
            'due_date': timezone.now(),
            'priority': 1,
            'status': 'pending',
            'task_list': tasklist.id
        }
        form = TaskForm(data=form_data)
        assert form.is_valid()

    def test_invalid_task_form(self):
        form = TaskForm(data={})
        assert not form.is_valid()
        assert 'title' in form.errors

@pytest.mark.django_db
class TestEdgeCases:
    def test_long_title(self, tasklist):
        long_title = 'x' * 256
        with pytest.raises(Exception):
            Task.objects.create(
                title=long_title,
                task_list=tasklist
            )

    def test_invalid_priority(self, tasklist):
        with pytest.raises(Exception):
            Task.objects.create(
                title='Test Task',
                priority=-1,
                task_list=tasklist
            )

    def test_unauthorized_access(self, client, tasklist):
        url = reverse('tasklist-detail', kwargs={'pk': tasklist.pk})
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_delete_tasklist_cascade(self, tasklist, task):
        tasklist_id = tasklist.id
        task_id = task.id
        tasklist.delete()
        assert not TaskList.objects.filter(id=tasklist_id).exists()
        assert not Task.objects.filter(id=task_id).exists()