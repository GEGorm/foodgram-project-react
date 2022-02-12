from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser import views
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngridient, ShoppingList, Tag)
from .permissions import OwnerOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeIngridientsSerializer,
                          RecipeSerializer, RecipeSerializerCreate,
                          ShoppingListSerializer, TagSerializer)
from .mixins import (CreateDestroyMixin, CreateListDeleteViewSet,
                     ListOneMixin, ShoppingFavoriteMixin)
from .filters import RecipeFilter

User = get_user_model()


class IngredientsViewSet(ListOneMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(ListOneMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(CreateListDeleteViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (OwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeSerializerCreate
        return RecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        return queryset.add_flags(self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeIngridientsViewSet(CreateListDeleteViewSet):
    queryset = RecipeIngridient.objects.all()
    serializer_class = RecipeIngridientsSerializer
    permission_classes = (AllowAny,)


@api_view()
@permission_classes([IsAuthenticated, ])
def shopping_list_file(request):
    recipes = list(request.user.shopping_list.all()
                   .values_list('recipe', flat=True))
    ingridients = (RecipeIngridient.objects.all()
                   .filter(recipe__in=recipes)
                   .values('ingredient').annotate(amount=Sum('amount')))

    filename = "my-file.txt"
    content = ""
    for line in ingridients:
        ingredient_id = line.get('ingredient')
        ingridient = get_object_or_404(Ingredient, id=ingredient_id)
        line.get('ingredient')
        m_unit = ingridient.measurement_unit
        content += f'{ingridient.name}  {m_unit}  {line.get("amount")} \n'
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


class ShoppingListViewSet(ShoppingFavoriteMixin):
    model = ShoppingList
    serializer_class = ShoppingListSerializer
    queryset = ShoppingList.objects.all()


class FavoriteViewSet(ShoppingFavoriteMixin):
    model = Favorite
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()


class UserViewSet(views.UserViewSet):

    def get_queryset(self):
        user_id = self.request.user.id
        return self.queryset.all().annotate(
            is_subscribed=Exists(
                Follow.objects.filter(
                    user_id=user_id, author__id=OuterRef('id')
                )
            )
        )


class FollowViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    model = Follow
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user_id = self.request.user.id
        return (self.request.user.follower.all()
                .annotate(recipes_count=Count('author__recipes'))
                .annotate(is_subscribed=Exists(
                    Follow.objects.filter(
                        user_id=user_id, author__id=OuterRef('id')
                    )
                )))

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        serializer.save(user=self.request.user, author=author)


class FollowEditViewSet(CreateDestroyMixin):
    model = Follow
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        return Follow.objects.filter(author=author)

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        serializer.save(user=self.request.user, author=author)

    def destroy(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        user = self.request.user
        instance = get_object_or_404(Follow, author=author, user=user)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
