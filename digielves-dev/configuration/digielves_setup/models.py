from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from digielves_setup.validations import *
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
# Create your models here.


# class UserManager(BaseUserManager):
#     use_in_migrations = True


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
    
class User(AbstractBaseUser, PermissionsMixin):
    email              = models.CharField(_('email'),max_length=100,unique=True,validators =[is_valid_mail])
    password           = models.CharField(max_length=150,null=True,blank=True, validators=[is_valid_password])
    firstname           = models.CharField(max_length=40,null=True,blank=True, validators=[is_valid_name])
    lastname           = models.CharField(max_length=40,null=True,blank=True, validators=[is_valid_name])
    phone_no           = models.CharField(max_length=10,null=True,blank=True, validators=[is_valid_phone])
    user_role          = models.CharField(max_length=25,null=False,blank=False, validators=[is_valid_string])
    user_type          = models.CharField(max_length=25,null=False,blank=False, validators=[is_valid_string])
    verified           = models.CharField(max_length= 20, null=True, blank=True, choices = ((2, "2"),(1, "1"),(0, "0")) , default =0)  
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)
    
    


    objects = UserManager()
    USERNAME_FIELD='email'
    REQUIRED_FIELD=[]
    




class Address(models.Model):
    user_id            = models.ForeignKey(User,on_delete=models.CASCADE, max_length=10,null=False,blank=False, unique=True)
    street_name        = models.CharField(max_length=40, null=True, blank=True, validators=[is_valid_address])
    land_mark          = models.CharField(max_length=50, null=True, blank=True, validators=[is_valid_address])
    city               = models.CharField(max_length=35, null=True, blank=True, validators=[is_valid_string])
    pincode            = models.CharField(max_length=14, null=True, blank=True,validators=[is_valid_pincode])
    state              = models.CharField(max_length=35, null=True, blank=True, validators=[is_valid_string])
    country            = models.CharField(max_length=40, null=True, blank=True, validators=[is_valid_string])
    Organization_code  = models.CharField(max_length=40, null=True, blank=True, validators=[is_valid_employee_id])
    description        = models.CharField(max_length=1500, null=True, blank=True, validators=[is_valid_string])
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)
    
  
class OrganizationDetails(models.Model):
    user_id            = models.ForeignKey(User,on_delete=models.CASCADE,max_length=10, null=False, blank=False, unique=True)
    name               = models.CharField(max_length=50, null=True,blank=True,validators=[is_valid_string])
    support_mail       = models.EmailField(max_length=50, null=True, blank=True,validators =[is_valid_mail])
    number_of_employee = models.IntegerField(max_length=12, null=True,blank=True, validators=[is_valid_sessions])
    number_of_subscription = models.IntegerField(max_length=12, null=True,blank=True, validators=[is_valid_sessions])  
    mail_extension     = models.CharField(max_length=10, null=True,blank=True,validators=[is_valid_string]) 
    organization_code  = models.CharField(max_length=100, null=True, blank=True,validators=[is_valid_string])
    org_description    = models.CharField(max_length=2500, null=True, blank=True,validators=[is_valid_string])
    org_website_link   = models.CharField(max_length=250, null=True, blank=True,validators=[is_valid_url]) 
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)


class EmployeePersonalDetails(models.Model):
    user_id            = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    organization_id    = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE,null=True,blank=True)
    employee_id        = models.CharField(max_length=10,null=True, blank=True, unique=True,validators=[is_valid_employee_id])
    firstname          = models.CharField(max_length=35,null=True,blank=True,validators=[is_valid_name])
    lastname           = models.CharField(max_length=35,null=True,blank=True,validators=[is_valid_name])

    date_of_birth      = models.CharField(max_length=20,null=True,blank=True,validators=[is_valid_date_of_birth])
    phone_no           = models.CharField(max_length=10,null=True,blank=True,validators =[is_valid_phone])
    job_title          = models.CharField(max_length=40,null=True,blank=True,validators=[is_valid_string])
    designation        = models.CharField(max_length=100,null=True, validators=[is_valid_string])
    department         = models.CharField(max_length=100,null=True, validators=[is_valid_string])

    gender             = models.CharField(max_length=15,null=True,blank=True, validators=[is_valid_string])
    work_location      = models.CharField(max_length=60,null=True,blank=True,validators=[is_valid_string])
    profile_picture    = models.CharField(max_length=50,null=True,blank=True,validators=[is_valid_image])
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)

class DoctorPersonalDetails(models.Model):
    user_id            = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,unique=True)
    firstname          = models.CharField(max_length=20,null=True,blank=True,validators=[is_valid_name])
    lastname           = models.CharField(max_length=20,null=True,blank=True,validators=[is_valid_name])

    phone_no          = models.CharField(max_length=10,null=True,blank=True,validators =[is_valid_phone])
    speciality         = models.CharField(max_length=200,null=True,blank=True,validators =[is_valid_string])
    license_no         = models.CharField(max_length=50,null=True,blank=True,validators =[is_valid_employee_id])
    year_of_experience = models.CharField(max_length=20,null=True,blank=True,validators =[is_valid_string])
    gender             = models.CharField(max_length=10,null=True,blank=True,validators =[is_valid_string])
    language_spoken    = models.CharField(max_length=20,null=True,blank=True,validators=[is_valid_string])
    profile_picture    = models.CharField(max_length=50,null=True,blank=True,validators =[is_valid_string])
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)


class UserCreation(models.Model):
    organization_id    = models.ForeignKey(OrganizationDetails,on_delete=models.CASCADE, max_length=10,null=False,blank=False)
    created_by         = models.ForeignKey(User,on_delete=models.CASCADE,related_name='creator_id', db_column='created_by_id', max_length=10,null=False,blank=False)
    user_id            = models.ForeignKey(User,on_delete=models.CASCADE, related_name='user_id',db_column='employee_user_id', max_length=10,null=True,blank=True)
    email              = models.CharField(max_length=100,null=False,blank=False,validators =[is_valid_mail])
    company_employee_id= models.CharField(max_length=50,null=True,blank=True, validators=[is_valid_employee_id])
    token              = models.CharField(max_length=100,null=False,blank=False, validators=[is_valid_string])
    processed          = models.CharField(max_length= 20, null=True, blank=True, choices = ((3, "3"),(2, "2"),(1, "1"),(0, "0")) , default =0) 
    verified           = models.CharField(max_length= 20, null=True, blank=True, choices = ((2, "2"),(1, "1"),(0, "0")) , default =0)  
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)


class DoctorAchivement(models.Model):
    user_id            = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    achivement_title   = models.CharField(max_length=50,null=True,blank=True)
    achivement_file    = models.CharField(max_length=104857,null=True,blank=True)
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)
   
    
class SubscribedApp(models.Model):
    user_id            = models.ForeignKey(User,on_delete=models.CASCADE,null=False,blank=False)
    app_name           = models.CharField(max_length=50,null=False,blank=False)
    app_logo           = models.CharField(max_length=50,null=True,blank=True)
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)


class DoctorConsultationDetails(models.Model):
    employee_id                  = models.ForeignKey(User,on_delete=models.CASCADE, db_column='employee_id', max_length=10,null=False,blank=False)
    gender                   = models.CharField(max_length=20,null=True,blank=True)
    full_name                = models.CharField(max_length=20,null=True,blank=True)
    relationship             = models.CharField(max_length=100,null=True,blank=True)
    blood_group             = models.CharField(max_length=100,null=True,blank=True)
    marital_status           = models.CharField(max_length=100,null=True,blank=True)
    age                      = models.CharField(max_length=100,null=True,blank=True)
    gender                   = models.CharField(max_length=100,null=True,blank=True)
    phone_no                = models.CharField(max_length=100,null=True,blank=True)
    created_at               = models.DateField(default=timezone.now)
    updated_at               = AutoDateTimeField(default=timezone.now)
    
class DoctorConsultation(models.Model):
    doctor_id                = models.ForeignKey(User,related_name='doctor_id', db_column='doctor_user_id',on_delete=models.CASCADE,null=False,blank=False)
    employee_id              = models.ForeignKey(User,related_name='employee_id',db_column='employee_user_id',on_delete=models.CASCADE,null=False,blank=False)
    communication_preference = models.CharField(max_length=20,null=True,blank=True)
    consultation_for         = models.ForeignKey(DoctorConsultationDetails,on_delete=models.CASCADE,null=False,blank=False)
    transcript               = models.CharField(max_length=20,null=True,blank=True)
    next_appointment         = models.CharField(max_length=20,null=True,blank=True)
    appointment_date         = models.CharField(max_length=100,null=True,blank=True)
    appointment_time         = models.CharField(max_length=100,null=True,blank=True)
    reschedule_appointment   = models.CharField(max_length=100,null=True,blank=True)
    reason_for_reschedule    = models.CharField(max_length=100,null=True,blank=True)
    confirmed                = models.CharField(max_length=100,null=True,blank=True, choices = ((2, "2"),(1, "1"),(0, "0")) , default =0)
    status                   = models.CharField(max_length=100,null=True,blank=True, default ="Booked")
    meeting_url              = models.CharField(max_length=100,null=True,blank=True)
    meeting_pref_type        = models.CharField(max_length=100,null=True,blank=True) 
    reschedule_by            = models.CharField(max_length=100,null=True,blank=True) 
    reports                  = models.CharField(max_length=100,null=True,blank=True)
    reason_for_consultation  = models.CharField(max_length=100,null=True,blank=True)
    reason_for_rejection     = models.CharField(max_length=100,null=True,blank=True)
    dignosis                 = models.CharField(max_length=100,null=True,blank=True)
    advice                   = models.CharField(max_length=100,null=True,blank=True)
    prescription_url         = models.CharField(max_length=100,null=True,blank=True)
    created_at               = models.DateField(default=timezone.now)
    updated_at               = AutoDateTimeField(default=timezone.now)



class DoctorPrescriptions(models.Model):
    consultation_id          = models.ForeignKey(DoctorConsultation,on_delete=models.CASCADE,null=True,blank=True)
    employee_id              = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    medicine_name            = models.CharField(max_length=30,null=True,blank=True)
    quantity                 = models.CharField(max_length=10,null=True,blank=True)
    doses                    = models.CharField(max_length=20,null=True,blank=True)
    dose_type                = models.CharField(max_length=20,null=True,blank=True)
    frequency                = models.CharField(max_length=20,null=True,blank=True)
    to_be_taken              = models.CharField(max_length=20,null=True,blank=True)
    consumption_type         = models.CharField(max_length=20,null=True,blank=True)

    created_at               = models.DateField(default=timezone.now)
    updated_at               = AutoDateTimeField(default=timezone.now)



class Insurance(models.Model):
    user_id                  = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True) 
    employee_id              = models.ForeignKey(EmployeePersonalDetails,on_delete=models.CASCADE,null=True,blank=True) 
    company_name             = models.CharField(max_length=50,null=True,blank=True,validators=[is_valid_string])
    policy_number            = models.CharField(max_length=20,null=True,blank=True,validators=[validate_policy_number])
    premium                  = models.CharField(max_length=10,null=True,blank=True)
    insurance_plan           = models.CharField(max_length=50,null=True,blank=True)
    type_of_policy           = models.CharField(max_length=20,null=True,blank=True)
    start_date               = models.DateField()
    end_date                 = models.DateField()
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)



class FamilyInsurance(models.Model):
    user_id                  = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True) 
    relation                 = models.CharField(max_length=200,null=True,blank=True)
    name                     = models.CharField(max_length=200,null=True,blank=True,validators=[is_valid_string])
    age                      = models.CharField(max_length=200,null=True,blank=True)
    gender                   = models.CharField(max_length=200,null=True,blank=True)
    policy_number            = models.CharField(max_length=200,null=True,blank=True, validators=[validate_policy_number])
    company_name             = models.CharField(max_length=200,null=True,blank=True)
    premium                  = models.CharField(max_length=200,null=True,blank=True)
    Insurance_plan           = models.CharField(max_length=200,null=True,blank=True)
    start_date               = models.DateField()
    end_date                 = models.DateField()
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)




class Tasks(models.Model):
    employee_id              = models.ForeignKey(EmployeePersonalDetails,on_delete=models.CASCADE,null=True,blank=True) 
    task_topic               = models.CharField(max_length=200,null=True,blank=True)
    due_date                 = models.CharField(max_length=200,null=True,blank=True)
    task_description         = models.CharField(max_length=200,null=True,blank=True)
    attachment               = models.CharField(max_length=200,null=True,blank=True)
    assign                   = models.CharField(max_length=200,null=True,blank=True)
    urgent_status            = models.CharField(max_length=200,null=True,blank=True)
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)




class SelfTask(models.Model):
    user_id                  = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True) 
    task_topic               = models.CharField(max_length=200,null=True,blank=True)
    due_date                 = models.CharField(max_length=200,null=True,blank=True)
    task_description         = models.CharField(max_length=200,null=True,blank=True)
    attachment               = models.CharField(max_length=1000,null=True,blank=True)
    created_at         = models.DateField(default=timezone.now)
    updated_at         = AutoDateTimeField(default=timezone.now)


