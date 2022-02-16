from django_filters import FilterSet, ModelMultipleChoiceFilter, BooleanFilter
from django_filters.widgets import BooleanWidget

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = BooleanFilter(method="favorited", widget=BooleanWidget())
    is_in_shopping_cart = BooleanFilter(method="shopping_cart",
                                        widget=BooleanWidget())

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
