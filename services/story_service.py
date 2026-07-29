from .prompt_builder import *
from .hf_service import *

def create_new_story(instructions, genre, topic):
    prompt = craft_story_prompt(instructions, genre, topic)
    content = generate_story(prompt)
    return content