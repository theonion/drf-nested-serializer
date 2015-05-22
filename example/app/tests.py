from django.test import TestCase

from .serializers import QuizSerializer, ArticleSerializer
from .models import *  # noqa


class ArticleCase(TestCase):
    def test_serialization(self):
        feature_type = FeatureType.objects.create(name="A.V. Q&A")
        article = Article.objects.create(title="Some thinkpiece", feature_type=feature_type)

        serializer = ArticleSerializer(instance=article)

        self.assertEqual(serializer.data, {
            'id': article.id,
            'title': 'Some thinkpiece',
            'feature_type': {
                'id': feature_type.id,
                'name': 'A.V. Q&A'
            },
            'tags': []
        })

    def test_nested_create(self):
        self.assertEqual(FeatureType.objects.count(), 0)
        serializer = ArticleSerializer(data={
            'title': 'testing',
            'feature_type': {
                'name': 'testing'
            }
        })
        assert serializer.is_valid()
        _ = serializer.save()

        self.assertEqual(FeatureType.objects.count(), 1)

        ft = FeatureType.objects.get()
        serializer = ArticleSerializer(data={
            'title': 'testing 2',
            'feature_type': {
                'id': ft.id,
                'name': ft.name
            }
        })
        assert serializer.is_valid()
        _ = serializer.save()

        self.assertEqual(FeatureType.objects.count(), 1)

    def test_nested_list_create(self):
        """POST
        {
          "title": "whatever",
          "feature_type": {
            "name": "some new feature type"
          },
          "tags": [{
            "id": 1,
            "name": "some existing tag"
          }, {
            "id": 2,
            "name": "another existing tag"
          }]
        }
        """
        self.assertEqual(Tag.objects.count(), 0)
        tag1 = Tag.objects.create(name='tag uno')
        tag2 = Tag.objects.create(name='tag dos')
        serializer = ArticleSerializer(data={
            'title': 'lets test some tags',
            'feature_type': {
                'name': 'tag tester',
            },
            'tags': [{
                'id': tag1.id,
                'name': tag1.name,
            }, {
                'id': tag2.id,
                'name': tag2.name,
            }]
        })
        assert serializer.is_valid()
        _ = serializer.save()
        self.assertEqual(FeatureType.objects.count(), 1)
        self.assertEqual(Tag.objects.count(), 2)

    def test_nested_list_create_full(self):
        """POST
        {
          "title": "whatever",
          "feature_type": {
            "name": "some new feature type"
          },
          "tags": [{
            "name": "some new tag"
          }, {
            "name": "another new tag"
          }]
        }
        """
        self.assertEqual(Tag.objects.count(), 0)
        self.assertEqual(Tag.objects.count(), 0)
        serializer = ArticleSerializer(data={
            'title': 'lets test some tags',
            'feature_type': {
                'name': 'tag tester',
            },
            'tags': [{
                'name': 'tag 1'
            }, {
                'name': 'tag 2'
            }]
        })
        assert serializer.is_valid()
        _ = serializer.save()
        self.assertEqual(FeatureType.objects.count(), 1)
        self.assertEqual(Tag.objects.count(), 2)

    def test_nested_update(self):
        """PUT
        {
          "title": "whatever",
          "feature_type": {
            "id": 2,
            "name": "some existing feature type that wasn't the originally used one"
          }
        }
        """
        self.assertEqual(FeatureType.objects.count(), 0)
        serializer = ArticleSerializer(data={
            'title': 'testing',
            'feature_type': {
                'name': 'DVR Club',
            },
        })
        assert serializer.is_valid()
        _ = serializer.save()
        self.assertEqual(FeatureType.objects.count(), 1)
        ft = FeatureType.objects.create(name='AV Undercover')

        updated_data = serializer.data
        updated_data['feature_type'] = {
            'id': ft.id,
            'name': ft.name,
        }
        serializer = ArticleSerializer(data=updated_data)
        assert serializer.is_valid()
        _ = serializer.save()
        self.assertEqual(_.feature_type.id, ft.id)

    def test_nested_list_update(self):
        """PUT
        {
          "title": "whatever",
          "feature_type": {
            "id": 1,
            "name": "some existing feature type"
          },
          "tags": [{
            "id": 1,
            "name": "some existing tag that wasn't originally used in post"
          }]
        }
        """
        serializer = ArticleSerializer(data={
            'title': 'testing',
            'feature_type': {
                'name': 'Blah blah blah',
            },
        })
        assert serializer.is_valid()
        _ = serializer.save()
        self.assertEqual(Tag.objects.count(), 0)
        tag = Tag.objects.create(name='this is a tag')

        updated_data = serializer.data
        updated_data['tags'].append({
            'id': tag.id,
            'name': tag.name,
        })
        serializer = ArticleSerializer(data=updated_data)
        assert serializer.is_valid()
        _ = serializer.save()
        self.assertEqual(Tag.objects.count(), 1)

    def test_nested_list_update_full(self):
        """PUT
        {
          "title": "whatever",
          "feature_type": {
            "id": 1,
            "name": "some existing feature type"
          },
          "tags": [{
            "name": "some new tag"
          }]
        }
        """
        self.assertEqual(Tag.objects.count(), 0)
        serializer = ArticleSerializer(data={
            'title': 'testing',
            'feature_type': {
                'name': 'Blah blah blah',
            },
        })
        assert serializer.is_valid()
        _ = serializer.save()
        self.assertEqual(Tag.objects.count(), 0)


        updated_data = serializer.data
        updated_data['tags'].append({
            'name': 'this is another tag',
        })
        serializer = ArticleSerializer(data=updated_data)
        assert serializer.is_valid()
        _ = serializer.save()
        self.assertEqual(Tag.objects.count(), 1)


class QuizCase(TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.create(title='testing quiz')
        self.outcome = QuizOutcome.objects.create(text='You win', quiz=self.quiz)
        self.question = QuizQuestion.objects.create(quiz=self.quiz, text='What is the meaning?')
        self.answer = QuizAnswer.objects.create(question=self.question, outcome=self.outcome, text="42")

    def test_serialization(self):
        serializer = QuizSerializer(instance=self.quiz)
        self.assertEqual(serializer.data, {
            'id': self.quiz.id,
            'title': 'testing quiz',
            'outcome_set': [{
                'quiz': self.quiz.id,
                'id': self.outcome.id,
                'text': 'You win'
            }],
            'question_set': [{
                'id': self.question.id,
                'text': 'What is the meaning?',
                'quiz': self.quiz.id,
                'answer_set': [{
                    'id': self.answer.id,
                    'text': '42',
                    'question': self.question.id,
                    'outcome': self.outcome.id
                }]
            }]
        })

    def test_update_field(self):
        serializer = QuizSerializer(instance=self.quiz)
        updated_data = serializer.data

        updated_data['title'] = 'universe quiz'
        updated_data['outcome_set'][0]['text'] = 'You really won that!'

        self.assertEqual(QuizOutcome.objects.count(), 1)

        serializer = QuizSerializer(instance=self.quiz, data=updated_data)
        assert serializer.is_valid()
        serializer.save()

        self.assertEqual(serializer.data['title'], 'universe quiz')
        self.assertEqual(serializer.data['outcome_set'][0]['id'], self.outcome.id)
        self.assertEqual(serializer.data['outcome_set'][0]['text'], 'You really won that!')

        self.assertEqual(QuizOutcome.objects.count(), 1)

        quiz = Quiz.objects.get(id=self.quiz.id)
        self.assertEqual(quiz.title, 'universe quiz')

    def test_nested_errors(self):
        serializer = QuizSerializer(instance=self.quiz)
        updated_data = serializer.data

        updated_data['outcome_set'].append({
            'quiz': self.quiz.id
        })
        serializer = QuizSerializer(instance=self.quiz, data=updated_data)
        assert serializer.is_valid() is False
        self.assertEqual(serializer.errors, {'outcome_set': [{}, {'text': ['This field is required.']}]})

    def test_add_remove_outcome(self):
        serializer = QuizSerializer(instance=self.quiz)
        updated_data = serializer.data

        updated_data['outcome_set'].append({
            'text': 'You lost...',
            'quiz': self.quiz.id
        })

        self.assertEqual(QuizOutcome.objects.count(), 1)

        serializer = QuizSerializer(instance=self.quiz, data=updated_data)
        assert serializer.is_valid()
        serializer.save()

        self.assertEqual(len(serializer.data['outcome_set']), 2)
        self.assertEqual(QuizOutcome.objects.count(), 2)

        updated_data['outcome_set'].pop()  # Kill that last item

        serializer = QuizSerializer(instance=self.quiz, data=updated_data)
        assert serializer.is_valid()
        serializer.save()

        self.assertEqual(len(serializer.data['outcome_set']), 1)
        self.assertEqual(QuizOutcome.objects.count(), 1)
