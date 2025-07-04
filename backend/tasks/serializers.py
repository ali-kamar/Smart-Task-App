from rest_framework import serializers
from .models import User, Board, Column, Task, Subtask

# 🔹 Subtask Serializer
class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['id', 'title', 'is_completed']
        read_only_fields = ['id']

# 🔹 Task Serializer
class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubtaskSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'subtasks']
        read_only_fields = ['id']

# 🔹 Column Serializer
class ColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'name', 'tasks']
        read_only_fields = ['id']

class BoardSerializer(serializers.ModelSerializer):

    class Meta:
        model = Board
        fields = ['id', 'name']
        read_only_fields = ['id']

# Column Create Serializer related to board
class ColumnCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['name']

class BoardCreateSerializer(serializers.ModelSerializer):
    columns = ColumnCreateSerializer(many=True, required=False)

    class Meta:
        model = Board
        fields = ['id', 'name', 'columns']
        read_only_fields = ['id']

    def create(self, validated_data):
        columns_data = validated_data.pop('columns', [])
        user = self.context['request'].user
        board = Board.objects.create(owner=user, **validated_data)
        for column_data in columns_data:
            Column.objects.create(board=board, **column_data)
        return board

# 🔹 User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user