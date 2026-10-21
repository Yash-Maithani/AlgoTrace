/* Lesson content for Topological Sort (Kahn's algorithm). Contract:
   static/js/lessons/README.md. Figures describe the /run_topological_sort
   endpoint (algotrace/algorithms/graph/topological_sort.py), which keeps its queue in a collections.deque, so taking
   from the front costs O(1). tests/unit/test_topological_sort.py measures every figure. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.topological_sort = {
    id: 'topological_sort',
    name: 'Topological Sort',
    family: 'graph',

    idea: [
        'Count, for every node, how many arrows come into it: its in-degree.',
        'Every node with in-degree 0 depends on nothing, so put them in a queue; take one from the front, place it next in the order, and remove its arrows.',
        'Removing arrows lowers other in-degrees, and any node that reaches 0 joins the queue; if the queue empties before every node is placed, the nodes left hold a cycle.'
    ],
    analogy: 'Planning a degree from course prerequisites. You can take any course whose prerequisites you have all passed; passing it may free up the courses that needed it. If two courses each require the other, no plan works.',
    whenToUse: 'Whenever tasks depend on other tasks and need an order that respects every dependency: build systems, spreadsheet recalculation, course plans, installing packages. It also tells you when the dependencies form a loop, so no order exists.',
    stable: null,

    code: {
        pseudocode: [
            { id: null, text: 'set every in-degree to 0', indent: 0 },
            { id: null, text: 'for each arrow u → v:', indent: 0 },
            { id: 'count', text: 'add 1 to the in-degree of v', indent: 1 },
            { id: null, text: 'for each node u, in input order:', indent: 0 },
            { id: 'seed', text: 'if its in-degree is 0, put it in the queue', indent: 1 },
            { id: null, text: 'while the queue is not empty:', indent: 0 },
            { id: 'remove', text: 'take u from the front and place it next in the order', indent: 1 },
            { id: null, text: 'for each arrow u → v:', indent: 1 },
            { id: 'decrement', text: 'take 1 off the in-degree of v', indent: 2 },
            { id: 'enqueue', text: 'if that makes it 0, put v at the back of the queue', indent: 2 },
            { id: null, text: 'if some nodes were never placed:', indent: 0 },
            { id: 'cycle', text: 'report them: they hold a cycle, so no order exists', indent: 1 }
        ],
        python: [
            { id: null, text: 'in_degree = {u: 0 for u in graph}', indent: 0 },
            { id: null, text: 'for u in graph:', indent: 0 },
            { id: null, text: 'for v in graph[u]:', indent: 1 },
            { id: 'count', text: 'in_degree[v] += 1', indent: 2 },
            { id: null, text: 'queue = deque()', indent: 0 },
            { id: null, text: 'for u in graph:', indent: 0 },
            { id: null, text: 'if in_degree[u] == 0:', indent: 1 },
            { id: 'seed', text: 'queue.append(u)', indent: 2 },
            { id: null, text: 'order = []', indent: 0 },
            { id: null, text: 'while queue:', indent: 0 },
            { id: 'remove', text: 'u = queue.popleft()', indent: 1 },
            { id: null, text: 'order.append(u)', indent: 1 },
            { id: null, text: 'for v in graph[u]:', indent: 1 },
            { id: 'decrement', text: 'in_degree[v] -= 1', indent: 2 },
            { id: null, text: 'if in_degree[v] == 0:', indent: 2 },
            { id: 'enqueue', text: 'queue.append(v)', indent: 3 },
            { id: null, text: 'if len(order) < len(graph):', indent: 0 },
            { id: 'cycle', text: 'remaining = [u for u in graph if in_degree[u] > 0]', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(V plus E)',
                theta: 'V plus E',
                reason: 'Even the easiest graph has every arrow counted and every node checked for in-degree 0 before anything is placed: V + E steps before the main loop starts.'
            },
            average: {
                value: 'O(V plus E)',
                theta: 'V plus E',
                reason: 'Each node is taken from the queue at most once, and each of its arrows is removed once when it is, so the main loop adds at most another V + E.'
            },
            worst: {
                value: 'O(V plus E)',
                theta: 'V plus E',
                reason: 'Counting, seeding and the main loop each touch a node or an arrow at most once, and popleft on a deque costs O(1), so no graph costs more than a constant times V + E. A cycle only stops the loop early.'
            }
        },
        overall: { O: 'V plus E', Omega: 'V plus E', Theta: 'V plus E' },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        caseScope: 'The cases are over directed graphs with V nodes and E arrows, with or without a cycle. Every arrow is counted before anything else happens, so a cycle that stops the main loop early still cannot take the work below V + E.',
        worked: {
            input: 'A → B, A → C, B → D, C → D, D → E',
            comparisons: 20,
            note: 'V = 5 and E = 5. It counts the 5 arrows, queues A, the only node with in-degree 0, then places all 5 nodes, removing their 5 arrows and queueing B, C, D and E as each reaches in-degree 0: 5 + 1 + 5 + 5 + 4 = 20 steps, and the order A, B, C, D, E. On any graph with no cycle the count is exactly 2(V + E): every node joins the queue once and leaves it once, and every arrow is counted once and removed once.'
        },
        space: {
            value: 'O(V)',
            what: 'the in-degree of every node, the queue and the order, each holding at most one entry per node'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The sizes above are this one graph; the figure is how the work would grow if the graph got bigger.',
        growth: null,
        growthBasis: null,
        growthNote:
            'O(V plus E) depends on two numbers at once, the nodes and the arrows, ' +
            'so it is not one of the curves below. On a graph with about as many ' +
            'arrows as nodes it grows like the O(n) line.',
        divergence: 'None. A plain Python list would make taking from the front O(V) and the whole run O(V squared) on a long chain; the deque keeps it at V + E. A depth-first search can also produce a topological order, but it does not report the cycle as directly.'
    }
};
