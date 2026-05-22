from django.db import models

from infrastructure.models.business_partner_db import BusinessPartner
from infrastructure.models.delivery_type_db import DeliveryType
from infrastructure.models.payment_terms_db import PaymentTerms
from infrastructure.models.sale_type_db import SaleType
from infrastructure.models.seller_db import Seller
from infrastructure.models.tax_doc_type_db import TaxDocumentType

class Document(models.Model):
    doc_entry = models.IntegerField()
    doc_num = models.IntegerField()
    folio = models.IntegerField()

    date_document = models.DateField()
    delivery_date = models.DateField()
    delivery_schedule = models.DateTimeField()

    reference = models.CharField(max_length=255)
    comment = models.CharField(max_length=255)

    total_before_discount = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2)
    total_document = models.DecimalField(max_digits=12, decimal_places=2)

    code_sale = models.IntegerField()

    office_address = models.CharField(max_length=255)
    address_delivery = models.CharField(max_length=255)

    related_docEntry = models.IntegerField(null=True, blank=True)

    document_status = models.CharField(max_length=50)

    # Relaciones
    sale_type = models.ForeignKey(SaleType, on_delete=models.CASCADE)
    tax_document_type = models.ForeignKey(TaxDocumentType, on_delete=models.CASCADE)
    delivery_type = models.ForeignKey(DeliveryType, on_delete=models.CASCADE)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.CASCADE)
    business_partner = models.ForeignKey(BusinessPartner, on_delete=models.CASCADE)

    class Meta:

        db_table = 'documents'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    def __str__(self):
        return f'Document {self.doc_entry}'