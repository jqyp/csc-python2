# Задание 1 (4 балла)

**a)** Используя библиотеку `hypothesis`, напишите property-based тесты для следующих
знакомых функций: `common_prefix`, `factor` и `chunked`

* `common_prefix` из задания 04
* `factor` из задания 05,
* `chunked` из задания 08.

Все тестируемые функции нужно поместить в отдельный модуль с именем `sut.py`.
Для запуска тестов воспользуйтесь командой `python3 -m pytest task11.py`. Для
установки пакетов `pytest` и `hypothesis` можно воспользоваться утилитой
[pipenv](https://pipenv.readthedocs.io/en/latest/). Не нужно сдавать файл
`sut.py`.


# Задание 2 (4 балла)

В этом задании реализуем прототип библиотеки для тестирования свойств. В основе
библиотеки две сущности

  * класс `Strategy`, специфицирующий, как порождать значения разных типов,
  * декоратор `given`, позволяющий проверить свойство с использованием указанных
    стратегий.


Структура базового класса `Strategy` следующая:

```
from collections.abc import Iterator


class Strategy(Iterator):
    def __or__(self, other):
        return OneOfStrategy(self, other)

    def example(self):
        return next(self)
```

Класс реализует два метода:

  * `__or__` объединяет две стратегии в одну, порождающую значения из из одной
    или из другой стратегии -- из какой именно, выбирается случайным образом.
  * `example` возвращает случайное значение, порождённое стратегией.

Наследники класса должны определить метод `__next__`.

**a)** Реализуйте стратегию `OneOfStrategy`, принимающую несколько других стратегий.
При порождении элемента эта стратегия случайным образом выбирает стратегию из
переданных, а затем порождает значение с её помощью.

Вам может быть полезна функция `random.choice`, выбирающая случайный элемент из
переданной коллекции:

```
>>> random.choice([4, 2, 1, 3])
3
>>> random.choice([4, 2, 1, 3])
2
```

**b)** Напишите стратегию `ConstStrategy`. Она порождает только переданное ей
значение.

```
>>> s = ConstStrategy(42)
>>> s.example()
42
>>> s.example()
42
```

**c)** Для реализацйии следующих стратегий порождения чисел с плавающей точкой
понадобится модуль [`random`](https://docs.python.org/3/library/random.html).

* `UniformFloatStrategy` порождает значения из равномерного распределения на
  интервале `[0, 1)`.

   ```
   >>> UniformFloatStrategy().example()
   0.3262700324855873
   ```
   
* `GaussianFloatStrategy` порождает значения из стандартного нормального
  распределения.

   ```
   >>> GaussianFloatStrategy().example()
   -0.06090826963332564
   ```
   
* `BoundedFloatStrategy` порождает случайные значения из интервала
  `(sys.float_info.min, sys.float_info.max)`.

* `NastyFloatStrategy` порождает специальные значения чисел с плавающей точкой:

   ```
   >>> float("inf")
   inf
   >>> -float("inf")
   -inf
   >>> float("nan")
   nan
   >>> +0.0
   0.0
   >>> -0.0
   -0.0
   >>> sys.float_info.min
   2.2250738585072014e-308
   >>> sys.float_info.max
   1.7976931348623157e+308
   ```


Теперь можно объявить составную стратегию для чисел с плавающей точкой:

```
def floats():
    return (UniformFloatStrategy() | GaussianFloatStrategy() |
            BoundedFloatStrategy() | NastyFloatStrategy())
```

**d)**  Реализуйте декоратор `given`. Декоратор принимает произвольное
количество аргументов-стратегий и натуральное число `n_trials` -- количество
случайных проверок, которые необходимо совершить. Функция-обёртка должна
запустить декорируемую функцию `n_trials` раз на входе, порождённом
стратегиями, и в случае ошибки вывести в `sys.stderr` контрпример.

```
>>> @given(floats(), n_trials=1024)
... def test_add(x):
...     assert x + 1 == 42
...
>>> test_add()
Counterexample:  test_add(0.6932690929242101)
Traceback (most recent call last):
  ...
AssertionError
```

К сожалению, магия `py.test` не позволяет безболезненно заменить функцию с
аргументом на функцию-обёртку без аргументов. Чтобы убедить `py.test` в наших
намерениях, нужно удалить у функции-обёртки атрибут `__wrapped__`, установленный
декоратором `functools.wraps`. Честное решение проблемы требует использования
модуля `inspect`, который выходит за рамки домашнего задания.
