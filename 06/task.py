def peel(cls):
    return {attr for attr in dir(cls) if not attr.startswith("_")}


def implements(interface):
    def inner(cls):
        not_implemented = peel(interface) - peel(cls)
        assert not not_implemented, (
            f"methods {not_implemented} are not implemented"
        )
    return inner


class Expr():
    def __call__(self, **env):
        pass

    def d(self, wrt):
        pass

    @property
    def simplified(self):
        return self

    def __neg__(self):
        return Product(Const(-1), self)

    def __pos__(self):
        return self

    def __add__(self, other):
        return Sum(self, other)

    def __sub__(self, other):
        return Sum(self, -other)

    def __mul__(self, other):
        return Product(self, other)

    def __truediv__(self, other):
        return Fraction(self, other)

    def __pow__(self, power, modulo=None):
        return Power(self, power)


class Const(Expr):
    def __init__(self, value):
        self.value = value

    def __call__(self, **env):
        return self.value

    def d(self, wrt):
        return Const(0)

    def __repr__(self):
        return f"Const({self.value})"

    def __str__(self):
        return str(self.value)

    @property
    def is_constexpr(self):
        return True


class Var(Expr):
    def __init__(self, variable):
        self.variable = variable

    def __call__(self, **env):
        return env[self.variable]

    def d(self, wrt):
        return Const(int(self.variable == wrt.variable))

    def __repr__(self):
        return f"Var({self.variable!r})"

    def __str__(self):
        return str(self.variable)

    @property
    def is_constexpr(self):
        return False


C = Const
V = Var


class BinOp(Expr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return f"{self.__class__.__name__}({self.lhs!r}, {self.rhs!r})"

    def __str__(self):
        return f"({self.sign} {self.lhs} {self.rhs})"

    @property
    def is_constexpr(self):
        return self.lhs.is_constexpr and self.rhs.is_constexpr

    @property
    def simplified(self):
        if self.is_constexpr:
            return C(self())
        return self.__class__(self.lhs.simplified, self.rhs.simplified)


class Sum(BinOp):
    sign = "+"

    def __call__(self, **env):
        return self.lhs(**env) + self.rhs(**env)

    def d(self, wrt):
        return self.lhs.d(wrt) + self.rhs.d(wrt)


class Product(BinOp):
    sign = "*"

    def __call__(self, **env):
        return self.lhs(**env) * self.rhs(**env)

    def d(self, wrt):
        return self.lhs.d(wrt) * self.rhs + self.lhs * self.rhs.d(wrt)


class Fraction(BinOp):
    sign = "/"

    def __call__(self, **env):
        return self.lhs(**env) / self.rhs(**env)

    def d(self, wrt):
        numerator = self.lhs.d(wrt) * self.rhs - self.lhs * self.rhs.d(wrt)
        denominator = self.rhs * self.rhs
        return numerator / denominator


class Power(BinOp):
    sign = "**"

    def __call__(self, **env):
        return self.lhs(**env) ** self.rhs(**env)

    def d(self, wrt):
        if self.rhs() == 0:
            return Const(0)
        return self.lhs.d(wrt) * self.rhs * self.lhs ** (self.rhs - Const(1))


def newton_raphson(f, x_0, *, threshold):
    d = f.d(V("x"))

    x_current = x_0
    x_next = x_current - f(x=x_current) / d(x=x_current)

    while abs(x_next - x_current) > threshold:
        x_current = x_next
        x_next = x_current - f(x=x_current) / d(x=x_current)

    return x_next
