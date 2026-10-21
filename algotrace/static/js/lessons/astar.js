/* Lesson content for A* on a grid. Contract: static/js/lessons/README.md
   Figures describe algotrace/algorithms/grid/astar.py: 4 directional moves of cost 1,
   the Manhattan heuristic, and a binary heap ordered by lowest f, then lowest
   h, then the order entries were pushed. Dijkstra is the same code with h = 0.
   tests/unit/test_astar.py measures every figure stated here. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.astar = {
    id: 'astar',
    name: 'A* Search',
    family: 'graph',

    idea: [
        'Keep an open set of cells to look at, each with g, the steps taken to reach it, and h, a guess of the steps still needed to the goal.',
        'Always expand the open cell with the lowest f = g + h, and give each of its free neighbours g one higher.',
        'Because h never overestimates, the goal is reached by a shortest path, usually after looking at far fewer cells than a search that ignores where the goal is.'
    ],
    analogy: 'Walking to a building you can see across town. You keep choosing the street that has cost you least so far plus looks shortest from there, and only try side streets when the direct way is blocked.',
    whenToUse: 'Shortest paths when you know where the goal is and can estimate the distance to it: route finding in games and maps, robot navigation. With no useful estimate, h = 0, it is exactly Dijkstra.',
    stable: null,

    code: {
        pseudocode: [
            { id: 'push-start', text: 'put the start in the open set with g = 0', indent: 0 },
            { id: null, text: 'while the open set is not empty:', indent: 0 },
            { id: null, text: 'take the entry with the lowest f, then lowest h, then oldest', indent: 1 },
            { id: 'stale', text: 'if its cell was already expanded more cheaply, skip it', indent: 1 },
            { id: 'expand', text: 'expand the cell: its g is now final', indent: 1 },
            { id: 'path', text: 'if it is the goal, follow the cells back to the start and stop', indent: 1 },
            { id: null, text: 'for each free neighbour, up, right, down, left:', indent: 1 },
            { id: 'improve', text: 'if g + 1 beats its best g so far, or it has none:', indent: 2 },
            { id: 'push', text: 'record it and push it with f = (g + 1) + h', indent: 3 },
            { id: 'no-path', text: 'the open set is empty: there is no path', indent: 0 }
        ],
        python: [
            { id: null, text: 'g = {start: 0}', indent: 0 },
            { id: 'push-start', text: 'heap_push(heap, (h(start), h(start), 0, start, 0))', indent: 0 },
            { id: null, text: 'while heap:', indent: 0 },
            { id: null, text: 'f, h_cell, _, cell, cell_g = heap_pop(heap)', indent: 1 },
            { id: null, text: 'if cell in closed or g[cell] != cell_g:', indent: 1 },
            { id: 'stale', text: 'continue', indent: 2 },
            { id: 'expand', text: 'closed.add(cell)', indent: 1 },
            { id: null, text: 'if cell == goal:', indent: 1 },
            { id: 'path', text: 'return path_back(came_from, start, goal)', indent: 2 },
            { id: null, text: 'for nb in free_neighbours(cell):  # up, right, down, left', indent: 1 },
            { id: null, text: 'if nb in closed: continue', indent: 2 },
            { id: 'improve', text: 'if nb not in g or cell_g + 1 < g[nb]:', indent: 2 },
            { id: null, text: 'g[nb], came_from[nb] = cell_g + 1, cell', indent: 3 },
            { id: null, text: 'order += 1', indent: 3 },
            { id: 'push', text: 'heap_push(heap, (g[nb] + h(nb), h(nb), order, nb, g[nb]))', indent: 3 },
            { id: 'no-path', text: 'return None', indent: 0 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(1)',
                theta: '1',
                reason: 'The goal beside the start: the start is expanded, at most four neighbours are pushed, and the goal, with f = 1 and h = 0, comes straight out. The size of the grid never matters.'
            },
            average: {
                value: 'O(V log V)',
                theta: 'V log V',
                reason: 'A wall between start and goal with one gap at the far end, the Wall with a gap preset: the cells near the wall look best, so a fixed share of the grid, about 40 percent, is expanded before f has grown enough to send the search round. Each push and pop costs up to log V comparisons in the heap.'
            },
            worst: {
                value: 'O(V log V)',
                theta: 'V log V',
                reason: 'The goal walled off, the No path preset: every cell the start can reach is expanded, each pushes at most four entries, and every push and pop climbs a heap that holds up to 4V entries, log V comparisons each.'
            }
        },
        overall: { O: 'V log V', Omega: '1', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        caseScope: 'V is the number of cells in the grid; every cell has at most four neighbours, so the edges are at most 4V and do not need a letter of their own. The cases are kinds of grid: the goal beside the start, a wall to go round, and a goal no path reaches. The average here is that detour case, chosen because it is typical of a maze, not an average over every possible grid.',
        worked: {
            input: '3 rows by 4 columns, walls at (1, 1) and (1, 2), start (1, 0), goal (1, 3)',
            comparisons: 6,
            note: 'The number here is cells expanded. A* expands 6: the start, then along the top row, steered by h, and the goal, for a path of 5 steps. Dijkstra on the same grid expands all 10 free cells and finds a path of the same length. The heap makes 5 comparisons for A* and 8 for Dijkstra.'
        },
        space: {
            value: 'O(V)',
            what: 'the g and came-from tables and the closed set, one entry per cell, and the heap, which holds at most four entries per cell'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The sizes above are this one graph; the figure is how the work would grow if the graph got bigger.',
        countsNote: 'Why Manhattan distance is safe here. A move goes one cell up, down, left or right and costs 1, so reaching the goal needs at least as many moves as the rows plus the columns between, |dr| + |dc|, and walls can only add to that. The guess h never overestimates, which is what makes the first path A* finds a shortest one. It is also consistent: moving one cell changes h by exactly 1, the cost of the move, so f never drops along a path and a cell, once expanded, never needs expanding again.',
        growth: 'nlogn',
        growthBasis: 'V, the number of cells',
        growthNote: null,
        divergence: 'Textbook A* is often written with a decrease-key on the heap. This one pushes a cell again when its g improves and skips the older entry when it comes out, which costs a little heap space and keeps the heap simple. The tie-break, lowest f, then lowest h, then oldest entry, is this site\'s choice, written down so that every language takes the same steps; ties broken by h head straight for the goal on an open grid.'
    }
};
