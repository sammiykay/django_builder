from django.test import TestCase, Client
from django.urls import reverse
from .models import Project
import pytest
from django.core.exceptions import ValidationError

@pytest.mark.django_db
class TestProject:
    def test_project_creation(self):
        project = Project.objects.create(
            title="Test Project",
            description="Test Description",
            technology="Python, Django"
        )
        assert project.title == "Test Project"
        assert project.description == "Test Description"
        assert project.technology == "Python, Django"

    def test_project_str_method(self):
        project = Project.objects.create(
            title="Test Project",
            description="Test Description"
        )
        assert str(project) == "Test Project"

    def test_project_title_max_length(self):
        with pytest.raises(ValidationError):
            project = Project.objects.create(
                title="A" * 201,  # Assuming max_length is 200
                description="Test Description"
            )
            project.full_clean()

    def test_project_blank_title(self):
        with pytest.raises(ValidationError):
            project = Project.objects.create(
                title="",
                description="Test Description"
            )
            project.full_clean()

    def test_project_optional_fields(self):
        project = Project.objects.create(
            title="Test Project",
            description="Test Description"
        )
        assert project.technology == ""  # Assuming technology is optional

    def test_project_update(self):
        project = Project.objects.create(
            title="Test Project",
            description="Test Description"
        )
        project.title = "Updated Project"
        project.save()
        updated_project = Project.objects.get(id=project.id)
        assert updated_project.title == "Updated Project"

    def test_project_deletion(self):
        project = Project.objects.create(
            title="Test Project",
            description="Test Description"
        )
        project_id = project.id
        project.delete()
        with pytest.raises(Project.DoesNotExist):
            Project.objects.get(id=project_id)

    def test_multiple_projects(self):
        Project.objects.create(
            title="Project 1",
            description="Description 1"
        )
        Project.objects.create(
            title="Project 2",
            description="Description 2"
        )
        assert Project.objects.count() == 2

    def test_project_unique_titles(self):
        Project.objects.create(
            title="Unique Project",
            description="Description"
        )
        with pytest.raises(ValidationError):
            project = Project.objects.create(
                title="Unique Project",
                description="Another Description"
            )
            project.full_clean()

    def test_project_long_description(self):
        long_description = "A" * 1000
        project = Project.objects.create(
            title="Test Project",
            description=long_description
        )
        assert project.description == long_description

    @pytest.mark.parametrize(
        "title,description,technology,valid",
        [
            ("Valid Title", "Valid Description", "Python", True),
            ("", "Description", "Python", False),
            ("Title", "", "Python", False),
            ("A" * 201, "Description", "Python", False),
        ],
    )
    def test_project_validation(self, title, description, technology, valid):
        project = Project(
            title=title,
            description=description,
            technology=technology
        )
        if valid:
            project.full_clean()
        else:
            with pytest.raises(ValidationError):
                project.full_clean()