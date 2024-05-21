from django.shortcuts import render, redirect
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .forms import *
import bcrypt
import requests
from django.urls import reverse

def anonymous_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        user_id = request.COOKIES.get('user_id')
        if user_id is not None:
            return redirect('main_page')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func
@anonymous_required
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            mail = form.cleaned_data['mail']
            password = form.cleaned_data['password'].encode('utf-8')  # Convert the password to bytes
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE mail = %s", [mail])
                user = cursor.fetchone()
                if user is not None:
                    hashed_password = user[5].encode('utf-8')  # Convert the hashed password to bytes
                    if bcrypt.checkpw(password, hashed_password):  # Check if the entered password matches the hashed password
                        response = redirect('main_page')
                        response.set_cookie('user_id', user[0])  # Set the user_id cookie
                        return response
                    else:
                        form.add_error(None, 'Invalid email or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# @anonymous_required
# def register_view(request):
#     if request.method == 'POST':
#         form = RegisterForm(request.POST)
#         if form.is_valid():
#             first_name = form.cleaned_data['first_name']
#             last_name = form.cleaned_data['last_name']
#             mail = form.cleaned_data['mail']
#             phone_number = form.cleaned_data['phone_number']
#             password = form.cleaned_data['password']
#             with connection.cursor() as cursor:
#                 cursor.execute("CALL add_user(%s, %s, %s, %s, %s)", [first_name, last_name, mail, phone_number, password])
#             return redirect('login')
#     else:
#         form = RegisterForm()
#     return render(request, 'register.html', {'form': form})

@anonymous_required
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Prepare data for the API request
            data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'mail': form.cleaned_data['mail'],
                'phone_number': form.cleaned_data['phone_number'],
                'password': form.cleaned_data['password'],
            }
            # Get the full URL for the API endpoint
            api_url = request.build_absolute_uri(reverse('api_create_user'))
            # Make the API request
            response = requests.post(api_url, json=data)
            # Check the response status code
            if response.status_code == 201:
                return redirect('login')
            else:
                # Handle error (you can customize this part to suit your needs)
                print(f"API request failed with status code {response.status_code}")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    response = redirect('login')
    response.delete_cookie('user_id')  # Delete the user_id cookie
    return response


@anonymous_required
def hero_page(request):
    if request.user.is_authenticated:
        return redirect("main_page")
    return render(request, "hero.html")



def main_page(request):
    user_id = request.COOKIES.get('user_id')
    if user_id is None:
        # User is not logged in, redirect to login page
        return redirect('login')
    else:
        # User is logged in, render the main page
        if request.method == 'POST':
            form = ReservationForm(request.POST)
            if form.is_valid():
                # Prepare data for the API request
                data = {
                    'user_ID': form.cleaned_data['user_ID'],
                    'gym_ID': form.cleaned_data['gym_ID'],
                    'trainer_ID': form.cleaned_data['trainer_ID'],
                    'date': form.cleaned_data['date'].strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                }
                # Get the full URL for the API endpoint
                api_url = request.build_absolute_uri(reverse('api_add_reservation'))
                # Make the API request
                response = requests.post(api_url, json=data)
                # Check the response status code
                if response.status_code != 201:
                    # Handle error (you can customize this part to suit your needs)
                    print(f"API request failed with status code {response.status_code}")
        else:
            form = ReservationForm(initial={'user_ID': user_id})
        return render(request, "main.html", {'form': form})


class CreateUserAPIView(APIView):
    serializer_class = UserSerializer

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                try:
                    cursor.execute("CALL add_user(%s, %s, %s, %s, %s)", [
                        data['first_name'],
                        data['last_name'],
                        data['mail'],
                        data['phone_number'],
                        data['password']
                    ])
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetUserAPIView(APIView):
    def get(self, request, user_id):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", [user_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                user_data = dict(zip(columns, row))
                serializer = UserSerializer(user_data)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)



class AddTrainerAPIView(APIView):
    serializer_class = TrainerSerializer

    @swagger_auto_schema(request_body=TrainerSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                try:
                    cursor.callproc("CALL add_trainer(%s, %s, %s, %s, %s)", [
                        data['first_name'],
                        data['last_name'],
                        data['hourly_cost'],
                        data['specialization'],
                        data['description']
                    ])
                    return Response({'message': 'Trainer added successfully'}, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddGymAPIView(APIView):
    serializer_class = GymSerializer

    @swagger_auto_schema(request_body=GymSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                try:
                    cursor.callproc("CALL add_gym(%s, %s, %s, %s)", [
                        data['name'],
                        data['phone_number'],
                        data['address'],
                        data['limit']
                    ])
                    return Response({'message': 'Gym added successfully'}, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddReservationAPIView(APIView):
    serializer_class = ReservationSerializer

    @swagger_auto_schema(request_body=ReservationSerializer)
    def post(self, request, *args, **kwargs):
        request_data = request.data.copy()

        if request_data.get('trainer_ID') == 0:
            request_data['trainer_ID'] = None

        serializer = self.serializer_class(data=request_data)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                try:
                    date_without_tz = data['date'].strftime('%Y-%m-%d %H:%M:%S')

                    cursor.execute("CALL add_reservation(%s, %s, %s, %s)", [
                        data['user_ID'],
                        data['gym_ID'],
                        date_without_tz,
                        data['trainer_ID'],
                    ])

                    return Response({'message': 'Reservation added successfully'}, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetReservationAPIView(APIView):
    def get(self, request, reservation_id, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM reservations WHERE reservation_id = %s", [reservation_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                reservation_data = dict(zip(columns, row))
                return Response(reservation_data)
            else:
                return Response({'error': 'Reservation not found'}, status=status.HTTP_404_NOT_FOUND)


class ModifyReservationAPIView(APIView):
    serializer_class = UpdateReservationSerializer

    @swagger_auto_schema(request_body=UpdateReservationSerializer)
    def put(self, request, reservation_id, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM reservations WHERE reservation_id = %s", [reservation_id])
            row = cursor.fetchone()
            if not row:
                return Response({'error': 'Reservation not found'}, status=status.HTTP_404_NOT_FOUND)
            columns = [col[0] for col in cursor.description]
            current_data = dict(zip(columns, row))

        update_data = request.data
        trainer_id_to_update = update_data.get('trainer_ID', current_data.get('trainer_id'))

        serializer = self.serializer_class(data={**current_data, 'trainer_ID': trainer_id_to_update, **update_data}, partial=True)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                try:
                    cursor.execute("CALL modify_reservation(%s, %s, %s)", [
                        reservation_id,
                        trainer_id_to_update,
                        data.get('status', current_data['status'])
                    ])
                    return Response({'message': 'Reservation modified successfully'}, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckGymAvailabilityAPIView(APIView):
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('gym_ID', openapi.IN_QUERY, description="Gym ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('date', openapi.IN_QUERY, description="Date and Time", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
    ])
    def get(self, request, *args, **kwargs):
        gym_ID = request.query_params.get('gym_ID')
        date = request.query_params.get('date')
        if gym_ID and date:
            with connection.cursor() as cursor:
                cursor.callproc("check_gym_availability", [gym_ID, date])
                result = cursor.fetchone()
                return Response({'available': result[0]})
        return Response({'error': 'Missing gym_ID or date parameter'}, status=status.HTTP_400_BAD_REQUEST)
class CheckTrainerAvailabilityAPIView(APIView):
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('trainer_ID', openapi.IN_QUERY, description="Trainer ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('date', openapi.IN_QUERY, description="Date and Time", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
    ])
    def get(self, request, *args, **kwargs):
        trainer_ID = request.query_params.get('trainer_ID')
        date = request.query_params.get('date')
        if trainer_ID and date:
            with connection.cursor() as cursor:
                cursor.callproc("check_trainer_availability", [trainer_ID, date])
                result = cursor.fetchone()
                return Response({'available': result[0]})
        return Response({'error': 'Missing trainer_ID or date parameter'}, status=status.HTTP_400_BAD_REQUEST)
