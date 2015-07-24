from rest_framework import routers, viewsets

from .models import Article, Quiz
from .serializers import ArticleSerializer, QuizSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()


class QuizViewSet(viewsets.ModelViewSet):
    serializer_class = QuizSerializer
    queryset = Quiz.objects.all()


router = routers.DefaultRouter(trailing_slash=True)
router.register(r'articles', ArticleViewSet, base_name='article')
router.register(r'quizzes', QuizViewSet, base_name='quiz')
