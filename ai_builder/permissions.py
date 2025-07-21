from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the project.
        return obj.owner == request.user

class IsProjectOwner(permissions.BasePermission):
    """
    Custom permission for project-related objects
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        # For models that have a project field
        if hasattr(obj, 'project'):
            return obj.project.owner == request.user
        # For project model itself
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False