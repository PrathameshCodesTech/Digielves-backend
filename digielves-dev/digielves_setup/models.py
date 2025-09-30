from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from configuration import settings
from digielves_setup.validations import *
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
# Create your models here.
from django.contrib.auth import get_user_model
from datetime import date, datetime

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.contrib.postgres.fields import JSONField
import os
from django.db import transaction
from django.db.models.signals import pre_save
from datetime import datetime, date, time
import uuid


class UserManager(BaseUserManager):
    use_in_migrations = True
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)
    

class AutoDateTimeField(models.DateTimeField):
    def pre_save(self, model_instance, add):
        return timezone.now()

# Verified choices should be 0(Not Verified Yet) ,1(Verified) ,2(Rejected)
class User(AbstractBaseUser, PermissionsMixin):
    email               = models.CharField(_('email'),max_length=100,unique=True,validators =[is_valid_mail])
    password            = models.CharField(max_length=150,null=True,blank=True)
    firstname           = models.CharField(max_length=40,null=True,blank=True)
    lastname            = models.CharField(max_length=40,null=True,blank=True)
    phone_no            = models.CharField(max_length=10,null=True,blank=True)
    user_role           = models.CharField(max_length=25,null=False,blank=False)
    user_type           = models.CharField(max_length=25,null=False,blank=False)
    verified            = models.CharField(max_length= 20, null=True, blank=True, choices = ((2, "2"),(1, "1"),(0, "0")) , default =0)
    active              = models.BooleanField(default=True)  
    created_at          = models.DateTimeField(default=timezone.now)
    is_staff            = models.BooleanField(default=False)
    is_superuser        = models.BooleanField(default=False)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
    objects = UserManager()
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=[]
    
    def save(self, *args, **kwargs):
        self.email = self.email.lower()  # Convert email to lowercase before saving
        super().save(*args, **kwargs)
    

class Address(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE, max_length=10,null=False,blank=False, unique=True)
    street_name         = models.CharField(max_length=40, null=True, blank=True)
    land_mark           = models.CharField(max_length=50, null=True, blank=True)
    city                = models.CharField(max_length=35, null=True, blank=True)
    pincode             = models.CharField(max_length=14, null=True, blank=True)
    state               = models.CharField(max_length=35, null=True, blank=True)
    country             = models.CharField(max_length=40, null=True, blank=True)
    Organization_code   = models.CharField(max_length=40, null=True, blank=True)
    description         = models.CharField(max_length=1500, null=True, blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
  
class OrganizationDetails(models.Model):
    # user_id             = models.ForeignKey(User,on_delete=models.CASCADE,max_length=10, null=False, blank=False, unique=True,validators=[validate_user])
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, max_length=10, null=False, blank=False, unique=True)

    name                = models.CharField(max_length=50, null=True,blank=True)
    support_mail        = models.EmailField(max_length=50, null=True, blank=True)
    number_of_employee  = models.IntegerField(max_length=12, null=True,blank=True,default=0)
    number_of_subscription      = models.IntegerField(max_length=12, null=True,blank=True)  
    mail_extension      = models.CharField(max_length=10, null=True,blank=True) 
    organization_code   = models.CharField(max_length=100, null=True, blank=True)
    org_description     = models.CharField(max_length=2500, null=True, blank=True)
    org_website_link    = models.CharField(max_length=250, null=True, blank=True) 
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.support_mail = self.support_mail.lower()  # Convert email to lowercase before saving
        super().save(*args, **kwargs)



class OrganizationBranch(models.Model):
    org                 = models.ForeignKey(OrganizationDetails, on_delete=models.CASCADE, max_length=10, null=False, blank=False)
    branch_name         = models.CharField(max_length=100,null=False, blank=False)
    Address             = models.CharField(max_length=200,null=True, blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)




class EmployeePersonalDetails(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    organization_id     = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=True,blank=True)
    organization_location  = models.ForeignKey(OrganizationBranch,on_delete=models.CASCADE,null=True,blank=True)
    #employee_id         = models.CharField(max_length=10,null=True, blank=True, unique=True)
    employee_id         = models.CharField(max_length=10,null=True, blank=True)
    firstname           = models.CharField(max_length=35,null=True,blank=True)
    lastname            = models.CharField(max_length=35,null=True,blank=True) 
    date_of_birth       = models.CharField(max_length=20,null=True,blank=True)
    phone_no            = models.CharField(max_length=10,null=True,blank=True)
    job_title           = models.CharField(max_length=40,null=True,blank=True)
    designation         = models.CharField(max_length=100,null=True)
    department          = models.CharField(max_length=100,null=True)
    gender              = models.CharField(max_length=15,null=True,blank=True)
    work_location       = models.CharField(max_length=60,null=True,blank=True)
    profile_picture     = models.TextField(null=True,blank=True)
    report_to           = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='report_to')
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    



class OrganizationSubscriptionRequest(models.Model):
    organization        = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=False,blank=False)
    subscription_before = models.IntegerField(null=True,blank=True)
    subscription_want   = models.IntegerField(null=False,blank=False)
    approved            = models.BooleanField(default=False)
    approval_phase      = models.CharField(max_length= 10, null=True, blank=True, choices = ((2, "2"),(1, "1")) , default =1)
    approver            = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
class TaskStatus(models.Model):
    user_admin          = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    organization        = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=True,blank=True)
    status_name         = models.CharField(max_length=25,null=False,blank=False)
    fixed_state         = models.CharField(max_length=25,null=False,blank=False,default="Pending",choices = (("Pending", "Pending"),("InProgress", "InProgress"), ("InReview", "InReview"),("OnHold", "OnHold"),("Completed", "Completed"),("Closed", "Closed"),("Client Action Pending", "Client Action Pending")))
    color               = models.CharField(max_length=10,null=True,blank=True)
    order               = models.IntegerField(null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
    

class DoctorPersonalDetails(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,unique=True)
    firstname           = models.CharField(max_length=20,null=True,blank=True)
    lastname            = models.CharField(max_length=20,null=True,blank=True)
    phone_no            = models.CharField(max_length=10,null=True,blank=True)
    speciality          = models.CharField(max_length=200,null=True,blank=True)
    license_no          = models.CharField(max_length=50,null=True,blank=True)
    year_of_experience  = models.CharField(max_length=20,null=True,blank=True)
    gender              = models.CharField(max_length=10,null=True,blank=True)
    language_spoken     = models.CharField(max_length=20,null=True,blank=True)
    profile_picture     = models.TextField(null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class DoctorSlot(models.Model):
    doctor               = models.ForeignKey(DoctorPersonalDetails,on_delete=models.CASCADE,null=False,blank=False)
    organization_branch  = models.ForeignKey(OrganizationBranch,on_delete=models.CASCADE,null=True,blank=True)
    organization         = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=True,blank=True)
    slots                = models.JSONField(null=False, blank=False,default=None) 
    freeze               = models.CharField(max_length=10,null=False,blank=False,default=False)
    date                 = models.DateField(null=True, blank=True,default=date.today)
    meeting_mode         = models.CharField(max_length=10,null=False,blank=False,default="Offline",choices = (("Online", "Online"),("Offline", "Offline"),))
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)



    
    # def save(self, *args, **kwargs):

    #     existing_slot = DoctorSlot.objects.filter(doctor=self.doctor, date=self.date).first()

    #     if existing_slot:
            
    #         return
    #     else:
    #         super().save(*args, **kwargs)

class DoctorLeaves(models.Model):
    doctor               = models.ForeignKey(DoctorPersonalDetails,on_delete=models.CASCADE,null=False,blank=False)
    date                 = models.DateField(null=False, blank=False)
    on_leave             = models.BooleanField(default=False)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
    
    

class Events(models.Model):
    user_id              = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    guest                = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='event_guests')
    category             = models.CharField(max_length=10,null=False,blank=False,default="Event")
    title                = models.TextField(null=False,blank=False)
    from_date            = models.DateField(null=False, blank=False,default=date.today)
    from_time            = models.TimeField(null=True,blank=True)
    to_date              = models.DateField(null=True, blank=True)
    to_time              = models.TimeField(null=True,blank=True)
    description          = models.TextField(null=True,blank=True)
    attachment           = models.CharField(max_length=1000,null=True,blank=True,default=None)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)

@receiver(post_save, sender=Events)
def create_events_calender_reminder(sender, instance, created, **kwargs):
    if created:
        def on_commit_callback():
            reminder = CalenderReminder.objects.create(
                user=instance.user_id,
                title=instance.title,
                category="Event",
                from_datetime=datetime.combine(instance.from_date, instance.from_time or time(0, 0)),
                to_datetime=datetime.combine(instance.to_date, instance.to_time or time(23, 59)) if instance.to_date else None,
                description=instance.description,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id
            )

            if instance.guest.exists():
                reminder.shared_with_users.set(instance.guest.all())

            reminder.save()
        transaction.on_commit(on_commit_callback)

@receiver(pre_save, sender=Events)
def update_events_calender_reminder(sender, instance, **kwargs):
    if instance.pk:
        original_event = Events.objects.get(pk=instance.pk)
        if (original_event.from_date != instance.from_date or 
            original_event.from_time != instance.from_time or 
            original_event.title != instance.title or
            set(original_event.guest.all()) != set(instance.guest.all())):
            try:
                reminder = CalenderReminder.objects.get(object_id=instance.id, content_type=ContentType.objects.get_for_model(instance))
                
                # Ensure from_date is not None
                if instance.from_date:
                    reminder.from_datetime = datetime.combine(instance.from_date, instance.from_time or time(0, 0))
                else:
                    raise ValueError("from_date cannot be None")

                # Ensure to_date is not None
                if instance.to_date:
                    reminder.to_datetime = datetime.combine(instance.to_date, instance.to_time or time(23, 59))
                else:
                    reminder.to_datetime = None  # Handle as per your requirement

                reminder.shared_with_users.set(instance.guest.all())
                reminder.title = instance.title
                reminder.save()
            except CalenderReminder.DoesNotExist:
                pass
class Meettings(models.Model):
    user_id              = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    participant          = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='meeting_participants')
    other_participant_email    = models.TextField(null=True, blank=True)
    category             = models.CharField(max_length=10,null=False,blank=False,default="Meeting")
    meet_link            = models.TextField(null=True,blank=True)
    meet_id              = models.TextField(null=True,blank=True)
    uuid                 = models.TextField(null=True,blank=True)
    title                = models.TextField(null=False,blank=False)
    purpose              = models.TextField(null=True,blank=True)
    from_date            = models.DateField(null=False, blank=False,default=date.today)
    from_time            = models.TimeField(null=True,blank=True)
    to_date              = models.DateField(null=True, blank=True)
    to_time              = models.TimeField(null=True,blank=True)
    status_complete      = models.BooleanField(default=False)
    meet_start_time      = models.DateTimeField(null=True,blank=True)
    meeting_processed    = models.BooleanField(default=False)
    summery_got          = models.BooleanField(default=False)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
@receiver(post_save, sender=Meettings)
def create_meetings_calender_reminder(sender, instance, created, **kwargs):
    if created:
        def on_commit_callback():
            # Check if from_date is None and handle accordingly
            from_datetime = datetime.combine(instance.from_date, instance.from_time or time(0, 0)) if instance.from_date else timezone.now()
            # Check if to_date is None and handle accordingly
            to_datetime = datetime.combine(instance.from_date, instance.to_time or time(23, 59)) if instance.from_date else None

            reminder = CalenderReminder.objects.create(
                user=instance.user_id,
                title=instance.title,
                category="Meeting",
                from_datetime=from_datetime,
                to_datetime=to_datetime,
                description=instance.purpose,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id
            )

            if instance.participant.exists():
                reminder.shared_with_users.set(instance.participant.all())
            
            reminder.save()

        transaction.on_commit(on_commit_callback)



@receiver(pre_save, sender=Meettings)
def update_meetings_calender_reminder(sender, instance, **kwargs):
    if instance.pk:
        original_meeting = Meettings.objects.get(pk=instance.pk)
        if (original_meeting.from_date != instance.from_date or 
            original_meeting.from_time != instance.from_time or 
            original_meeting.title != instance.title or
            set(original_meeting.participant.all()) != set(instance.participant.all())):
            try:
                reminder = CalenderReminder.objects.get(object_id=instance.id, content_type=ContentType.objects.get_for_model(instance))
                
                # Ensure from_date is not None
                if instance.from_date:
                    reminder.from_datetime = datetime.combine(instance.from_date, instance.from_time or time(0, 0))
                else:
                    raise ValueError("from_date cannot be None")

                # Ensure to_date is not None
                if instance.to_date:
                    reminder.to_datetime = datetime.combine(instance.to_date, instance.to_time or time(23, 59))
                else:
                    reminder.to_datetime = None  # Handle as per your requirement

                reminder.shared_with_users.set(instance.participant.all())
                reminder.title = instance.title
                reminder.save()
            except CalenderReminder.DoesNotExist:
                pass
        
        if original_meeting != instance.status_complete:
            reminder = CalenderReminder.objects.get(object_id=instance.id, content_type=ContentType.objects.get_for_model(instance))
            reminder.completed=True
            reminder.save()

class MeettingSummery(models.Model):
    meettings            = models.ForeignKey(Meettings,on_delete=models.CASCADE,null=False,blank=False)
    meet_transcript      = models.CharField(max_length=1000,null=True,blank=True,default=None)
    meet_audio           = models.CharField(max_length=2000,null=True,blank=True,default=None)
    meet_summery         = models.TextField(null=True,blank=True)
    meet_video         = models.TextField(null=True,blank=True)

    meet_tasks           = models.TextField(null=True,blank=True)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)


# reporting_user user is reporting to reporting_to_user
class ReportingRelationship(models.Model):
    reporting_user      = models.ForeignKey('UserCreation', on_delete=models.CASCADE, related_name='reporting_relationships')
    reporting_to_user   = models.ForeignKey('UserCreation', on_delete=models.CASCADE, related_name='reporting_to_relationships')
    
    hierarchy           = models.PositiveIntegerField()
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
# processed choices should be 0 (Not Verified Yet), 1 (Registered), 2 (Personal Details Added), 3 (Rejected)
# Verified choices should be 0(Not Verified Yet) ,1 (Verified) ,2 (Rejected)
class UserCreation(models.Model):
    organization_id     = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE, max_length=10,null=False,blank=False)
    organization_location  = models.ForeignKey(OrganizationBranch,on_delete=models.CASCADE,null=True,blank=True)
    created_by          = models.ForeignKey(User,on_delete=models.CASCADE,related_name='creator_id', db_column='created_by_id', max_length=10,null=False,blank=False)
    employee_user_id    = models.ForeignKey(User,on_delete=models.CASCADE, related_name='employee_user_id',db_column='employee_user_id', max_length=10,null=True,blank=True,)
    email               = models.CharField(max_length=100,null=False,blank=False)
    company_employee_id = models.CharField(max_length=50,null=True,blank=True)
    token               = models.CharField(max_length=100,null=False,blank=False)
    processed           = models.CharField(max_length= 20, null=True, blank=True, choices = ((3, "3"),(2, "2"),(1, "1"),(0, "0")) , default =0) 
    verified            = models.CharField(max_length= 20, null=True, blank=True, choices = ((2, "2"),(1, "1"),(0, "0")) , default =0)
    reporting_to       = models.ManyToManyField('self', through=ReportingRelationship, symmetrical=False, null=True, blank=True, default=None, related_name='report_to')
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.email = self.email.lower()  # Convert email to lowercase before saving
        
        super().save(*args, **kwargs)

class UserPosition(models.Model):
    user                = models.ForeignKey(UserCreation, on_delete=models.CASCADE)
    x                   = models.FloatField()
    y                   = models.FloatField()
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class DoctorAchivement(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    achivement_title    = models.CharField(max_length=50,null=True,blank=True)
    achivement_file     = models.CharField(max_length=104857,null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
   
    
class SubscribedApp(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    app_name            = models.CharField(max_length=50,null=False,blank=False)
    app_logo            = models.CharField(max_length=50,null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class DoctorConsultationDetails(models.Model):
    employee_id         = models.ForeignKey(User,on_delete=models.CASCADE, db_column='employee_id', max_length=10,null=False,blank=False)
    gender              = models.CharField(max_length=20,null=True,blank=True)
    full_name           = models.CharField(max_length=20,null=True,blank=True)
    relationship        = models.CharField(max_length=100,null=True,blank=True)
    blood_group         = models.CharField(max_length=100,null=True,blank=True)
    marital_status      = models.CharField(max_length=100,null=True,blank=True)
    age                 = models.CharField(max_length=100,null=True,    blank=True)
    gender              = models.CharField(max_length=100,null=True,blank=True)
    phone_no            = models.CharField(max_length=100,null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    

# Confirm choices should be only 0(Pending) ,1(Accept) ,2(Reject)
class DoctorConsultation(models.Model):
    doctor_id           = models.ForeignKey(User,related_name='doctor_id', db_column='doctor_user_id',on_delete=models.CASCADE,null=False,blank=False,)
    employee_id         = models.ForeignKey(User,related_name='employee_id',db_column='employee_user_id',on_delete=models.CASCADE,null=False,blank=False)
    communication_preference = models.CharField(max_length=20,null=True,blank=True)
    consultation_for    = models.ForeignKey(DoctorConsultationDetails,on_delete=models.CASCADE,null=False,blank=False)
    transcript          = models.CharField(max_length=20,null=True,blank=True)
    next_appointment    = models.CharField(max_length=20,null=True,blank=True)
    appointment_date    = models.CharField(max_length=100,null=True,blank=True)
    doctor_slot         = models.ForeignKey(DoctorSlot,on_delete=models.SET_NULL,null=True,blank=True)
    organization_id     = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=True,blank=True)
    organization_branch_id = models.ForeignKey(OrganizationBranch,on_delete=models.CASCADE,null=True,blank=True)


    reschedule_appointment      = models.CharField(max_length=100,null=True,blank=True)
    reason_for_reschedule       = models.CharField(max_length=100,null=True,blank=True)
    confirmed           = models.CharField(max_length=100,null=True,blank=True, choices = ((2, "2"),(1, "1"),(0, "0")) , default =0)
    status              = models.CharField(max_length=100,null=True,blank=True, default ="Booked")
    meeting_url         = models.CharField(max_length=100,null=True,blank=True)
    meeting_pref_type   = models.CharField(max_length=100,null=True,blank=True) 
    reschedule_by       = models.CharField(max_length=100,null=True,blank=True) 
    
    reason_for_consultation     = models.CharField(max_length=100,null=True,blank=True)
    reason_for_rejection= models.CharField(max_length=100,null=True,blank=True)
    
    dignosis            = models.CharField(max_length=500,null=True,blank=True)
    advice              = models.CharField(max_length=500,null=True,blank=True)
    prescription_url    = models.CharField(max_length=1000,null=True,blank=True)
    summery             = models.TextField(null=True,blank=True)
    meeting_id          = models.TextField(null=True,blank=True)
    meeting_uuid        = models.TextField(null=True,blank=True)
    meeting_transcript  = models.TextField(null=True,blank=True)
    precaution          = models.TextField(null=True,blank=True)
    meeting_summery     = models.TextField(null=True,blank=True)
    meeting_audio       = models.TextField(null=True,blank=True)
    summery_generating  = models.BooleanField(default=False)
    summery_got         = models.BooleanField(default=False)
    cancellation_reason = models.TextField(null=True,blank=True)
    cancelled_by        = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    reschedule_date     = models.DateField(null=True,blank=True)
    reschedule_time     = models.CharField(max_length=15,null=True,blank=True)
    
    
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

@receiver(post_save, sender=DoctorConsultation)
def create_doctor_consultation_calender_reminder(sender, instance, created, **kwargs):
    if created:
        def on_commit_callback():
            slot = instance.doctor_slot
            if slot:
                slot_times = slot.slots.split(' - ')
                from_time = datetime.strptime(slot_times[0], '%H:%M').time()
                to_time = datetime.strptime(slot_times[1], '%H:%M').time()
                from_datetime = datetime.combine(datetime.strptime(instance.appointment_date, '%Y-%m-%d').date(), from_time)
                to_datetime = datetime.combine(datetime.strptime(instance.appointment_date, '%Y-%m-%d').date(), to_time)

                reminder = CalenderReminder.objects.create(
                    user=instance.employee_id,
                    title=instance.reason_for_consultation or "Doctor Consultation",
                    category="Consultation",
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    description=instance.summery,
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=instance.id
                )
                reminder.shared_with_users.add(instance.doctor_id)
                reminder.save()
                slot.freeze = True
                slot.save()

        transaction.on_commit(on_commit_callback)


# @receiver(pre_save, sender=DoctorConsultation)
# def update_doctor_consultation_calender_reminder(sender, instance, **kwargs):
#     if instance.pk:
#         original_consultation = DoctorConsultation.objects.get(pk=instance.pk)
#         if (original_consultation.appointment_date != instance.appointment_date or 
#             original_consultation.reason_for_consultation != instance.reason_for_consultation or
#             original_consultation.doctor_slot != instance.doctor_slot):
            
#             try:
#                 reminder = CalenderReminder.objects.get(object_id=instance.id, content_type=ContentType.objects.get_for_model(instance))
#                 slot = instance.doctor_slot
#                 if slot:
#                     slot_times = slot.slots.split(' - ')
#                     from_time = datetime.strptime(slot_times[0], '%H:%M').time()
#                     to_time = datetime.strptime(slot_times[1], '%H:%M').time()
#                     reminder.from_datetime = datetime.combine(datetime.strptime(instance.appointment_date, '%Y-%m-%d').date(), from_time)
#                     reminder.to_datetime = datetime.combine(datetime.strptime(instance.appointment_date, '%Y-%m-%d').date(), to_time)

#                     reminder.title = instance.reason_for_consultation or "Doctor Consultation"
#                     reminder.shared_with_users.set([instance.doctor_id])
#                     reminder.save()
#                     slot.freeze = True
#                     slot.save()

#             except CalenderReminder.DoesNotExist:
#                 pass


class ConsultationReport(models.Model):
    consultation         = models.ForeignKey(DoctorConsultation, on_delete=models.CASCADE, related_name='consultation_reports', null=True, blank=True)
    report_type                = models.CharField(max_length=15,null=True,blank=True)
    reports             = models.TextField(null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    

class EmployeeCancelConsultationLimit(models.Model):
    consultation = models.ForeignKey(
        DoctorConsultation,
        on_delete=models.DO_NOTHING,
        related_name='cancel_limits',
        null=True,
        blank=True
    )
    cancel_date = models.DateField(null=False, blank=False, default=date.today)
    employee_id         = models.ForeignKey(User,related_name='employeee_id',db_column='cancelled_employee',on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = AutoDateTimeField(default=timezone.now)

    
class DoctorPrescriptions(models.Model):
    consultation_id     = models.ForeignKey(DoctorConsultation,on_delete=models.CASCADE,null=True,blank=True)
    employee_id         = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    medicine_name       = models.CharField(max_length=30,null=True,blank=True)
    strength            = models.CharField(max_length=30,null=True,blank=True)
    doses               = models.CharField(max_length=20,null=True,blank=True)
    units               = models.CharField(max_length=10,null=True,blank=True)
    frequency           = models.CharField(max_length=20,null=True,blank=True) 
    consumption_quantity= models.CharField(max_length=20,null=True,blank=True)
    method              = models.CharField(max_length=20,null=True,blank=True)
    duration            = models.CharField(max_length=20,null=True,blank=True)
    notes              = models.TextField(null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone. now)
 

class Insurance(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True) 
    employee_id         = models.ForeignKey(EmployeePersonalDetails,on_delete=models.CASCADE,null=True,blank=True,) 
    company_name        = models.CharField(max_length=50,null=True,blank=True,validators=[is_valid_string])
    policy_number       = models.CharField(max_length=20,null=True,blank=True,validators=[validate_policy_number])
    premium             = models.CharField(max_length=10,null=True,blank=True)
    insurance_plan      = models.CharField(max_length=50,null=True,blank=True)
    type_of_policy      = models.CharField(max_length=20,null=True,blank=True)
    start_date          = models.DateField()
    end_date            = models.DateField()
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)



class FamilyInsurance(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,validators=[validate_user]) 
    relation            = models.CharField(max_length=200,null=True,blank=True,validators=[validate_String_Length])
    name                = models.CharField(max_length=200,null=True,blank=True,validators=[is_valid_string])
    age                 = models.CharField(max_length=200,null=True,blank=True,validators=[validate_age])
    gender              = models.CharField(max_length=200,null=True,blank=True,validators=[validate_gender])
    policy_number       = models.CharField(max_length=200,null=True,blank=True, validators=[validate_policy_number])
    company_name        = models.CharField(max_length=200,null=True,blank=True)
    premium             = models.CharField(max_length=200,null=True,blank=True)
    Insurance_plan      = models.CharField(max_length=200,null=True,blank=True)
    start_date          = models.DateField()
    end_date            = models.DateField()
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)




class Helpdesk(models.Model):
    issue_raised_by              = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    issue_assigned_to            = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='issue_assigned_to')
    issue_status                 = models.CharField(max_length=20, null=True, blank=True,choices = (("Open", "Open"),("Pending", "Pending"),("Solved", "Solved"),("Closed", "Closed")) , default ="Open")
    issue_subject                = models.CharField(max_length=100,null=True,blank=True)
    issue_description            = models.TextField(null=True,blank=True)
    issue_priority               = models.CharField(max_length=20, null=True, blank=True,choices = (("Low", "Low"),("Medium", "Medium"),("High", "High"),("Critical", "Critical")) , default ="Low")
    issue_category               = models.CharField(max_length=20, null=True, blank=True)
    issue_date                   = models.DateTimeField(default=timezone.now)
    additional_info_for_support  = models.TextField(null=True,blank=True)
    preferred_support_contact    = models.CharField(max_length=10, null=True, blank=True)
    organization                 = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=False,blank=False)
    organization_branch          = models.ForeignKey(OrganizationBranch,on_delete=models.CASCADE,null=True,blank=True)
    comment_box                  = models.TextField(null=True,blank=True)
    created_at                   = models.DateTimeField(default=timezone.now)
    updated_at                   = AutoDateTimeField(default=timezone.now)

class HelpdeskAction(models.Model):
    user                         = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False) 
    helpdesk                     = models.ForeignKey(Helpdesk,on_delete=models.CASCADE,null=False,blank=False) 
    remark                       = models.TextField(null=False,blank=False)
    created_at                   = models.DateTimeField(default=timezone.now)
    updated_at                   = AutoDateTimeField(default=timezone.now)

class HelpdeskAttachment(models.Model):
    helpdesk                     = models.ForeignKey(Helpdesk,on_delete=models.CASCADE,null=False,blank=False)
    attachment                   = models.CharField(max_length=1000,null=False,blank=False)
    created_at                   = models.DateTimeField(default=timezone.now)
    updated_at                   = AutoDateTimeField(default=timezone.now)






class Birthdays(models.Model):
    user_id              = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    firstname            = models.TextField(null=True,blank=True)
    lastname             = models.TextField(null=True, blank=True)
    date_of_birth        = models.DateField(null=True, blank=True) 
    email                = models.TextField(null=True,blank=True)
    phone_no             = models.TextField(null=True,blank=True)
    profile_picture      = models.ImageField(upload_to='employee/birthday_cards/profile/', null=True, blank=True, default=None)
    card_added           = models.BooleanField(default=False) # because condition on bdCard is not working
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
class BirthdayTemplates(models.Model):
    user_id              = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    birthday             = models.ForeignKey(Birthdays,on_delete=models.CASCADE,null=False,blank=False)
    card_name            = models.TextField(null=True,blank=True)
    bdCard               = models.ImageField(upload_to='employee/birthday_cards/card/', null=True, blank=True, default=None)
    bd_wish              = models.TextField(null=True,blank=True)
    card_profile         = models.ImageField(upload_to='employee/birthday_cards/profile/custom_profile/', null=True, blank=True, default=None)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)


class SummeryNdTask(models.Model):
    user                         = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    summery                      = models.TextField(null=True,blank=True)
    tasks                        = models.TextField(null=True,blank=True)
    file_name                    = models.TextField(null=True,blank=True)
    summery_generated            = models.BooleanField(default=False)
    created_at                   = models.DateTimeField(default=timezone.now)
    updated_at                   = AutoDateTimeField(default=timezone.now)







class Category(models.Model):
    name                = models.CharField(max_length=100,null=False,blank=False)                                                                                                         
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
 
class Template(models.Model):
    category            = models.ForeignKey(Category,on_delete=models.CASCADE,null=False,blank=False)
    template_name       = models.CharField(max_length=100,null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
class TemplateChecklist(models.Model):
    template            = models.ForeignKey(Template,on_delete=models.CASCADE,null=False,blank=False)
    name                = models.CharField(max_length=100,null=False,blank=False,validators=[validate_String_Length])
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class TemplateTaskList(models.Model):
    checklist           = models.ForeignKey(TemplateChecklist,on_delete=models.CASCADE,null=False,blank=False)
    task_name           = models.CharField(max_length=600,null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class TemplateAttachments(models.Model):
    template            = models.ForeignKey(Template,on_delete=models.CASCADE,null=False,blank=False)
    attachment          = models.CharField(max_length=1000,null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)





 
class Board(models.Model):
    template            = models.ForeignKey(Template,on_delete=models.CASCADE,null=True,blank=True)
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, default=None)
    assign_to           = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='assign_to_board')
    board_name          = models.CharField(max_length=600,null=False,blank=False)
    due_date            = models.DateField(null=True,blank=True)
    category            = models.CharField(max_length=200,null=True,blank=True)
    favorite            = models.BooleanField(default=None,null=True, blank=True) # just for showing not really save data into it 
    image               = models.ImageField(upload_to='employee/board/', null=True, blank=True)
    summery             = models.TextField(null=True, blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
class FevBoard(models.Model):
    user                = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, default=None)
    board               = models.ManyToManyField(Board,null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
class Checklist(models.Model):
    board               = models.ForeignKey(Board,on_delete=models.CASCADE,null=False,blank=False)
    name                = models.CharField(max_length=100,null=False,blank=False)
    sequence            = models.CharField(max_length=100,null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
 
 
class UTCDateTimeField(models.DateTimeField):
    def to_python(self, value):
        if isinstance(value, str):
            # Remove the timezone information from the input datetime string
            value = value.split(' GMT')[0]
            
            try:
                # Parse the input datetime string
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M')
            except ValueError:
                # If the above format doesn't match, try parsing with the alternative format
                value = datetime.strptime(value, '%a %b %d %Y %H:%M:%S')
                
            # Convert the parsed date to a timezone-aware UTC datetime object
            value = timezone.make_aware(value, timezone=timezone.utc)
            
        return value    

    def from_db_value(self, value, expression, connection):
        # Ensure that the value returned from the database is timezone-aware UTC datetime
        if value is not None and timezone.is_naive(value):
            value = timezone.make_aware(value, timezone=timezone.utc)
        return value



class Tasks(models.Model):
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name='created_by')
    assign_to           = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='assign_to_task')
    assigned_created_by = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='assigned_created_by')
    checklist           = models.ForeignKey(Checklist, on_delete=models.CASCADE, null=True, blank=True)
    task_topic          = models.CharField(max_length=300,null=False,blank=False)
    due_date_exiting    = models.CharField(max_length=100,null=True,blank=True)
    due_date_latest_existing = UTCDateTimeField(null=True,blank=True)
    due_date            = models.DateTimeField(null=True,blank=True)
    task_description    = models.CharField(max_length=500,null=True,blank=True)
    urgent_status       = models.BooleanField(default=False)
    completed           = models.BooleanField(default=False)
    status              = models.ForeignKey(TaskStatus,on_delete=models.SET_NULL, null=True, blank=True)
    sequence            = models.CharField(max_length=100,null=True,blank=True)
    is_personal         = models.BooleanField(default=False)
    reopened_count      = models.PositiveIntegerField(default=0,null=False, blank=False)
    inTrash             = models.BooleanField(default=False)
    project_file_name   = models.CharField(max_length=100,null=True,blank=True, default=None)
    start_date          = models.DateTimeField(default=timezone.now)
    end_date            = models.DateTimeField(null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        # If the task is being created and the status is not set, set it to the default for the user
        if not self.status and self.created_by:
            
            get_org_id = EmployeePersonalDetails.objects.get(user_id=self.created_by.id)
            task_status = TaskStatus.objects.filter(organization=get_org_id.organization_id,fixed_state="Pending").order_by('order').first()
            
            if not task_status:
                raise ValueError("Default TaskStatus not found for the user.")
            else:
                self.status = task_status
        if not self.start_date:
            self.start_date = timezone.now()

        super().save(*args, **kwargs)
    

# Signal to create a CalenderReminder after a Task is created
@receiver(post_save, sender=Tasks)
def create_calender_reminder(sender, instance, created, **kwargs):
    if created:
        def on_commit_callback():
            reminder = CalenderReminder.objects.create(
                user=instance.created_by,
                title=instance.task_topic,
                category="Task",
                from_datetime=instance.due_date,
                to_datetime=instance.due_date,
                description=f"Reminder for the task: {instance.task_topic}",
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id
            )
            
            # Adding all the assigned users to the reminder's shared_with_users
            if instance.assign_to.exists():  # Check if there are users to assign
                reminder.shared_with_users.set(instance.assign_to.all())
            
            reminder.save()

        # Use transaction.on_commit to ensure this runs after the transaction is fully complete it can handle assign to
        transaction.on_commit(on_commit_callback)

@receiver(pre_save, sender=Tasks)
def update_calender_reminder(sender, instance, **kwargs):
    # Check if the task is being updated
    if instance.pk:
        original_task = Tasks.objects.get(pk=instance.pk)
        
        if original_task.due_date != instance.due_date or original_task.assign_to.all() != instance.assign_to.all() or original_task.task_topic != instance.task_topic:
            try:
                reminder = CalenderReminder.objects.get(object_id=instance.id, content_type=ContentType.objects.get_for_model(instance))
                
                reminder.from_datetime = instance.due_date
                reminder.to_datetime = instance.due_date
                reminder.title = instance.task_topic
                reminder.shared_with_users.set(instance.assign_to.all())
                
                reminder.save()
            except CalenderReminder.DoesNotExist:
                pass 
        
            
        status_changed = original_task.status != instance.status
        if status_changed:
            try:
                reminder = CalenderReminder.objects.get(object_id=instance.id, content_type=ContentType.objects.get_for_model(instance))
                # Import the function here to avoid circular import
                from employee.views.controllers.status_controllers import get_status_ids_from_creater_side
                int_status = int(instance.status.id)
                closed_status_ids = get_status_ids_from_creater_side(instance.created_by , True)
                if int_status in closed_status_ids:
                    reminder.completed = True
                    reminder.save()
                else:
                    reminder.completed = False
                    reminder.save()
            except CalenderReminder.DoesNotExist:
                pass
            
class TaskAttachments(models.Model):
    task                = models.ForeignKey(Tasks,on_delete=models.CASCADE,null=False,blank=False)
    attachment          = models.CharField(max_length=1000,null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class TaskAction(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False) 
    task                = models.ForeignKey(Tasks,on_delete=models.CASCADE,null=False,blank=False) 
    remark              = models.CharField(max_length=1000,null=False,blank=False,default=None)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


@receiver(post_save, sender=TaskAction)
def chattingAndAction_handler(sender, instance, created, **kwargs):
   
    
    if created:

        channel_layer = get_channel_layer()
        sender_user = User.objects.get(id=instance.user_id.id)
     
        data = {
            'message': instance.remark,
            'created_at': str(instance.created_at),
            'is_seen': False,
            'sender_id': instance.user_id.id,
            "task_id":instance.task.id,
            "username": f"{sender_user.firstname} {sender_user.lastname}"
        }
     
                
        async_to_sync(channel_layer.group_send)(
            f'task_{instance.task.id}', {
                'type': 'chat_added',
                'value': data
            }
        )   
class TaskChatting(models.Model):
    task                = models.ForeignKey(Tasks,on_delete=models.CASCADE,null=False,blank=False)
    sender              = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name='sender_chats')
    # receiver            = models.ManyToManyField(User,null=False, blank=False, related_name='receiver_chats') 
    # message             = models.CharField(max_length=1000,null=False,blank=False)
    message             = models.TextField(null=False, blank=False)
    is_read             = models.BooleanField(default=False,null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now) 



@receiver(post_save, sender=TaskChatting)
def chattingAndAction_handler(sender, instance, created, **kwargs):
    
    if created:
        
        channel_layer = get_channel_layer()
        sender_user = User.objects.get(id=instance.sender_id)
        
        if instance.message and 'chat_files' in instance.message:
            file_path = os.path.join(settings.MEDIA_ROOT, instance.message)

            
            # Get the file size
            try:
                size = os.path.getsize(file_path)
                # Convert size to human-readable format
                size_kb = size / 1024
                size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
            except Exception as e:
                # Handle error if unable to get file size
                size_str = 'Unknown'

        else:
            size_str = -1
            
        data = {
            'message': instance.message,
            'created_at': str(instance.created_at),
            'is_seen': instance.is_read,
            'sender_id': instance.sender_id,
            "task_id":instance.task.id,
            "username": f"{sender_user.firstname} {sender_user.lastname}",
            'file_size': size_str
        }
       
                
        async_to_sync(channel_layer.group_send)(
            f'task_{instance.task.id}', {
                'type': 'chat_added',
                'value': data
            }
        )   

class TaskComments(models.Model):
    
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False) 
    task                = models.ForeignKey(Tasks,on_delete=models.CASCADE,null=False,blank=False) 
    comment              = models.CharField(max_length=1000,null=False,blank=False,default=None)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)




class MultiLevelTask(models.Model):
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name='multilevel_created_by')
    assign_to           = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='multilevel_assign_to')
    checklist           = models.ForeignKey(Checklist, on_delete=models.CASCADE, null=True, blank=True)
    task_topic          = models.CharField(max_length=300,null=False,blank=False)
    due_date            = models.DateTimeField(null=True,blank=True)
    task_description    = models.CharField(max_length=500,null=True,blank=True)
    urgent_status       = models.BooleanField(default=False)
    status              = models.ForeignKey(TaskStatus,on_delete=models.SET_NULL, null=True, blank=True)
    sequence            = models.CharField(max_length=100,null=True,blank=True)
    is_personal         = models.BooleanField(default=False)
    reopened_count      = models.PositiveIntegerField(default=0,null=False, blank=False)
    inTrash             = models.BooleanField(default=False)
    project_file_name   = models.CharField(max_length=100,null=True,blank=True, default=None)
    start_date          = models.DateTimeField(default=timezone.now)
    end_date            = models.DateTimeField(null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class TaskHierarchy(models.Model):
    TRASH_With_CHOICES = [
        ('Manually', 'Manually'),
        ('Relatively_task', 'Relatively_task')
    ]
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name='task_hierarchy_created_by')
    assign_to           = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='task_hierarchy_assign_to')
    checklist           = models.ForeignKey(Checklist, on_delete=models.CASCADE, null=True, blank=True)
    task_topic          = models.CharField(max_length=300,null=False,blank=False)
    due_date            = models.DateTimeField(null=True,blank=True)
    task_description    = models.CharField(max_length=500,null=True,blank=True)
    urgent_status       = models.BooleanField(default=False)
    status              = models.ForeignKey(TaskStatus,on_delete=models.SET_NULL, null=True, blank=True)
    sequence            = models.CharField(max_length=100,null=True,blank=True)
    parent              = models.ForeignKey('self',on_delete=models.CASCADE, related_name='children',blank=True,null=True )
    depend_on           = models.ManyToManyField('self', symmetrical=False, related_name='dependent_children',blank=True,null=True,  )
    task_level          = models.PositiveIntegerField(default=0,null=False, blank=False)

    is_personal         = models.BooleanField(default=False)
    reopened_count      = models.PositiveIntegerField(default=0,null=False, blank=False)
    inTrash             = models.BooleanField(default=False)
    trashed_with        = models.CharField(max_length=20, choices=TRASH_With_CHOICES, default = None ,null=True, blank=True)
    project_file_name   = models.CharField(max_length=100,null=True,blank=True, default=None)
    start_date          = models.DateTimeField(null=True,blank=True)
    end_date            = models.DateTimeField(null=True,blank=True)
    status_changed_by_user = models.BooleanField(default=False)
    status_changed_to_complete = models.BooleanField(default=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
    
    def save(self, *args, **kwargs):
        # If the task is being created and the status is not set, set it to the default for the user
        if not self.status and self.created_by:
            
            get_org_id = EmployeePersonalDetails.objects.get(user_id=self.created_by.id)
            organization_id = get_org_id.organization_id

            states = ["Pending", "InProgress", "OnHold"]

            task_status = None
            for state in states:
                task_status = TaskStatus.objects.filter(organization=organization_id, fixed_state=state).order_by('order').first()
                if task_status:
                    break

            
            if not task_status:
                raise ValueError("Default TaskStatus not found for the user.")
            else:
                self.status = task_status
                
                
        # Check if the status is being changed by a user for the first time
        if self.pk and not self.status_changed_by_user:
            current_status = TaskHierarchy.objects.filter(pk=self.pk).values('status').first()
            if current_status and current_status['status'] != self.status.id:
                self.start_date = timezone.now()
                self.status_changed_by_user = True

        super().save(*args, **kwargs)
    
class TaskHierarchyAttachments(models.Model):
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='task_attachment_created_by')
    task                = models.ForeignKey(TaskHierarchy,on_delete=models.CASCADE,null=False,blank=False, related_name='task_hierarchy')
    task_attachment     = models.FileField(upload_to='employee/task_attachment/', null=False, blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
    
class TaskHierarchyAction(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False) 
    task                = models.ForeignKey(TaskHierarchy,on_delete=models.CASCADE,null=False,blank=False, related_name='task_hierarchy_action') 
    remark              = models.CharField(max_length=1000,null=False,blank=False,default=None)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


@receiver(post_save, sender=TaskAction)
def chattingAndAction_handler(sender, instance, created, **kwargs):
   
    
    if created:

        channel_layer = get_channel_layer()
        sender_user = User.objects.get(id=instance.user_id.id)
     
        data = {
            'message': instance.remark,
            'created_at': str(instance.created_at),
            'is_seen': False,
            'sender_id': instance.user_id.id,
            "task_id":instance.task.id,
            "username": f"{sender_user.firstname} {sender_user.lastname}"
        }
     
                
        async_to_sync(channel_layer.group_send)(
            f'task_{instance.task.id}', {
                'type': 'chat_added',
                'value': data
            }
        )   
class TaskHierarchyChatting(models.Model):
    task                = models.ForeignKey(TaskHierarchy,on_delete=models.CASCADE,null=False,blank=False, related_name='task_hierarchy_chatting')
    sender              = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name='sender_chat_hierarchy')

    message             = models.TextField(null=False, blank=False)
    is_read             = models.BooleanField(default=False,null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now) 



@receiver(post_save, sender=TaskHierarchyChatting)
def chattingAndAction_handler(sender, instance, created, **kwargs):
    
    if created:
        
        channel_layer = get_channel_layer()
        sender_user = User.objects.get(id=instance.sender_id)
        
        if instance.message and 'chat_files' in instance.message:
            file_path = os.path.join(settings.MEDIA_ROOT, instance.message)

            
            # Get the file size
            try:
                size = os.path.getsize(file_path)
                # Convert size to human-readable format
                size_kb = size / 1024
                size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
            except Exception as e:
                # Handle error if unable to get file size
                size_str = 'Unknown'

        else:
            size_str = -1
            
        data = {
            'message': instance.message,
            'created_at': str(instance.created_at),
            'is_seen': instance.is_read,
            'sender_id': instance.sender_id,
            "task_id":instance.task.id,
            "username": f"{sender_user.firstname} {sender_user.lastname}",
            'file_size': size_str
        }
       
                
        async_to_sync(channel_layer.group_send)(
            f'task_{instance.task.id}', {
                'type': 'chat_added',
                'value': data
            }
        )   

class TaskHierarchyComments(models.Model):
    
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False) 
    task                = models.ForeignKey(TaskHierarchy,on_delete=models.CASCADE,null=False,blank=False, related_name='task_hierarchy_comment') 
    comment              = models.CharField(max_length=1000,null=False,blank=False,default=None)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class TaskHierarchyChecklist(models.Model):
    TRASH_With_CHOICES = [
        ('Manually', 'Manually'),
        ('Relatively_task', 'Relatively_task')
    ]
    Task                = models.ForeignKey(TaskHierarchy,on_delete=models.CASCADE,null=False,blank=False,default=None, related_name='task_hierarchy_checklist')
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='task_hierarchy_checklist_created_by')
    name                = models.CharField(max_length=100,null=False,blank=False)
    inTrash             = models.BooleanField(default=False)
    trashed_with        = models.CharField(max_length=20, choices=TRASH_With_CHOICES, default = None ,null=True, blank=True) # New field to track how trashed the checklist 
    reopened_count      = models.PositiveIntegerField(default=0,null=False, blank=False)
    completed           = models.BooleanField(default=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class TaskHierarchyDueRequest(models.Model):
    sender               = models.ForeignKey(User, related_name='sender_requests', on_delete=models.CASCADE)
    receiver             = models.ForeignKey(User, related_name='receiver_requests', on_delete=models.CASCADE, default=None)
    task                 = models.ForeignKey(TaskHierarchy, on_delete=models.CASCADE, default = None,  null = True, blank =True)
    current_due_date     = models.DateTimeField(null=True,blank=True)
    proposed_due_date    = models.DateTimeField(null=True,blank=True)
    status               = models.CharField(max_length=20, choices=(('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')), default='pending')
    inTrash              = models.BooleanField(default=False)             
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)

class TaskChecklist(models.Model):
    TRASH_With_CHOICES = [
        ('Manually', 'Manually'),
        ('Relatively_task', 'Relatively_task')
    ]
    Task                = models.ForeignKey(Tasks,on_delete=models.CASCADE,null=False,blank=False,default=None)
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='checklist_created_by')
    name                = models.CharField(max_length=100,null=False,blank=False)
    inTrash             = models.BooleanField(default=False)
    trashed_with        = models.CharField(max_length=20, choices=TRASH_With_CHOICES, default = None ,null=True, blank=True) # New field to track how trashed the checklist 
    reopened_count      = models.PositiveIntegerField(default=0,null=False, blank=False)
    completed           = models.BooleanField(default=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
 

class SubTasks(models.Model):
    TRASH_With_CHOICES = [
        ('Manually', 'Manually'),
        ('Relatively_task', 'Relatively_task'),
        ('Relatively_checklist', 'Relatively_checklist')
    ]
    Task                = models.ForeignKey(Tasks,on_delete=models.CASCADE,null=True,blank=True,default=None)
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='task_created_by')
    assign_to           = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='assign_to_task_checklist')
    task_topic          = models.CharField(max_length=300,null=True,blank=True)
    due_date_existing   = models.CharField(max_length=200,null=True,blank=True)
    due_date_latest_existing = UTCDateTimeField(null=True,blank=True)
    due_date            = models.DateTimeField(null=True,blank=True)
    task_description    = models.CharField(max_length=200,null=True,blank=True)
    urgent_status       = models.BooleanField(default=False)
    completed           = models.BooleanField(default=False)
    status              = models.ForeignKey(TaskStatus,on_delete=models.SET_NULL, null=True, blank=True)
    inTrash             = models.BooleanField(default=False)
    trashed_with        = models.CharField(max_length=20, choices=TRASH_With_CHOICES, default = None ,null=True, blank=True) # New field to track how trashed the checklist 
    reopened_count      = models.PositiveIntegerField(default=0,null=False, blank=False)
    start_date          = models.DateTimeField(default=timezone.now)
    end_date            = models.DateTimeField(null=True,blank=True)
    system_assigned     = models.BooleanField(default=True)
    
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


    def save(self, *args, **kwargs):

        if not self.status and self.created_by:
            get_org_id = EmployeePersonalDetails.objects.get(user_id=self.created_by.id)
            task_status = TaskStatus.objects.filter(organization=get_org_id.organization_id,fixed_state="Pending").order_by('order').first()

            if not task_status:

                raise ValueError("Default TaskStatus not found for the user.")
            else:
                self.status = task_status
                
                 
            
        
        if not self.start_date:
            self.start_date = timezone.now()

        super().save(*args, **kwargs)
        
        # Assign to users from the parent Task if available
        # if not self.pk:  # Check if this is a new instance
        #     if self.Task:
        #         assigned_users = self.Task.assign_to.all()
        #         self.assign_to.set(assigned_users)

        # super().save(*args, **kwargs)  # Call save again to save the changes


class SubTaskChild(models.Model):
    TRASH_With_CHOICES = [
        ('Manually', 'Manually'),
        ('Relatively_task', 'Relatively_task'),
        ('Relatively_checklist', 'Relatively_checklist')
    ]
    subtasks            = models.ForeignKey(SubTasks,on_delete=models.CASCADE,null=False,blank=False,default=None)
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='subtask_child_created_by')
    assign_to           = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='assign_to_subtask_child')
    task_topic          = models.CharField(max_length=300,null=True,blank=True)
    due_date            = models.DateTimeField(null=True,blank=True)
    task_description    = models.CharField(max_length=200,null=True,blank=True)
    urgent_status       = models.BooleanField(default=False)
    completed           = models.BooleanField(default=False)
    status              = models.ForeignKey(TaskStatus,on_delete=models.SET_NULL, null=True, blank=True)
    inTrash             = models.BooleanField(default=False)
    trashed_with        = models.CharField(max_length=20, choices=TRASH_With_CHOICES, default = None ,null=True, blank=True) # New field to track how trashed the checklist 
    reopened_count      = models.PositiveIntegerField(default=0,null=False, blank=False)
    start_date          = models.DateTimeField(default=timezone.now)
    end_date            = models.DateTimeField(null=True,blank=True)
    system_assigned     = models.BooleanField(default=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):

        if not self.status and self.created_by:
            get_org_id = EmployeePersonalDetails.objects.get(user_id=self.created_by.id)
            task_status = TaskStatus.objects.filter(organization=get_org_id.organization_id,fixed_state="Pending").order_by('order').first()

            if not task_status:

                raise ValueError("Default TaskStatus not found for the user.")
            else:
                self.status = task_status
                
                 
            
        
        if not self.start_date:
            self.start_date = timezone.now()

        super().save(*args, **kwargs)

class SocialMedia(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    platform            = models.CharField(max_length=20,null=False,blank=False)
    active              = models.BooleanField(default=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class MetaAuth(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    metaplatform        = models.CharField(max_length=20,null=False,blank=False,default="Facebook")
    status_login        = models.BooleanField(null=True,default=False)
    metaplatform_id     = models.TextField(null=False,blank=False)
    username            = models.TextField(null=True,blank=True)
    token               = models.TextField(null=True,blank=True)
    profile_picture     = models.CharField(max_length=1000,null=True,blank=True)
    other_field         = models.TextField(null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class GmailAuth(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    platform            = models.CharField(max_length=20,null=False,blank=False,default="Google")
    status_login        = models.BooleanField(null=True,default=False)
    access_token        = models.TextField(null=True,blank=True)
    expires_at          = models.CharField(max_length=200,null=True,blank=True) 
    expires_in          = models.CharField(max_length=100,null=True,blank=True)  
    scope               = models.CharField(max_length=200,null=True,blank=True) 
    state               = models.CharField(max_length=200,null=True,blank=True)  
    token_type          = models.CharField(max_length=50,null=True,blank=True) 
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class OutlookAuth(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    platform            = models.CharField(max_length=20,null=False,blank=False,default="Outlook")
    status_login        = models.BooleanField(null=True,default=False)
    outlook_id          = models.TextField(null=False,blank=False)
    username            = models.TextField(null=True,blank=True)
    token               = models.TextField(null=True,blank=True)
    profile_picture     = models.CharField(max_length=1000,null=True,blank=True)
    other_field         = models.TextField(null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)



class TelegramAuth(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    platform            = models.CharField(max_length=20,null=False,blank=False,default="Telegram")
    status_login        = models.BooleanField(null=True,default=False)
    mobile_number       = models.TextField(primary_key=True, null=False, blank=False)
    username            = models.TextField(null=True,blank=True)
    otp                 = models.CharField(null=True,blank=True,max_length=10)
    password            = models.CharField(null=True,blank=True,max_length=100)
    other_field         = models.TextField(null=True,blank=True)
    session_file        = models.CharField(null=True,blank=True,max_length=2000)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class TeleUser(models.Model):
    telegram_auth       = models.ForeignKey(TelegramAuth, on_delete=models.CASCADE, to_field='mobile_number', null=False, blank=False)
    username            = models.TextField(null=True, blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
    
       
class Notification(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    notification_to     = models.ManyToManyField(User, null=True, blank=True, default=None, related_name='notification_to')
    where_to            = models.CharField(max_length=20,null=False,blank=False,default="nowhere")           
    notification_msg    = models.TextField(null=False,blank=False)
    other_id            = models.PositiveIntegerField(null=True, blank=True)
    action_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    action_id           = models.PositiveIntegerField(null=True, blank=True)
    action_object       = GenericForeignKey('action_content_type', 'action_id')
    is_seen             = models.BooleanField(default=False)
    is_clicked          = models.BooleanField(default=False)  # field for tracking if notification icon is clicked
    other_details       = models.CharField(max_length=50,null=True,blank=True) # used in rescheduling
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    

@receiver(post_save, sender=Notification)
def notification_handler(sender, instance, created, **kwargs):
    
    if created:
        print("Printed Notification")
        channel_layer = get_channel_layer()
        data = {
            'notification_msg': instance.notification_msg,
            'created_at': str(instance.created_at),
            'is_seen': instance.is_seen,
            'where_to': instance.where_to,
            'action_id': instance.action_id,
            'other_id': instance.other_id,
            'other_details':instance.other_details,
            'is_clicked': instance.is_clicked
            # Add other fields as needed
        }
        
        # print(f'User Channel Name: user_{instance.notification_to.id}')
        notification_to_users = instance.notification_to.all()
        for usere in notification_to_users:

            async_to_sync(channel_layer.group_send)(
                f'user_{usere.id}', {
                    'type': 'notification_added',
                    'value': data
                }
            )

def serialize_notifications(notifications):

        # Serialize Notification objects to a format suitable for sending over WebSocket
    serialized_notifications = []
    for notification in notifications:
        serialized_notification = {
            'notification_msg': notification.notification_msg,
            'created_at': str(notification.created_at),
            'is_seen': notification.is_seen,
        }
        serialized_notifications.append(serialized_notification)
    return serialized_notifications
class Redirect_to(models.Model):
    notification        = models.ForeignKey(Notification,on_delete=models.CASCADE,null=False,blank=False)
    link                = models.TextField(null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class SalesStatus(models.Model):
    user_admin          = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    organization        = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=True,blank=True)
    status_name         = models.CharField(max_length=25,null=False,blank=False)
    fixed_state         = models.CharField(max_length=25,null=False,blank=False,default=None,choices = (("Pending", "Pending"),("Assigned", "Assigned"), ("Contacted", "Contacted"),("InProgress", "InProgress"),("Qualified", "Qualified"),("Lost", "Lost"),("PendingApproval", "PendingApproval"), ("Won", "Won")))
    color               = models.CharField(max_length=10,null=True,blank=True)
    order               = models.IntegerField(null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
class SalesLead(models.Model):
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name='lead_created_by')
    assign_to           = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='lead_assign_to')
    lead_source         = models.CharField(max_length=50,null=True,blank=True)
    reference_source    = models.CharField(max_length=50,null=True,blank=True)
    urgent_status       = models.BooleanField(default=False)
    lead_created_date   = models.DateTimeField(default=timezone.now,null=True,blank=True)
    next_followup_date  = models.DateTimeField(null=True,blank=True )
    first_name          = models.CharField(max_length=50,null=True,blank=True)
    last_name           = models.CharField(max_length=50,null=True,blank=True)
    email               = models.CharField(max_length=50,null=True,blank=True)
    phone_number        = models.CharField(max_length=15, null=True, blank=True)
    address             = models.TextField(null=True, blank=True)
    company_name        = models.CharField(max_length=50,null=True,blank=True)
    designation         = models.CharField(max_length=50,null=True,blank=True)
    budget              = models.CharField(max_length=50,null=True,blank=True)
    annual_income       = models.CharField(max_length=50,null=True,blank=True)
    status              = models.ForeignKey(SalesStatus,on_delete=models.SET_NULL, null=True, blank=True)
    notes               = models.TextField(null=True, blank=True)
    inTrash             = models.BooleanField(default=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
class SaleStatusTrack(models.Model):
    changed_by          = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False, default =None)
    sales_lead          = models.ForeignKey(SalesLead, on_delete=models.CASCADE, null=False, blank=False)
    from_status         = models.ForeignKey(SalesStatus,on_delete=models.SET_NULL, null=True, blank=True, related_name='from_status')
    to_status           = models.ForeignKey(SalesStatus,on_delete=models.SET_NULL, null=True, blank=True,related_name='to_status')
    from_status_date    = models.DateTimeField( null=True, blank=True)
    status_change_date  = models.DateTimeField(default=timezone.now)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class SalesAttachments(models.Model):
    sales_lead = models.ForeignKey(SalesLead, on_delete=models.CASCADE, null=False, blank=False)
    attachment = models.FileField(upload_to='employee/sales_attachments/', null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = AutoDateTimeField(default=timezone.now)

class SalesFollowUp(models.Model):
    user            = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False, default =None)
    sales_lead      = models.ForeignKey(SalesLead, on_delete=models.CASCADE, null=False, blank=False)
    followup_date   = models.DateTimeField(default=timezone.now)
    description     = models.TextField(null=True, blank=True)
    notes           = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = AutoDateTimeField(default=timezone.now)


class SalesLeadSpecialAccess(models.Model):

    ACCESS_CHOICES = [
        ('view', 'view'),
        ('edit', 'edit'),
    ]

    user                = models.ForeignKey(User, on_delete=models.CASCADE)
    access_to           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_to_user')
    access_type         = models.CharField(max_length=4, choices=ACCESS_CHOICES, default="view")
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class PersonalStatus(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    status_name         = models.CharField(max_length=25,null=False,blank=False)
    fixed_state         = models.CharField(max_length=25,null=False,blank=False,default="Pending",choices = (("Pending", "Pending"),("InProgress", "InProgress"), ("InReview", "InReview"),("OnHold", "OnHold"),("Completed", "Completed")))
    order               = models.IntegerField(null=True,blank=True)
    color               = models.CharField(max_length=10,null=True,blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
class PersonalTask(models.Model):
    user_id                = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    task_topic          = models.CharField(max_length=300,null=False,blank=False)
    # due_date            = models.CharField(max_length=100,null=True,blank=True)
    due_date            = models.DateTimeField(null=True,blank=True)
    task_description    = models.CharField(max_length=500,null=True,blank=True)
    urgent_status       = models.BooleanField(default=False)
    completed           = models.BooleanField(default=False)
    status              = models.ForeignKey(PersonalStatus,on_delete=models.SET_NULL, null=True, blank=True)
    sequence            = models.CharField(max_length=100,null=True,blank=True)
    is_personal         = models.BooleanField(default=True)
    reopened_count      = models.PositiveIntegerField(default=0,null=False, blank=False)
    inTrash             = models.BooleanField(default=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        # If the task is being created and the status is not set, set it to the default for the user
        if not self.status and self.user_id:
            personal_status = PersonalStatus.objects.filter(user_id=self.user_id, fixed_state="Pending").order_by('order').first()
            if not personal_status:
                personal_status = PersonalStatus.objects.filter(user_id=self.user_id, fixed_state="InProgress").order_by('order').first()
            
            self.status = personal_status



        super().save(*args, **kwargs)
    

class PersonalTaskAttachments(models.Model):
    personaltask_id = models.ForeignKey(PersonalTask, on_delete=models.CASCADE, null=False, blank=False)
    attachment = models.FileField(upload_to='employee/personal_attachments/', null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = AutoDateTimeField(default=timezone.now)
class Medicines(models.Model):
    medicine_name       = models.TextField(null=False, blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    

class BgImage(models.Model):
    user                = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, unique=True)
    image               = models.ImageField(upload_to='employee/bg_images/', null=False, blank=False, default=None)
    index               = models.PositiveIntegerField(null=True, blank=True)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
class BusinessCard(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE)
    card_image      = models.ImageField(upload_to='employee/BusinessCard/card/', null=True, blank=True)
    profile_image   = models.ImageField(upload_to='employee/BusinessCard/profile/', null=True, blank=True)
    card_name       = models.CharField(max_length=100, null=True, blank=True)
    full_name       = models.CharField(max_length=100, null=True, blank=True)
    designation     = models.CharField(max_length=30, null=True, blank=True)
    phone_number    = models.CharField(max_length=14, null=True, blank=True)
    email           = models.EmailField(null=True, blank=True)
    company_name    = models.CharField(max_length=100, null=True, blank=True)
    website         = models.CharField(max_length=30, null=True, blank=True)
    address         = models.CharField(max_length=100, null=True, blank=True)
    other           = models.CharField(max_length=100, null=True, blank=True)
    created_at      = models.DateTimeField(default=timezone.now)
    updated_at      = AutoDateTimeField(default=timezone.now)


class UserFilters(models.Model):
    user                 = models.ForeignKey(User, on_delete=models.CASCADE, unique = True)
    myboard_view         = models.CharField(max_length=25,null=False,blank=False,default="Kanban",choices = (("Kanban", "Kanban"),("List", "List")))
    custom_board_view    = models.CharField(max_length=25,null=False,blank=False,default="Kanban",choices = (("Kanban", "Kanban"),("List", "List")))
    personal_board_view  = models.CharField(max_length=25,null=False,blank=False,default="Kanban",choices = (("Kanban", "Kanban"),("List", "List")))
    sales_board_view     = models.CharField(max_length=25,null=False,blank=False,default="Kanban",choices = (("Kanban", "Kanban"),("List", "List")))
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
# not related to user this is only for development
class ExtAvailableSlots(models.Model):
    user_email           = models.EmailField(null=False, blank=False)
    date                 = models.DateField(null =True, blank=True)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
class ExtAvailableSlotsTime(models.Model):
    ext_available_slots  = models.ForeignKey(ExtAvailableSlots, on_delete=models.CASCADE,null=False,blank=False)
    time_slot            = models.CharField(max_length=25,null=False,blank=False)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
class ProjectUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    work_file_name = models.CharField(max_length=100, null=False, blank=False)
    
    def upload_to_user_directory(instance, filename):
        # Upload to a user-specific subfolder in the 'project_work_file' directory
        return f'employee/project_work_file/{instance.user_id}/{filename}'

    work_file = models.FileField(upload_to=upload_to_user_directory, null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = AutoDateTimeField(default=timezone.now)


class DueRequest(models.Model):
    sender               = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    receiver             = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE, default=None)
    task                 = models.ForeignKey(Tasks, on_delete=models.CASCADE, default = None,  null = True, blank =True)
    subtasks             = models.ForeignKey(SubTasks, on_delete=models.CASCADE, default = None, null = True, blank =True)
    subtaskchild         = models.ForeignKey(SubTaskChild, on_delete=models.CASCADE, default = None,  null = True, blank =True)
    current_due_date     = models.DateTimeField(null=True,blank=True)
    proposed_due_date    = models.DateTimeField(null=True,blank=True)
    status               = models.CharField(max_length=20, choices=(('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')), default='pending')
    inTrash              = models.BooleanField(default=False)             
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)


class GmailEmail(models.Model):
    user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    email               = models.EmailField(null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)



# class OutsiderUser(models.Model):
#     email               = models.EmailField(null=False,blank=False)
#     is_onboarded        = models.BooleanField(default=False) 
#     created_at          = models.DateTimeField(default=timezone.now)
#     updated_at          = AutoDateTimeField(default=timezone.now) 
    

# class BoardAccess(models.Model):
#     user_id             = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)

# class OrganizationWorkSchedule(models.Model):
#     pass

class OrganizationWorkSchedule(models.Model):
    organization        = models.ForeignKey(OrganizationDetails, on_delete=models.CASCADE)
    start_time          = models.TimeField()
    end_time            = models.TimeField()
    working_hours       = models.CharField(max_length=50, null=True, blank=True)
    
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
class Weekday(models.Model):
    organizationworkschedule = models.ForeignKey(OrganizationWorkSchedule, on_delete=models.CASCADE)
    WEEKDAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    name                 = models.CharField(max_length=10, choices=WEEKDAY_CHOICES)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    

class CalenderReminder(models.Model):
    user                 = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_with_users    = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='shared_with_users')
    title                = models.TextField(null=False,blank=False)
    category             = models.CharField(max_length=15,null=True,blank=True)
    subcategory          = models.CharField(max_length=15, null=True,blank=True)
    from_datetime        = models.DateTimeField(null=True, blank=True, default=timezone.now)
    to_datetime          = models.DateTimeField(null=True, blank=True)
    description          = models.TextField(null=True,blank=True)
    platform_id          = models.PositiveIntegerField(default= None, null=True, blank=True)
    completed            = models.BooleanField(default=False)
    content_type         = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True,blank=True)
    object_id            = models.PositiveIntegerField(null=True,blank=True)
    content_object       = GenericForeignKey('content_type', 'object_id')
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)






class CalenderReminderTest(models.Model):
    user                 = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_with_users    = models.ManyToManyField(User,null=True, blank=True, default=None, related_name='shared_with_users_test')
    title                = models.TextField(null=False,blank=False)
    category             = models.CharField(max_length=15,null=True,blank=True)
    subcategory          = models.CharField(max_length=15, null=True,blank=True)
    from_datetime        = models.DateTimeField(null=True, blank=True, default=timezone.now)
    to_datetime          = models.DateTimeField(null=True, blank=True)
    description          = models.TextField(null=True,blank=True)
    platform_id          = models.TextField(default= None, null=True, blank=True)
    content_type         = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True,blank=True)
    object_id            = models.PositiveIntegerField(null=True,blank=True)
    content_object       = GenericForeignKey('content_type', 'object_id')
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)

class UserWorkSchedule(models.Model):
    user                 = models.ForeignKey(User, on_delete=models.CASCADE)
    date                 = models.DateField(null=True, blank=True,default=date.today)
    working_hours        = models.CharField(max_length=50, null=True, blank=True)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
    
    
class UserWorkSlot(models.Model):
    user_work_schedule     = models.ForeignKey(UserWorkSchedule, on_delete=models.CASCADE)
    slot                 = models.CharField(max_length=15)
    freeze               = models.BooleanField(default=False)
    reschedule           = models.BooleanField(default=False)
    # Generic ForeignKey fields
    content_type         = models.ForeignKey(ContentType, on_delete=models.CASCADE,null=True,blank=True)
    object_id            = models.PositiveIntegerField(null=True,blank=True)
    content_object       = GenericForeignKey('content_type', 'object_id')
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
    

# class Policies(models.Model):
#     user                 = models.ForeignKey(User, on_delete=models.CASCADE)
#     policy_for           = models.CharField(max_length=20,null=True,blank=True)
#     person_name          = models.CharField(max_length=100,null=True,blank=True)
#     date_of_birth        = models.DateField(null=True, blank=True)
#     disease_description  = models.TextField(null=True,blank=True)
#     created_at           = models.DateTimeField(default=timezone.now)
#     updated_at           = AutoDateTimeField(default=timezone.now)


class Policies(models.Model):
    user                            = models.ForeignKey(User, on_delete=models.CASCADE)
    organization                    = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=True,blank=True)
    # Policy Details
    policy_category                 = models.CharField(max_length=10, choices=[('Existing', 'Existing'), ('New', 'New')])
    policy_number                   = models.CharField(max_length=20, unique=True, null=True, blank=True)
    policy_name                     = models.CharField(max_length=100, null=True, blank=True)
    insurance_provider_name         = models.CharField(max_length=100, null=True, blank=True)
    policy_type                     = models.CharField(max_length=50,null=True, blank=True, choices=[('individual', 'Individual'), ('family', 'Family'), ('group', 'Group')])
    start_date                      = models.DateField(null=True, blank=True)
    end_date                        = models.DateField(null=True, blank=True)
    policy_status                   = models.CharField(max_length=20,null=True, blank=True, choices=[('active', 'Active'), ('inactive', 'Inactive'), ('expired', 'Expired')])

    # Policyholder Information
    policyholder_name               = models.CharField(max_length=100)
    policyholder_dob                = models.DateField()
    policyholder_gender             = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    policyholder_address            = models.TextField()
    policyholder_contact_number     = models.CharField(max_length=15)
    policyholder_email_address      = models.EmailField()

    # Coverage Details
    coverage_amount                 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Premium Details
    premium_amount                  = models.DecimalField(max_digits=16, null=True, blank=True, decimal_places=2)
    payment_frequency               = models.CharField(max_length=20, null=True, blank=True, choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annually', 'Annually')])
    next_payment_due_date           = models.DateField( null=True, blank=True)

    # Beneficiary Information
    beneficiary_names               = models.TextField(null=True, blank=True)
    beneficiary_relationships       = models.TextField(null=True, blank=True)
    beneficiary_contact_info        = models.TextField(null=True, blank=True)
    beneficiary_dob                 = models.DateField(null=True, blank=True)
    beneficiary_gender              = models.CharField(max_length=10, null=True, blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])

    # Policy Documents
    policy_document                 = models.FileField(upload_to='employee/policy_documents/', null=True, blank=True)
    identification_proof            = models.FileField(upload_to='employee/policy_documents/id_proof/', null=True, blank=True)
    medical_report                  = models.FileField(upload_to='employee/policy_documents/medical_report/', null=True, blank=True)

    created_at                      = models.DateTimeField(default=timezone.now)
    updated_at                      = AutoDateTimeField(default=timezone.now)
 
class InsuredMember(models.Model):
    policy                          = models.ForeignKey(Policies, on_delete=models.CASCADE, related_name='insured_members')
    name                            = models.CharField(max_length=100)
    dob                             = models.DateField()
    gender                          = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    relationship_to_policyholder    = models.CharField(max_length=50)
    created_at                      = models.DateTimeField(default=timezone.now)
    updated_at                      = AutoDateTimeField(default=timezone.now)
class PolicyDocument(models.Model):
    policy                          = models.ForeignKey(Policies, on_delete=models.CASCADE, related_name='documents')
    document_name                   = models.CharField(max_length=100)
    document_file                   = models.FileField(upload_to='employee/policy_documents/other_documents/')
    created_at                      = models.DateTimeField(default=timezone.now)
    updated_at                      = AutoDateTimeField(default=timezone.now)

class ExtensionMeetingDateOptions(models.Model):
    user                 = models.ForeignKey(User, on_delete=models.CASCADE)
    date                 = models.DateField(null=True, blank=True,default=date.today)
    platform             = models.CharField(max_length=10, null = True, blank = True)
    added_date           = models.DateTimeField(default=timezone.now)
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)
    
    
    
class ExtensionDateSlot(models.Model):
    extension_meeting_date_options     = models.ForeignKey(ExtensionMeetingDateOptions, on_delete=models.CASCADE)
    slot                 = models.CharField(max_length=20)
    freeze               = models.BooleanField(default=False)
    # Generic ForeignKey fields
    content_type         = models.ForeignKey(ContentType, on_delete=models.CASCADE,null=True,blank=True)
    object_id            = models.PositiveIntegerField(null=True,blank=True)
    content_object       = GenericForeignKey('content_type', 'object_id')
    created_at           = models.DateTimeField(default=timezone.now)
    updated_at           = AutoDateTimeField(default=timezone.now)


class OutsiderUser(models.Model):
    added_by            = models.ForeignKey(User,on_delete=models.CASCADE,related_name='added_by_id', db_column='added_by_id', null=False,blank=False)
    secondary_adders    = models.ManyToManyField(User, null=True, blank=True, default=None, related_name='secondary_adders')
    organization        = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,related_name='organization_id', db_column='organization_id', null=True,blank=True)
    approved_by         = models.ForeignKey(User,on_delete=models.CASCADE,related_name='approved_by_id', db_column='approved_by_id', null=True,blank=True)
    approved_date       = models.DateTimeField(null = True, blank= True)
    approval_user_role  = models.CharField(max_length=20,null=True,blank=True, default= "Employee")
    related_id          = models.ForeignKey(User,on_delete=models.CASCADE,related_name='related_id', db_column='related_id', null=True,blank=True)
    employee_id         = models.TextField(null=True,blank=True)
    profile_image       = models.ImageField(upload_to='employee/outsider/profile/', null=True, blank=True)
    gender              = models.CharField(max_length= 20, null =True, blank = True)
    department          = models.CharField(max_length= 30, null =True, blank = True)
    designation         = models.CharField(max_length= 30, null =True, blank = True)
    dob                 = models.DateField(null = True, blank= True)
    token               = models.CharField(max_length=30,null=True,blank=True)
    email               = models.EmailField(null=False,blank=False)
    token               = models.CharField(max_length=100,null=False,blank=False)
    processed           = models.CharField(max_length= 20, null=True, blank=True, choices = ((3, "3"),(2, "2"),(1, "1"),(0, "0")) , default =0) 
    verified            = models.CharField(max_length= 20, null=True, blank=True, choices = ((2, "2"),(1, "1"),(0, "0")) , default =0)
    invited_date        = models.DateTimeField(default=timezone.now)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now) 

    def save(self, *args, **kwargs):
        self.email = self.email.lower()  # Convert email to lowercase before saving
        
        super().save(*args, **kwargs)



class TaskSpecialAccess(models.Model):

    ACCESS_CHOICES = [
        ('view', 'view'),
        ('edit', 'edit'),
    ]

    user                = models.ForeignKey(User, on_delete=models.CASCADE)
    access_to           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_to')
    access_type         = models.CharField(max_length=4, choices=ACCESS_CHOICES, default="view")
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class BoardPermission(models.Model):
    user                = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions')
    access_to           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_permissions_to')
    board               = models.ForeignKey(Board, on_delete=models.CASCADE)
    can_view_board      = models.BooleanField(default=True)
    can_view_checklists = models.BooleanField(default=False)
    checklist_permissions = models.ManyToManyField(Checklist, blank=True, related_name='checklist_permissions')
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class TaskInBoardPermission(models.Model):
    user                = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_permissions')
    access_to           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_access_permissions_to')
    board               = models.ForeignKey(Board, on_delete=models.CASCADE)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    

class ReminderToSchedule(models.Model):
    user                = models.ForeignKey(User, on_delete=models.CASCADE)
    # Generic ForeignKey fields
    content_type        = models.ForeignKey(ContentType, on_delete=models.CASCADE,null=True,blank=True)
    object_id           = models.PositiveIntegerField(null=True,blank=True)
    content_object      = GenericForeignKey('content_type', 'object_id')
    calendar_reminder   = models.ForeignKey(CalenderReminder, on_delete=models.CASCADE, related_name='reminder_schedules', null=True, blank=True) #not user yet
    scheduled_time      = models.DateTimeField(default=timezone.now)  
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)


class TestSavedTemplate(models.Model):
    user                = models.ForeignKey(User, on_delete=models.CASCADE)
    category            = models.ForeignKey(Category,on_delete=models.CASCADE,null=False,blank=False)
    template            = models.ManyToManyField(Template,null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    

class SavedCategory(models.Model):
    user                = models.ForeignKey(User, on_delete=models.CASCADE)
    board               = models.ForeignKey(Board,on_delete=models.CASCADE,null=True,blank=True)
    name                = models.CharField(max_length=100,null=False,blank=False)  
    blank               = models.BooleanField(default=False)                                                                                                       
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
 
class SavedTemplates(models.Model):
    category            = models.ForeignKey(SavedCategory,on_delete=models.CASCADE,null=False,blank=False, related_name='saved_category')
    template_name       = models.CharField(max_length=100,null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)
    
class SavedTemplateChecklist(models.Model):
    template            = models.ForeignKey(SavedTemplates,on_delete=models.CASCADE,null=False,blank=False, related_name='saved_checklist')
    name                = models.CharField(max_length=100,null=False,blank=False,validators=[validate_String_Length])
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)

class SavedTemplateTaskList(models.Model):
    checklist           = models.ForeignKey(SavedTemplateChecklist,on_delete=models.CASCADE,null=False,blank=False, related_name='saved_task')
    task_name           = models.CharField(max_length=600,null=False,blank=False)
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = AutoDateTimeField(default=timezone.now)