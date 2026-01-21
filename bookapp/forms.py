from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = '__all__'
        widgets = {
            "published_date": forms.DateInput(attrs={"type": "date"}),
            "read_date": forms.DateInput(attrs={"type": "date"}),
            "authors": forms.CheckboxSelectMultiple()
        }
        error_messages = {
            "title": {
                "max_length": "The title must be less than 50 characters long",
                "required": "The title is mandatory"
            }
        }