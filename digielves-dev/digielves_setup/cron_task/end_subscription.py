

from digielves_setup.models import Notification, OrganizationDetails, User, notification_handler
from django.db.models import F
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType


def check_end_of_subscription():
    check_sub_end = OrganizationDetails.objects.filter(
    number_of_employee=F('number_of_subscription')
    )
    print(check_sub_end)
    user = User.objects.filter(user_role="Dev::Admin").first()
    
    
    for org_detail in check_sub_end:
        print(org_detail.id)
        print(org_detail.user_id.id)
        post_save.disconnect(notification_handler, sender=Notification)
        print("-----ahsayya")
        notification = Notification.objects.create(
            user_id=user,
            where_to="org",
            notification_msg = f"Important Notice: Your employee management subscription has reached its limit. Consider upgrading to accommodate more employees.",
            action_content_type=ContentType.objects.get_for_model(OrganizationDetails),
            action_id=org_detail.id  
        )
        print("-----namaa")
        notification.notification_to.set([org_detail.user_id.id])
        
        post_save.connect(notification_handler, sender=Notification)
        post_save.send(sender=Notification, instance=notification, created=True)


    
    




   