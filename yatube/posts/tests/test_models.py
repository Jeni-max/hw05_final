from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
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
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(str(PostModelTest.post), 'Тестовый пост')
        self.assertEqual(str(PostModelTest.group), 'Тестовая группа')
        self.assertEqual(
            PostModelTest.post._meta.get_field('text').verbose_name,
            'Текст поста'
        )
        self.assertEqual(
            PostModelTest.post._meta.get_field('group').verbose_name,
            'Группа'
        )
        self.assertEqual(
            PostModelTest.post._meta.get_field('text').help_text,
            'Введите текст поста'
        )
        self.assertEqual(
            PostModelTest.post._meta.get_field('group').help_text,
            'Группа, к которой относится пост'
        )
