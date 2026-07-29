from gradio_client import Client

hf_client = Client("htc-hekima/htc-StoryGenerator", httpx_kwargs={"timeout": None})
def generate_story(prompt):
    try:
        response = hf_client.predict(
            message=prompt,
            api_name="/custom_ai_chat"
        )
        # If Gradio returns a dictionary structure, extract the text payload directly
        if isinstance(response, dict):
            return response.get("content", "") or response.get("text", "")
            
        return str(response)
    except Exception as e:
        return f"Error reaching permanent AI server: {str(e)}"
