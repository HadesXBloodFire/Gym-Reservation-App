from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    mail = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)


class GymSerializer(serializers.Serializer):
    gym_ID = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=80)
    phone_number = serializers.IntegerField()
    address = serializers.CharField(max_length=80)
    limit = serializers.IntegerField(required=True)


class LogSerializer(serializers.Serializer):
    log_ID = serializers.IntegerField(read_only=True)
    reservation_ID = serializers.IntegerField()
    status = serializers.IntegerField()
    log_date = serializers.DateField()


class ReservationSerializer(serializers.Serializer):
    reservation_ID = serializers.IntegerField(read_only=True)
    user_ID = serializers.IntegerField()
    gym_ID = serializers.IntegerField()
    trainer_ID = serializers.IntegerField(allow_null=True, required=False, default=None)
    status = serializers.CharField(max_length=1, default='A')
    date = serializers.DateTimeField()


class UpdateReservationSerializer(serializers.Serializer):
    reservation_ID = serializers.IntegerField(read_only=True)
    user_ID = serializers.IntegerField(read_only=True)
    gym_ID = serializers.IntegerField(read_only=True)
    trainer_ID = serializers.IntegerField(allow_null=True, required=False, default=None)
    status = serializers.CharField(max_length=1, default='A')
    date = serializers.DateTimeField(read_only=True)


class TrainerSerializer(serializers.Serializer):
    trainer_ID = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    hourly_cost = serializers.IntegerField()
    specialization = serializers.CharField(max_length=40)
    description = serializers.CharField(max_length=400)