import os
from datetime import date, datetime, timedelta
from django.conf import settings
from django.utils import timezone
from groq import Groq 
from .models import RateLimit, StoryChunk
from .promts import get_system_prompt, build_message, parse_ai_response

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def check_rate_limit(ip_address: str) -> tuple[bool, str]:
    today = date.today()
    record, created = RateLimit.objects.get_or_create(
        ip_address=ip_address,
        date=today,
        defaults={'requests_today': 0, 'requests_this_minute': 0}
    )

    if record.requests_today >= settings.GROQ_REQUESTS_PER_DAY:
        return False, f"Daily limit ({settings.GROQ_REQUESTS_PER_DAY}) reached."
    
    one_minute_ago = timezone.now() - timedelta(minutes=1)
    if record.last_request_at < one_minute_ago:
        record.requests_this_minute = 0

    if record.requests_this_minute >= settings.GROQ_REQUESTS_PER_MINUTE:
        return False, f"Minute limit ({settings.GROQ_REQUESTS_PER_MINUTE}) reached."
    
    return True, ""
    
def increment_rate_limit(ip_address: str):
    today = date.today()
    record, _ = RateLimit.objects.get_or_create(
        ip_address=ip_address,
        date=today,
        defaults={'requests_today': 0, 'requests_this_minute': 0}
    )
    record.requests_today += 1
    record.requests_this_minute += 1
    record.save()

def generate_story_continuation(story, user_input: str) -> tuple[str, list[str]]:
    chunks = story.chunks.all()
    messages = build_message(story.genre, chunks)

    messages.append({
        'role': 'user',
        'content': user_input,
    })

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {'role': 'system', 'content': get_system_prompt(story.genre)},
            *messages,
        ],
        max_tokens=settings.GROQ_MAX_TOKENS,
        temperature=0.85,
    )

    raw_text = response.choices[0].message.content
    return parse_ai_response(raw_text)

    