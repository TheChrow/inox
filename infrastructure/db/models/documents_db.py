from django.db import models

class Document(models.Model):
    
    doc_entry  = models.IntegerField(null=True)
    doc_num = models.IntegerField(null=True)
    folio = models.IntegerField(null=True)
    date_document = models.DateField(null=True)
    delivery_date = models.DateField(null=True)
    delivery_schedule = models.DateField(null=True)
    reference = models.CharField(max_length=255, null=True)
    comment = models.TextField(null=True)
    total_before_discount = models.FloatField()
    discount = models.FloatField()
    total_document = models.FloatField()
    code_sale = models.IntegerField()
    office_address = models.CharField(max_length=255, null=True)
    address_delivery = models.CharField(max_length=255, null=True)
    related_docEntry = models.IntegerField(null=True)
    document_status = models.CharField(max_length=50, null=True)
    """
    foreign key

    sale_type_id
    tax_document_type_id
    delivery_type_id
    seller_id
    description_id
    payment_terms_id
    business_partner_id

    """

    class Meta:

        db_table = 'documents'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    def __str__(self):
        return f'Document {self.doc_entry}'