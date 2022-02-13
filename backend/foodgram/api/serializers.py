from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngridient, ShoppingList, Tag)
from .fields import ImageField, TagsField

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'id', 'is_subscribed')
        read_only_fields = ['id']


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name', 'color')


class RecipeIngridientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngridient
        fields = ('amount', 'id', 'name', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngridientsSerializer(source='recipeingridient_set',
                                              read_only=True,
                                              many=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'text', 'cooking_time', 'image',
                  'is_favorited', 'is_in_shopping_cart')


class RecipeSerializerCreate(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        pk_field=TagsField()
    )
    image = ImageField()
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngridientsSerializer(source='recipeingridient_set',
                                              many=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('tags', 'ingredients', 'name', 'text',
                  'cooking_time', 'image', 'id', 'author',
                  'is_favorited', 'is_in_shopping_cart')
        read_only_fields = ['id', 'author',
                            'is_favorited', 'is_in_shopping_cart']

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return ShoppingList.objects.filter(user=user, recipe=obj).exists()

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingridient_set')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        return self.update_related_data(ingredients_data, tags_data, recipe)

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        return self.update_related_data(ingredients_data, tags_data, instance)

    def update_related_data(self, ingredients_data, tags_data, recipe):
        for tag in tags_data:
            recipe.tags.add(tag)
        for ingredient_el in ingredients_data:
            ingredient_id = ingredient_el['ingredient'].get('id')
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            RecipeIngridient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_el['amount']
            )
        return recipe

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data

        if data['cooking_time'] < 1:
            raise serializers.ValidationError(
                    'Время приготовления должно быть больше ноля')
        ingredients = []
        for ingredient in data['recipeingridient_set']:
            ingredients.append(ingredient['ingredient'].get('id'))
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество ингредиентов должно быть больше ноля')
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'В запросе присутствуют дублирующиеся ингредиенты')
        if len(data['tags']) != len(set(data['tags'])):
            raise serializers.ValidationError(
                'В запросе присутствуют дублирующиеся тэги')
        return data


class ShoppingListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    cooking_time = serializers.CharField(source='recipe.cooking_time',
                                         read_only=True)
    image = serializers.CharField(source='recipe.image', read_only=True)

    class Meta:
        model = ShoppingList
        fields = ('id', 'name', 'cooking_time', 'image')

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data

        recipe_id = request.parser_context.get('kwargs').get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.context['request'].user
        if ShoppingList.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                'Нельзя добавить в список покупок один рецепт дважды')
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    cooking_time = serializers.CharField(source='recipe.cooking_time',
                                         read_only=True)
    image = serializers.CharField(source='recipe.image', read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'cooking_time', 'image')

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data

        recipe_id = request.parser_context.get('kwargs').get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.context['request'].user

        if Favorite.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                'Нельзя добавить в избранное один рецепт дважды')
        return data


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'password', 'id')
        read_only_fields = ['id']


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(source='author.first_name',
                                       read_only=True)
    last_name = serializers.CharField(source='author.last_name',
                                      read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes = RecipeShortSerializer(source='author.recipes',
                                    many=True,
                                    read_only=True)

    class Meta:
        model = Follow
        fields = ('email',  'id', 'username',
                  'first_name', 'last_name',
                  'recipes_count', 'recipes', 'is_subscribed')

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data
        author_id = request.parser_context.get('kwargs').get('author_id')
        author = get_object_or_404(User, id=author_id)
        user = self.context['request'].user
        if author == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')
        if Follow.objects.filter(author=author, user=user).exists():
            raise serializers.ValidationError(
                'Нельзя подписаться дважды')
        return data
