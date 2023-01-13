# posts/tests/test_urls.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=StaticURLTests.user,
            text='Тестовый пост',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(StaticURLTests.user)

    def test_homepage(self):
        # Создаем экземпляр клиента
        guest_client = Client()
        # Делаем запрос к главной странице и проверяем статус
        response = guest_client.get('/')
        # Утверждаем, что для прохождения теста код
        # должен быть равен HTTPStatus.OK
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_free_access(self):
        """Открытые страницы доступны любому пользователю."""
        testing_pages = (
            '/',
            f'/group/{StaticURLTests.group.slug}/',
            f'/profile/{StaticURLTests.user}/',
            f'/posts/{StaticURLTests.post.pk}/',
        )
        for page in testing_pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Недоступна страница {page}')

    def test_non_free_access(self):
        """Тест страниц с ограниченным доступом."""
        testing_pages = (
            '/create/',
            f'/posts/{StaticURLTests.post.pk}/edit/',
        )
        # Проверяем доступ неавторизованным клиентом
        for page in testing_pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.FOUND,
                    f'\nНеавторизованны доступ к {page}')
        # Проверяем доступ авторизованным клиентом
        for page in testing_pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'\nНедоступна страница {page}')

    def test_edit_no_author(self):
        """Проверка редактирования поста не автором"""
        # Создаем нового пользователя и авторизованный клиент
        user_testing = User.objects.create_user(username='tester')
        testing_client = Client()
        testing_client.force_login(user_testing)
        response = testing_client.get(
            f'/posts/{StaticURLTests.post.pk}/edit/'
        )
        self.assertNotEqual(
            response.status_code,
            HTTPStatus.OK,
            'Не автор получил доступ к редактированию поста'
        )

    def test_templates(self):
        testing_pages = {
            '/':
                'posts/index.html',
            f'/group/{StaticURLTests.group.slug}/':
                'posts/group_list.html',
            f'/profile/{StaticURLTests.user}/':
                'posts/profile.html',
            f'/posts/{StaticURLTests.post.pk}/':
                'posts/post_detail.html',
            '/create/':
                'posts/create_post.html',
            f'/posts/{StaticURLTests.post.pk}/edit/':
                'posts/create_post.html',
        }
        for page, template in testing_pages.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
            self.assertTemplateUsed(response, template)

    def test_unknown_page(self):
        """Запрос к несуществующей странице"""
        response = self.guest_client.get('unknown_page')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'Ошибка запроса к несуществующей странице'
        )
