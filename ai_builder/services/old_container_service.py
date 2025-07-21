import docker
import os
import shutil
from pathlib import Path
from django.conf import settings
import subprocess
import time
import logging
import platform
import json
import uuid
logger = logging.getLogger(__name__)


class ContainerService:
    def __init__(self):
        try:
            # For Windows, try different Docker connection methods
            logger.info(platform.system())
            if platform.system() == "Windows":
                try:
                    # Try named pipe first (Docker Desktop default)
                    self.client = docker.from_env()
                except:
                    # Try TCP connection as fallback
                    self.client = docker.DockerClient(base_url='tcp://localhost:2375')
            else:
                self.client = docker.from_env()
                
            # Test connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
        
        self.projects_dir = Path(settings.USER_PROJECTS_DIR)
        self.projects_dir.mkdir(exist_ok=True)
        
    def create_django_project(self, project_name: str, project_id: str) -> str:
        """Create a new Django project directory"""
        project_path = self.projects_dir / project_id
        
        try:
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Save current directory
            original_dir = os.getcwd()
            
            # Change to project directory
            os.chdir(project_path)
            
            # Create the Django project
            cmd = ['django-admin', 'startproject', project_name.replace(' ', '_').lower(), '.']
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Create requirements.txt
            requirements_content = """Django==5.0.7
djangorestframework==3.15.2
python-dotenv==1.0.1
"""
            with open(project_path / 'requirements.txt', 'w') as f:
                f.write(requirements_content)
            
            # Create .env file
            env_content = f"""DEBUG=True
SECRET_KEY=django-insecure-{project_id}
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
"""
            with open(project_path / '.env', 'w') as f:
                f.write(env_content)
            
            # Restore original directory
            os.chdir(original_dir)
            
            return str(project_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create Django project: {e}")
            raise Exception(f"Failed to create Django project: {e}")
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
        finally:
            # Ensure we restore the original directory
            try:
                os.chdir(original_dir)
            except:
                pass
    
    def start_container(self, project_id: str, port: int = 8001) -> dict:
        """Start a Django development container"""
        if not self.client:
            return {'error': 'Docker client not available. Please start Docker Desktop.'}

        project_path = self.projects_dir / project_id

        if not project_path.exists():
            return {'error': 'Project directory not found'}

        try:
            # Stop any existing container
            self.stop_container(project_id)

            # Sanitize and define image tag
            image_tag = f"django-project-{project_id}".lower().replace(" ", "-")

            # Create Dockerfile
            dockerfile_content = """
    FROM python:3.11-slim

    WORKDIR /app

    RUN apt-get update && apt-get install -y \\
        build-essential \\
        libpq-dev \\
        gcc \\
        python3-dev \\
        curl \\
        && rm -rf /var/lib/apt/lists/*

    RUN pip install --upgrade pip

    COPY requirements.txt ./
    RUN pip install -r requirements.txt

    COPY . .

    EXPOSE 8000

    CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
    """
            dockerfile_path = project_path / 'Dockerfile'
            dockerfile_path.write_text(dockerfile_content)
            requirements_file = project_path / 'requirements.txt'
            if not requirements_file.exists():
                raise FileNotFoundError(f"Missing requirements.txt at {requirements_file}")
            # Build Docker image
            logger.info(f"Building Docker image for project {project_id}...")
            logs = self.client.api.build(
                path=str(project_path),
                tag=image_tag,
                rm=True,
                forcerm=True,
                # buildargs={"CACHE_BUST": str(uuid.uuid4())},
                decode=True
            )

            # Check build output for errors
            for chunk in logs:
                if 'stream' in chunk:
                    print(chunk['stream'], end='')
                elif 'error' in chunk:
                    logger.error(f"Build error: {chunk['error']}")
                    return {'error': chunk['error'], 'status': 'failed'}

            # Verify the image was created
            images = self.client.images.list(name=image_tag)
            if not any(image_tag in tag for image in images for tag in image.tags):
                return {'error': f"Docker image '{image_tag}' not found after build.", 'status': 'failed'}

            # Run the container
            logger.info(f"Starting container for project {project_id}")
            container = self.client.containers.run(
                image=image_tag,
                ports={'8000/tcp': port},
                volumes={str(project_path): {'bind': '/app', 'mode': 'rw'}},
                name=f"django-container-{project_id}",
                detach=True,
                # remove=True,
                environment={
                    'DJANGO_SETTINGS_MODULE': 'settings',
                    'PYTHONUNBUFFERED': '1'
                }
            )

            # Allow time for container to boot
            time.sleep(3)

            # Print logs (optional but helpful for debugging)
            for line in container.logs(stream=True):
                print(line.decode('utf-8').strip())

            return {
                'container_id': container.id,
                'port': port,
                'status': 'running'
            }

        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def stop_container(self, project_id: str):
        """Stop and remove project container"""
        if not self.client:
            return
            
        container_name = f"django-container-{project_id}"
        container_name = f"django-container-{project_id}"

        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=10)
            container.remove(force=True)  # ✅ Remove after stopping
            logger.info(f"Stopped and removed container {container_name}")
        except docker.errors.NotFound:
            logger.info(f"Container {container_name} not found, skipping stop/remove.")
        except Exception as e:
            logger.error(f"Error stopping/removing container: {e}")
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=10)
            logger.info(f"Stopped container {container_name}")
        except docker.errors.NotFound:
            pass  # Container doesn't exist
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
    
    def execute_command(self, project_id: str, command: str) -> dict:
        """Execute a command in the project container"""
        if not self.client:
            return {'error': 'Docker client not available', 'success': False}
            
        container_name = f"django-container-{project_id}"
        print(container_name)
        try:
            container = self.client.containers.get(container_name)
            print(container)
            result = container.exec_run(command, workdir='/app')
            
            return {
                'exit_code': result.exit_code,
                'output': result.output.decode('utf-8'),
                'success': result.exit_code == 0
            }
        except docker.errors.NotFound:
            return {
                'error': 'Container not found. Please start the server first.',
                'success': False
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    def get_file_content(self, project_id: str, file_path: str) -> str:
        """Get content of a file from the project"""
        project_path = self.projects_dir / project_id / file_path
        
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return f"Error reading file: {str(e)}"
    
    def save_file_content(self, project_id: str, file_path: str, content: str) -> bool:
        """Save content to a file in the project"""
        project_path = self.projects_dir / project_id / file_path
        
        try:
            # Create directory if it doesn't exist
            project_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(project_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False
    
    def list_project_files(self, project_id: str) -> list:
        """List all files in a project"""
        project_path = self.projects_dir / project_id
        files = []
        
        if not project_path.exists():
            return files
        
        try:
            for file_path in project_path.rglob('*'):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    relative_path = file_path.relative_to(project_path)
                    files.append({
                        'path': str(relative_path),
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    })
        except Exception as e:
            logger.error(f"Error listing files: {e}")
        
        return files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            '__pycache__',
            '.git',
            '.env',
            'Dockerfile',
            '.pyc',
            'db.sqlite3',
            'staticfiles',
            'media'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in ignore_patterns)