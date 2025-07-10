from rest_framework import serializers
from .models import Board, Column, Task, Subtask, User
from django.db import transaction


class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['id', 'title', 'is_completed']
        read_only_fields = ['id']


class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubtaskSerializer(many=True, required=False)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'column', 'subtasks']
        read_only_fields = ['id']

    def create(self, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        with transaction.atomic():
            task = Task.objects.create(**validated_data)
            for subtask_data in subtasks_data:
                Subtask.objects.create(task=task, **subtask_data)
        return task

    def update(self, instance, validated_data):
        subtasks_data = validated_data.pop('subtasks', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if subtasks_data:
                instance.subtasks.all().delete()
                for subtask_data in subtasks_data:
                    Subtask.objects.create(task=instance, **subtask_data)

        return instance


class ColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'name', 'board', 'tasks']
        read_only_fields = ['id']


class ColumnCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['id', 'name']
        read_only_fields = ['id']


class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnCreateSerializer(many=True, required=False)

    class Meta:
        model = Board
        fields = ['id', 'name', 'columns']
        read_only_fields = ['id']

    def create(self, validated_data):
        columns_data = validated_data.pop('columns', [])
        with transaction.atomic():
            board = Board.objects.create( **validated_data)
            for column_data in columns_data:
                Column.objects.create(board=board, **column_data)
        return board
    
    def update(self, instance, validated_data):
        updated_data = validated_data.pop('columns', None)
        #this atomic block ensures that all operations within it are treated as a single transaction. If any operation fails, all changes will be rolled back, maintaining data integrity.
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if updated_data:
                # Clear existing items
                instance.columns.all().delete()
                # Create new items
                for item in updated_data:
                    Column.objects.create(board=instance, **item)
        return instance


class BoardDetailSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'name', 'columns']
        read_only_fields = ['id']

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