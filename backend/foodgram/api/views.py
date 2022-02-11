from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from recipes.models import (Tag, Recipe, RecipeIngridients,
                            ShoppingList, Favorite, Ingredient, Follow)
from rest_framework import filters, mixins, status, viewsets
from .serializers import (TagSerializer, RecipeSerializer,
                          RecipeSerializerCreate, RecipeIngridientsSerializer,
                          ShoppingListSerializer, FavoriteSerializer,
                          FollowSerializer, IngredientSerializer)
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Sum, OuterRef, Count, Exists
from django.contrib.auth import get_user_model
from djoser import views
from .permissions import OwnerOrReadOnly

User = get_user_model()


class CreateListDeleteViewSet(mixins.CreateModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin,
                              mixins.DestroyModelMixin,
                              viewsets.GenericViewSet):
    pass


class ListOneMixin(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    pass


class CreateDestroyMixin(mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    pass


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

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeSerializerCreate
        return RecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == 1:
            fav = list(user.favorite.all().values_list('recipe', flat=True))
            queryset = queryset.filter(id__in=fav)
        in_cart = self.request.query_params.get('is_in_shopping_cart')
        if in_cart == 1:
            shop_list = list(user.shopping_list.all().
                             values_list('recipe', flat=True))
            queryset = queryset.filter(id__in=shop_list)
        tags = self.request.query_params.getlist('tags')
        if len(tags) > 0:
            queryset = queryset.filter(tags__slug__in=tags)
        author = self.request.query_params.get('author')
        if author is not None:
            queryset = queryset.filter(author=author)
        return queryset.add_flags(user.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = RecipeSerializer(
            instance=serializer.instance)

        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        response_serializer = RecipeSerializer(
            instance=serializer.instance)
        return Response(response_serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeIngridientsViewSet(CreateListDeleteViewSet):
    queryset = RecipeIngridients.objects.all()
    serializer_class = RecipeIngridientsSerializer
    permission_classes = (AllowAny,)


@api_view()
@permission_classes([IsAuthenticated, ])
def shopping_list_file(request):
    recipes = list(request.user.shopping_list.all()
                   .values_list('recipe', flat=True))
    ingridients = RecipeIngridients.objects.all() \
        .filter(recipe__in=recipes) \
        .values('ingredient').annotate(amount=Sum('amount'))

    filename = "my-file.txt"
    content = ""
    for line in ingridients:
        id = line.get('ingredient')
        ingridient = get_object_or_404(Ingredient, id=id)
        line.get('ingredient')
        m_unit = ingridient.measurement_unit
        content += f'{ingridient.name}  {m_unit}  {line.get("amount")} \n'
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


class ShoppingListViewSet(CreateDestroyMixin):
    model = ShoppingList
    serializer_class = ShoppingListSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ShoppingList.objects.all()

    def get_queryset(self):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        return ShoppingList.objects.filter(recipe=recipe)

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        serializer.save(user=self.request.user, recipe=recipe)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        user = self.request.user
        instance = get_object_or_404(ShoppingList, recipe=recipe, user=user)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(CreateDestroyMixin):
    model = Favorite
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Favorite.objects.all()

    def get_queryset(self):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        return Favorite.objects.filter(recipe=recipe)

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        serializer.save(user=self.request.user, recipe=recipe)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        user = self.request.user
        instance = get_object_or_404(Favorite, recipe=recipe, user=user)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
