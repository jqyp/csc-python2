import socket
from collections import Counter, namedtuple
from contextlib import contextmanager
from itertools import cycle, groupby, islice
from functools import partial, wraps


@contextmanager
def connection(host, port, token=None, *, mode="r"):
    with socket.create_connection((host, port)) as sock:
        if token is not None:
            sock.sendall(f"{token}\r\n".encode())
        with sock.makefile(mode, buffering=1,
                           encoding="ascii",
                           newline="\r\n") as conn:
            yield conn


def handshake(host, port):
    token, servers = None, []
    with connection(host, port) as conn:
        token = next(conn).strip()
        for host_and_port in conn:
            host, port = host_and_port.strip().split(":", 1)
            servers.append((host, int(port)))
    return token, servers


def follow(host, port, token):
    while True:
        try:
            with connection(host, port, token) as conn:
                groups = (
                    g for k, g in groupby(conn, lambda s: s == "\r\n") if not k
                )
                for g in groups:
                    yield map(str.strip, g)
        except OSError:
            continue
        break


def coroutine(g):
    @wraps(g)
    def inner(*args, **kwargs):
        gen = g(*args, **kwargs)
        next(gen)
        return gen
    return inner


def round_robin(sources, target):
    num_active = len(sources)
    nexts = cycle(iter(it).__next__ for it in sources)
    while num_active:
        try:
            for next in nexts:
                target.send(next())
        except StopIteration:
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))


HTTPRequest = namedtuple("HTTPRequest",
                         ["method", "resource", "protocol", "headers"],
                         defaults=["GET", "/", "HTTP/1.1", None])


@coroutine
def parse_http(target):
    while True:
        request = yield
        method, resource, protocol = next(request).split()
        headers = {
            k.strip().lower(): v.strip()
            for k, v in (s.split(":", 1) for s in request)
        }
        target.send(HTTPRequest(method, resource, protocol, headers))


@coroutine
def per_user(wait, target_factory):
    flush = object()
    d = {}
    while True:
        for i in range(wait):
            request = yield
            user = request.headers.get("from", "<unknown>")
            if user not in d:
                d[user] = target_factory(user, flush)
            target = d[user]
            target.send(request)
        for k in d:
            d[k].send(flush)


@coroutine
def number_of_requests(user, flush, target):
    n_requests = 0
    while True:
        request = yield
        if request is flush:
            target.send(("requests", user, n_requests))
            n_requests = 0
        else:
            n_requests += 1


@coroutine
def number_of_bytes(user, flush, target):
    n_bytes = 0
    while True:
        request = yield
        if request is flush:
            target.send(("bytes", user, n_bytes))
            n_bytes = 0
        else:
            n_bytes += int(request.headers.get("content-length", 0))


@coroutine
def popular_resources(user, flush, target):
    resources = Counter()
    while True:
        request = yield
        if request is flush:
            for resource in resources:
                target.send(("resources", user, resource))
            resources = Counter()
        else:
            resources[request.headers["host"] + request.resource] += 1


@coroutine
def ip_addresses(user, flush, target):
    addresses = set()
    while True:
        request = yield
        if request is flush:
            for address in addresses:
                target.send(("ipaddr", user, address))
            addresses = set()
        elif "x-forwarded-for" in request.headers:
            addresses.add(request.headers["x-forwarded-for"].split(",", 1)[0])


@coroutine
def broadcast(targets):
    while True:
        item = yield
        for target in targets:
            target.send(item)


@coroutine
def report(host, port, token):
    while True:
        try:
            with connection(host, port, token) as conn:
                id, user, statistic = yield
                conn.write(f"{id}: {user} {statistic}\r\n")
        except OSError:
            continue
        break


if __name__ == "__main__":
    host, port = "spyke.compscicenter.ru", 7182
    token, servers = handshake(host, port)
    wait = 4096

    r = report(host, port, token)
    analyzer = broadcast([
        per_user(wait, partial(number_of_requests, target=r)),
        per_user(wait, partial(number_of_bytes, target=r)),
        per_user(wait, partial(popular_resources, target=r)),
        per_user(wait, partial(ip_addresses, target=r)),
    ])
    round_robin([
        follow(host, port, token) for host, port in servers
    ], parse_http(analyzer))
