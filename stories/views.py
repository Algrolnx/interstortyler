from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from .models import Story, StoryChunk
from .services import generate_story_continuation, check_rate_limit, increment_rate_limit, get_client_ip

def home(request):
    stories = Story.objects.filter(is_finished=False).order_by('-updated_at')[:10]
    finished = Story.objects.filter(is_finished=True).order_by('-updated_at')[:5]
    return render(request, 'stories/home.html', {
        'stories': stories,
        'finished_stories': finished,
        'genres': Story.GENRE_CHOICES
    })

@require_http_methods(["POST"])
def create_story(request):
    title = request.POST.get('title', '').strip()
    genre = request.POST.get('genre', 'fantasy')
    opening = request.POST.get('opening', '').strip()

    if not title or not opening:
        return redirect('home')

    story = Story.objects.create(title=title, genre=genre)

    StoryChunk.objects.create(
        story=story,
        role='user',
        content=opening,
        order=1
    )

    ip = get_client_ip(request)
    allowed, error = check_rate_limit(ip)

    if not allowed:
        story.delete()
        return render(request, 'stories/home.html', {
            'error': error,
            'stories': Story.objects.filter(is_finished=False)[:10],
            'genres': Story.GENRE_CHOICES,
        })

    try:
        story_text, choices = generate_story_continuation(story, opening)
        increment_rate_limit(ip)

        StoryChunk.objects.create(
            story=story,
            role='assistant',
            content=story_text,
            order=2,
        )

    except Exception as e:
        story.delete()
        return redirect('home')

    return redirect('story_detail', pk=story.pk)

def story_detail(request, pk):
    story = get_object_or_404(Story, pk=pk)
    chunks = story.chunks.all()

    last_assistant = chunks.filter(role='assistant').last()
    choices = []

    if last_assistant:
        from .promts import parse_ai_response
        _, choices = parse_ai_response(last_assistant.content)

    return render(request, 'stories/story.html', {
        'story': story,
        'chunks': chunks,
        'choices': choices,
    })
@require_http_methods(["POST"])
def continue_story(request, pk):
    story = get_object_or_404(Story, pk=pk)
    if story.is_finished:
        return HttpResponse("Story is already finished.", status=400)
    user_choice = request.POST.get('choice', '').strip()
    if not user_choice:
        return HttpResponse("No choice provided.", status=400)
    ip = get_client_ip(request)
    allowed, error = check_rate_limit(ip)
    if not allowed:
        return HttpResponse(f'<p class="error">{error}</p>', status=429)
    last_order = story.chunks.count()
    StoryChunk.objects.create(
        story=story,
        role='user',
        content=user_choice,
        order=last_order + 1,
    )
    try:
        story_text, choices = generate_story_continuation(story, user_choice)
        increment_rate_limit(ip)
    except Exception as e:
        return HttpResponse('<p class="error">AI error. Try again.</p>', status=500)
    StoryChunk.objects.create(
        story=story,
        role='assistant',
        content=story_text,
        order=last_order + 2,
    )
    return render(request, 'stories/_chunk.html', {
        'story': story,
        'chunk_text': story_text,
        'choices': choices,
    })
@require_http_methods(["POST"])
def finish_story(request, pk):
    story = get_object_or_404(Story, pk=pk)
    story.is_finished = True
    story.save()
    return redirect('story_detail', pk=story.pk)