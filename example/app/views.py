from rest_framework import routers, viewsets

from .models import Article
from .serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()


router = routers.DefaultRouter(trailing_slash=True)
router.register(r'articles', ArticleViewSet, base_name='article')
