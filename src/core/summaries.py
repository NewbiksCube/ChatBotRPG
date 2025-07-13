from core.make_inference import make_inference
from config import get_default_model

def summarize_scenes_with_llm(messages, follower_name, followed_name):
    if not messages:
        return ""
    def get_speaker(m):
        meta = m.get('metadata', {})
        char_name = meta.get('character_name')
        if char_name:
            return char_name
        elif m.get('role') == 'user':
            return 'Player'
        else:
            return m.get('role', '?').capitalize()
    dialogue_log = "\n".join([
        f"[Scene {m.get('scene', '?')}] {get_speaker(m)}: {m.get('content', '')}"
        for m in messages
    ])
    system_prompt = (
        f"You are a helpful assistant. Summarize the following roleplay dialogue log for {follower_name}, "
        f"focusing on what {follower_name} and {followed_name} experienced together. "
        f"Be concise but include key events, relationships, and facts relevant to both. "
        f"Do not invent details."
    )
    context = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": dialogue_log}
    ]
    summary = make_inference(
        context=context,
        user_message=dialogue_log,
        character_name=follower_name,
        url_type=get_default_model(),
        max_tokens=512,
        temperature=0.2,
        is_utility_call=True
    )
    return summary
