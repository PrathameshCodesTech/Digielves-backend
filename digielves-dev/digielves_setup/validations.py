# importing validationerror
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen
from django.core.exceptions import ValidationError
import re
from PIL import Image
import datetime

from digielves_setup.models import  *



# creating a validator function
def is_valid_mail(email):
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') # regex pattern to match email addresses
    match = pattern.match(email)
    if match:
        return True
    else:
        raise ValidationError("Email address is not valid.")

    


def is_valid_employee_id(employee_id):
    employee_id_pattern = re.compile(r'^[A-Za-z0-9.-@]+$')
    if bool(employee_id_pattern.match(employee_id)):
        return True
    else:
        raise ValidationError("Employee id is not valid.")


def is_valid_name(name):
    name_pattern = re.compile(r'^[A-Za-z]+(?:\s[A-Za-z]+)?$')
    if bool(name_pattern.match(name)):
        return True
    else:
        raise ValidationError("Name is not valid.")

def is_valid_phone(phone_number):
    # remove any whitespace or hyphens from the phone number
    print(phone_number)
    phone_number = re.sub(r'\s|-', '', phone_number)
    # check if the phone number is a valid format
    if not re.match(r'^\d{10}$', phone_number):
        raise ValidationError("Invalid Phone Number")
    return True


def validate_policy_number(policy_number):
    policy_number_pattern = r'^[A-Z]{2}-\d{10}$'

    if not re.match(policy_number_pattern, policy_number):
        raise ValueError('Invalid policy number')

def is_valid_image(file_path):
    try:
        img = Image.open(file_path)
        img.verify()
        return True
    except Exception as e:
        print(f"{file_path} is not a valid image file: {e}")
        raise ValidationError("Please enter a valid Image")

def validate_String_Length(str):
    max_length = 20
    min_length = 2
    if str!=None or str !="":
        if len(str) > max_length:
            raise ValidationError(f"String should not exceed {max_length} characters.")
        elif len(str) < min_length:
            raise ValidationError(f"String should not less than {min_length} characters.")
        else:
            return True
    else:
        return True



def is_valid_password(password):
    # check the length of the password
    print(password)
    if len(password) < 8 or len(password) == 0:
        raise ValidationError("Password length shoud be greater than 8")
    # check if the password contains at least one uppercase letter
    if not any(c.isupper() for c in password):
        raise ValidationError("Password should contain a uppercase letter")
    # check if the password contains at least one lowercase letter
    if not any(c.islower() for c in password):
        raise ValidationError("Password should contain a lowercase letter")
    # check if the password contains at least one digit
    if not any(c.isdigit() for c in password):
        raise ValidationError("Password should contain a digit")
    # check if the password contains at least one special character
    if not any(c in "!@#$%^&*()-+?_=,<>/:" for c in password):
        raise ValidationError("Password should contain a special character")
    return True



def validate_task(value):
    if not Tasks.objects.filter(pk=value).exists():
        raise ValidationError("Invalid task.")
    else:
        return True
    
def validate_user(value):
    if not User.objects.filter(pk=value).exists():
        raise ValidationError("Invalid User ID.")
    else:
        return True

def validate_OrganizationDetails(value):
    if not OrganizationDetails.objects.filter(pk=value).exists():
        raise ValidationError("Invalid Organization ID.")
    else:
        return True 

def validate_DoctorConsultationDetails(value):
    if not DoctorConsultationDetails.objects.filter(pk=value).exists():
        raise ValidationError("Invalid Doctor Consultation Details ID.")
    else:
        return True 
    

def validate_DoctorConsultation(value):
    if not DoctorConsultation.objects.filter(pk=value).exists():
        raise ValidationError("Invalid Doctor Consultation ID.")
    else:
        return True 



def validate_EmployeePersonalDetails(value):
    if not EmployeePersonalDetails.objects.filter(pk=value).exists():
        raise ValidationError("Invalid EmployeePersonalDetails ID.")
    else:
        return True 

def validate_Template(value):
    if not Template.objects.filter(pk=value).exists():
        raise ValidationError("Invalid EmployeePersonalDetails ID.")
    else:
        return True 
    
def validate_Board(value):
    if not Board.objects.filter(pk=value).exists():
        raise ValidationError("Invalid Board ID.")
    else:
        return True 


def validate_Checklist(value):
    if not Checklist.objects.filter(pk=value).exists():
        raise ValidationError("Invalid Checklist ID.")
    else:
        return True 

def validate_TemplateChecklist(value):
    if not TemplateChecklist.objects.filter(pk=value).exists():
        raise ValidationError("Invalid TemplateChecklist ID.")
    else:
        return True 

def validate_age(value):
    try:
        age = int(value)
        if age < 0 or age > 120:
            raise ValidationError("Invalid age.")
    except ValueError:
        raise ValidationError("Age must be a valid integer.")

def validate_gender(value):
    valid_genders = ["Male", "Female", "Other"]
    if value not in valid_genders:
        raise ValidationError("Invalid gender.")
    
def validate_task_status(value):
    valid_statuses = ["Pending", "InProgress", "Completed"]
    if value not in valid_statuses:
        raise ValidationError("Invalid task status.")

def is_valid_url(url):
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return False
        response = urlopen(url)
        return True
    except URLError:
        raise ValidationError("Invalid URL")
    

def is_valid_string(field):
    # check if the field is a string
    print(field)
    if not isinstance(field, str):
        raise ValidationError("Invalid input not a string")

    # check if the field contains only alphabets or spaces
    if not all(c.isalpha() or c.isdigit() or  c.isspace() or  c in ('.','-',',', '/',"'" , '(', ')',':') for c in field) :
        print(all(c.isalpha() or c.isspace() for c in field))
        raise ValidationError("Invalid input chart")
    return True


def is_valid_weight(weight):
    try:
        weight = float(weight)
        if weight <= 0:
            raise ValidationError("Weight can not be zero")
    except ValidationError:
            raise ValidationError("Invalid weight")
    return True


def is_valid_height(height):
    try:
        height = float(height)
        if height <= 0:
            raise ValidationError("Height must be greater than 0.")
    except ValidationError:
        raise ValidationError("Height must be a number.")
    return True


def is_valid_pincode(pincode):
    if not pincode.isdigit():
        raise ValidationError("Invalid Pincode.")
    
    if len(pincode) < 3 and len(pincode) > 13:
        raise ValidationError("Pincode must be a >3 - digit number.")
    return True


def is_valid_latitude(latitude):
    pattern = r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)$'
    print(str(latitude))
    if bool(re.match(pattern, str(latitude))):
        return True
    raise ValidationError("Invalid Latitude.")

def is_valid_longitude(longitude):
    pattern = r'^[-+]?((1[0-7]|[1-9])?\d(\.\d+)?|180(\.0+)?)$'
    if bool(re.match(pattern, str(longitude))):
        return True
    raise ValidationError("Invalid Longitude.")


def is_valid_date_of_birth(date_str):
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.date.today()
        age = today.year - date_obj.year - ((today.month, today.day) < (date_obj.month, date_obj.day))
        print("Age____________________________")
        print(age)
        if age >= 18 and age <= 120: # Reasonable age range'
            return True
    except ValueError:
        raise ValidationError("Please enter valid age between 18 to 120")
    raise ValidationError("Please enter valid age between 18 to 120")



def is_valid_address(landmark_str):
    pattern = r'^\d+ \w+ \w+, \w+ \d{5}$'
    if bool(re.match(pattern, landmark_str)):
        raise ValidationError("Invalid input string")
    return True





def is_valid_commission(commission):
    if isinstance(commission, (float, int)):
        if commission >= 0:
            return True
    raise ValidationError("Invalid Commision.")


def is_valid_rating(rating, min_rating=0, max_rating=5):
    if isinstance(rating, (float, int)):
        if min_rating <= rating <= max_rating:
            return True
    raise ValidationError("Invalid rating.")

def is_valid_time(time_str, start_time=None, end_time=None):
    try:
        time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
    except ValueError:
        raise ValidationError("Invalid Time.")
    return True


def is_valid_price(price):
    if isinstance(price, (float, int)):
        if price >= 0:
            return True
    raise ValidationError("Invalid Price")


def is_valid_sessions(sessions):
    if isinstance(sessions, int):
        if sessions > 0:
            return True
    raise ValidationError("Invalid Count")


def is_valid_date(date_str):
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError("Invalid Date")
    return True


def is_valid_datetime(datetime_str, start_datetime=None, end_datetime=None):
    try:
        datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise ValidationError("Invalid DateTime")
    return True


def is_valid_bank_account_name(name):
    if not isinstance(name, str):
        raise ValidationError("Invalid Bank Account Name")
    if len(name) < 1 or len(name) > 100:
        raise ValidationError("Invalid Bank Account Name")
    if not all(c.isalpha() or c.isspace() or c == '-' for c in name):
        raise ValidationError("Invalid Bank Account Name")
    return True


def is_valid_bank_account_number(account_number):
    if not isinstance(account_number, str):
        raise ValidationError("Invalid Bank Account Number")
    if not account_number.isdigit():
        raise ValidationError("Invalid Bank Account Number")
    if len(account_number) < 6 or len(account_number) > 20:
        raise ValidationError("Invalid Bank Account Number")
    # additional validation rules specific to the bank can be added here
    return True

def is_valid_account_type(account_type):
    valid_types = ["savings", "current", "checking", "money market", "certificate of deposit"]
    if account_type.lower() in valid_types:
        raise ValidationError("Invalid Bank Account Type")
    # additional validation rules specific to the bank can be added here
    return True





def is_valid_ifsc(ifsc_code):
    pattern = re.compile("^[A-Z]{4}0[A-Z0-9]{6}$")
    if bool(re.match(pattern, ifsc_code)):
        raise ValidationError("Invalid IFSC Code.")
    return True



# password = input("Enter your password: ")

# # Password must be at least 8 characters long, contain at least one uppercase letter, 
# # one lowercase letter, one digit, and one special character.
# pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"

# if re.match(pattern, password):
#     print("Valid password")
# else:
#     print("Invalid password")