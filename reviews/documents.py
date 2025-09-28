from django_opensearch_dsl import Document
from django_opensearch_dsl.registries import registry

from .models import Review


@registry.register_document
class ReviewDocument(Document):
    class Index:
        name = 'reviews'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
        auto_refresh = False

    class Django:
        model = Review
        fields = ['text']
        queryset_pagination = 5000
