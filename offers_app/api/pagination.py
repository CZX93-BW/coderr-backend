"""Paginate offers and let callers choose the page size."""

from rest_framework.pagination import PageNumberPagination


class OfferPagination(PageNumberPagination):
    """Return offers in pages with a bounded client-selected page size."""

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100
