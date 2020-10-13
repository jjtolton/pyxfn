import builtins
import itertools
import random
from collections import deque
from functools import reduce

__author__ = "James J. Tolton"


class Reduced:
    def __init__(self, x):
        self.value = x


class ThrowReduced(Exception):
    pass


class nil:
    """The absence of a value.  Used to differentiate where 'None' might be
    considered a valid value.  Try not to use this as a return value
    or pass it around, otherwise it loses effectiveness.  Primarily
    used in the kwargs."""


def is_reduced(x):
    return isinstance(x, Reduced)


def reduced(x):
    return Reduced(x)


def comp(*fns):
    def composed(x):
        return xreduce(lambda a, b: b(a), reversed(fns), x)

    return composed


def undreduced(x):
    if is_reduced(x):
        return x.value
    return x


def ensure_reduced(x):
    if is_reduced(x):
        return x
    else:
        return reduced(x)


def xreduce(f, coll, init):
    # reduce with a cc style escape for "reduced" values
    try:
        def ccshim(a, b):
            if is_reduced(a):
                xreduce.res = undreduced(a)
                raise ThrowReduced
            else:
                return f(a, b)

        return reduce(ccshim, coll, init)
    except ThrowReduced:
        return xreduce.res


def transduce(xfn, fn_start, fn_end, init, coll):
    def arrity_shim(*args):
        if len(args) == 2:
            return fn_start(*args)
        elif len(args) == 1:
            return fn_end(*args)
        else:
            raise Exception("This shouldn't have happened.  "
                            "Please open a ticket.  Thanks. --J")

    f = xfn(arrity_shim)
    res = xreduce(f, coll, init)
    return f(res)


def eduction(*xfn, multi=False):
    *xfns, initial = xfn
    xs = iter(initial)

    def eductor(*args):
        def eductor0():
            return None

        def eductor1(acc):
            return acc

        def eductor2(acc, o):
            eductor.__next.appendleft(o)
            return acc

        mapper = {0: eductor0, 1: eductor1, 2: eductor2}
        return mapper[len(args)](*args)

    eductor.__next = deque()

    xfns = comp(*xfns)(eductor)
    completed = False
    while not completed:
        try:
            while len(eductor.__next) == 0 and not completed:
                if multi is True:
                    x = xfns(*[None, *next(xs)])
                else:
                    x = xfns(None, next(xs))
                if is_reduced(x):
                    xfns(None)
                    completed = True

            while eductor.__next:
                yield eductor.__next.pop()

        except StopIteration:
            xfns(None)
            completed = True
            while eductor.__next:
                yield eductor.__next.pop()


def xmap(f):
    def _map(rf):
        def map0():
            return rf()

        def map1(a):
            return rf(a)

        def map2(a, b):
            return rf(a, f(b))

        def mapn(a, b, *c):
            return rf(a, f(b, *c))

        mapper = {0: map0,
                  1: map1,
                  2: map2}

        def __map(*args):
            return mapper.get(len(args), mapn)(*args)

        return __map

    return _map


def map(*args):
    if len(args) >= 2:
        return builtins.map(*args)
    else:
        return xmap(*args)


def xfilter(pred):
    def _filter(rf):

        def filter1(res):
            return rf(res)

        def filter2(res, input):
            if pred(input):
                return rf(res, input)
            else:
                return res

        mapper = {0: rf,
                  1: filter1,
                  2: filter2}

        def __filter(*args):
            return mapper[len(args)](*args)

        return __filter

    return _filter


def filter(*args):
    if len(args) > 2:
        return filter(*args)
    else:
        return xfilter(*args)


def preserving_reduced(rf):
    def _preserving_reduced(a, b):
        res = rf(a, b)
        if is_reduced(res):
            return reduced(res)
        return res

    return _preserving_reduced


def cat(rf):
    rf1 = preserving_reduced(rf)

    def cat2(res, input):
        return xreduce(rf1, input, res)

    mapper = {0: rf, 1: rf, 2: cat2}

    def _cat(*args):
        return mapper[len(args)](*args)

    return _cat


def drop(n):
    def _drop(rf):
        def __drop(*args):
            return __drop.mapper[len(args)](*args)

        def drop2(res, input):
            n = __drop.n
            __drop.n -= 1
            if n > 0:
                return res
            else:
                return rf(res, input)

        mapper = {0: rf, 1: rf, 2: drop2}
        __drop.mapper = mapper
        __drop.n = n
        return __drop

    return _drop


def drop_while(pred):
    def _drop_while(rf):
        def __drop_while(*args):
            return __drop_while.mapper[len(args)](*args)

        def drop2(res, input):
            should_drop = __drop_while.should_drop
            if should_drop and pred(input):
                return res
            else:
                __drop_while.should_drop = False
                return rf(res, input)

        __drop_while.should_drop = True
        __drop_while.mapper = {0: rf, 1: rf, 2: drop2}
        return __drop_while

    return _drop_while


def interpose(sep):
    def _interpose(rf):
        def __interpose(*args):
            return __interpose.mapper[len(args)](*args)

        def interpose2(res, input):
            if __interpose.started is True:
                sepr = rf(res, sep)
                if is_reduced(sep):
                    return sepr
                else:
                    return rf(sepr, input)
            else:
                __interpose.started = True
                return rf(res, input)

        __interpose.mapper = {0: rf, 1: rf, 2: interpose2}
        __interpose.started = False
        return __interpose

    return _interpose


def remove(pred):
    return xfilter(lambda x: not pred(x))


def distinct(rf):
    def _distinct(*args):
        return _distinct.mapper[len(args)](*args)

    def distinct2(res, input):
        if input in _distinct.seen:
            return res
        else:
            _distinct.seen.add(input)
            return rf(res, input)

    _distinct.mapper = {0: rf, 1: rf, 2: distinct2}
    _distinct.seen = set()

    return _distinct


def partition_all(n):
    def _partition_all(rf):
        def __partition_all(*args):
            return __partition_all.mapper[len(args)](*args)

        def partition_all1(res):
            if len(__partition_all.a) != 0:
                v = [x for x in __partition_all.a]
                __partition_all.a.clear()
                res = undreduced(rf(res, v))
            return rf(res)

        def partition_all2(res, input):
            __partition_all.a.append(input)
            if len(__partition_all.a) == n:
                v = [x for x in __partition_all.a]
                __partition_all.a.clear()
                return rf(res, v)
            else:
                return res

        __partition_all.mapper = {0: rf, 1: partition_all1, 2: partition_all2}
        __partition_all.a = []
        return __partition_all

    return _partition_all


def take_while(pred):
    def _take_while(rf):
        def __take_while(*args):
            return __take_while.mapper[len(args)](*args)

        def take_while2(res, input):
            if pred(input):
                return rf(res, input)
            else:
                return reduced(res)

        __take_while.mapper = {0: rf, 1: rf, 2: take_while2}
        return __take_while

    return _take_while


def take_nth(n):
    def _take_nth(rf):
        def __take_nth(*args):
            return __take_nth.mapper[len(args)](*args)

        def take_nth2(res, input):
            __take_nth.ia += 1
            i = __take_nth.ia
            if i % n == 0:
                return rf(res, input)
            else:
                return res

        __take_nth.mapper = {0: rf, 1: rf, 2: take_nth2}
        __take_nth.ia = -1
        return __take_nth

    return _take_nth


def partition_by(f):
    def _partition_by(rf):
        def __partition_by(*args):
            return __partition_by.mapper[len(args)](*args)

        def partition_by1(res):
            if len(__partition_by.a) != 0:
                v = []
                while __partition_by.a:
                    v.append(__partition_by.a.pop())
                __partition_by.a.clear()
                res = undreduced(rf(res, v))
            return rf(res)

        def partition_by2(res, input):
            pval = __partition_by.pa.pop()
            val = f(input)
            __partition_by.pa.append(val)
            if pval is nil or val == pval:
                __partition_by.a.appendleft(input)
                return res
            else:
                v = []
                while __partition_by.a:
                    v.append(__partition_by.a.pop())
                res = rf(res, v)
                if not is_reduced(res):
                    __partition_by.a.appendleft(input)
                return res

        __partition_by.pa = [nil]
        __partition_by.a = deque()
        __partition_by.mapper = {0: rf, 1: partition_by1, 2: partition_by2}

        return __partition_by

    return _partition_by


class Halt:
    def __init__(self, value):
        self.value = value


def halt_when(pred, retf=nil):
    if retf is nil:
        retf = None

    def _halt_when(rf):
        def __halt_when(*args):
            return __halt_when.mapper[len(args)](*args)

        def halt_when1(res):
            if isinstance(res, Halt):
                return res.value
            return rf(res)

        def halt_when2(res, input):
            if pred(input):
                if retf:
                    res = retf(rf(res), input)
                else:
                    res = input
                return reduced(Halt(res))
            else:
                return rf(res, input)

        __halt_when.mapper = {0: rf, 1: halt_when1, 2: halt_when2}
        return __halt_when

    return _halt_when


def map_indexed(f):
    def _map_indexed(rf):
        def __map_indexed(*args):
            return __map_indexed.mapper[len(args)](*args)

        def map_indexed2(res, input):
            __map_indexed.i += 1
            return rf(res, f(__map_indexed.i, input))

        __map_indexed.i = -1
        __map_indexed.mapper = {0: rf, 1: rf, 2: map_indexed2}
        return __map_indexed

    return _map_indexed


def keep_indexed(f):
    def _keep_indexed(rf):
        def __keep_indexed(*args):
            return __keep_indexed.mapper[len(args)](*args)

        def keep_indexed2(res, input):
            __keep_indexed.i += 1
            i = __keep_indexed.i
            v = f(i, input)
            if v is None:
                return res
            else:
                return rf(res, v)

        __keep_indexed.i = -1
        __keep_indexed.mapper = {0: rf, 1: rf, 2: keep_indexed2}
        return __keep_indexed

    return _keep_indexed


def take(n):
    def _take(rf):
        def __take(*args):
            return __take.mapper[len(args)](*args)

        def take2(res, input):
            n = __take.na
            __take.na -= 1
            nn = __take.na
            if n > 0:
                res = rf(res, input)
            else:
                res = res
            if (nn > 0) is not True:
                return ensure_reduced(res)
            return res

        __take.na = n
        __take.mapper = {0: rf, 1: rf, 2: take2}
        return __take

    return _take


def mapcat(f):
    return comp(map(f), cat)


def random_sample(prob):
    return filter(lambda _: prob < random.random())


if __name__ == '__main__':
    def inc(x):
        return x + 1


    def identity(x):
        return x


    print(transduce(comp(map(inc),
                         map(inc)),
                    lambda a, b: a + b,
                    identity,
                    0,
                    range(10)))

    print(transduce(comp(cat, map(inc)),
                    lambda a, b: [*a, b],
                    identity,
                    [],
                    [[1, 2], [3, 4]]))

    print(list(eduction(cat,
                        map(inc),
                        drop_while(lambda x: x < 5),
                        drop(10),
                        take(20),
                        filter(lambda x: x % 2 == 0),
                        [range(4), range(4), range(20)])))

    print(list(eduction(take_while(lambda x: x < 5),
                        interpose("-"),
                        distinct,
                        partition_all(2), range(10))))

    print(list(eduction(take_while(lambda x: x < 3), range(10))))

    print(list(eduction(take_nth(3), partition_all(2), interpose("-"),
                        list(range(10)))))

    print(transduce(comp(take_nth(3),
                         partition_all(2),
                         interpose("-"),
                         map(lambda x: [x] if isinstance(x, str) else x),
                         cat,
                         xmap(str)),
                    lambda a, b: (a.append(b), a)[1],
                    lambda res: ''.join(res),
                    [],
                    range(20)))

    print(list(eduction(partition_by(lambda x: x < 4), range(10))))

    print(transduce(halt_when(lambda x: x == 10,
                              lambda res, input: (
                                  reduce(lambda a, b: a + b, res, input))),
                    lambda x, y: (x.append(y), x)[1],
                    identity,
                    [],
                    range(20)))

    print(list(eduction(map_indexed(lambda a, b: [a, b]), range(10))))

    print(list(eduction(keep_indexed(lambda i, x: i + x if i < 10 else None),
                        range(20))))

    print(tuple(eduction(take(10), range(10))))

    print(transduce(
        comp(random_sample(0.5), mapcat(lambda x: [x] * x), take(10)),
        lambda res, x: (res.append(x), res)[-1], lambda res: res, [],
        range(10000)))
