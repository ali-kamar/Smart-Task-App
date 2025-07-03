from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import re, os

class AIAssistantView(APIView):
    def post(self, request):
        user_input = request.data.get("task_description", "")
        token = os.getenv("TOKEN", "").strip()
        url = os.getenv("URL", "").strip()
        API_URL = url

        headers = {
            "Authorization": f"Bearer {token}",
        }

        payload = {
        "model": "deepseek/deepseek-r1-turbo",
        "messages": [
            {
            "role": "user",
            "content": (
                f"List exactly 5 unique, meaningful, and descriptive subtasks for the task: '{user_input}'. "
                "Format the response as a numbered list with each title in bold markdown, like this:\n"
                "1. **Title One**\n"
                "2. **Title Two**\n"
                "3. **Title Three**\n"
                "4. **Title Four**\n"
                "5. **Title Five**\n"
                "Do not include any other text or explanations."
            )
        }
    ]
}

        def extract_subtasks(content):
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
            match = re.search(r"(?s)Here are .*?5 subtasks.*?(---\s*)(.*)", content)
            return match.group(2).strip() if match else content.strip()

        def parse_titles(markdown_text):
            pattern = r"\d+\.\s+\*\*(.*?)\*\*"
            titles = re.findall(pattern, markdown_text.strip())

            # Fallback: try to match bullet points like - **Title**
            if not titles:
                pattern_alt = r"-\s+\*\*(.*?)\*\*"
                titles = re.findall(pattern_alt, markdown_text.strip())

            return [{"title": title.strip()} for title in titles]

        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            data = response.json()
            message = data["choices"][0]["message"]["content"]
            subtasks_block = extract_subtasks(message)
            titles_only = parse_titles(subtasks_block)

            return Response({"subtasks": titles_only})

        except Exception as e:
            return Response({
                "error": str(e),
                "raw_response": response.text if 'response' in locals() else ''
            }, status=500)