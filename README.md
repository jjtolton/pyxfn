# Transducers!

If you love `functools.reduce`, you're in the right place!

Transducers are `reduce` on steroids.

## Status

Super alpha.  No tests, no docs.  Have fun! 

```python 

from xfn import transduce, xmap, xfilter, comp, take, partition_all

def inc(n): return n + 1
def identity(x): return x
def conj(xs, x): return [*xs, x]
def is_even(n): return n % 2 == 0

>>> transduce(comp(xmap(inc), 
                   xfilter(is_even),
                   partition_all(2),
                   take(3)),
              conj,
              identity,
              [],
              range(100))
[[2, 4], [6, 8], [10, 12]]
```

