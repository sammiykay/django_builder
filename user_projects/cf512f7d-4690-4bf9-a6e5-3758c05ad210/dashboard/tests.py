from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Dashboard, Widget
import pytest
from django.core.exceptions import ValidationError

@pytest.mark.django_db
class TestDashboard:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username='testuser', password='12345')

    @pytest.fixture
    def dashboard(self, user):
        return Dashboard.objects.create(
            title='Test Dashboard',
            owner=user,
            description='Test Description'
        )

    @pytest.fixture
    def widget(self, dashboard):
        return Widget.objects.create(
            dashboard=dashboard,
            title='Test Widget',
            widget_type='chart',
            position=1
        )

    def test_dashboard_creation(self, dashboard):
        assert dashboard.title == 'Test Dashboard'
        assert dashboard.description == 'Test Description'

    def test_dashboard_str(self, dashboard):
        assert str(dashboard) == 'Test Dashboard'

    def test_widget_creation(self, widget):
        assert widget.title == 'Test Widget'
        assert widget.widget_type == 'chart'
        assert widget.position == 1

    def test_widget_str(self, widget):
        assert str(widget) == 'Test Widget'

    def test_dashboard_delete_cascades_to_widgets(self, dashboard, widget):
        dashboard_id = dashboard.id
        widget_id = widget.id
        dashboard.delete()
        
        with pytest.raises(Dashboard.DoesNotExist):
            Dashboard.objects.get(id=dashboard_id)
        with pytest.raises(Widget.DoesNotExist):
            Widget.objects.get(id=widget_id)

    def test_invalid_widget_type(self, dashboard):
        with pytest.raises(ValidationError):
            Widget.objects.create(
                dashboard=dashboard,
                title='Invalid Widget',
                widget_type='invalid_type',
                position=1
            )

class TestDashboardView:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def user(self):
        user = User.objects.create_user(username='testuser', password='12345')
        return user

    @pytest.fixture
    def dashboard(self, user):
        return Dashboard.objects.create(
            title='Test Dashboard',
            owner=user,
            description='Test Description'
        )

    def test_dashboard_view_authenticated(self, client, user, dashboard):
        client.login(username='testuser', password='12345')
        response = client.get(reverse('dashboard-detail', kwargs={'pk': dashboard.pk}))
        assert response.status_code == 200
        assert 'Test Dashboard' in str(response.content)

    def test_dashboard_view_unauthenticated(self, client, dashboard):
        response = client.get(reverse('dashboard-detail', kwargs={'pk': dashboard.pk}))
        assert response.status_code == 302  # Redirect to login

    def test_dashboard_create_view(self, client, user):
        client.login(username='testuser', password='12345')
        response = client.post(reverse('dashboard-create'), {
            'title': 'New Dashboard',
            'description': 'New Description'
        })
        assert response.status_code == 302  # Redirect after creation
        assert Dashboard.objects.filter(title='New Dashboard').exists()

    def test_dashboard_update_view(self, client, user, dashboard):
        client.login(username='testuser', password='12345')
        response = client.post(
            reverse('dashboard-update', kwargs={'pk': dashboard.pk}),
            {'title': 'Updated Dashboard', 'description': 'Updated Description'}
        )
        dashboard.refresh_from_db()
        assert dashboard.title == 'Updated Dashboard'

    def test_dashboard_delete_view(self, client, user, dashboard):
        client.login(username='testuser', password='12345')
        response = client.post(reverse('dashboard-delete', kwargs={'pk': dashboard.pk}))
        assert response.status_code == 302
        assert not Dashboard.objects.filter(pk=dashboard.pk).exists()

@pytest.mark.django_db
class TestWidgetAPI:
    @pytest.fixture
    def api_client(self):
        return Client()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username='testuser', password='12345')

    @pytest.fixture
    def dashboard(self, user):
        return Dashboard.objects.create(
            title='Test Dashboard',
            owner=user,
            description='Test Description'
        )

    def test_widget_list_api(self, api_client, user, dashboard):
        api_client.login(username='testuser', password='12345')
        response = api_client.get(reverse('widget-list', kwargs={'dashboard_id': dashboard.pk}))
        assert response.status_code == 200

    def test_widget_create_api(self, api_client, user, dashboard):
        api_client.login(username='testuser', password='12345')
        response = api_client.post(
            reverse('widget-create', kwargs={'dashboard_id': dashboard.pk}),
            {
                'title': 'API Widget',
                'widget_type': 'chart',
                'position': 1
            }
        )
        assert response.status_code == 201
        assert Widget.objects.filter(title='API Widget').exists()

    def test_widget_update_api(self, api_client, user, dashboard, widget):
        api_client.login(username='testuser', password='12345')
        response = api_client.put(
            reverse('widget-update', kwargs={'pk': widget.pk}),
            {
                'title': 'Updated Widget',
                'widget_type': 'chart',
                'position': 2
            },
            content_type='application/json'
        )
        widget.refresh_from_db()
        assert widget.title == 'Updated Widget'

    def test_widget_delete_api(self, api_client, user, dashboard, widget):
        api_client.login(username='testuser', password='12345')
        response = api_client.delete(reverse('widget-delete', kwargs={'pk': widget.pk}))
        assert response.status_code == 204
        assert not Widget.objects.filter(pk=widget.pk).exists()