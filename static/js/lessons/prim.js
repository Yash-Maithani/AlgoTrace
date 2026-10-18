/* Lesson content for Prim's Algorithm. Contract: static/js/lessons/README.md
   Figures describe the /run_prim endpoint in app.py, which uses heapq and
   pushes one heap entry per edge it meets. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.prim = {
    id: 'prim',
    name: "Prim's Algorithm",
    family: 'graph',

    idea: [
        'Start a tree from any single node, and put every edge leaving it into a heap.',
        'Repeatedly take the cheapest edge out of the heap, and if it reaches a node not yet in the tree, add both the edge and the node.',
        'Each new node brings its own edges into the heap, so the tree grows outwards until it spans everything it can reach.'
    ],
    analogy: 'Laying cable from one building. At every stage you lay the cheapest run that connects somewhere new, never a run between two buildings you have already wired.',
    whenToUse: 'Connecting everything as cheaply as possible when the graph is dense, since it works from the nodes outwards rather than sorting every edge first.',
    stable: null,

    code: {
        pseudocode: [
            { id: 'start', text: 'put the start node in the tree', indent: 0 },
            { id: 'push-edges', text: 'put every edge leaving it into the heap', indent: 0 },
            { id: null, text: 'while the heap is not empty:', indent: 0 },
            { id: 'pop-min', text: 'take the cheapest edge out', indent: 1 },
            { id: 'skip-visited', text: 'if it reaches a node already in the tree, drop it', indent: 2 },
            { id: 'add-edge', text: 'otherwise add the edge and the node to the tree', indent: 2 },
            { id: null, text: 'and put that node\'s edges into the heap', indent: 2 }
        ],
        python: [
            { id: 'start', text: 'visited.add(start)', indent: 0 },
            { id: 'push-edges', text: 'heapq.heappush(min_heap, (weight, start, neighbor))', indent: 0 },
            { id: null, text: 'while min_heap:', indent: 0 },
            { id: 'pop-min', text: 'weight, u, v = heapq.heappop(min_heap)', indent: 1 },
            { id: 'skip-visited', text: 'if v in visited: continue', indent: 2 },
            { id: 'add-edge', text: 'mst_edges.append((u, v, weight)); visited.add(v)', indent: 2 },
            { id: null, text: 'for neighbor, w in graph[v].items(): heappush(...)', indent: 2 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(V)',
                theta: 'V',
                reason: 'A path that begins at the start: each node that joins the tree pushes the one edge to its unvisited neighbour, so the heap never holds more than a couple of entries and every push and pop is constant time. That is V-1 rounds.'
            },
            average: {
                value: 'O(E log E)',
                theta: 'E log E',
                reason: 'On a random connected graph up to E edges are pushed and popped, and the heap grows to a size in proportion to E, so each push and pop costs about log E.'
            },
            worst: {
                value: 'O(E log E)',
                theta: 'E log E',
                reason: 'A complete graph: an edge whose far end is already in the tree is still pushed, popped and only then discarded, so the heap traffic is driven by E and not by V, and the heap holds a share of all E edges at once.'
            }
        },
        overall: { O: 'E log E', Omega: 'V', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        caseScope: 'The cases are over graphs in which the start reaches every node, which is what the page generator makes. A start that reaches fewer nodes does less work, because the part it cannot reach is never touched.',
        worked: {
            input: 'A-B 4, A-C 2, B-D 5, C-D 8, D-E 6 starting at A',
            comparisons: 4,
            note: 'V = 5, so the tree takes 4 edges: A-C 2, A-B 4, B-D 5, D-E 6, weighing 17. The heap handed back 5 edges to get them, because C-D 8 came out after D was already in the tree and was dropped. That dropped edge is the gap between E pops and V-1 additions.'
        },
        space: {
            value: 'O(V + E)',
            what: 'the heap, which can hold one entry per edge, plus the visited set and the tree itself'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The sizes above are this one graph; the figure is how the work would grow if the graph got bigger.',
        growth: 'nlogn',
        growthBasis: 'E, the number of edges',
        growthNote: null,
        divergence: 'Prim is sometimes quoted at O(E log V), which comes from a heap that holds at most one entry per node and updates keys in place. This endpoint pushes a separate entry for every edge, so the heap holds up to E items and the honest figure is O(E log E). Since E is at most V squared, log E is at most 2 log V, so the two differ by a constant factor rather than a different shape.'
    }
};
