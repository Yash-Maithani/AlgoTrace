/* Lesson content for Bellman-Ford. Contract: static/js/lessons/README.md
   Figures describe the /run_bellman_ford endpoint in app.py, which sweeps
   every edge for up to V-1 passes, stops early on a quiet pass, and then makes
   one more check to detect a negative cycle. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.bellman_ford = {
    id: 'bellman_ford',
    name: 'Bellman-Ford',
    family: 'graph',

    idea: [
        'Give the start a distance of zero and every other node infinity, then sweep the whole edge list.',
        'For each edge, if going through it reaches the far end more cheaply than the number on record, write the better one down.',
        'Repeat the sweep up to one fewer time than there are nodes, because a shortest path can grow by only one edge per sweep.'
    ],
    analogy: 'Passing a rumour round a room. On each round everyone tells their neighbours the cheapest price they have heard, and after enough rounds the best price has reached everybody.',
    whenToUse: 'Shortest paths when some edges are negative, which Dijkstra cannot handle. It is also the only one here that can tell you a negative cycle exists, meaning no shortest path does.',
    stable: null,

    code: {
        pseudocode: [
            { id: null, text: 'distance to start = 0, every other = infinity', indent: 0 },
            { id: null, text: 'repeat up to n-1 times:', indent: 0 },
            { id: 'edge-loop', text: 'for every edge from u to v:', indent: 1 },
            { id: 'relax', text: 'if distance[u] + weight < distance[v], write it down', indent: 2 },
            { id: 'no-improve', text: 'otherwise leave it alone', indent: 2 },
            { id: 'pass-done', text: 'if nothing changed this pass, stop early', indent: 1 },
            { id: null, text: 'one more sweep: anything still improvable is on a negative cycle', indent: 0 }
        ],
        python: [
            { id: null, text: 'distances = {node: INF for node in nodes}; distances[start] = 0', indent: 0 },
            { id: null, text: 'for iteration in range(1, max(len(nodes), 1)):', indent: 0 },
            { id: 'edge-loop', text: 'for u, v, weight in edge_list:', indent: 1 },
            { id: 'relax', text: 'if distances[u] != INF and distances[u] + weight < distances[v]:', indent: 2 },
            { id: null, text: 'distances[v] = distances[u] + weight', indent: 3 },
            { id: 'no-improve', text: 'else: nothing to do for this edge', indent: 2 },
            { id: 'pass-done', text: 'if not changed: break', indent: 1 },
            { id: null, text: 'has_negative_cycle = any(still improvable)', indent: 0 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(E)',
                theta: 'E',
                reason: 'When the edges are listed outward from the start, the first pass settles every distance, the second changes nothing, and the loop stops: two sweeps of E edges.'
            },
            average: {
                value: 'O(k times E)',
                theta: 'k times E',
                reason: 'Each pass sweeps all E edges and the loop stops after k passes, where k is one more than the number of passes it takes to settle every distance. That depends on how many edges the shortest paths have and the order the edges are listed in, so it is written with its own letter. On random connected graphs k stays small.'
            },
            worst: {
                value: 'O(V times E)',
                theta: 'V times E',
                reason: 'A path listed from its far end back to the start: each pass settles just one more node, so all V-1 passes run, each sweeping all E edges.'
            }
        },
        overall: { O: 'V times E', Omega: 'E', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        caseScope: 'The cases are over graphs in which the start reaches every node, which is what the page generator makes. A start that reaches fewer nodes does less work, because the part it cannot reach is never touched.',
        worked: {
            input: 'A-B 4, A-C 2, B-D 5, C-D 8, D-E 6 starting at A',
            comparisons: 20,
            note: 'The undirected graph gives 10 directed edges, so one pass is 10 edge checks. This run takes 2 passes, 20 checks, of which 4 improved a distance: the first pass settles everything and the second one proves it by changing nothing. Without the early exit it would have run all 4 passes, 40 checks.'
        },
        space: {
            value: 'O(V + E)',
            what: 'one distance per node, plus the flattened list of edges the sweeps read'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The sizes above are this one graph; the figure is how the work would grow if the graph got bigger.',
        growth: null,
        growthBasis: null,
        growthNote:
            'O(V times E) depends on two numbers at once, the nodes and the ' +
            'edges, so it is not one of the curves below.',
        divergence: 'Textbook Bellman-Ford always runs V-1 passes, giving a best case of O(V times E) as well. This version keeps a changed flag and breaks out of a quiet pass, so its best case is O(E). That is the same early exit bubble sort lacks, and here it is the difference between 20 edge checks and 40 on the worked example above.'
    }
};
