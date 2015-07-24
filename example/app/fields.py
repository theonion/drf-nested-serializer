from nested_serializers.fields import NestedModelField

from .models import UnnecessaryModel, Tag, FeatureType, QuizQuestion, QuizOutcome, QuizAnswer


class NestedUnnecessaryField(NestedModelField):
    class Meta(object):
        model = UnnecessaryModel


class NestedTagField(NestedModelField):
    class Meta(object):
        model = Tag


class NestedFeatureTypeField(NestedModelField):
    class Meta(object):
        model = FeatureType


class NestedQuizAnswerField(NestedModelField):
    class Meta(object):
        model = QuizAnswer


class NestedQuizOutcomeField(NestedModelField):
    class Meta(object):
        model = QuizOutcome


class NestedQuizQuestionField(NestedModelField):
    answer_set = NestedQuizAnswerField(many=True, allow_null=True)

    class Meta(object):
        model = QuizQuestion
