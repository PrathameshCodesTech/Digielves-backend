from django.urls import path
from employee.views.calender.birthday import BirthdayViewset




urlpatterns = [

    path(r'calender/get-birthdays/',BirthdayViewset.as_view({'get':'getBirthday'})),
    path(r'calender/add-birthday/',BirthdayViewset.as_view({'post':'add_birthday'})),
    path(r'calender/get-users-birthday/',BirthdayViewset.as_view({'get':'get_birthdays'})),
    path(r'calender/update-birthday/',BirthdayViewset.as_view({'put':'update_birthday'})),
    path(r'calender/delete-birthday/',BirthdayViewset.as_view({'delete':'Birthdaydelete'})),
    path(r'calender/send_wish/',BirthdayViewset.as_view({'post':'send_bd_wish'})),


]