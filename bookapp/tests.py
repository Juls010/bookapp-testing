import shutil
import os
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from datetime import date

from .models import Book, Author
from .forms import BookForm

# Usamos la carpeta 'testfiles' como vimos en clase
@override_settings(MEDIA_ROOT='testfiles')

class BookModelTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="George", last_name="Orwell")

# Borramos la carpeta al terminar para no ensuciar el proyecto. 'rmtree' significa que elimina la carpeta, con todo su cotenido.   
    def tearDown(self):
        shutil.rmtree('testfiles', ignore_errors=True)

# Probamos que se crea bien con los datos minimos
    def test_creation_correct(self):
        book = Book(title="1984", pages=300, rating=5, status="FI", published_date=date(1949, 6, 8))
        try:
            book.full_clean()
            book.save()
        except ValidationError:
            self.fail("The book should have been created correctly.")

# Corrección: El enunciado pedía mínimo 1 pagina
    def test_invalid_pages(self):
        book = Book(title="Bad Pages", pages=0, status="RE", published_date=date.today())
        with self.assertRaises(ValidationError):
            book.full_clean()

# El rating no puede ser mayor de 5
    def test_invalid_rating(self):
        book = Book(title="Bad Rating", pages=100, rating=6, status="RE", published_date=date.today())
        with self.assertRaises(ValidationError):
            book.full_clean()

# Corrección: La fecha de lectura no puede ser anterior a la publicacion
    def test_read_date_before_published_date(self):
        book = Book(
            title="Time Traveler", pages=100, status="FI",
            published_date=date(2023, 1, 1), read_date=date(2022, 1, 1)
        )
        with self.assertRaises(ValidationError):
            book.full_clean()

# Probamos añadir un autor
    def test_creation_with_author(self):
        book = Book.objects.create(title="Animal Farm", pages=100, status="FI", published_date=date.today())
        book.authors.add(self.author)
        self.assertEqual(book.authors.count(), 1)

# Probamos subir una imagen
    def test_creation_with_cover(self):
        image = SimpleUploadedFile("cover.jpg", b"fake_content", content_type="image/jpeg")
        book = Book(title="Cover Book", pages=100, status="FI", published_date=date.today(), cover_image=image)
        try:
            book.full_clean()
            book.save()
        except ValidationError:
            self.fail("Creation with image failed")


class BookFormTest(TestCase):

    def setUp(self):
        self.author = Author.objects.create(name="J.K.", last_name="Rowling")

# Formulario correcto
    def test_form_valid(self):
        form_data = {'title': 'Harry Potter', 'pages': 223, 'rating': 5, 'status': 'FI', 'published_date': '1997-06-26'}
        form = BookForm(data=form_data)
        self.assertTrue(form.is_valid())

# Probamos el mensaje de error de longitud
    def test_form_title_too_long(self):
        form_data = {'title': 'a' * 51, 'pages': 100, 'status': 'RE', 'published_date': '2022-01-01'}
        form = BookForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("The title must be less than 50 characters long", form.errors['title'])

# Probamos el mensaje de titulo obligatorio
    def test_form_title_empty(self):
        form_data = {'title': '', 'pages': 100, 'status': 'RE', 'published_date': '2022-01-01'}
        form = BookForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("The title is mandatory", form.errors['title'])

# Probamos paginas incorrectas en el form
    def test_form_invalid_pages(self):
        form_data = {'title': 'Bad Pages', 'pages': 0, 'status': 'RE', 'published_date': '2022-01-01'}
        form = BookForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('pages', form.errors)

# Probamos rating incorrecto en el form
    def test_form_invalid_rating(self):
        form_data = {'title': 'Bad Rating', 'pages': 10, 'rating': 6, 'status': 'RE', 'published_date': '2022-01-01'}
        form = BookForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

# Validamos que salte el error de fechas cruzadas
    def test_form_read_date_invalid(self):
        form_data = {
            'title': 'Fechas Mal', 'pages': 100, 'status': 'FI',
            'published_date': '2023-01-01', 'read_date': '2020-01-01'
        }
        form = BookForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(any("The read date must be after the published date" in str(err) for err in form.errors.values()))

# Formulario con autor seleccionado
    def test_form_with_author(self):
        form_data = {
            'title': 'With Author', 'pages': 100, 'status': 'FI', 
            'published_date': '2022-01-01', 'authors': [self.author.id]
        }
        form = BookForm(data=form_data)
        self.assertTrue(form.is_valid())

# Formulario con archivo
    def test_form_with_cover(self):
        image = SimpleUploadedFile("cover.jpg", b"fake", content_type="image/jpeg")
        form_data = {'title': 'With Cover', 'pages': 100, 'status': 'FI', 'published_date': '2022-01-01'}
        form = BookForm(data=form_data, files={'cover_image': image})
        self.assertTrue(form.is_valid())


class BookControllerTest(TestCase):

# Usuario normal y usuario admin
    def setUp(self):
        self.client = Client()
        self.user_normal = User.objects.create_user(username='pepe', password='password123')
        self.user_admin = User.objects.create_user(username='admin', password='password123')
        
        content_type = ContentType.objects.get_for_model(Book)
        permissions = Permission.objects.filter(content_type=content_type)
        self.user_admin.user_permissions.set(permissions)
        
        self.book = Book.objects.create(title="Libro Test", pages=100, status="RE", published_date="2023-01-01")

#  LIST . EL usuario normal puede ver la lista
    def test_list_view_user_normal(self):
        self.client.force_login(self.user_normal)
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)

# El admin tambien
    def test_list_view_admin(self):
        
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)

#  DETAIL . Usuario autenticado puede ver detalle
    def test_detail_view_user_normal(self):
        url = reverse('book_detail', args=[self.book.id])
        self.client.force_login(self.user_normal)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_view_admin(self):
        url = reverse('book_detail', args=[self.book.id])
        self.client.force_login(self.user_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

#  CREATE FORM .
# Corrección : Usuario normal no debe poder crear 
    def test_create_view_user_normal(self):
        url = reverse('form')
        self.client.force_login(self.user_normal)
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

# Admin si puede crear
    def test_create_view_admin(self):
        url = reverse('form')
        self.client.force_login(self.user_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

#   EDIT . Usuario normal no puede editar
    def test_edit_view_user_normal(self):
        url = reverse('book_edit', args=[self.book.id])
        self.client.force_login(self.user_normal)
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

# Admin si puede editar
    def test_edit_view_admin(self):
        url = reverse('book_edit', args=[self.book.id])
        self.client.force_login(self.user_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

#  DELETE . Usuario normal no puede borrar
    def test_delete_view_user_normal(self):
        url = reverse('book_delete', args=[self.book.id])
        self.client.force_login(self.user_normal)
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

# Admin si puede borrar
    def test_delete_view_admin(self):
        url = reverse('book_delete', args=[self.book.id])
        self.client.force_login(self.user_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)