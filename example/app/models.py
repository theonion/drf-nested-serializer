from django.db import models

# A simple article model

class Tag(models.Model):
    name = models.CharField(max_length=255)


class FeatureType(models.Model):
    name = models.CharField(max_length=255)


class UnnecessaryModel(models.Model):
    name = models.CharField(max_length=244)


class Article(models.Model):
    title = models.CharField(max_length=255)
    unnecessary = models.ForeignKey(UnnecessaryModel, null=True, blank=True, default=None)
    tags = models.ManyToManyField(Tag)
    feature_type = models.ForeignKey(FeatureType)


# A much more complex quiz model

class Quiz(models.Model):
    title = models.CharField(max_length=255)


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='question_set')
    text = models.CharField(max_length=255)


class QuizOutcome(models.Model):
    quiz = models.ForeignKey(Quiz, related_name="outcome_set")
    text = models.CharField(max_length=255)


class QuizAnswer(models.Model):
    question = models.ForeignKey(QuizQuestion, related_name='answer_set')
    text = models.CharField(max_length=255)
    outcome = models.ForeignKey(QuizOutcome, null=True, blank=True)
