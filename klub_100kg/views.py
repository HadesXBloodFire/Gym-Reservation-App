from django.shortcuts import render, redirect
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .forms import *
import bcrypt
import json
import requests
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

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


@anonymous_required
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'mail': form.cleaned_data['mail'],
                'phone_number': form.cleaned_data['phone_number'],
                'password': form.cleaned_data['password'],
            }
            api_url = request.build_absolute_uri(reverse('api_create_user'))
            response = requests.post(api_url, json=data)
            if response.status_code == 201:
                return redirect('login')
            else:
                print(f"API request failed with status code {response.status_code}")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    response = redirect('login')
    response.delete_cookie('user_id')
    return response


@anonymous_required
def hero_page(request):
    if request.user.is_authenticated:
        return redirect("main_page")
    return render(request, "hero.html")



def main_page(request):
    user_id = request.COOKIES.get('user_id')
    if user_id is None:
        return redirect('login')
    return render(request, "main.html")

def new_reservation_view(request):
    user_id = request.COOKIES.get('user_id')
    if user_id is None:
        return redirect('login')
    else:
        if request.method == 'POST':
            form = ReservationForm(request.POST)
            if form.is_valid():
                data = {
                    'user_ID': form.cleaned_data['user_ID'],
                    'gym_ID': form.cleaned_data['gym_ID'],
                    'trainer_ID': form.cleaned_data['trainer_ID'],
                    'date': form.cleaned_data['date'].strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                }
                api_url = request.build_absolute_uri(reverse('api_add_reservation'))
                response = requests.post(api_url, json=data)
                if response.status_code != 201:
                    print(f"API request failed with status code {response.status_code}")
        else:
            form = ReservationForm(initial={'user_ID': user_id})
        return render(request, "new_reservation.html", {'form': form})


def modify_reservation_view(request):
    user_id = request.COOKIES.get('user_id')
    if user_id is None:
        return redirect('login')

    # Fetch gym names using SQL query
    reservations_with_gym_names = {}
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT r.reservation_ID, g.name AS gym_name
            FROM reservations r
            INNER JOIN gyms g ON r.gym_ID = g.gym_ID
            WHERE r.user_ID = %s AND r.status = 'A'
        """, [user_id])
        for row in cursor.fetchall():
            reservation_id, gym_name = row
            reservations_with_gym_names[reservation_id] = gym_name

    # Fetch active reservations for the logged-in user using API
    api_url = request.build_absolute_uri(reverse('get_reservations', args=[user_id]))
    response = requests.get(api_url)
    reservations = []
    if response.status_code == 200:
        for res in response.json():
            if res['status'] == 'A':
                # Update each reservation with the gym name
                res['gym_name'] = reservations_with_gym_names.get(res['reservation_id'], 'Unknown Gym')
                reservations.append(res)
    else:
        print(f"API request failed with status code {response.status_code}")

    form = ModifyReservationForm()

    form.fields['trainer_ID'].choices = get_trainers()

    return render(request, "modify_reservation.html", {'active_reservations': reservations, 'form': form})
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


@csrf_exempt
def update_trainer_reservation_view(request, reservation_id):
    if request.method == 'POST':
        trainer_id = request.POST.get('trainer_ID')
        if trainer_id == 'None':  # Check if the trainer is given as none
            trainer_id = 0  # Convert it to 0
        api_url = request.build_absolute_uri(reverse('api_update_trainer_reservation', args=[reservation_id]))
        data = {'trainer_ID': trainer_id}
        response = requests.put(api_url, json=data)
        if response.status_code == 200:
            return redirect('modify_reservation')
        else:
            print(f"API request failed with status code {response.status_code}")
    return redirect('modify_reservation')


from django.http import JsonResponse

@csrf_exempt
def cancel_reservation_view(request, reservation_id):
    if request.method == 'POST':
        api_url = request.build_absolute_uri(reverse('api_cancel_reservation', args=[reservation_id]))
        response = requests.put(api_url)
        if response.status_code == 200:
            return redirect('modify_reservation')
        else:
            print(f"API request failed with status code {response.status_code}")
            return JsonResponse(response.json(), status=response.status_code)
    return redirect('modify_reservation')
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


class UpdateTrainerReservationAPIView(APIView):
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

        update_data = request.data.copy()
        if update_data.get('trainer_ID') == 0:
            update_data['trainer_ID'] = None

        serializer = self.serializer_class(data={**current_data, 'trainer_ID': update_data['trainer_ID'], **update_data}, partial=True)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                try:
                    cursor.execute("CALL modify_reservation(%s, %s, %s)", [
                        reservation_id,
                        data['trainer_ID'],
                        current_data['status']
                    ])
                    return Response({'message': 'Reservation modified successfully'}, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelReservationAPIView(APIView):
    serializer_class = UpdateReservationSerializer

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('reservation_id', openapi.IN_PATH, description="Reservation ID", type=openapi.TYPE_INTEGER)
    ])
    def put(self, request, reservation_id, *args, **kwargs):
        with connection.cursor() as cursor:
            try:
                # Call the stored procedure
                cursor.execute("CALL cancel_reservation(%s)", [reservation_id])
                return Response({'message': 'Reservation cancelled successfully'}, status=status.HTTP_200_OK)
            except Exception as e:
                # If an error occurs, return a 400 error with detailed message
                return Response({'error': 'An error occurred: {}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)


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


class GetGymAPIView(APIView):
    def get(self, request, gym_id):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM gyms WHERE gym_ID = %s", [gym_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                gym_data = dict(zip(columns, row))
                return Response(gym_data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)


class AddGymAPIView(APIView):
    serializer_class = GymSerializer

    @swagger_auto_schema(request_body=GymSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                try:
                    cursor.execute("CALL add_gym(%s, %s, %s, %s)", [
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


class AddTrainerAPIView(APIView):
    serializer_class = TrainerSerializer

    @swagger_auto_schema(request_body=TrainerSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            with connection.cursor() as cursor:
                try:
                    cursor.execute("CALL add_trainer(%s, %s, %s, %s, %s)", [
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


class GetReservationsAPIView(APIView):
    def get(self, request, user_id, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM reservations WHERE user_ID = %s", [user_id])
            rows = cursor.fetchall()
            if rows:
                columns = [col[0] for col in cursor.description]
                reservations_data = [dict(zip(columns, row)) for row in rows]
                return Response(reservations_data)
            else:
                return Response({'error': 'No reservations found for this user'}, status=status.HTTP_404_NOT_FOUND)


class GetGymsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM gyms")
            rows = cursor.fetchall()
            if rows:
                columns = [col[0] for col in cursor.description]
                gyms_data = [dict(zip(columns, row)) for row in rows]
                return Response(gyms_data)
            else:
                return Response({'error': 'No gyms found'}, status=status.HTTP_404_NOT_FOUND)


