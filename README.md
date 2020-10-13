# Transducers!

If you love `functools.reduce`, you're in the right place!

Transducers are `reduce` on steroids.

## Overview

Transducers are a collection of techniques for transforming sequential data.
A regular function is sometimes abbreviated as `fn`.  
A transducing `fn` is sometimes abbreviated as `xfn`, which is 
where this library derives its name.

Transducers were invented by Rich Hickey and introduced in Clojure v1.7.
However, they are a general technique akin to `map`, `filter`, and `reduce`.
The code here is a transcription of the code and API.


## Status

Alpha.  
All functions believed to be working, but no tests yet.
API subject to change, specifically the signature for `transduce`, 
pending user feedback.


### Functions that use transducers

This library features two functions that use transducers:

| fn | Description |
|---|---|
| transduce | Passes items through a transducer then aggregates them |
| eduction | a generator that lazily pass items through a transducer |

### Transducers - the toolkit

| xfn | Description |
|---|---|
| cat | Concatenate lists on the fly | 
| distinct | Remove duplicates on the fly |
| drop | drop the first `n` items from the sequence|
| drop_while | drop items while a condition exists |
| filter | only keep items that match a certain criteria |
| halt_when | stop processing items when an item is encountered that meets some criteria |
| interpose | insert an element of your choice between items |
| keep_indexed | `filter` based on index and value |
| map | transform items on the fly |
| map_indexed | transform items based on index and value |
| mapcat | transform items and concatenate the results on the fly |
| partition_all | group items by a chunk size |
| partition_by | group sequences of item matching a criteria |
| random_sample | include result based on probability threshold |
| remove | opposite of `filter`, remove items matching some criteria |
| take | stop after processing a certain number of items |
| take_nth | only process every `n` items |
| take_while | continue processing while some criteria is met, then stop |

### Helper functions

| fn | description |
|---|---|
| comp | combine xfns together into a reusable data processing pipeline |
| reduced | call this on an item to return immediately from the transducer |


### Quickstart
#### eduction, map, filter, and comp

`eduction` used with `map` is the easiest way to get a feel for transducers.
(**Note:** `from xfn import *` overloads the builtin `map` function so that 
if acts as a transducer if given only one argument.  If given more than one
argument, it calls `builtins.map`)

```Python 
>>> from xfn import *
>>> def inc(x): return x + 1
>>> nums = range(10)
>>> nums_plus_1 = eduction(map(inc), nums))
>>> nums_plus_1
<generator object eduction at 0x7f65a95eeed0>
>>> list(nums_plus_1)
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
>>> list(nums_plus_1)
[]
```

You can combine multiple `map` `xfns` together with `comp`.

```Python
>>> def double_item(x): return x * 2
>>> double_items = map(double_item)
>>> quadruple_items = comp(double_items, double_items)
>>> list(eduction(quadruple_items, range(10)))
[0, 4, 8, 12, 16, 20, 24, 28, 32, 36]
```

Use `filter` to remove items from the final output.
(**Note:** `from xfn import *` overloads the builtin `filter` function so that 
if acts as a transducer if given only one argument.  If given more than one
argument, it calls `builtins.filter`)

```Python
>>> def is_even(x): return x % 2 == 0
>>> list(eduction(filter(is_even), range(10)))
[0, 2, 4, 6, 8]
```

Combine `map` and `filter` with `comp` to fine-tune results.

```Python
>>> list(eduction(comp(filter(is_even), quadruple_items), range(10)))
[0, 8, 16, 24, 32]
```

### Fear not the transducer

the arguments to `transduce` are as follows:

| argument | explanation |
|---|---|
| xfn | the same thing you would use in `eduction` |
| fn_start | *exactly* the same as the function you would use in `reduce` |
| fn_end | a final aggregation after `reduce`, see below |
| init | like the `init` argument to `reduce` |
| coll| like the `coll` argument to `reduce` |

If you don't understand `reduce`, `transduce` will make very little sense.
Start there and then come back here. Otherwise, read on!

`transduce` is useful in the following situation:

```Python
def message(n):
    return f"{n} is the best number!"
def add(a, b):
    return a + b

items = [] # init
nums = [1, 1, 2, 4, 3, 3, 5, 2, 9] # coll
for item in eduction(filter(is_even), nums):
   items.append(item) # xfn
output = reduce(add, items) # fn_start
print(message(output)) # fn_end
``` 

This situation could be done with `transduce` as follows:

```python 
def append(items, item):
    items.append(item)
    return items

>>> transduce(xfn=filter(is_even),
              fn_start=append,
              fn_end=message,
              init=[],
              coll=[1, 1, 2, 4, 3, 3, 5, 2, 9])
```

It's also perfectly valid for one or more of the parameters to `transduce` 
to be "no-ops".

For instance, if you want to put things into a `dict` but don't need a final 
aggregation, you could do something like this:

```python 

>>> def tally(d, n): return {**d, n: d[n]+1} if n in d else {**d, n:0}
>>> def noop(res): return res
>>> transduce(xfn=filter(is_even), 
              fn_start=tally, 
              fn_end=noop, 
              init={}, 
              coll=[1, 1, 2, 3, 5, 5, 8, 8, 2])
{2: 2, 8: 2}
```

If you decide you want the frequencies instead of the raw count, simply
replace `noop` with a final aggregation function.

```python 
def frequencies(d):
   total = sum(d.values())
   res = {}
   if total == 0:
       return d
   for k, v in d.items():
       res[k] = v / total
   return res

>>> transduce(xfn=filter(is_even), 
              fn_start=tally, 
              fn_end=frequencies, 
              init={}, 
              coll=[1, 1, 2, 3, 5, 5, 8, 8, 2])
{2: 0.5, 8: 0.5}
```

### Toolkit rundown

The following examples will show how the transducers reshape data.
For brevity, the transducers will be in a table with their name, an explanation,
and input/output examples.  For instance:

|  | | | 
|---|---|---|
| xfn-name | xfn-description | |
| params1 | input1 | output1 |
| params2 | input2 | output2 |

would correspond with the following code:

```python 
>>> list(eduction(xfn_name(*params1), input1))
output1
>>> list(eduction(xfn_name(*params2), input2))
output2
```


| | | |
|---|---|---|
|cat| Concatenate lists on the fly | |
| N/A | [[1, 2], [3, 4]] | [1, 2, 3, 4] |

| | | |
|---|---|---|
| distinct | Remove duplicates on the fly | |
| N/A | [1, 2, 1, 3] | [1, 2, 3] |

| | | |
|---|---|---|
| drop |  drop the first `n` items from the sequence | |
| 0 | [1, 2, 3, 4, 5] | [1, 2, 3, 4, 5] |
| 2 | [1, 2, 3, 4, 5] | [3, 4, 5] |
| 4 | [1, 2, 3, 4, 5] | [5] |
| 10 | [1, 2, 3, 4, 5] | [] |

| | | |
|---|---|---|
| drop_while | drop items while a condition exists | |
| lambda x: x < 3 | [1, 2, 1, 3, 4] | [3, 4] |
| lambda x: x == 1 | [1, 2, 1, 3, 4] | [2, 1, 3, 4] |

| | | |
|---|---|---|
| filter | only keep items that match a certain criteria | |
| lambda x: x < 3 | [1, 2, 1, 3] | [1, 2] |
| lambda x: x == 1 | [1, 2, 1, 3] | [1, 1] |

| | | |
|---|---|---|
| halt_when | stop processing items when an item is encountered that meets some criteria | |
| lambda x: x == 2 | [1, 2, 1, 3] | [1, 2] |
| lambda x: x < 3 | [1, 2, 1, 3] | [1] |
| lambda x: x > 3 | [1, 2, 1, 3] | [1, 2, 1, 3] |

| | | |
|---|---|---|
| interpose | insert an element of your choice between items | |
| "-" | [1, 2, 1, 3] | [1, "-", 2, "-", 1, "-", 3] |

| | | |
|---|---|---|
| keep_indexed | `filter` based on index and value | |
| lambda i, v: i < 1 or v == 5 | [1, 2, 1, 3, 5] | [1, 2, 3, 5] |

| | | |
|---|---|---|
| map | transform items on the fly | |
| lambda x: x + 1 | [1, 2, 1, 3] | [2, 3, 2, 4] |
| lambda x: x >= 2 | [1, 2, 1, 3] | [False, True, False, True] |

| | | |
|---|---|---|
| map_indexed | transform items based on index and value | |
| N/A | [1, 2, 1, 3] | [1, 2, 3] |

| | | |
|---|---|---|
| mapcat | transform items and concatenate the results on the fly | |
| lambda x: [x] * x | [1, 2, 1, 3] | [1, 2, 2, 1, 3, 3, 3] |
| lambda x: x[0] | [[[1, 2], [3, 4]], [[5, 6], [7,8]]] | [1, 2, 5, 6]

| | | |
|---|---|---|
| partition_all | group items by a chunk size | |
| 1 | [1, 2, 1, 3] | [[1], [2], [1], [3]] |
| 2 | [1, 2, 1, 3] | [[1, 2], [1, 3]] |
| 3 | [1, 2, 1, 3] | [[1, 2, 1], [3]] |
| 4 | [1, 2, 1, 3] | [[1, 2, 1, 3]] |
| 5 | [1, 2, 1, 3] | [[1, 2, 1, 3]] |

| | | |
|---|---|---|
| partition_by | group sequences of item matching a criteria | |
| lambda x: x < 3 | [1, 2, 1, 3, 1, 2, 4, 5] | [[1, 2, 1], [3], [1, 2], [4, 5]] |

| | | |
|---|---|---|
| random_sample | include result based on probability threshold | |
| 0.5 | [1, 2, 1, 3] | [1, 3] |
| 0.5 | [1, 2, 1, 3] | [1, 1, 3] |
| 0.5 | [1, 2, 1, 3] | [1, 2] |
| 0.5 | [1, 2, 1, 3] | [2, 3] |

| | | |
|---|---|---|
| remove | opposite of `filter`, remove items matching some criteria | |
| lambda x: x in {1, 3} | [1, 2, 1, 3] | [2] |
| lambda x: x % 2 == 0 | [1, 2, 1, 3] | [1, 1, 3] |

| | | |
|---|---|---|
| take | stop after processing a certain number of items | |
| 0 | [1, 2, 1, 3] | [] |
| 1 | [1, 2, 1, 3] | [1] |
| 3 | [1, 2, 1, 3] | [1, 2, 1] |
| 5 | [1, 2, 1, 3] | [1, 2, 1, 3] |

| | | |
|---|---|---|
| take_nth | only process every `n` items | |
| 1 | [1, 2, 1, 3] | [1, 2, 1, 3] |
| 2 | [1, 2, 1, 3] | [1, 1] |
| 3 | [1, 2, 1, 3] | [1, 3] |
| 4 | [1, 2, 1, 3] | [1] |
| 5 | [1, 2, 1, 3] | [1] |

| | | |
|---|---|---|
| take_while | continue processing while some criteria is met, then stop | |
| lambda x: x == 1 | [1, 2, 1, 3] | [1] |
| lambda x: x < 3 | [1, 2, 1, 3] | [1, 2, 1] | 
| lambda x: x == 2 | [1, 2, 1, 3] | [] |


### Roadmap

* [x] accessible documentation
* [x] examples
* [ ] test coverage  
* [ ] function docstrings
* [ ] CI/CD
* [ ] "how to write a transducer"
* [ ] wiki
* [ ] stabilized API

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

