/* Lesson content for Dijkstra's Algorithm. Contract: static/js/lessons/README.md
   Figures describe the /run_dijkstra endpoint in app.py, which finds the next
   node with a linear min() scan rather than a priority queue. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.dijkstra = {
    id: 'dijkstra',
    name: "Dijkstra's Algorithm",
    family: 'graph',

    idea: [
        'Give every node a best known distance from the start: zero for the start, infinity for the rest.',
        'Repeatedly settle the nearest unvisited node, because no later route can reach it more cheaply.',
        'From that node, check whether going through it gives any neighbour a shorter distance, and write the better number down.'
    ],
    analogy: 'Planning a drive. You work outwards from home, and once you know the quickest way to a nearby town you never need to reconsider it, because any other route there would be longer already.',
    whenToUse: 'Shortest routes when edges carry a cost and none of them is negative. Road networks, latency between servers, cheapest connection through a network of prices.',
    stable: null,

    code: {
        pseudocode: [
            { id: null, text: 'distance to start = 0, every other = infinity', indent: 0 },
            { id: null, text: 'while there are unvisited nodes:', indent: 0 },
            { id: 'pick-min', text: 'settle the unvisited node with the smallest distance', indent: 1 },
            { id: null, text: 'for each unvisited neighbour of it:', indent: 1 },
            { id: 'relax', text: 'if going through it is shorter, write the new distance', indent: 2 }
        ],
        python: [
            { id: null, text: "distances = {node: float('infinity') for node in graph}", indent: 0 },
            { id: null, text: 'while unvisited:', indent: 0 },
            { id: 'pick-min', text: 'current = min(unvisited, key=lambda node: distances[node])', indent: 1 },
            { id: null, text: 'for neighbor, weight in graph[current].items():', indent: 1 },
            { id: 'relax', text: 'if distances[current] + weight < distances[neighbor]:', indent: 2 },
            { id: null, text: 'distances[neighbor] = distances[current] + weight', indent: 3 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(V squared)',
                theta: 'V squared',
                reason: 'Even the cheapest graph in which the start reaches every node needs V picks, and each pick walks every one of the V nodes in node_order to find the nearest unvisited one, whatever the weights are.'
            },
            average: {
                value: 'O(V squared)',
                theta: 'V squared',
                reason: 'V scans of up to V nodes gives V squared, and the relaxation loop adds only E on top, which is the smaller term on a dense graph.'
            },
            worst: {
                value: 'O(V squared)',
                theta: 'V squared',
                reason: 'The scan cost does not depend on the weights or the edges: any graph in which the start reaches every node pays V scans of V nodes. The relaxation loop adds E on top, and E is at most V squared.'
            }
        },
        overall: { O: 'V squared', Omega: 'V squared', Theta: 'V squared' },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        caseScope: 'The cases are over graphs in which the start reaches every node, which is what the page generator makes. A start that reaches fewer nodes does less work, because the part it cannot reach is never touched.',
        worked: {
            input: 'A-B 4, A-C 2, B-D 5, C-D 8, D-E 6 starting at A',
            comparisons: 5,
            note: 'V = 5, so there are 5 settle steps and the min() scans read 5 + 4 + 3 + 2 + 1 = 15 distances between them. This run also makes 5 relaxations. Note that A reaches D through B at 9, not through C at 10, even though C is the nearer neighbour.'
        },
        space: {
            value: 'O(V)',
            what: 'one distance and one predecessor per node, plus the set of unvisited nodes'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The sizes above are this one graph; the figure is how the work would grow if the graph got bigger.',
        growth: 'n2',
        growthBasis: 'V, the number of nodes',
        growthNote: null,
        divergence: 'Dijkstra is usually quoted at O((V + E) log V), which assumes a binary heap hands back the nearest node in log time. This endpoint uses min() over a set instead, a plain linear scan, so it is the O(V squared) form. That is actually the better choice on a dense graph, where E approaches V squared anyway. There is a second consequence: when two nodes tie on distance, min() breaks the tie by set iteration order, which Python varies between runs, so a tied graph can animate in a different order after a restart.'
    }
};
