# posts/tests/test_views.py
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

# Импортируем глобальные константы
from django.conf import settings

# Импортируем модели и формы проекта
from ..models import Group, Post, Comment
from ..forms import PostForm, CommentForm

User = get_user_model()


class ViewsTests(TestCase):
    """Тесты views"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='auth')
        # Создаем группу
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        # Создаем пост
        cls.post = Post.objects.create(
            author=ViewsTests.user,
            text='Тестовый пост',
            group=ViewsTests.group,
        )
        # Создаем комментарий
        cls.comment = Comment.objects.create(
            author=ViewsTests.user,
            text='Тестовый комментарий',
            post=ViewsTests.post,
        )

    def setUp(self):
        # Создаем клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(ViewsTests.user)

    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, ViewsTests.user)
        self.assertEqual(post.pub_date, ViewsTests.post.pub_date)
        self.assertEqual(post.text, ViewsTests.post.text)
        self.assertEqual(post.group, ViewsTests.post.group)

    def test_templates(self):
        testing_pages = {
            reverse('posts:index'):
                'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': ViewsTests.group.slug}
            ):
                'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': ViewsTests.user.username}
            ):
                'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': ViewsTests.post.pk}
            ):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': ViewsTests.post.pk}):
                'posts/create_post.html',
        }
        for page, template in testing_pages.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertTemplateUsed(response, template)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': ViewsTests.post.pk}
                )
            )
        )
        self.check_context_contains_page_or_post(response.context, True)
        self.assertIsInstance(response.context['form'], CommentForm)
        self.assertIn('comments', response.context)
        comment = response.context['comments'][0]
        self.assertEqual(comment.author, ViewsTests.user)
        self.assertEqual(comment.pub_date, ViewsTests.comment.pub_date)
        self.assertEqual(comment.text, ViewsTests.comment.text)

    def test_create_and_edit_pages_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        testing_pages = (
            [reverse('posts:post_create'), False],
            [reverse('posts:post_edit', args=[ViewsTests.post.pk]), True],
        )
        for url, is_edit_value in testing_pages:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIsInstance(
                    response.context['form'], PostForm
                )
                self.assertIn(
                    'is_edit',
                    response.context
                )
                self.assertIsInstance(
                    response.context['is_edit'],
                    bool
                )
                self.assertEqual(
                    response.context['is_edit'],
                    is_edit_value
                )
                if is_edit_value:
                    self.assertEqual(
                        response.context['post_id'],
                        str(ViewsTests.post.pk)
                    )

    def test_paginate_page_show_correct_context(self):
        """Тестируем пажинированные страницы"""
        # Страница и ожидаемое количество постов
        paginate_pages = (
            (1, settings.POSTS_ON_PAGE),
            (2, 1),
        )
        # Тестируемые страницы
        testing_pages = (
            ['posts:index', None],
            ['posts:group_list', ViewsTests.group.slug],
            ['posts:profile', ViewsTests.user.username],
        )
        # Создаем тестовые посты
        bulk_data = []
        for index in range(settings.POSTS_ON_PAGE):
            bulk_data.append(
                Post(
                    author=ViewsTests.user,
                    text=f'Тестовый пост {index}',
                    group=ViewsTests.group
                )
            )
        Post.objects.bulk_create(bulk_data)
        # Тестируем страницы и число постов на них
        for urls, args in testing_pages:
            for page, count in paginate_pages:
                with self.subTest(urls=urls, page=page):
                    if args:
                        response = self.authorized_client.get(
                            reverse(urls, args=[args]),
                            {'page': page}
                        )
                    else:
                        response = self.authorized_client.get(
                            reverse(urls),
                            {'page': page}
                        )
                    self.assertEqual(
                        len(response.context['page_obj']),
                        count
                    )

    def test_homepage_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:index'
                )
            )
        )
        self.check_context_contains_page_or_post(response.context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:profile',
                    args=[ViewsTests.user.username]
                )
            )
        )
        self.check_context_contains_page_or_post(response.context)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], ViewsTests.user)
        self.assertIn('following', response.context)
        self.assertIsInstance(response.context['following'], bool)

    def test_group_list_page_showe_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:group_list',
                    args=[ViewsTests.group.slug]
                )
            )
        )
        self.assertEqual(
            response.context['page_obj'][0],
            ViewsTests.post
        )

    def test_post_in_group_list(self):
        """Проверяем, что пост не попал в группу,
        для которой не был предназначен."""
        # Создаем новую группу
        new_group = Group.objects.create(
            title='Тестовая группа',
            slug='new_slug',
            description='Тестовое описание',
        )
        # Создаем новый пост
        new_post = Post.objects.create(
            author=ViewsTests.user,
            text='Новый тестовый пост',
            group=new_group,
        )
        # Проверяем что пост есть на нужной странице
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:group_list',
                    args=[new_group.slug]
                )
            )
        )
        self.assertEqual(
            response.context['page_obj'][0],
            new_post
        )
        # Провераем что поста нет на ненужной странице
        response = (
            self.authorized_client.
            get(reverse('posts:group_list', args=[ViewsTests.group.slug]))
        )
        self.assertNotIn(
            new_post,
            response.context['page_obj']
        )

    def test_add_comment(self):
        """Проверяем, что комментарий не попал на страницу,
        для которой не был предназначен."""
        # Создаем новый пост
        new_post = Post.objects.create(
            author=ViewsTests.user,
            text='Новый тестовый пост',
        )
        # Создаем новый комментарий
        new_comment = Comment.objects.create(
            author=ViewsTests.user,
            text='Новый тестовый комментарий',
            post=new_post
        )
        # Проверяем что комментарий есть на нужной странице
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:post_detail',
                    args=[new_post.pk]
                )
            )
        )
        self.assertEqual(
            response.context['comments'][0],
            new_comment
        )
        # Провераем что комментария нет на ненужной странице
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:post_detail',
                    args=[ViewsTests.post.pk]
                )
            )
        )
        self.assertNotIn(
            new_comment,
            response.context['comments']
        )