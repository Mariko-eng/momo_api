from django.urls import path
from .import views

urlpatterns = [
    path('', view=views.index),
    
    # Init Products
    path('collections/init/', view=views.initialize_collections_view),
    path('disbursements/init/', view=views.initialize_disbursements_view),
    path('remittances/init/', view=views.initialize_remittances_view),
    
    # Collections 
    path('collections/request_to_pay/', view=views.request_payment_view),
    path('collections/payment_notification/', view=views.request_payment_delivery_notification_view),
    path('collections/payment_status/', view=views.request_payment_status_inquiry_view),
    
    # Disbursements 


]
