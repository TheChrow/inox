from rest_framework import serializers


class QuotationLineSerializer(serializers.Serializer):
    default_code = serializers.CharField(max_length=64)
    quantity = serializers.FloatField(min_value=0.001)
    price_unit = serializers.FloatField(min_value=0)
    discount = serializers.FloatField(min_value=0, max_value=100, required=False, default=0)
    description = serializers.CharField(required=False, allow_blank=True)


class CreateQuotationRequestSerializer(serializers.Serializer):
    partner_id = serializers.IntegerField(min_value=1)
    lines = QuotationLineSerializer(many=True)
    validity_date = serializers.DateField(required=False)
    client_order_ref = serializers.CharField(max_length=128, required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError("Debe enviar al menos una línea.")
        return value
