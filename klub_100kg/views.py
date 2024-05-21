from django.db import connection
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
import datetime


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
