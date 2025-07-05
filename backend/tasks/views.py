from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import re, os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .models import Board, Column, Task, Subtask
from .serializers import (
    BoardSerializer,
    BoardDetailSerializer,
    ColumnSerializer,
    TaskSerializer,
    SubtaskSerializer,
)
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class CustomUserViewSet(UserViewSet):
    def perform_create(self, serializer):
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        self.token_data = {
            "access": str(refresh.access_token),
        }

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            response.data.update(self.token_data)
        return response

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


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

    def get_queryset(self):
        return Board.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BoardDetailSerializer  # includes columns, tasks, subtasks
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def set_columns(self, request, pk=None):
        board = self.get_object()
        Column.objects.filter(board=board).delete()  # delete old columns

        columns_data = request.data.get('columns', [])
        for column_data in columns_data:
            Column.objects.create(board=board, **column_data)

        return Response({'status': 'columns updated'})


class ColumnViewSet(viewsets.ModelViewSet):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer

    def get_queryset(self):
        return Column.objects.filter(board__owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        column = self.get_object()
        column.delete()
        return Response({'status': 'column deleted'}, status=status.HTTP_204_NO_CONTENT)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(column__board__owner=self.request.user)

    def create(self, request, *args, **kwargs):
        subtasks_data = request.data.pop('subtasks', [])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        for subtask_data in subtasks_data:
            Subtask.objects.create(task=task, **subtask_data)

        return Response(self.get_serializer(task).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        subtasks_data = request.data.pop('subtasks', None)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        if subtasks_data is not None:
            Subtask.objects.filter(task=task).delete()
            for subtask_data in subtasks_data:
                Subtask.objects.create(task=task, **subtask_data)

        return Response(self.get_serializer(task).data)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        task.delete()
        return Response({'status': 'task deleted'}, status=status.HTTP_204_NO_CONTENT)


class SubtaskViewSet(viewsets.ModelViewSet):
    queryset = Subtask.objects.all()
    serializer_class = SubtaskSerializer

    def get_queryset(self):
        return Subtask.objects.filter(task__column__board__owner=self.request.user)
