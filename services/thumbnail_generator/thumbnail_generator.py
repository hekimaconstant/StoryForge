import urllib.parse
import random

def generate_story_thumbnail(art_description):
    if not art_description:
        prompt="A mysterious book cover illustration"
    else :
        prompt = f"Cinematic book cover illustration, {art_description.strip()}, highly detailed, digital painting, 4k"
    random_seed = random.randint(1, 999999)
    encoded_prompt = urllib.parse.quote(prompt)
    thumbnail_url = f"https://image.pollinations.ai/{encoded_prompt}?width=800&height=550"
    return thumbnail_url
