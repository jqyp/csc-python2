# Задание 1 (4 балла)

Следующие задания можно реализовать либо с помощью
`reduce`, либо без него -- руководствуйтесь здравым смыслом.

**a)** Используя оператор `|`, реализуйте функцию `union`, возвращающую
объединение произвольного числа множеств.

```
>>> union({1, 2, 3}, {10}, {2, 6})
{1, 2, 3, 6, 10}
```

**b)** Реализуйте функцию `digits`, возвращающую список цифр неотрицательного
целого числа.

```
>>> digits(0)
[0]
>>> digits(1914)
[1, 9, 1, 4]
```

Пользоваться функцией `str` для реализации функции `digits` нельзя.

**c)** Напишите функцию `lcm`, вычисляющую НОК (наименьшее общее кратное) двух и
более целых чисел.

```
>>> lcm(100500, 42)
703500
>>> lcm(*range(2, 40, 8))
19890
```

**d)** Реализуйте функцию `compose`, которая принимает две и более функции от
одного аргумента, и возвращает их композицию.

```
>>> f = compose(lambda x: 2 * x, lambda x: x + 1, lambda x: x % 9)
>>> f(42)
14
>>> 2 * ((42 % 9) + 1)
14
```

# Задание 2 (4 балла)

Все декораторы из последующих заданий должны корректно работать с внутренними
атрибутами функции, например, `__name__`.


**a)** Измените декоратор `once` из лекции, чтобы он поддерживал функции,
возвращающие не `None` значения.

```
>>> @once
... def initialize_settings():
...     print("Settings initialized.")
...     return {"token": 42}
...
>>> initialize_settings()
Settings initialized.
{'token': 42}
>>> initialize_settings()
{'token': 42}
```

Для функций, возвращающих `None`, декоратор должен продолжать
работать.

**b)** Измените декоратор `trace`, чтобы он выводил информацию о
вызове функции, только если переданные аргументы удовлетворяют предикату.

```
>>> @trace_if(lambda x, y, **kwargs: kwargs.get("integral"))
... def div(x, y, integral=False):
...     return x // y if integral else x / y
...
>>> div(4, 2)
2.0
>>> div(4, 2, integral=True)
div(4, 2, integral=True) = ...
div(4, 2, integral=True) = 2
2
```



**c)** Реализуйте декоратор `n_times`. Результатом его работы должна быть
функцию, вызывающая декорируемую функцию `n` раз. Возвращаемое значение
декорируемой функции можно игнорировать.

```
>>> @n_times(3)
... def do_something():
...     print("Something is going on!")
...
>>> do_something()
Something is going on!
Something is going on!
Something is going on!
```

# Задание 3, Pyke (4 балла)

Существует много инструментов для сборки проектов, например, `make`, `ant`,
`rake`. Обилие вариантов -- следствие того, что идеального решения этой задачи
ещё нет. Мы попробуем реализовать прототип похожего инструмента в виде
библиотеки на Python.

**a)** Описание сборки проекта -- это набор заданий. Напишите функцию `project`,
которая возвращает декоратор `register`. С помощью декоратора `register` можно
запомнить (зарегистрировать) функцию как задание для сборки. Можно считать, что
декоратор `register` будет применяться только к функциям без аргументов и без
возвращаемого значения. Список имён всех заданий в порядке объявления в модуле
должен быть доступен через метод `get_all` у декоратора `register`.

```
>>> register = project()
>>> @register
... def do_something():
...     print("doing something")
...
>>> @register
... def do_other_thing():
...     print("doing other thing")
...
>>> register.get_all()
['do_something', 'do_other_thing']
```

Добавить метод `get_all` к декоратору `register` можно через присванивание.
Например, если бы мы хотели, чтобы функция `get_all` возвращала пустой список,
мы бы сделали так:

```
>>> register.get_all = lambda: []
>>> register.get_all()
[]
```

Вызов задания должен работать как вызов обычной функции.
 
```
>>> do_something()
doing something
>>> do_other_thing()
doing other thing
```

**b)** Реализуйте возможность указывать зависимости между заданиями, как это
показано в примере:

```
>>> @register
... def do_something():
...     print("doing something")
...
>>> @register(depends_on=["do_something"])
... def do_other_thing():
...     print("doing other thing")
...
```

Список зависимостей для задачи должен быть доступен через метод
`get_dependencies`:

```
>>> do_something.get_dependencies()
[]
>>> do_other_thing.get_dependencies()
['do_something']
```

**c)** Можно заметить, что все объявления задач образуют ориентированный граф, в
котором каждой задаче соответствутет вершина, а ребро между задачами `a` и `b`
проводится, если

```
"b" in a.get_dependencies()
```

Будем называть этот граф *графом зависимостей*. Для простоты давайте считать,
что граф ацикличен.

Измените логику выполнения зарегистрированных задач таким образом, чтобы перед
выполнением задачи сначала выполнились все её зависимости в порядке обратной
топологической сортировки.

Для задач без зависимостей логика выполнения должна остаться без изменений.

```
>>> @register
... def do_something():
...     print("doing something")
...
>>> @register(depends_on=["do_something"])
... def do_other_thing():
...     print("doing other thing")
...
>>> do_something()
doing something
>>> do_other_thing()
doing something
doing other thing
```

В данном случае граф состоит всего из двух вершин:

```
do_something <- do_other_thing
```

Более интересный пример выглядит так:

```
>>> register = project()
>>> @register
... def task_a():
...     print("task_a")
...
>>> @register(depends_on=["task_a"])
... def task_b():
...     print("task_b")
...
>>> @register(depends_on=["task_a"])
... def task_c():
...     print("task_c")
...
>>> @register(depends_on=["task_b", "task_c"])
... def task_d():
...     print("task_d")
...
>>> task_d()
task_a
task_b
task_c
task_d
```

Ему соответствует такой граф:

```
    task_a
    ^    ^
   /      \
 task_b   task_c
   ^      ^
    \    /
    task_d
```

В данном случае, есть два возможных порядка исполнения заданий:
`a, b, c, d` или `a, c, b, d`.