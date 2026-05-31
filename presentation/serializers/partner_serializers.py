from rest_framework import serializers


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    function = serializers.CharField(max_length=128, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    mobile = serializers.CharField(max_length=64, required=False, allow_blank=True)


class AddressSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["invoice", "delivery", "other"])
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    street = serializers.CharField(max_length=255)
    street2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=128, required=False, allow_blank=True)
    zip = serializers.CharField(max_length=32, required=False, allow_blank=True)
    country_id = serializers.IntegerField(required=False)
    state_id = serializers.IntegerField(required=False)
    phone = serializers.CharField(max_length=64, required=False, allow_blank=True)


class CustomerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    is_company = serializers.BooleanField()
    vat = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    mobile = serializers.CharField(max_length=64, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)
    country_id = serializers.IntegerField(required=False)
    state_id = serializers.IntegerField(required=False)


class CreatePartnerRequestSerializer(serializers.Serializer):
    customer = CustomerSerializer()
    contacts = ContactSerializer(many=True, required=False, default=list)
    addresses = AddressSerializer(many=True, required=False, default=list)

    def validate(self, attrs):
        customer = attrs["customer"]
        if not customer["is_company"] and attrs.get("contacts"):
            raise serializers.ValidationError(
                {"contacts": "Una persona natural no puede tener contactos hijos."}
            )
        return attrs
