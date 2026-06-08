from rest_framework import serializers


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    function = serializers.CharField(max_length=128, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=64, required=False, allow_blank=True)


class CustomerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    is_company = serializers.BooleanField()
    vat = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)
    street = serializers.CharField(max_length=255, required=False, allow_blank=True)
    street2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=128, required=False, allow_blank=True)
    zip = serializers.CharField(max_length=32, required=False, allow_blank=True)
    country_id = serializers.IntegerField(required=False)
    state_id = serializers.IntegerField(required=False)


class CustomerUpdateSerializer(CustomerSerializer):
    """Variante para PUT: todos los campos opcionales (write parcial)."""
    name = serializers.CharField(max_length=255, required=False)
    is_company = serializers.BooleanField(required=False)


class CreatePartnerRequestSerializer(serializers.Serializer):
    customer = CustomerSerializer()
    contacts = ContactSerializer(many=True, required=False, default=list)

    def validate(self, attrs):
        customer = attrs["customer"]
        if not customer["is_company"] and attrs.get("contacts"):
            raise serializers.ValidationError(
                {"contacts": "Una persona natural no puede tener contactos hijos."}
            )
        if len(attrs.get("contacts") or []) > 1:
            raise serializers.ValidationError(
                {"contacts": "Solo se admite un contacto principal por cliente."}
            )
        return attrs


class UpdatePartnerRequestSerializer(serializers.Serializer):
    customer = CustomerUpdateSerializer()
    contact = ContactSerializer(required=False, allow_null=True)

    def validate(self, attrs):
        customer = attrs["customer"]
        if customer.get("is_company") is False and attrs.get("contact"):
            raise serializers.ValidationError(
                {"contact": "Una persona natural no puede tener contacto hijo."}
            )
        return attrs
