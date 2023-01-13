# posts/tests/test_forms.py
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

# Импортируем модели и формы проекта
from ..models import Group, Post, Comment

User = get_user_model()


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

    def setUp(self):
        # Создаем клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(FormsTests.user)

    def test_create_post(self):
        """Тестируем создание поста"""
        form = {
            'text': 'Текст поста',
            'group': FormsTests.group.pk
        }
        self.authorized_client.post(
            reverse(
                'posts:post_create'
            ),
            data=form
        )
        new_post = Post.objects.first()
        self.assertEqual(
            new_post.text,
            'Текст поста'
        )
        self.assertEqual(
            str(new_post.group),
            'Тестовая группа'
        )

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
