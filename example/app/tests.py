from django.test import TestCase


from .serializers import QuizSerializer, ArticleSerializer
from .models import *  # noqa


class ArticleCase(TestCase):
	
	def test_update(self):
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
