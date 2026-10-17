/* Lesson content for Depth-First Search. Contract: static/js/lessons/README.md
   Figures describe the /run_dfs endpoint in app.py. Its stack is a plain list,
   and the membership test on that list is what costs it the V in V times E. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.dfs = {
    id: 'dfs',
    name: 'Depth-First Search',
    family: 'graph',

    idea: [
        'Put the starting node on a stack, then take nodes off the top one at a time.',
        'Each time you visit a node, push every neighbour you have not seen on top of the stack.',
        'Because the stack is last in first out, the search follows one path to its end before backing up to try another.'
    ],
    analogy: 'Walking a maze with one hand on the wall. You go as far as the corridor leads, and only when it dead ends do you back up to the last junction.',
    whenToUse: 'To find out whether a path exists at all, to detect cycles, or to sort tasks into dependency order. It is also the shape of most recursive tree walks.',
    stable: null,

    code: {
        pseudocode: [
            { id: 'start', text: 'put the start node on the stack', indent: 0 },
            { id: null, text: 'while the stack is not empty:', indent: 0 },
            { id: 'pop', text: 'take the node on top and visit it', indent: 1 },
            { id: null, text: 'for each neighbour, in reverse order:', indent: 1 },
            { id: 'push', text: 'if it is new, push it on top of the stack', indent: 2 }
        ],
        python: [
            { id: 'start', text: 'stack = [start]', indent: 0 },
            { id: null, text: 'while stack:', indent: 0 },
            { id: 'pop', text: 'node = stack.pop()', indent: 1 },
            { id: null, text: 'for neighbor in reversed(graph.get(node, [])):', indent: 1 },
            { id: 'push', text: 'if neighbor not in visited and neighbor not in stack:', indent: 2 },
            { id: null, text: 'stack.append(neighbor)', indent: 3 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(V times E)',
                reason: 'Like the breadth-first endpoint it has no early exit, so it empties the stack whatever it finds on the way.'
            },
            average: {
                value: 'O(V times E)',
                reason: 'The `neighbor not in stack` test scans a list that can hold up to V nodes, and it runs once per edge.'
            },
            worst: {
                value: 'O(V times E)',
                reason: 'Same scan once per edge. Taking from the top of the stack is cheap, unlike the front of a queue, so this is the only linear cost.'
            }
        },
        worked: {
            input: 'A-B, A-C, B-D, C-D, D-E starting at A',
            comparisons: 5,
            note: 'V = 5 and E = 5, the same graph the breadth-first lesson uses, and the same 5 nodes visited in 11 frames. Only the order differs: depth first reaches E before it comes back for C, while breadth first takes C second.'
        },
        space: {
            value: 'O(V)',
            what: 'the stack and the visited set, which between them hold at most one entry per node'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The sizes above are this one graph; the figure is how the work would grow if the graph got bigger.',
        growth: null,
        growthBasis: null,
        growthNote:
            'O(V times E) depends on two numbers at once, the nodes and the ' +
            'edges, so it is not one of the curves below.',
        divergence: 'Depth-first search is usually quoted at O(V + E). Taking from the end of a list really is constant time, so unlike the queue version this endpoint pays nothing there. What costs it is the same `not in stack` membership test, a linear scan once per edge. A set alongside the stack would make it O(V + E).'
    }
};
