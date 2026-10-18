/* Lesson content for Breadth-First Search. Contract: static/js/lessons/README.md
   Figures describe the /run_bfs endpoint in app.py, which keeps its queue in a
   plain list. That choice, not the algorithm, is what costs it the V in V times E. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.bfs = {
    id: 'bfs',
    name: 'Breadth-First Search',
    family: 'graph',

    idea: [
        'Put the starting node in a queue, then take nodes off the front one at a time.',
        'Each time you visit a node, add every neighbour you have not seen to the back of the queue.',
        'Because the queue is first in first out, everything one step away is visited before anything two steps away.'
    ],
    analogy: 'Ripples from a stone dropped in water. The ring one metre out is complete before the ring two metres out begins.',
    whenToUse: 'To find the fewest hops between two nodes in an unweighted graph, or to sweep a whole network level by level. On an unweighted graph it gives the shortest path and is cheaper than Dijkstra.',
    stable: null,

    code: {
        pseudocode: [
            { id: 'start', text: 'put the start node in the queue', indent: 0 },
            { id: null, text: 'while the queue is not empty:', indent: 0 },
            { id: 'pop', text: 'take the node at the front and visit it', indent: 1 },
            { id: null, text: 'for each neighbour of that node:', indent: 1 },
            { id: 'enqueue', text: 'if it is new, add it to the back of the queue', indent: 2 }
        ],
        python: [
            { id: 'start', text: 'queue = [start]', indent: 0 },
            { id: null, text: 'while queue:', indent: 0 },
            { id: 'pop', text: 'node = queue.pop(0)', indent: 1 },
            { id: null, text: 'for neighbor in graph.get(node, []):', indent: 1 },
            { id: 'enqueue', text: 'if neighbor not in visited and neighbor not in queue:', indent: 2 },
            { id: null, text: 'queue.append(neighbor)', indent: 3 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(V)',
                theta: 'V',
                reason: 'A path that begins at the start: the queue never holds more than one node, so every visit and every `not in queue` check costs a constant amount, V of them in all.'
            },
            average: {
                value: 'O(V times E)',
                theta: 'V times E',
                reason: 'On a random connected graph the queue holds a steady share of all the nodes for much of the run, and the `neighbor not in queue` scan runs for a steady share of the edges, so the scans add up to a constant fraction of V times E.'
            },
            worst: {
                value: 'O(V times E)',
                theta: 'V times E',
                reason: 'A star or a complete graph: the start puts all its neighbours in the queue at once, so later edges each scan a queue of about V nodes. On top of that queue.pop(0) shifts every remaining element along, once per visit.'
            }
        },
        overall: { O: 'V times E', Omega: 'V', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        caseScope: 'The cases are over graphs in which the start reaches every node, which is what the page generator makes. A start that reaches fewer nodes does less work, because the part it cannot reach is never touched.',
        worked: {
            input: 'A-B, A-C, B-D, C-D, D-E starting at A',
            comparisons: 5,
            note: 'V = 5 and E = 5. The run visits all 5 nodes and queues 4 more after the start, which is 10 node events and a closing frame. The number counted here is nodes visited; every node is visited exactly once however many edges point at it.'
        },
        space: {
            value: 'O(V)',
            what: 'the queue and the visited set, which between them hold at most one entry per node'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The sizes above are this one graph; the figure is how the work would grow if the graph got bigger.',
        growth: null,
        growthBasis: null,
        growthNote:
            'O(V times E) depends on two numbers at once, the nodes and the ' +
            'edges, so it is not one of the curves below.',
        divergence: 'Breadth-first search is usually quoted at O(V + E). That assumes a deque for the queue and a set for the membership test, both of which answer in constant time. This endpoint uses a list for both, so taking from the front is O(V) and the `not in queue` check is another O(V), once per edge. Swapping in collections.deque and a set would make it the familiar O(V + E) without changing a single step it draws.'
    }
};
