import base64
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from recipes.models import (Tag, Recipe, Ingredient,
                            RecipeIngridients, Follow, ShoppingList, Favorite)
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model


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


class RecipeIngridientsSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngridients
        fields = ('amount', 'name', 'id', 'measurement_unit')

    def get_name(self, obj):
        return obj.ingredient.name

    def get_id(self, obj):
        return obj.ingredient.id

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name', 'color')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngridientsSerializer(source='recipeingridients_set',
                                              read_only=True,
                                              many=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'text', 'cooking_time', 'image',
                  'is_favorited', 'is_in_shopping_cart')


class ImageField(serializers.Field):

    def to_representation(self, value):
        return 'sdfsdf'

    def to_internal_value(self, data):
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        image = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return image


class RecipeIngridientsSerializerCreate(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngridients
        fields = ('amount', 'id')


class RecipeSerializerCreate(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = ImageField()
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngridientsSerializerCreate(many=True)

    class Meta:
        model = Recipe
        fields = ('tags', 'ingredients', 'name', 'text',
                  'cooking_time', 'image', 'id', 'author')
        read_only_fields = ['id', 'author']

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        for i in range(len(tags_data)):
            recipe.tags.add(tags_data[i])
        for i in range(len(ingredients_data)):
            ingredient = ingredients_data[i]['id']
            RecipeIngridients.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredients_data[i]['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        for i in range(len(ingredients_data)):
            ingredient = ingredients_data[i]['id']
            RecipeIngridients.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=ingredients_data[i]['amount'])

        return instance


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
