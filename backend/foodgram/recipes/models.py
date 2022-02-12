from django.db import models
from django.db.models import Exists, OuterRef

from users.models import User


class Ingredient(models.Model):
    name = models.CharField(max_length=100, verbose_name='name')
    measurement_unit = models.CharField(max_length=15,
                                        verbose_name='measurement_unit')

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return self.name + ', ' + self.measurement_unit


class Tag(models.Model):
    name = models.CharField(max_length=100, verbose_name='name')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='slug')
    color = models.CharField(max_length=15, verbose_name='color')

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class RecipeQuerySet(models.QuerySet):
    def add_flags(self, user_id):
        return self.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user_id=user_id, recipe=OuterRef('id')
                )
            )
        ).annotate(
            is_in_shopping_cart=Exists(
                ShoppingList.objects.filter(
                    user_id=user_id, recipe=OuterRef('id')
                )
            )
        )


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, verbose_name='tag')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор')
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='ingredients',
                                         through='RecipeIngridient')
    name = models.CharField(max_length=100, verbose_name='name')
    text = models.TextField('Текст')
    cooking_time = models.PositiveSmallIntegerField(
        default=0,
        null=True,
        blank=True,
        verbose_name='время приготовления')
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    pub_date = models.DateTimeField("date published",
                                    auto_now_add=True,)

    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngridient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        default=0,
        null=False,
        verbose_name='количество')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='UniqueRecipeIngridient'),
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='favorites')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='UniqueFavoriteEntry'),
        ]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Кулинар')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-author']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='UniqueFollowEntry'),
        ]


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='shop_list',)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='UniqueShoppingEntry'),
        ]
