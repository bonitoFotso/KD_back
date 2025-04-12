from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

class LoginSerializer(serializers.Serializer):
   email = serializers.EmailField()
   password = serializers.CharField(write_only=True)

   def validate(self, data):
       email = data.get('email')
       password = data.get('password')
       
       user = authenticate(username=email, password=password)
       
       if not user:
           raise serializers.ValidationError('Invalid credentials')

       if not user.is_active:
           raise serializers.ValidationError('User account is disabled')
           
       refresh = RefreshToken.for_user(user)

       return {
           'success': True,
           'user': {
               '_id': user.id,
               'email': user.email,
               'username': user.username,
               'departement': user.departement
           },
           'token': str(refresh.access_token)
       }