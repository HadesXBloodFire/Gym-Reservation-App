# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Gyms(models.Model):
    gym_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80)
    phone_number = models.IntegerField()
    address = models.CharField(max_length=80)
    limit = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gyms'


class Logs(models.Model):
    log_id = models.AutoField(primary_key=True)
    reservation = models.ForeignKey('Reservations', models.DO_NOTHING)
    status = models.IntegerField()
    log_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'logs'


class Reservations(models.Model):
    reservation_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    gym = models.ForeignKey(Gyms, models.DO_NOTHING)
    trainer = models.ForeignKey('Trainers', models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=1)
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'reservations'


class Trainers(models.Model):
    trainer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    hourly_cost = models.IntegerField()
    specialization = models.CharField(max_length=40)
    description = models.CharField(max_length=400)

    class Meta:
        managed = False
        db_table = 'trainers'


class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mail = models.CharField(max_length=100)
    phone_number = models.IntegerField()
    password = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'users'
