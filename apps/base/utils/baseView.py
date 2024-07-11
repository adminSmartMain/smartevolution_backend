from rest_framework.views import APIView
# Utils
from apps.base.utils.index import CustomPagination


class BaseAV(APIView):
        pagination_class = CustomPagination

        @property
        def paginator(self):
            """The paginator instance associated with the view, or `None`."""
            if not hasattr(self, '_paginator'):
                if self.pagination_class is None:
                    self._paginator = None
                else:
                    self._paginator = self.pagination_class()
            return self._paginator

        def paginate_queryset(self, queryset):
            """Return a single page of results, or `None` if pagination is disabled."""
            if self.paginator is None:
                return None

            return self.paginator.paginate_queryset(queryset, self.request, view=self)


        def get_paginated_response(self, data):
            """Return a paginated style `Response` object for the given output data."""
            assert self.paginator is not None
            return self.paginator.get_paginated_response(data)



'''
example
city = City.objects.all().order_by('description')
                    page = self.paginate_queryset(city)
                    if page is not None:
                        serializer = CitySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
'''