from rest_framework import serializers
from utils.sanitize_tel import ussd_support_tel
from utils.ussd import standard_urn

class PaymentSerializer(serializers.Serializer):
    amount = serializers.IntegerField()    
    msidn = serializers.CharField()

    def validate_msisdn(self, value):
        try:
            for_ussd = ussd_support_tel(value)
            standard_telephone = standard_urn(for_ussd)
        except Exception as error:
            raise serializers.ValidationError(str(error))
        return standard_telephone

    def validate_amount(self, value):
        try:
            amount = float(value)
        except Exception as error:
            raise serializers.ValidationError(str(error))
        return amount


class PaymentDeliveryNotificationSerializer(serializers.Serializer):
    x_reference_id = serializers.CharField()
    message = serializers.CharField()


class PaymentStatusInquirySerializer(serializers.Serializer):
    transaction_id = serializers.CharField()
    send_notification = serializers.BooleanField()


class DisburseSerializer(serializers.Serializer):
    amount = serializers.IntegerField()    
    msidn = serializers.CharField()

    def validate_msisdn(self, value):
        try:
            for_ussd = ussd_support_tel(value)
            standard_telephone = standard_urn(for_ussd)
        except Exception as error:
            raise serializers.ValidationError(str(error))
        return standard_telephone

    def validate_amount(self, value):
        try:
            amount = float(value)
        except Exception as error:
            raise serializers.ValidationError(str(error))
        return amount


class RefundSerializer(serializers.Serializer):
    transaction_id = serializers.CharField()
    msidn = serializers.CharField()
    amount = serializers.IntegerField()    

    def validate_msisdn(self, value):
        try:
            for_ussd = ussd_support_tel(value)
            standard_telephone = standard_urn(for_ussd)
        except Exception as error:
            raise serializers.ValidationError(str(error))
        return standard_telephone

    def validate_amount(self, value):
        try:
            amount = float(value)
        except Exception as error:
            raise serializers.ValidationError(str(error))
        return amount