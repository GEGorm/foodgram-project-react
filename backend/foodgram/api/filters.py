from django_filters import FilterSet, AllValuesMultipleFilter, BooleanFilter
from django_filters.widgets import BooleanWidget

from recipes.models import Recipe


class RecipeFilter(FilterSet):
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = BooleanFilter(method="favorited", widget=BooleanWidget())
    is_in_shopping_cart = BooleanFilter(method="shopping_cart", widget=BooleanWidget())

    def favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            return Recipe.objects.filter(favorites__user=user)
        return queryset

    def shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return Recipe.objects.filter(shop_list__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']
