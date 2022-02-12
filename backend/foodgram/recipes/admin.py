from django.contrib import admin
from .models import (Favorite, Follow, Ingredient, Recipe,
                     RecipeIngridient, ShoppingList, Tag)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author')
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('in_favorite',)

    def in_favorite(self, obj):
        return len(obj.favorites.all())


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngridient)
admin.site.register(Follow)
admin.site.register(ShoppingList)
admin.site.register(Favorite)
