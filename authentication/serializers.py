from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm')
    
    def validate_username(self, value):
        import re
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores")
        return value
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if not any(c.islower() for c in value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Password must contain at least one number")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords don't match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        try:
            # Create user profile and default billing subscription
            from ai_builder.models import UserProfile
            from ai_builder.billing_services import BillingService
            
            # Create user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Create default billing subscription
            try:
                billing_service = BillingService()
                subscription = billing_service.get_or_create_default_subscription(user)
                if not subscription:
                    # No default plan exists, log this but don't fail
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"No default billing plan found for user {user.username}")
            except Exception as billing_error:
                # Log billing error but don't fail registration
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to create default subscription for user {user.username}: {str(billing_error)}")
            
        except Exception as e:
            # If profile creation fails, still return the user but log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create user profile for user {user.username}: {str(e)}")
        
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')