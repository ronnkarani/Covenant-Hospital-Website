from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import HeroSlide, HeroContent, HomeCard, About, Service, BlogPost, PartnerLogo, BlogCategory, Comment
from .forms import CommentForm
from django.contrib.auth.decorators import login_required

#HOME PAGE
def index(request):
    hero_content = HeroContent.objects.first()
    hero_slides = HeroSlide.objects.all()
    home_cards = HomeCard.objects.all()
    about = About.objects.first()
    services = Service.objects.all()
    blogs = BlogPost.objects.order_by('-id')[:4]
    partners = PartnerLogo.objects.all()

    return render(request, 'index.html', {
        "hero_content": hero_content,
        "hero_slides": hero_slides,
        "home_cards": home_cards,
        "about": about,
        "services": services,
        "blogs": blogs,
        "partners": partners
    })


#ABOUT PAGE
def about(request):
    about_page = About.objects.first()
    services = Service.objects.all()
    partners = PartnerLogo.objects.all()

    return render(request, "about.html", {
        "about_page": about_page,
        "services": services,
        "partners": partners
    })

#BLOG PAGE
def blog(request):
    query = request.GET.get("q")
    category_id = request.GET.get("category")

    blogs = BlogPost.objects.all().order_by("-date")

    # Search
    if query:
        blogs = blogs.filter(title__icontains=query) | blogs.filter(content__icontains=query)

    # Category filter
    if category_id:
        blogs = blogs.filter(category__id=category_id)

    # Pagination
    paginator = Paginator(blogs, 4)  # 5 posts per page
    page = request.GET.get("page")
    blogs = paginator.get_page(page)

    categories = BlogCategory.objects.all()
    recent_posts = BlogPost.objects.order_by("-date")[:5]
    partners = PartnerLogo.objects.all()

    return render(request, "blog.html", {
        "blogs": blogs,
        "categories": categories,
        "recent_posts": recent_posts,
        "partners": partners
    })



def blog_detail(request, pk):
    blog = get_object_or_404(BlogPost, pk=pk)
    blog.views += 1
    blog.save()

    comments = blog.comments.filter(parent__isnull=True)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.blog = blog
            new_comment.save()
            return redirect("blog_detail", pk=pk)
    else:
        form = CommentForm()

    recent_posts = BlogPost.objects.order_by("-date")[:3]
    popular_posts = BlogPost.objects.order_by("-views")[:4]

    return render(request, "blog_detail.html", {
        "blog": blog,
        "comments": comments,
        "comment_form": form,
        "recent_posts": recent_posts,
        "popular_posts": popular_posts,
    })


@login_required
def blog_like(request, pk):
    blog = get_object_or_404(BlogPost, pk=pk)
    if request.user in blog.likes.all():
        blog.likes.remove(request.user)
    else:
        blog.likes.add(request.user)
    return redirect('blog_detail', pk=pk)

#CONTACT PAGE
def contact(request):
    return render(request, "contact.html")
