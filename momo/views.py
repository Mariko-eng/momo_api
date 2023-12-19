from django.shortcuts import render
import uuid
import base64
import requests
import json
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .tasks import create_perioidic_print_task
from .models import Product, APIUser, AccessToken 
from .models import COLLECTIONS_PRODUCT
from .models import DISBURSEMENT_PRODUCT
from .models import REMITTANCE_PRODUCT
from django.conf import settings
from .models import SAND_BOX, PRODUCTION
from .shared import CALL_SUCCESS
from .shared import MomoUserProvisioning
from .shared import MomoCollectionService
from .shared import MomoDisbursementService
from .serializers import PaymentSerializer
from .serializers import PaymentDeliveryNotificationSerializer
from .serializers import PaymentStatusInquirySerializer
from .serializers import DisburseSerializer
from .serializers import RefundSerializer


@api_view(['GET', 'POST'])
def index(request):
    # create_perioidic_print_task()

    return Response({
        "message": "Weelcome to Momo API"
        })


@api_view(['POST'])
def initialize_collections_view(request):
    collection, created = Product.objects.get_or_create(
        name = "collections",
        product_type = COLLECTIONS_PRODUCT,
        primary_key = '9f6f6921c8bc455daedd5c828fae41fa',
        secondary_key = '463a8f9dd85c44bca140d6403d1333f2'
    )

    user = MomoUserProvisioning(collection)
    result = user.create_user()

    if result['status_code'] == 201:
        apiuser = APIUser.objects.get(id = result['api_user'])

        apikey_result = MomoUserProvisioning.generate_api_key(apiuser)
        if apikey_result['status_code'] == 201:
            return Response({"message": "Collection initialized successfully!"}, status=201)
        else:
            return Response({"message": result['data']} ,status=result['status_code'])
    else:
        return Response({"message": result['data']} , status=result['status_code'])


@api_view(['POST'])
def initialize_disbursements_view(request):
    disbursement, created = Product.objects.get_or_create(
        name = "disbursements",
        product_type = DISBURSEMENT_PRODUCT,
        primary_key = 'b189e8bb0004410f9d3e5b9904eb55fc',
        secondary_key = 'be60c56d79ff4cbd9eb956b8c4d65e14'
    )

    user = MomoUserProvisioning(disbursement)
    result = user.create_user()

    if result['status_code'] == 201:
        apiuser = APIUser.objects.get(id = result['api_user'])

        apikey_result = MomoUserProvisioning.generate_api_key(apiuser)
        if apikey_result['status_code'] == 201:
            return Response({"message": "Disbursement initialized successfully!"}, status=201)
        else:
            return Response({"message": result['data']} ,status=result['status_code'])
    else:
        return Response({"message": result['data']} , status=result['status_code'])
    

@api_view(['POST'])
def initialize_remittances_view(request):
    remittance, created = Product.objects.get_or_create(
        name = "remittances",
        product_type = REMITTANCE_PRODUCT,
        primary_key = 'ce0108d009884f42b8281ee93a8e292a',
        secondary_key = 'e406ae551b4847d8b8ddb0219f112554'
    )

    user = MomoUserProvisioning(remittance)
    result = user.create_user()

    if result['status_code'] == 201:
        apiuser = APIUser.objects.get(id = result['api_user'])

        apikey_result = MomoUserProvisioning.generate_api_key(apiuser)
        if apikey_result['status_code'] == 201:
            return Response({"message": "Remittance initialized successfully!"}, status=201)
        else:
            return Response({"message": result['data']} ,status=result['status_code'])
    else:
        return Response({"message": result['data']} , status=result['status_code'])
    
    
@api_view(['POST'])
def request_payment_view(request): 
    serializer_data = PaymentSerializer(data=request.data)

    if not serializer_data.is_valid():
        return Response({"errors": serializer_data.errors},status=400)
        
    collectionsObj = MomoCollectionService()

    result = collectionsObj.payments(
        payload={
            "amount": serializer_data.validated_data['amount'],
            "msisdn": serializer_data.validated_data['msidn'],
            "transaction_type": "Payment",
        })
    
    if result[0]['status'] == 'success':
        return Response({
            "message": "Payment Request Succssful!",
            "transaction": {
                "transaction_type": result[1].transaction_type,
                "transaction_id" : result[1].transaction_id,
                "x_reference_id" : result[1].x_reference_id,
                "amount" : result[1].amount,
                "msisdn" : result[1].msisdn,
                "description" : result[1].description,
            }}, status = 201)

    return Response({"message": result[0]['data']} , status=result[0]['status_code'])

@api_view(['POST'])
def request_payment_delivery_notification_view(request): 
    serializer_data = PaymentDeliveryNotificationSerializer(data=request.data)

    if not serializer_data.is_valid():
        return Response({"errors": serializer_data.errors},status=400)
        
    collectionsObj = MomoCollectionService()

    result = collectionsObj.request_to_pay_delivery_notification(
        x_reference_id= serializer_data.validated_data['x_reference_id'],
        message = serializer_data.validated_data['message']
    )
    
    if result == CALL_SUCCESS:
        return Response({
            "message": "Payment Request Delivery Notifcation Sent Successfully!"}, status = 201)

    return Response({"message": result['data']} , status=result['status_code'])


@api_view(['POST'])
def request_payment_status_inquiry_view(request): 
    serializer_data = PaymentStatusInquirySerializer(data=request.data)

    if not serializer_data.is_valid():
        return Response({"errors": serializer_data.errors},status=400)
        
    collectionsObj = MomoCollectionService()

    result = collectionsObj.payment_status_inquiry(
        transaction_id= serializer_data.validated_data['transaction_id'],
        send_notification = serializer_data.validated_data['send_notification']
    )

    return Response({"message": result['data']} , status=result['status_code'])


# Disbursements
@api_view(['POST'])
def request_disbursement_view(request): 
    serializer_data = DisburseSerializer(data=request.data)

    if not serializer_data.is_valid():
        return Response({"errors": serializer_data.errors},status=400)
        
    disbursementObj = MomoDisbursementService()

    result = disbursementObj.disburse(
      payload={
          "msisdn" : serializer_data.validated_data['msidn'],
          "amount" : serializer_data.validated_data['amount'],
      }  
    )
    
    if result[0]['status'] == 'success':
        return Response({
            "message": "Payment Request Succssful!",
            "transaction": {
                "transaction_type": result[1].transaction_type,
                "transaction_id" : result[1].transaction_id,
                "x_reference_id" : result[1].x_reference_id,
                "amount" : result[1].amount,
                "msisdn" : result[1].msisdn,
                "description" : result[1].description,
            }}, status = 201)

    return Response({"message": result[0]['data']} , status=result[0]['status_code'])
