def craft_story_prompt(instructions, genre, topic):
    prompt = (f"""Write a '{genre}' story about '{topic}' Using these instructions {instructions}. Format in Markdown.
                Do not add some sub-titles, only put content in separated paragraphs.
                You must format your response EXACTLY like this template below using the [TITLE] [CONTENT] and [THUMBNAIL_PROMPT] tags:
                
                [TITLE]
                Type the story title here

                [CONTENT]
                Type the story content here
                
                [THUMBNAIL_PROMPT]
                Write a rich, highly descriptive visual scene concept for a digital artist. max length of prompt is 200 characters don't go beyond
                Focus purely on lighting, environment, mood, and dramatic character placement.
                Do not include conversational introductory text or text tags.
                """)
    return prompt