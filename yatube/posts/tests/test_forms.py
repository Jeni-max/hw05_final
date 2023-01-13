# posts/tests/test_forms.py
import shutil
import tempfile

from django.urls import reverse
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

# Импортируем модели и формы проекта
from ..models import Group, Post, Comment

# Импортируем глобальные константы
from django.conf import settings

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='auth')
        # Coздаем группу
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение,
        # изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(FormsTests.user)

    def test_create_post(self):
        """Тестируем создание поста"""
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form = {
            'text': 'Текст поста',
            'group': FormsTests.group.pk,
            'image': uploaded
        }
        self.authorized_client.post(
            reverse(
                'posts:post_create'
            ),
            data=form
        )
        self.assertEqual(
            Post.objects.all().count(),
            1
        )
        self.assertTrue(
            Post.objects.filter(
                text='Текст поста',
                group=FormsTests.group,
                author=FormsTests.user,
                image='posts/small.gif'
            ).exists()
        )
#        self.assertEqual(
#            new_post.text,
#            'Текст поста'
#        )
#        self.assertEqual(
#            str(new_post.group),
#            'Тестовая группа'
#        )

    def test_edit_post(self):
        """Тестируем редактирование поста"""
        post = Post.objects.create(
            author=FormsTests.user,
            text='Тестовый пост',
            group=FormsTests.group,
        )
        # Готовим данные для
        # редактирования поста
        form = {
            'text': 'Новый текст поста',
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                args=[post.pk]
            ),
            data=form
        )
        edited_post = Post.objects.first()
        self.assertEqual(
            edited_post.text,
            'Новый текст поста'
        )
        self.assertEqual(
            edited_post.group,
            None
        )

    def test_create_comment(self):
        """Тестируем создание сомментария"""
        post = Post.objects.create(
            author=FormsTests.user,
            text='Тестовый пост'
        )
        form = {
            'text': 'Текст сомментария',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                args=[post.pk]
            ),
            data=form
        )
        new_comment = Comment.objects.first()
        self.assertEqual(
            new_comment.text,
            'Текст сомментария'
        )
