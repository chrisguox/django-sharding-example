# django-sharding-example

项目代码借鉴了[django_table_sharding_example](https://github.com/iTraceur/django_table_sharding_example)，重新处理了下代码，并做了一些可读性上的处理；



## 实现

整体的实现其实是通过type，将abstract model “注册”成一个model。

其他使用过程跟model并无不同。



其他组件需要跟model对应的时候，只需要做类似如下处理就好，如 `django_filter`

```
class DemoViewSet:
	def _dynamic_filter_backend(self, queryset):
		class Meta:
			model = queryset.model
			fields = filters.DemoFilter._meta.fields

        filterset_class = (f"<Filter>", (filters.CoCoLineFilter, ), {"Meta": Meta})
        self.filterset_class = filterset_class
```



## 使用

```
from <path> import sharding

class DemoModel(sharding.PreciseShardingMixin, model.Model):
    class Meta:
        abstract = True

	# 定义分表数量
	_SHARDING_NUMBERS = 128


	...
	
# 注册映射的model
sharding.register_models(CoCoLineSharding)

```



```
# 通过sharding找到对应sharding model，与数据表一一对应
DemoModel.sharding(<number>).<func_method>
```

