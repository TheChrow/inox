from rest_framework import serializers


class ListQuotationsRequestSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=200, required=False, default=20)

    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
    date_doc = serializers.DateField(required=False, allow_null=True)

    doc_num = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    partner_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    salesperson_id = serializers.IntegerField(required=False, allow_null=True)
    salesperson_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    state = serializers.ChoiceField(
        choices=["", "O", "C", "Y"],
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    amount_total = serializers.FloatField(required=False, allow_null=True)


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
