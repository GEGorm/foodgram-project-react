from django.urls import include, path
from rest_framework.routers import SimpleRouter
from .views import (TagViewSet, RecipeViewSet, RecipeIngridientsViewSet,
                    shopping_list_file, IngredientsViewSet,
                    ShoppingListViewSet, FavoriteViewSet,
                    FollowViewSet, UserViewSet, FollowEditViewSet)

router_v1 = SimpleRouter()
router_v1.register('tags', TagViewSet, basename='Tag')
router_v1.register('recipes', RecipeViewSet, basename='Recipe')
router_v1.register('rec', RecipeIngridientsViewSet, basename='Rec')
router_v1.register('ingredients', IngredientsViewSet, basename='ingredients')
router_v1.register('users/subscriptions',
                   FollowViewSet,
                   basename='subscriptions')


urlpatterns = [
    path('auth/', include("djoser.urls.authtoken")),
    path('users/', UserViewSet.as_view({'get': 'list',
                                        'post': 'create',
                                        })),
    path('users/me/', UserViewSet.as_view({'get': 'me'})),
    path('users/<int:author_id>/subscribe/',
         FollowEditViewSet.as_view({'post': 'create',
                                    'delete': 'destroy',
                                    }),
         name='subscribe'),
    path('users/<int:id>/', UserViewSet.as_view({'get': 'retrieve'})),
    path('users/set_password/', UserViewSet.as_view({'post': 'set_password'})),
    path('recipes/<int:recipe_id>/favorite/',
         FavoriteViewSet.as_view({'post': 'create',
                                  'delete': 'destroy',
                                  }),
         name='favorites'),
    path('recipes/<int:recipe_id>/shopping_cart/',
         ShoppingListViewSet.as_view({'post': 'create',
                                      'delete': 'destroy',
                                      }),
         name='shopping_list'),
    path('', include(router_v1.urls)),
    path('download_shopping_cart/', shopping_list_file, name='shopping_file'),
]
