from django.conf import settings 

GENRE_STYLES = {
    'fantasy': 'epic fantasy with magic, mythical creatures, and heroic quests',
    'horror': 'psychological horror with dark atmosphere, suspense, and dread',
    'sci-fi': 'science fiction with futuristic technology, space exploration, and moral dilemmas',
    'romance': 'romantic drama with emotional depth, complex relationships, and heartfelt moments',
    'mystery': 'detective mystery with clever clues, red herrings, and a gripping investigation',
}

def get_system_prompt(genre: str) -> str:
    style = GENRE_STYLES.get(genre, 'engaging fiction')
    return f"""You are a master storyteller specializing in {style}.

RULES:
- Write vivid, immersive prose (2-4 paragraphs max per response)
- Stay consistent with characters, locations, and events already established
- Match the tone and style of the story so far
- Never repeat what was already written
- Keep descriptions rich but concise
RESPONSE FORMAT — you MUST always follow this exactly:
Write the story continuation first, then add a blank line, then write exactly:
CHOICES:
1. [first option - 1 sentence, action or decision]
2. [second option - 1 sentence, alternative action]
3. [third option - 1 sentence, unexpected twist]
The choices should be short (1 sentence each), specific, and meaningfully different from each other."""

def build_message(genre: str, chunks) -> list:
    messages = []
    for chunk in chunks:
        messages.append({
            'role': chunk.role,
            'content': chunk.content,
        })

    return messages

def parse_ai_response(response_text: str) -> tuple[str, list[str]]:
    if 'CHOICES:' not in response_text:
        return response_text.strip(), []

    parts = response_text.split('CHOICES:')
    story_text = parts[0].strip()
    choices_block = parts[1].strip()

    choices = []
    for line in choices_block.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and '.' in line:
            choice_text = line.split('.', 1)[1].strip()
            choices.append(choice_text)

    return story_text, choices[:3]