from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Reseña, Usuario


Usuario = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    provincia = forms.ModelChoiceField(
        queryset=Usuario._meta.get_field('provincia').related_model.objects.all(), 
        required=True,  
        error_messages={'required': 'Debes seleccionar una provincia'}
    )
    municipio = forms.ModelChoiceField(
        queryset=Usuario._meta.get_field('municipio').related_model.objects.all(), 
        required=True,  
        error_messages={'required': 'Debes seleccionar un municipio'}
    )
    zona = forms.ModelChoiceField(
        queryset=Usuario._meta.get_field('zona').related_model.objects.all(), 
        required=True,  
        error_messages={'required': 'Debes seleccionar una zona'}
    )
    teléfono = forms.CharField(max_length=15, required=False)
    dirección = forms.CharField(max_length=255, required=False)
    cómo_nos_conoció = forms.ChoiceField(choices=Usuario.COMO_NOS_CONOCIO_CHOICES, required=False)

    class Meta:
        model = Usuario
        fields = [
            "username", "first_name", "last_name", "email", "provincia", "municipio", "zona",
            "teléfono", "dirección", "cómo_nos_conoció"
        ]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "zona": "Zona",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if isinstance(visible.field.widget, forms.Select):
                visible.field.widget.attrs['class'] = 'form-select'
            else:
                visible.field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        # Convert username to lowercase before saving
        user = super().save(commit=False)
        user.username = user.username.lower()
        if commit:
            user.save()
        return user




class ReseñaForm(forms.ModelForm):
    class Meta:
        model = Reseña
        fields = ['puntuación', 'comentario']
        widgets = {
            'puntuación': forms.Select(choices=[(i, f"{i} estrellas") for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 4}),
        }


class UsuarioForm(forms.ModelForm):
    provincia = forms.ModelChoiceField(
        queryset=Usuario._meta.get_field('provincia').related_model.objects.all(), 
        required=True,  
        error_messages={'required': 'Debes seleccionar una provincia'}
    )
    municipio = forms.ModelChoiceField(
        queryset=Usuario._meta.get_field('municipio').related_model.objects.all(), 
        required=True,  
        error_messages={'required': 'Debes seleccionar un municipio'}
    )
    zona = forms.ModelChoiceField(
        queryset=Usuario._meta.get_field('zona').related_model.objects.all(), 
        required=True,  
        error_messages={'required': 'Debes seleccionar una zona'}
    )
    teléfono = forms.CharField(max_length=15, required=False)
    dirección = forms.CharField(max_length=255, required=False)
    cómo_nos_conoció = forms.ChoiceField(choices=Usuario.COMO_NOS_CONOCIO_CHOICES, required=False)

    class Meta:
        model = Usuario
        fields = [
            "username", "first_name", "last_name", "email", "provincia", "municipio", "zona",
            "teléfono", "dirección", "cómo_nos_conoció"
        ]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "zona": "Zona",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if isinstance(visible.field.widget, forms.Select):
                visible.field.widget.attrs['class'] = 'form-select'
            else:
                visible.field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        # Convert username to lowercase before saving
        user = super().save(commit=False)
        user.username = user.username.lower()
        if commit:
            user.save()
        return user            
