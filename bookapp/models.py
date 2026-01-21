from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError 

class Author(models.Model):
    # Corrección: CharField necesita max_length obligatoriamente
    name = models.CharField(max_length=100) 
    last_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name} {self.last_name}"

class Book(models.Model):
    STATUS_CHOICES = [
        ('PE', 'Pending'),
        ('RE', 'Reading'),
        ('FI', 'Finished')
    ]
    title = models.CharField(max_length=50)
    
    # Correción: El enunciado pide mínimo 1, y antes era 0
    pages = models.IntegerField(validators=[MinValueValidator(1)]) 
    
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES
    )
    published_date = models.DateField()
    read_date = models.DateField(blank=True, null=True)
    authors = models.ManyToManyField(Author, blank=True)
    cover_image = models.FileField(upload_to='covers/', blank=True)

    def clean(self):
        super().clean()
        # Corrección: La fecha de lectura no puede ser anterior a la de publicación. Se corrigió la comparación a < en lugar de >
        # El error debe saltar si read es menor < que published
        if self.read_date and self.read_date < self.published_date:
            raise ValidationError({"read_date": "The read date must be after the published date"})

    def __str__(self):
        return self.title