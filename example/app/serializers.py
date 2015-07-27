from nested_serializers import NestedModelSerializer

from .fields import NestedUnnecessaryField, NestedTagField, NestedFeatureTypeField, NestedQuizQuestionField, \
    NestedQuizOutcomeField, NestedAuthorField
from .models import Quiz, Article


class QuizSerializer(NestedModelSerializer):
    """Serializes our fabulous quiz content."""
    question_set = NestedQuizQuestionField(many=True, allow_null=True)
    outcome_set = NestedQuizOutcomeField(many=True, allow_null=True)

    class Meta:
        model = Quiz
        depth = 2


class ArticleSerializer(NestedModelSerializer):
    unnecessary = NestedUnnecessaryField(allow_null=True)
    tags = NestedTagField(many=True, allow_null=True)
    feature_type = NestedFeatureTypeField()
    authors = NestedAuthorField(many=True)

    class Meta:
        model = Article
        depth = 1
