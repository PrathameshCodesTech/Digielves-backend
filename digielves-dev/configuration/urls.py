"""
URL configuration for configuration project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import re_path


schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
 

    path('api/admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/', include('digielves_setup.urls.address_urls')),
    path('api/', include('digielves_setup.urls.outlook_login_urls')),

    path('api/', include('digielves_setup.urls.registration_urls')),
    path('api/', include('digielves_setup.urls.login_urls')),
    path('api/', include('digielves_setup.urls.onboarding_urls')),
    path('api/', include('digielves_setup.urls.yahoo_login_urls')),
    path('api/', include('digielves_setup.urls.github_login_urls')),




    
    
    

    
    path('api/doctor/', include('doctor.urls.personal_details_urls')),
    path('api/doctor/', include('doctor.urls.achievement_urls')),
    path('api/doctor/', include('doctor.urls.consultation_urls')),
    path('api/doctor/', include('doctor.urls.prescription_urls')),
    path('api/doctor/', include('doctor.urls.doctor_slot_urls')),
    path('api/doctor/', include('doctor.urls.calender_urls')),

    
    path('api/organization/', include('organization.urls.organization_details_urls')),
    path('api/organization/', include('organization.urls.registration_urls')),
    path('api/organization/', include('organization.urls.organization_helpdesk_urls')),




    path('api/employee/', include('employee.urls.calender.teamsMeetingUrls')),


    path('api/employee/', include('employee.urls.personal_details_urls')),
    path('api/employee/', include('employee.urls.registration_urls')),
    path('api/employee/', include('employee.urls.doctor_consultation_urls')),
    path('api/employee/', include('employee.urls.template_urls')),
    path('api/employee/', include('employee.urls.template_checklist_urls')),
    path('api/employee/', include('employee.urls.template_checklist_task_urls')),
    path('api/employee/', include('employee.urls.board_urls')),
    path('api/employee/', include('employee.urls.board_checklist_urls')),
    path('api/employee/', include('employee.urls.task_urls')),
    path('api/employee/', include('employee.urls.attachment_urls')),
    path('api/employee/', include('employee.urls.task_action_urls')),
    path('api/employee/', include('employee.urls.task_chats_urls')),
    path('api/employee/', include('employee.urls.task_comments_urls')),
    path('api/employee/', include('employee.urls.board_checklist_task_urls')),
    path('api/employee/', include('employee.urls.users_urls')),
    path('api/employee/', include('employee.urls.task_checklist_urls')),
    path('api/employee/', include('employee.urls.task_checklist_task_urls')),
    path('api/employee/', include('employee.urls.helpdesk_urls')),
    path('api/employee/', include('employee.urls.calender.event_urls')),
    path('api/employee/', include('employee.urls.calender.meeting_urls')),
    path('api/employee/', include('employee.urls.calender.birthday_urls')),
    path('api/employee/', include('employee.urls.social_media.social_media_urls')),
    path('api/employee/', include('employee.urls.social_media.meta_auth_urls')),
    path('api/employee/', include('employee.urls.social_media.gmail_auth_urls')),
    path('api/employee/', include('employee.urls.social_media.telegram_auth_urls')),
    path('api/employee/', include('employee.urls.social_media.outlook_auth_urls')),
    path('api/employee/', include('employee.urls.calender.summery_urls')),
    path('api/employee/', include('employee.urls.notification_urls')),
    
    path('api/employee/', include('employee.urls.personal_board_urls')),
    path('api/employee/sales/', include('employee.urls.sales_lead_urls')),
     path('api/employee/', include('employee.urls.add_ons_urls')),
    
    path('api/admin_level/', include('admin_app.urls.admin_urls')),
    path('api/admin_level/', include('admin_app.urls.consultations_urls')),
    path('api/admin_level/task/', include('admin_app.urls.task_view_urls')),
    path('api/error/', include('admin_app.urls.send_error_urls')),

    path('api/profile/', include('digielves_setup.urls.profile_urls')),

    path('api/employee/', include('employee.urls.trash_urls')),
    path('api/employee/', include('employee.urls.bg_image_urls')),

    path('api/ai/', include('ai.urls.summery_urls')),
    path('api/ai/', include('ai.urls.audio_transcript_urls')),
    
    #  path('api/employee/', include('employee.urls.ai_model_urls')),
    path('api/organization/', include('organization.urls.hierarchy_urls')),
    
    path('api/organization/', include('organization.urls.organization_branch_urls')),
    
    path('api/organization/', include('organization.urls.work_schedule_urls')),
    
    path('api/for_check/', include('digielves_setup.urls.check_server_urls')),
    
    path('api/status/', include('organization.urls.task_status_urls')),
    path('api/sales/status/', include('organization.urls.sales_status_urls')),
    path('api/employee/', include('employee.urls.sales_lead_attachments_urls')),
    path('api/employee/', include('employee.urls.cards.business_card_urls')),
    path('api/employee/', include('employee.urls.filters.board_view_urls')),
    
    path('api/employee/', include('employee.urls.cards.birthday_card_urls')),
    
    path('api/employee/', include('employee.urls.cards.birthday_card_urls')),
    
    path('api/employee/custom_board/', include('employee.urls.project_upload_urls')),
    
    path('api/employee/personal/status/', include('employee.urls.personal_board.personal_status_urls')),
    
    path('api/employee/extension/', include('employee.urls.extension.slots_urls')),
    
    path('api/employee/', include('employee.urls.subtaskchild_urls')),
    
    path('api/employee/', include('employee.urls.request_urls')),
    
    path('api/employee/', include('employee.urls.work_schedule_urls')),
    
    path('api/employee/', include('employee.urls.calender.calender_urls')),
    
    path('api/', include('outsider.urls.onboard_urls')),
    path('api/', include('outsider.urls.outsider_urls')),
    
    path('api/employee/policy/', include('employee.urls.policy_urls')),
    path('api/organization/policy/', include('organization.urls.policy_urls')),
    
    
    # v1 for task
    
    path('api/v1/employee/', include('employee.urls.task_hierarchy.task_urls')),
    path('api/v1/employee/', include('employee.urls.task_hierarchy.task_checklist_urls')),
    path('api/v1/employee/', include('employee.urls.task_hierarchy.task_attachment_urls')),
    path('api/', include('employee.urls.external.registration')),
    
]  


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # For production, it's better to let Nginx handle this, but if needed:
    from django.views.static import serve
    urlpatterns += [
        re_path(r'^api/media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

