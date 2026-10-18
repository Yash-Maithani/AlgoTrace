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
                value: 'O(V)',
                theta: 'V',
                reason: 'A path that begins at the start: the stack never holds more than one node, so each of the V visits and their `not in stack` checks costs a constant amount.'
            },
            average: {
                value: 'O(V times E)',
                theta: 'V times E',
                reason: 'On a random connected graph the stack holds a steady share of all the nodes for much of the run, and the `neighbor not in stack` test scans it for a steady share of the edges, so the total is a constant fraction of V times E.'
            },
            worst: {
                value: 'O(V times E)',
                theta: 'V times E',
                reason: 'A star or a complete graph: the start pushes all its neighbours at once, so later edges each scan a stack of about V nodes. Taking from the top of the stack is cheap, unlike the front of a queue, so the scan is the only linear cost.'
            }
        },
        overall: { O: 'V times E', Omega: 'V', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        caseScope: 'The cases are over graphs in which the start reaches every node, which is what the page generator makes. A start that reaches fewer nodes does less work, because the part it cannot reach is never touched.',
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
