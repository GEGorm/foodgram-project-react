from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from recipes.models import Recipe


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


class ShoppingFavoriteMixin(CreateDestroyMixin):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        return self.model.objects.filter(recipe=recipe)

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        serializer.save(user=self.request.user, recipe=recipe)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        user = self.request.user
        instance = get_object_or_404(self.model, recipe=recipe, user=user)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
