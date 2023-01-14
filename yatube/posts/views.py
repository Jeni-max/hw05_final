# posts/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.cache import cache_page

from django.conf import settings

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm


def paginated_context(request, post_list):
    # Из URL извлекаем номер запрошенной страницы
    page_number = request.GET.get('page')
    # Показывать POSTS_ON_PAGE записей на странице.
    paginator = Paginator(post_list, settings.POSTS_ON_PAGE)
    return paginator.get_page(page_number)


@cache_page(settings.CACHE_INDEX_PAGE)
def index(request):
    """Главная страница"""
    post_list = Post.objects.select_related('group')
    page_obj = paginated_context(request, post_list)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


@login_required
def follow_index(request):
    """Страница избранных авторов"""
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('group')
    page_obj = paginated_context(request, post_list)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    """Создаем подписку на автора"""
    author = get_object_or_404(User, username=username)
    if request.user.username != author.username:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Удаляем подписку на автора"""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', request.user.username)


def group_posts(request, slug):
    """Страница группы"""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginated_context(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница автора"""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginated_context(request, post_list)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница одного поста"""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создаем пост"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Редактируем пост"""
    post = get_object_or_404(Post, pk=post_id)
    if not post.author == request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post_id': post_id,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Добавляем комментарий"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)
