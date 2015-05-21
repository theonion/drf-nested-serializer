from rest_framework import serializers

from .models import Quiz, QuizAnswer, QuizOutcome, QuizQuestion, Article, Tag, FeatureType

from nested_serializers import NestedModelSerializer


class QuizOutcomeSerializer(NestedModelSerializer):

    class Meta:
        model = QuizOutcome


class QuizAnswerSerializer(NestedModelSerializer):

    class Meta:
        model = QuizAnswer


class QuizQuestionSerializer(NestedModelSerializer):
    answer_set = QuizAnswerSerializer(many=True, required=False)

    class Meta:
        model = QuizQuestion


class QuizSerializer(NestedModelSerializer):
    """Serializes our fabulous quiz content."""
    question_set = QuizQuestionSerializer(many=True, required=False)
    outcome_set = QuizOutcomeSerializer(many=True, required=False)

    class Meta:
        model = Quiz


class ArticleSerializer(NestedModelSerializer):

    class Meta:
        model = Article
        depth = 1