"""A* on a grid, instrumented for the visualization. Dijkstra is the same code
with every h set to 0.

The rules, which every language follows so every run gives identical steps
(reference_code/README.md, "Grid programs"):

  moves      up, right, down, left, in that order; each costs 1
  heuristic  Manhattan distance to the goal, |dr| + |dc|; 0 for Dijkstra
  open set   a binary min-heap of entries (f, h, order, cell, g), ordered by
             lowest f, then lowest h, then lowest order, where order counts
             the pushes made so far. No two entries tie on all three, so
             any correct heap pops them in the same sequence
  updates    a cell whose g improves is pushed again; the older entry stays
             in the heap and is skipped when it comes out (a stale entry)
  stop       when the goal is expanded, or the heap is empty (no path)

The heap is written out here rather than taken from heapq, so the C, C++ and
Java translations can copy it line for line, and so stats['comparisons']
counts every comparison between two entries: the heap's own work, which is
where the log in O(V log V) comes from.

Cells are named "r,c" in the steps. The line ids match the Python listing
in static/js/lessons/astar.js.
"""
from teacher import step

MOVES = ((-1, 0), (0, 1), (1, 0), (0, -1))     # up, right, down, left


def cell_name(cell):
    return '%d,%d' % cell


def shown(cell):
    return '(%d, %d)' % cell


def _less(a, b, stats):
    """Entry a comes out before entry b: lower f, then lower h, then pushed earlier."""
    stats['comparisons'] += 1
    if a[0] != b[0]:
        return a[0] < b[0]
    if a[1] != b[1]:
        return a[1] < b[1]
    return a[2] < b[2]


def heap_push(heap, entry, stats):
    heap.append(entry)
    i = len(heap) - 1
    while i > 0:
        parent = (i - 1) // 2
        if _less(heap[i], heap[parent], stats):
            heap[i], heap[parent] = heap[parent], heap[i]
            i = parent
        else:
            break


def heap_pop(heap, stats):
    top = heap[0]
    last = heap.pop()
    if heap:
        heap[0] = last
        i = 0
        n = len(heap)
        while True:
            left, right, best = 2 * i + 1, 2 * i + 2, i
            if left < n and _less(heap[left], heap[best], stats):
                best = left
            if right < n and _less(heap[right], heap[best], stats):
                best = right
            if best == i:
                break
            heap[i], heap[best] = heap[best], heap[i]
            i = best
    return top


def _sorted_entries(entries):
    return sorted(entries, key=lambda e: (e[0], e[1], e[2]))


def astar(rows, cols, walls, start, goal, draw, heuristic='manhattan', stats=None):
    """Find a shortest path from start to goal on a rows x cols grid.

    walls is a set of (r, c); start and goal are (r, c). draw(meta) records
    one frame; None records nothing and skips building the frames, which the
    growth tests use on big grids. Returns the path as a list of cells, or None."""
    if stats is None:
        stats = {}
    stats.setdefault('comparisons', 0)
    stats.setdefault('expanded', 0)
    stats.setdefault('pushes', 0)
    zero = heuristic == 'zero'

    def h_of(cell):
        if zero:
            return 0
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])

    g = {start: 0}
    came_from = {}
    closed = set()
    heap = []
    order = 0

    def state(current=None, extra=None):
        if draw is None:
            return {}
        out = {'open': sum(1 for e in heap if e[3] not in closed and g[e[3]] == e[4]),
               'closed': len(closed)}
        if current is not None:
            out['current'] = cell_name(current)
        if extra:
            out.update(extra)
        return out

    def frame(action, cells, values, line, variables, beginner, why, **fields):
        if draw is None:
            return
        meta = step(action, [cell_name(c) for c in cells], values, line, variables, beginner, why)
        meta.update(fields)
        draw(meta)

    h0 = h_of(start)
    heap_push(heap, (h0, h0, order, start, 0), stats)
    stats['pushes'] += 1
    frame('enqueue', [start], [0, h0], 'push-start',
          state(start, {'g': 0, 'h': h0, 'f': h0}),
          'The start %s goes into the open set with g = 0 and h = %d, so f = %d.'
          % (shown(start), h0, h0),
          'g is the cost so far and h the estimate of the cost still to go; '
          'the open set always gives back the cell with the lowest f = g + h.',
          g=0, h=h0, f=h0)

    while heap:
        # The candidates the next pop chooses between: the live entries, best
        # first, at most four distinct cells. Predict mode asks about them.
        live = [e for e in heap if e[3] not in closed and g[e[3]] == e[4]] if draw else []
        entry = heap_pop(heap, stats)
        f, h, _, cell, cell_g = entry
        if cell in closed or g[cell] != cell_g:
            frame('reject', [cell], [cell_g, h], 'stale',
                  state(cell, {'g': cell_g, 'h': h, 'f': f}),
                  '%s comes out with g = %d, but it was already reached for less. '
                  'This older entry is skipped.' % (shown(cell), cell_g),
                  'A cell is pushed again when a cheaper route to it turns up, '
                  'and the old entry is simply ignored when it surfaces.')
            continue
        candidates = []
        for e in _sorted_entries(live):
            if cell_name(e[3]) not in [c['cell'] for c in candidates]:
                candidates.append({'cell': cell_name(e[3]), 'g': e[4], 'h': e[1], 'f': e[0]})
            if len(candidates) == 4:
                break
        closed.add(cell)
        stats['expanded'] += 1
        # Say only what decided it: f alone, then h, then push order.
        same_f = [e for e in live if e[0] == f and e[3] != cell]
        if not same_f:
            decided = ''
        elif all(e[1] > h for e in same_f):
            decided = ', and the lowest h among the cells with that f'
        else:
            decided = (', tied on f and h with another cell; it was added to the '
                       'open set first, which breaks the tie')
        frame('visit', [cell], [cell_g, h], 'expand',
              state(cell, {'g': cell_g, 'h': h, 'f': f}),
              'Expand %s: it has the lowest f in the open set, %d = %d + %d%s.'
              % (shown(cell), f, cell_g, h, decided),
              'Once a cell comes out of the open set its g is final: no route '
              'found later can be shorter.' if not zero else
              'With h = 0 this is Dijkstra: cells come out in order of their '
              'distance from the start, in every direction at once.',
              candidates=candidates)
        if cell == goal:
            path = [cell]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            frame('done', path, [len(path) - 1], 'path',
                  state(None, {'length': len(path) - 1}),
                  'The goal %s is expanded, so its g = %d is the length of a '
                  'shortest path. %d cell%s expanded.'
                  % (shown(goal), len(path) - 1, stats['expanded'],
                     ' was' if stats['expanded'] == 1 else 's were'),
                  'Following each cell back to the cell it was reached from '
                  'traces the path from the goal to the start.')
            return path
        for dr, dc in MOVES:
            nb = (cell[0] + dr, cell[1] + dc)
            if not (0 <= nb[0] < rows and 0 <= nb[1] < cols) or nb in walls or nb in closed:
                continue
            ng = cell_g + 1
            if nb not in g or ng < g[nb]:
                improved = nb in g
                g[nb] = ng
                came_from[nb] = cell
                nh = h_of(nb)
                order += 1
                heap_push(heap, (ng + nh, nh, order, nb, ng), stats)
                stats['pushes'] += 1
                if improved:
                    frame('relax', [nb, cell], [ng, nh], 'improve',
                          state(nb, {'g': ng, 'h': nh, 'f': ng + nh}),
                          'A shorter route to %s through %s: g drops to %d, so f = %d. '
                          'It is pushed again.' % (shown(nb), shown(cell), ng, ng + nh),
                          'The open set keeps the best known cost of every cell it '
                          'has not finished with.', g=ng, h=nh, f=ng + nh)
                else:
                    frame('enqueue', [nb, cell], [ng, nh], 'push',
                          state(nb, {'g': ng, 'h': nh, 'f': ng + nh}),
                          '%s is reached from %s: g = %d, h = %d, f = %d. It joins '
                          'the open set.' % (shown(nb), shown(cell), ng, nh, ng + nh),
                          'Each step costs 1, so a neighbour is one more than the '
                          'cell it was reached from.', g=ng, h=nh, f=ng + nh)

    frame('done', [], [stats['expanded']], 'no-path',
          state(None),
          'The open set is empty and the goal %s was never reached, so there '
          'is no path. %d cell%s expanded.'
          % (shown(goal), stats['expanded'], ' was' if stats['expanded'] == 1 else 's were'),
          'Every cell reachable from the start has been expanded; walls cut '
          'the goal off from all of them.')
    return None
