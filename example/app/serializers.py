from .models import Quiz, QuizAnswer, QuizOutcome, QuizQuestion, FeatureType, UnnecessaryModel, Article

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


class FeatureTypeSerializer(NestedModelSerializer):
    class Meta:
        model = FeatureType


class UnnecessaryModelSerializer(NestedModelSerializer):
    class Meta:
        model = UnnecessaryModel


class ArticleSerializer(NestedModelSerializer):
    unnecessary = UnnecessaryModelSerializer(allow_null=True)

    class Meta:
        model = Article
        depth = 1
