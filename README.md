Django cors cache modeule
=========================

Модуль для обеспечения полного спектра кэширования.

Кэширование в шаблонах
----------------------

###Query cache

Кэширование доступно только для get/count запросов, остальные не являются эффективными.

###Обычный кэш

Полностью копирует аналогичный тег в Django.

	{% load cors_cache %}
	
	{% cache "cahce_block_name" var1 var2 ... varN cache=cache2 %}
		Content...
	{% endcache %}

###Умный кэш

Для блоков кэша которые должны сбрасываться сразу
после изменения.

   smart_cache block_name [model_links]
   model_links - объекты типа Model


	{% load cors_cache %}
	
	{% smart_cache "cahce_block_name" request.user cache=cache2 %}
		Content...
	{% end_smart_cache %}


Для сброса кэша при изменении других объектов не связанных с кэшем
можно реализовать карту инвалидации, или использовать параметр links.
	
	{% smart_cache "cahce_block_name" request.user cache=cache2 links="news.article.user" %}
		Content...
	{% end_smart_cache %}

Таким образом изменяя или создавая *news.article*, ищется тег с именем
*cahce_block_name* и связанным с полем user в модели news.
Но лучше релизовать карту инвалидации, для этого случая она будет такой:

```python
CORSCACHE_EXTENDET_LINKS = {
	'news.article': {
		'cahce_block_name': {'links':('user',),'cache':'cache2'},
	},
}
```

Example settings
----------------

```python
# -*- coding: utf-8 -*-

CORSCACHE_DEFAULT_TIME = 86400 # 24 Hour
CORSCACHE_DEFAULT_CACHE = 'level1'

# Префиксы к именам кэша
CORSCACHE_BLOCKS_PREFIX = 'blocks'
CORSCACHE_QUERYS_PREFIX = 'queryes'

CORSCACHE_ACTIVE = True
CORSCACHE_QUERYCACHE_ACTIVE = True

#
# Интелект - автоматическая отчистка связанных блоков.
# Если отчистка построена только на правилах то лучше выключить.
#
CORSCACHE_INTELLIGENCE = True

#
# Сторонние связки. [ Карта инвалидации ]
#
# Иногда невозможно реализовать динамическую привязку блока к объекту,
# Просто потому что это неимеет никакого смысла
# Ведь наша задача ограничить число запросов,
# и вот здесь помогут связки объекта с блоками.
#
# Определим какой объект должен влиять на блок
#
# 'news.article': { 'news': {'links':('user',),'cache':'cacheName'}, 'catalog.product': ('section',) }
# Он влияет на блок новостей посредством своей связи с пользователем.
# В этом случае блок у нас объявлен как:
#
# {% smart_cache "news" autor cache=cacheName %} ... {% end_smart_cache %}
#
# При изменении или создании новости сбрасывается кэш этой группу связанный с пользователем
#

# Карта инвалидации
CORSCACHE_EXTENDET_LINKS = {
	# Инвалидация по моим друзьям
	# Проводится при создании/удалении или изменении друга
	'friendlent.friend': {
		'user_info': ('user',), # Инвалидируем блок user_info связанный с user
		'planes_block': ('user',), # Обновим планы
		'notifi_block': ('user',), # Обновим уведомления
		'notifies_index': ('user',), # Обновим уведомления index
		'friendlent_general': ('user',), # Блок друзей справа
	},
	'profile.profile': {
		'user_info': ('user',), # Инвалидируем блок user_info связанный с user
	},
	# Блок хочу побывать справа
	'geographi.iwas': {
		'wantvisited_city': {'links':('user',),'cache':'level2'},
		'visited_city': {'links':('user',),'cache':'level2'},
	},
	# Обновление уведомлений
	'reester.atom': {
		'notifi_block': ('user',), # Обновим уведомления
		'notifies_index': ('user',), # Обновим уведомления index
	},
}

# Кэширование запросов
CORSCACHE_QUERY_CACHE = {
	'auth.user':{'get':3600}, # Получить Пользователя на час
	'profile.profile':{'get':3600}, # Получить профиль на час
	'*.*': {'count':3600,'cache':'level2'}, # Кэшируем все count запросы на час
}
```
