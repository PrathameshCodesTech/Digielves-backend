from django.urls import path

from outsider.views.onboard import OutsiderUserCreationClass




urlpatterns = [

    path(r'employee/outsider/invite/',OutsiderUserCreationClass.as_view({'post':'createOutsiderUser'})),
    path(r'employee/outsider/create/',OutsiderUserCreationClass.as_view({'post':'OutsideUserRegistraion'})),
    path(r'employee/outsider/create_password/',OutsiderUserCreationClass.as_view({'post':'createPasswordForOutsider'})),
    path(r'employee/outsider/add_details/',OutsiderUserCreationClass.as_view({'post':'addOutsiderDetails'})),
    path(r'employee/outsider/verify_user/',OutsiderUserCreationClass.as_view({'put':'verifyOutsiderUser'})),
 
]