#!/usr/bin/env python3
import argparse
from collections import deque
from itertools import permutations

def simulate_permutation(order, N, cache_lines, line_elems):
    """
    Simulate one permutation of the loops:
       for a in 0..N-1
         for b in 0..N-1
           for c in 0..N-1
             for d in 0..N-1
               elem1 = Y[c][a][d]
               elem2 = Z[d][b][c]
               elem3 = X[a][d][c]
               elem4 = elem3 - (elem2 + elem1)
               X[a][d][c] = elem4

    order: a 4‐tuple like ('a','b','c','d') giving the iteration order
    N: loop bound
    cache_lines: number of cache lines in the fully‐associative cache
    line_elems: how many array elements fit in one cache line
    """
    # LRU cache of size cache_lines, tags stored MRU→right
    cache = deque(maxlen=cache_lines)
    misses = 0
    accesses = 0

    # Lay out X, Y, Z back‐to‐back in element‐address space:
    #  X at [0 .. N^3-1], Y at [N^3 .. 2N^3-1], Z at [2N^3 .. 3N^3-1]
    base = {'X': 0, 'Y': N**3, 'Z': 2 * N**3}

    # Innermost‐body access sequence:
    # 1) read  Y[c][a][d]
    # 2) read  Z[d][b][c]
    # 3) read  X[a][d][c]
    # 4) write X[a][d][c]
    access_defs = [
      ('Y', lambda a,b,c,d: (c, a, d)),
      ('Z', lambda a,b,c,d: (d, b, c)),
      ('X', lambda a,b,c,d: (a, d, c)),  # read X
      ('X', lambda a,b,c,d: (a, d, c)),  # write X
    ]

    # Four nested loops in the order given by `order`
    for i1 in range(N):
        for i2 in range(N):
            for i3 in range(N):
                for i4 in range(N):
                    # assign the counters to a,b,c,d in this permutation
                    vals = [i1, i2, i3, i4]
                    idx  = dict(zip(order, vals))
                    a, b, c, d = idx['a'], idx['b'], idx['c'], idx['d']

                    # perform the four references
                    for arr, coord in access_defs:
                        i, j, k = coord(a, b, c, d)
                        addr    = base[arr] + ((i * N + j) * N + k)
                        tag     = addr // line_elems

                        if tag not in cache:
                            # miss → evict LRU if full, then append
                            misses += 1
                            if len(cache) == cache_lines:
                                cache.popleft()
                            cache.append(tag)
                        else:
                            # hit → move this tag to MRU
                            cache.remove(tag)
                            cache.append(tag)

                        accesses += 1

    return accesses, misses

def main():
    p = argparse.ArgumentParser(
        description="Fully-assoc LRU cache sim for all 24 loop orderings"
    )
    p.add_argument("--N",           type=int, default=32,
                   help="Loop bound per dimension")
    p.add_argument("--cache_lines", type=int, default=64,
                   help="Number of fully-assoc cache lines")
    p.add_argument("--line_elems",  type=int, default=4,
                   help="Elements per cache line")
    args = p.parse_args()

    print(f"N={args.N}, cache_lines={args.cache_lines}, line_elems={args.line_elems}")
    print(f"{'Order':<6} {'Accesses':>12} {'Misses':>12} {'MissRate':>10}")
    print("-"*44)

    for order in permutations('abcd'):
        acc, miss = simulate_permutation(order,
                                         args.N,
                                         args.cache_lines,
                                         args.line_elems)
        rate = miss / acc if acc else 0
        print(f"{''.join(order):<6} {acc:12,d} {miss:12,d} {rate:10.4%}")

if __name__ == "__main__":
    main()
