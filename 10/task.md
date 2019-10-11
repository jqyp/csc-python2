# Структуры


Механизм дескрипторов, который мы обсуждали на лекции, позволяет компактно
описывать классы с ограничениями на значения атрибутов. Мы будем называть такие
классы структурами в силу того, что их объявление напоминает структуры из
языка C.

Пример структуры:

```
class Person(Struct):
    name = StringField(max_len=64)
    age = PositiveIntegerField()
```

# Задание 1 (4 балла)

**a)** Реализуйте дескриптор данных `Field`. Конструктор дескриптора принимает
один аргумент `label` -- имя ключа в `__dict__` экземпляра, по которому
дескриптор будет хранить данные.

Класс должен реализовывать все три метода протокола дескрипторов. Несколько
нюансов протокола.

* Методы `__get__` и `__delete__` должны поднимать исключение `AttributeError`
  при попытке прочитать или удалить несуществующий атрибут.

* Аргумент `instance` метода `__get__` может принимать значение `None`. В этом
  случае нужно вернуть сам экземпляр дескриптора.

Пример использования дескриптора:

```
>>> class Point:
...     x = Field("x")
...     y = Field("y")
...
>>> p = Point()
>>> p.x
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError
>>> p.y = 42
>>> del p.y
>>> p.y
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError
```

**b)** Добавьте к классу `Field` метод `clean`. Задача метода `clean` ---
проверить значение, переданное в метод `__set__`, и привести его к нужному
типу. По умолчанию метод должен возвращать значение без изменений:

```
class Field:
    # ...

    def clean(self, value):
        return value
```

Измените метод `Field.__set__`, чтобы он сохранял в `__dict__` экземпляра чистое
значение.

**c)** Реализуйте три подкласса `Field`:

* `StringField` -- поле для строковых данных,
* `IntegerField` -- поле для целых чисел в диапазоне`[min_value, max_value]`,
* `ChoiceField` -- поле, значения которого ограничены заданными вариантами.

Все подклассы должны валидировать значения в методе `clean`. Метод должен
поднимать исключение `ValueError`, если переданное ему значение некорректно.

Пример работы с полями:

```
>>> class Band:
...     name = StringField("name")
...     country = ChoiceField("country", choices={"Russia", "France", "England"})
...     rating = IntegerField("rating", min_value=0, max_value=5)
...
>>>
>>> b = Band()
>>> b.name = "Portishead"
>>> b.origin = "England"
>>> b.rating = 5
>>> b.origin = "Poland"
Traceback (most recent call last):
  # ...
ValueError: Poland must be one of France, Russia, England
>>> b.rating = 42
Traceback (most recent call last):
  # ...
ValueError: 42 must be in [0, 5]
```

# Задание 2 (4 балла)


В текущем виде работа с полями выглядит довольно неудобно. Мы вынуждены
явно передавать метку для каждого поля:

```
>>> class Band:
...     name = StringField("name")  # :(
```

И вручную присваивать значения полям:

```
b = Band()
b.name = "Portishead"               # :(
```

Попробуем исправить ситуацию с помощью метаклассов!

**a)** Измените класс `Field`, чтобы он не требовл `label` в качестве аргумента
конструктора и использовал метод `__set__name` вместо него:

```
>>> class Band:
...     name = StringField()
...     country = ChoiceField(choices={"Russia", "France", "England"})
...     rating = IntegerField(min_value=0, max_value=5)
...
```

**b)** Реализуйте метакласс `StructMeta` с методом `__new__`. Метод `__new__`
должен добавлять к классу метод `__init__`, принимающий аргументы,
соответсвующие полям структуры, и инициализирующий поля. Порядок аргументов
должен быть таким же, как и порядок полей в определении класса.

```
class StructMeta(type):
    def __new__(metacls, name, bases, clsdict):
        if "__init__" not in clsdict:
            # No constructor? Generate the default implementation.
            clsdict["__init__"] = ...
        cls = super().__new__(metacls, name, bases, clsdict)
        return cls
```
 
Конструированние конструктора на лету может показатся магией, но на самом деле
это не очень сложно. Можно сконструировать строковое представление конструктора
и превратить его в функцию при помощи вызова `exec`. В случае с классом `Band`
создание конструктора может выглядеть так:

```
>>> init_source = """\
... def __init__(self, name, country, rating):
...     self.name = name
...     self.country = country
...     self.rating = rating
... """
>>> clsdict = {}
>>> exec(init_source, clsdict)
>>> clsdict["__init__"]
<function __init__ at 0x10dea3b70>
```

Вызов конструктора работает: 

```
>>> Band("Portishead", "England", 5)
<__main__.Band object at 0x105f89ef0>
```

Объявите базовый класс `Struct`, который избавит от необходимости каждый раз
указывать метакласс при объявлении структур:

```
class Struct(metaclass=StructMeta):
    pass
```

**c)** Измените метакласс `StructMeta` так, чтобы он кроме конструктора добавлял
структуре метод `__repr__`. Метод `__repr__` должен возвращать строку вида

```
SomeClass(field1=value1_repr, field2=value2_repr, ...)
```

Порядок пар в строке `field=value` соответствует порядку объявления полей в
структуре. Обратите внимание, что в данном случае можно обойтись без 
использования `exec`.

Итоговое API должно выглядеть так:

```
>>> class Band(Struct):
...     name = StringField()
...     origin = ChoiceField(choices={"Russia", "France", "England"})
...     rating = IntegerField(min_value=0, max_value=5)
...
>>> Band("Portishead", "England", 5)
Band(name='Portishead', origin='England', rating=5)
```

# Задание 3 (4 балла)


Добавим к встроенной коллекции `dict` поддержку отмены и повторения операций.
  

**a)** Реализуйте класс `UndoDict`, наследующийся от абстрактного базового
класса `MutableMapping` из модуля [`collections.abc`](https://docs.python.org/3/library/collections.abc).

Структура класса `UndoDict`:

```
class UndoDict(MutableMapping):
    def __init__(self, initial=None):
        self._data = initial or {}  # начальное значение словаря.

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def __iter__(self):
        pass

    def __len__(self):
        pass
```

Пример работы с классом::

```
>>> d = UndoDict({"foo": 42})
>>> d["foo"]
42
>>> d["bar"] = 24
>>> list(d)
['bar', 'foo']
```

**b)** Паттерн команда инкапсулирует логику прямого и обратного применения
некоторой операции. В Python команду удобно представить в виде класса, метод
`__call__` которого применяет операцию и возвращает новую операцию, отменяющую
результат только что применённой.

Реализуйте команды `SetCommand` и `DelCommand`. Команда `SetCommand` принимает
два аргумента: ключ и значение -- и реализует команду добавления ключа в
словарь, команда `DelCommand` принимает ключ и реализует операцию удаления ключа
из словаря. 

Общий вид классов:

```
class SetCommand:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __call__(self, data):
        # Примените команду к `data` и
        # верните обратную операцию.

class DelCommand:
    def __init__(self, key):
        self.key = key

    def __call__(self, data):
        # Примените команду к `data` и
        # верните обратную операцию.
```

**c)** Добавьте экземплярам `UndoDict` два внутренних атрибута:

* `_undo_log` -- список команд, возвращающих словарь к версии `initial`,
* `_redo_log` --- список команд, приводящих словарь к самой актуальной версии.

Измените методы словаря так, чтобы они добавляли или удаляли команды из
атрибутов `_undo_log` и `_redo_log`.

```
class UndoDict(MutableMapping):
    # ...

    def __setitem__(self, key, value):
        # Выполнить SetCommand и добавить в `_undo_log` обратную операцию.

    def __delitem__(self, key, value):
        # Выполнить DelCommand и добавить в `_undo_log` обратную операцию.
```

Обратите внимание, что история операций в `UndoDict` линейна, поэтому в методах
`__setitem__` и `__delitem__` следует очищать список `_redo_log`. Таким образом,
любое изменение словаря, находящегося на неактуальной версии, делает текущую
версию новой актуальной.

```
>>> d = UndoDict()
>>> d["foo"] = 42
>>> d["bar"] = 24
>>> d  # актуальная версия
{'foo': 42, 'bar': 24}
>>> d.undo()
>>> d["boo"] = 100500
>>> d  # новая актуальная версия
{'foo': 42, 'boo': 100500}
>>> d._redo_log
[]python
```

**d)** Реализуйте метод `UndoDict.undo`, откатывающий словарь на одну версию
*назад. Если текущая версия `initial`, метод должен поднять исключение.

**e)** Реализуйте метод `UndoDict.redo`, приводящий словарь к следующей версии.
*Если текущая версия самая актуальная, метод должен поднять исключение.

Обратите внимание, что последовательные вызовы методов `UndoDict.undo` и
`UndoDict.redo` должны оставить словарь без изменений.

```
>>> d = UndoDict({"foo": 42})
>>> d["bar"] = 24
>>> d
{'foo': 42, 'bar': 24}  # !
>>> d.undo()
>>> d
{'foo': 42}
>>> d.redo()
>>> d
{'foo': 42, 'bar': 24}  # !
```
