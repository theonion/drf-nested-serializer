from django.core.urlresolvers import reverse
from django.test import TestCase
from model_mommy import mommy
from rest_framework.test import APIClient

from .models import *  # noqa


class ArticleTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_serialization(self):
        ft = FeatureType.objects.create(name='some ft')
        article = Article.objects.create(title='some article', feature_type=ft)

        url = reverse('api:article-detail', kwargs={'pk': article.pk})
        response = self.client.get(url, format='json')
        response = response.data

        expected = {
            'id': article.id,
            'title': article.title,
            'unnecessary': None,
            'tags': [],
            'feature_type': {
                'id': ft.pk,
                'name': ft.name,
            },
        }

        self.assertEqual(response, expected)

    def test_create(self):
        url = reverse('api:article-list')

        ft = FeatureType.objects.create(name='article')

        payload = {
            'title': 'some dumb article',
            'feature_type': {
                'id': ft.pk,
            },
            'tags': [],
            'unnecessary': None,
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertIn(response.status_code, (200, 201, 202))

    def test_create_nested_model_raises_error(self):
        url = reverse('api:article-list')
        payload = {
            'title': 'some dumb article',
            'feature_type': {
                'name': 'ka-pow'
            },
            'tags': [],
            'unnecessary': None,
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_create_nested_list_raises_error(self):
        url = reverse('api:article-list')

        ft = mommy.make(FeatureType)
        ft.save()

        payload = {
            'title': 'another dumb article',
            'feature_type': {
                'id': ft.pk,
            },
            'tags': [{
                'name': 'Ka Pow!'
            }],
            'unnecessary': None,
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_update_primitive(self):
        ft = mommy.make(FeatureType)
        ft.save()
        article = mommy.make(Article, feature_type=ft)
        article.save()

        url = reverse('api:article-detail', kwargs={'pk': article.pk})

        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, 200)

        payload = get_response.data
        payload['title'] = 'some new title'

        update_response = self.client.put(url, data=payload, format='json')
        self.assertIn(update_response.status_code, (200, 201, 202))
        self.assertEqual(update_response.data['title'], payload['title'])

    def test_update_nested_model(self):
        ft = mommy.make(FeatureType)
        ft.save()
        article = mommy.make(Article, feature_type=ft)
        article.save()

        url = reverse('api:article-detail', kwargs={'pk': article.pk})

        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, 200)

        payload = get_response.data

        new_ft = mommy.make(FeatureType)
        payload['feature_type'] = {
            'id': new_ft.pk,
        }

        update_response = self.client.put(url, data=payload, format='json')
        self.assertIn(update_response.status_code, (200, 201, 202))
        self.assertEqual(update_response.data['feature_type']['id'], payload['feature_type']['id'])

        # link up nullable field
        unnecessary = mommy.make(UnnecessaryModel)
        unnecessary.save()
        count_unn = UnnecessaryModel.objects.all().count()

        payload = update_response.data
        payload['unnecessary'] = {
            'id': unnecessary.pk,
        }

        update_response = self.client.put(url, data=payload, format='json')
        self.assertIn(update_response.status_code, (200, 201, 202))
        self.assertEqual(update_response.data['unnecessary']['id'], payload['unnecessary']['id'])

        # remove it
        payload = update_response.data
        payload['unnecessary'] = None

        update_response = self.client.put(url, data=payload, format='json')
        self.assertIn(update_response.status_code, (200, 201, 202))
        self.assertEqual(update_response.data['unnecessary'], None)

        # make sure it still exists
        unns = UnnecessaryModel.objects.all().count()
        self.assertEqual(unns, count_unn)

    def test_update_nested_list(self):
        ft = mommy.make(FeatureType)
        ft.save()
        article = mommy.make(Article, feature_type=ft)
        article.save()

        url = reverse('api:article-detail', kwargs={'pk': article.pk})

        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, 200)

        payload = get_response.data

        tag = mommy.make(Tag)
        count_tags = Tag.objects.all().count()

        payload['tags'] = [{
            'id': tag.pk,
        }, ]

        update_response = self.client.put(url, data=payload, format='json')
        self.assertIn(update_response.status_code, (200, 201, 202))
        self.assertEqual(update_response.data['tags'][0]['id'], payload['tags'][0]['id'])

        # remove it
        payload['tags'] = []
        update_response = self.client.put(url, data=payload, format='json')
        self.assertIn(update_response.status_code, (200, 201, 202))
        self.assertEqual(len(update_response.data['tags']), 0)

        # but make sure it still exists
        tags = Tag.objects.all().count()
        self.assertEqual(tags, count_tags)


class QuizTests(TestCase):
    """tests complex serialization. other functionality is covered above.
    """
    def setUp(self):
        self.client = APIClient()

    def test_serialization(self):
        quiz = Quiz.objects.create(title='some quiz')
        question = QuizQuestion.objects.create(text='herr derr', quiz=quiz)
        outcome = QuizOutcome.objects.create(text='herr derr', quiz=quiz)
        answer = QuizAnswer.objects.create(text='herr derr', question=question, outcome=outcome)

        url = reverse('api:quiz-detail', kwargs={'pk': quiz.pk})
        response = self.client.get(url, format='json')
        response = response.data

        expected = {
            'id': quiz.pk,
            'title': quiz.title,
            'question_set': [{
                'id': question.pk,
                'text': question.text,
                'quiz': quiz.pk,  # could make this go away with an exclude in the meta...
                'answer_set': [{
                    'id': answer.pk,
                    'text': answer.text,
                    'question': question.pk,  # same here
                    'outcome': outcome.pk,
                }, ],
            }, ],
            'outcome_set': [{
                'id': outcome.pk,
                'text': outcome.text,
                'quiz': quiz.pk,  # and this too
            }],
        }

        self.assertEqual(response, expected)
