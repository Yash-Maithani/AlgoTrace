/* Lesson content for Floyd-Warshall. Contract: static/js/lessons/README.md
   Figures describe the /run_floyd_warshall endpoint in app.py, which keeps a
   full distance matrix and a next-hop matrix alongside it. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.floyd_warshall = {
    id: 'floyd_warshall',
    name: 'Floyd-Warshall',
    family: 'graph',

    idea: [
        'Build a table holding the distance between every pair of nodes, filled in at first with only the direct edges.',
        'Take each node in turn as a possible stopping point, and ask of every pair whether going via that node is shorter.',
        'After every node has had its turn, the table holds the shortest route between every pair at once.'
    ],
    analogy: 'A mileage chart in the back of a road atlas. You go through it asking, for every pair of towns, whether the trip is shorter if you route it through one particular town.',
    whenToUse: 'When you need every pair of distances rather than routes from one start, and the graph is small enough that a full table fits. It handles negative edges, unlike Dijkstra.',
    stable: null,

    code: {
        pseudocode: [
            { id: 'init', text: 'fill the table with the direct edges, infinity elsewhere', indent: 0 },
            { id: 'k-loop', text: 'for each node k as a stopping point:', indent: 0 },
            { id: null, text: 'for every pair i, j:', indent: 1 },
            { id: 'check-inf', text: 'if either half of the route is missing, skip', indent: 2 },
            { id: 'compare', text: 'compare the route via k against the one on record', indent: 2 },
            { id: 'update', text: 'if via k is shorter, write it into the table', indent: 3 },
            { id: 'keep', text: 'otherwise leave the table alone', indent: 3 },
            { id: 'k-done', text: 'the table now allows stops at every node up to k', indent: 1 }
        ],
        python: [
            { id: 'init', text: 'dist[i][j] = weight of the edge i-j, else infinity', indent: 0 },
            { id: 'k-loop', text: 'for k in range(n):', indent: 0 },
            { id: null, text: 'for i in range(n): for j in range(n):', indent: 1 },
            { id: 'check-inf', text: 'if dist[i][k] == INF or dist[k][j] == INF: continue', indent: 2 },
            { id: 'compare', text: 'via_k = dist[i][k] + dist[k][j]', indent: 2 },
            { id: 'update', text: 'if via_k < dist[i][j]: dist[i][j] = via_k', indent: 3 },
            { id: 'keep', text: 'else: keep the distance on record', indent: 3 },
            { id: 'k-done', text: 'iteration k complete', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(V cubed)',
                reason: 'Three nested loops over every node, with no condition that can cut any of them short. A graph with no edges at all still runs the full V cubed.'
            },
            average: {
                value: 'O(V cubed)',
                reason: 'Every one of the V stopping points is tried against every one of the V squared pairs.'
            },
            worst: {
                value: 'O(V cubed)',
                reason: 'Identical. This is the rare algorithm whose cost depends only on how many nodes there are, never on the edges between them.'
            }
        },
        worked: {
            input: 'A-B 4, A-C 2, B-D 5, C-D 8, D-E 6 over nodes A to E',
            comparisons: 100,
            note: 'V = 5, so 5 stopping points times 20 ordered pairs where i is not j, which is 100 checks exactly. Of those, 30 were skipped because one half of the route was missing, 70 were real comparisons, and 10 of those improved a distance. The whole run draws 182 frames.'
        },
        space: {
            value: 'O(V squared)',
            what: 'the full distance table, plus a second table of the same size holding the first hop of each route so the paths can be rebuilt'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        growth: 'n2',
        divergence: 'The time figure matches the textbook. The space does not: the usual O(V squared) counts the distance table alone, while this endpoint keeps a next-hop table of the same size so the results panel can show the actual route and not just its length. That is still O(V squared), but it is twice the memory.'
    }
};
