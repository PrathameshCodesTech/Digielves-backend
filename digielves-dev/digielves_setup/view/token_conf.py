from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from rest_framework.response import Response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            refresh_token = serializer.validated_data.get('refresh')
            token = RefreshToken(refresh_token)

            # Set the new expiration time for the refresh token
            new_refresh_token = token.access_token
            new_refresh_token.set_exp(from_time=token.current_time + timedelta(days=7))

            # Create the response with the new refresh token and access token
            response_data = {
                'refresh': str(new_refresh_token),
                'access': str(token.access_token),
            }
            return Response(response_data)

        return Response(serializer.errors, status=400)
