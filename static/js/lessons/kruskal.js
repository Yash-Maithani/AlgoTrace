/* Lesson content for Kruskal's Algorithm. Contract: static/js/lessons/README.md
   Figures describe the /run_kruskal endpoint in app.py, which sorts the whole
   edge list once and uses Union-Find with path halving and union by rank. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.kruskal = {
    id: 'kruskal',
    name: "Kruskal's Algorithm",
    family: 'graph',

    idea: [
        'Sort every edge in the graph by weight, cheapest first.',
        'Walk down that list and take each edge, unless its two ends are already connected to each other.',
        'Stop when the chosen edges span every node, which happens after exactly one fewer edge than there are nodes.'
    ],
    analogy: 'Building roads between towns on a budget. You work down the price list, and skip any road whose two towns can already reach each other some other way.',
    whenToUse: 'Connecting everything as cheaply as possible when the graph is sparse, or when the edges arrive already sorted. Unlike Prim it does not need a starting node, and it handles a disconnected graph by producing a forest.',
    stable: null,

    code: {
        pseudocode: [
            { id: 'sort', text: 'sort every edge by weight, cheapest first', indent: 0 },
            { id: null, text: 'for each edge in that order:', indent: 0 },
            { id: 'take-next', text: 'look at the two ends', indent: 1 },
            { id: 'cycle', text: 'if they are already connected, skip the edge', indent: 2 },
            { id: 'union', text: 'otherwise take it and merge the two groups', indent: 2 },
            { id: 'mst-complete', text: 'stop once n-1 edges have been taken', indent: 2 }
        ],
        python: [
            { id: 'sort', text: 'ordered = sorted(clean_edges, key=lambda e: e[2])', indent: 0 },
            { id: null, text: 'for u, v, weight in ordered:', indent: 0 },
            { id: 'take-next', text: 'if union(u, v):', indent: 1 },
            { id: 'union', text: 'mst_edges.append([u, v, weight])', indent: 2 },
            { id: 'mst-complete', text: 'if len(mst_edges) == spanning_total: break out', indent: 2 },
            { id: 'cycle', text: 'else: this edge would close a cycle', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(E)',
                theta: 'E',
                reason: 'Edges that arrive already in order of weight: Python\'s sort, Timsort, spots the sorted run in E-1 comparisons, and the walk down the list does one near constant Union-Find check per edge.'
            },
            average: {
                value: 'O(E log E)',
                theta: 'E log E',
                reason: 'Edges in shuffled order of weight cost about E log E comparisons to sort. The walk down the list is E steps, and each Union-Find query is near constant thanks to path halving and union by rank.'
            },
            worst: {
                value: 'O(E log E)',
                theta: 'E log E',
                reason: 'Same sort. The union and find operations grow so slowly, by the inverse Ackermann function, that they are effectively constant for any graph that fits in memory, so the sort sets the pace.'
            }
        },
        overall: { O: 'E log E', Omega: 'E', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        caseScope: 'The cases are over connected graphs, which is what the page generator makes.',
        worked: {
            input: 'A-B 4, A-C 2, B-D 5, C-D 8, D-E 6 over nodes A to E',
            comparisons: 5,
            note: 'E = 5 edges are sorted, then examined in the order 2, 4, 5, 6, 8. The first four are taken, giving a tree of weight 17; C-D 8 is rejected because C and D are already connected. The run stops examining once 4 edges are in, since 5 nodes need 4.'
        },
        space: {
            value: 'O(V + E)',
            what: 'the sorted copy of the edge list, plus one parent and one rank entry per node for Union-Find'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The sizes above are this one graph; the figure is how the work would grow if the graph got bigger.',
        growth: 'nlogn',
        growthBasis: 'E, the number of edges',
        growthNote: null,
        divergence: 'Often written O(E log V) rather than O(E log E). The two are the same thing, because E is at most V squared and so log E is at most 2 log V. This implementation keys Union-Find on the declared node list rather than on the nodes it meets in edges, which is what lets it return a spanning forest for a disconnected graph instead of failing.'
    }
};
