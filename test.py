import timeit

from sortedcontainers import SortedDict

# Setup data
n = 20000
keys = list(range(n))
values = list(range(n))
d = {k: v for k, v in zip(keys, values)}
sd = SortedDict(d)
lst = list(zip(keys, values))

# Lookup key
target = 5


# Benchmark functions
def dict_lookup():
    return d[target]


def sorted_dict_lookup():
    return sd.keys()[target]


def list_scan():
    for k, v in lst:
        if k == target:
            return v


print("running")
# Run benchmarks
dict_time = timeit.timeit(dict_lookup, number=10000)
sorted_dict_time = timeit.timeit(sorted_dict_lookup, number=1000)
list_time = timeit.timeit(list_scan, number=10000)

print(f"Dictionary lookup: {dict_time:.6f}  pseconds")
print(f"SortedDict lookup: {sorted_dict_time:.6f} seconds")
print(f"List scan lookup: {list_time:.6f} seconds")
