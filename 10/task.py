from collections.abc import MutableMapping


class Field:
    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self._name not in instance.__dict__:
            raise AttributeError
        return instance.__dict__[self._name]

    def __set__(self, instance, value):
        instance.__dict__[self._name] = self.clean(value)

    def __delete__(self, instance):
        if self._name not in instance.__dict__:
            raise AttributeError
        del instance.__dict__[self._name]

    def clean(self, value):
        return value

    def __set_name__(self, owner, name):
        self._name = name


class StringField(Field):
    def clean(self, value):
        if not isinstance(value, str):
            raise ValueError
        return value


class IntegerField(Field):
    def __init__(self, *, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value

    def clean(self, value):
        if not isinstance(value, int):
            raise ValueError
        if not self.min_value <= value <= self.max_value:
            raise ValueError(
                f"{value} must be in [{self.min_value}, {self.max_value}]"
            )
        return value


class ChoiceField(Field):
    def __init__(self, choices):
        self.choices = choices

    def clean(self, value):
        if value not in self.choices:
            raise ValueError(
                f"{value} must be one of {', '.join(self.choices)}"
            )
        return value


class StructMeta(type):
    def __new__(metacls, name, bases, clsdict):
        labels = [
            label for label in clsdict if isinstance(clsdict[label], Field)
        ]

        if "__init__" not in clsdict:
            if labels:
                func_header = f"def __init__(self, {', '.join(labels)}):"
                func_body = "\n\t".join(
                    f"self.{label} = {label}" for label in labels
                )
                init_source = f"{func_header}\n\t{func_body}"
                exec(init_source, clsdict)

        if "__repr__" not in clsdict:
            def repr(self):
                fields = (
                    f"{label}={getattr(self, label)!r}" for label in labels
                )
                return f"{name}({', '.join(fields)})"

            clsdict["__repr__"] = repr
        cls = super().__new__(metacls, name, bases, clsdict)
        return cls


class Struct(metaclass=StructMeta):
    pass


class Band(Struct):
    name = StringField()
    origin = ChoiceField(choices={"Russia", "France", "England"})
    rating = IntegerField(min_value=0, max_value=5)


class SetCommand:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __call__(self, data):
        if self.key in data:
            undo = SetCommand(self.key, data[self.key])
        else:
            undo = DelCommand(self.key)
        data[self.key] = data.value
        return undo


class DelCommand:
    def __init__(self, key):
        self.key = key

    def __call__(self, data):
        value = data.pop(self.key)
        return SetCommand(self.key, value)


class UndoDict(MutableMapping):
    def __init__(self, initial=None):
        self._data = initial or {}
        self._undo_log = []
        self._redo_log = []

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._redo_log.clear()
        command = SetCommand(key, value)(self._data)
        self._undo_log.append(command)

    def __delitem__(self, key):
        self._redo_log.clear()
        command = DelCommand(key)(self._data)
        self._undo_log.append(command)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def undo(self):
        if not self._undo_log:
            raise ValueError("It's the initial version of dictionary")
        command = self._undo_log.pop()(self._data)
        self._redo_log.append(command)

    def redo(self):
        if not self._redo_log:
            raise ValueError("It's the actual version of dictionary")
        command = self._redo_log.pop()(self._data)
        self._undo_log.append(command)
