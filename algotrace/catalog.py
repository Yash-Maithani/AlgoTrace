"""Which algorithms the site has, in one place.

Every picker, the /learn order, Home's "Start here", every count either page
prints and the sitemap's deep links are read from here, so no two of them can
disagree.
"""
from .algorithms.searching.binary_search import binary_search
from .algorithms.searching.jump_search import jump_search
from .algorithms.searching.linear_search import linear_search
from .algorithms.sorting.bubble_sort import bubble_sort
from .algorithms.sorting.counting_sort import counting_sort
from .algorithms.sorting.heap_sort import heap_sort
from .algorithms.sorting.insertion_sort import insertion_sort
from .algorithms.sorting.merge_sort import merge_sort
from .algorithms.sorting.quick_sort import quick_sort
from .algorithms.sorting.radix_sort import radix_sort
from .algorithms.sorting.selection_sort import selection_sort

# Dictionary of sorting algorithms
sorting_algo_dict = {
    "Bubble Sort": bubble_sort,
    "Selection Sort": selection_sort,
    "Insertion Sort": insertion_sort,
    "Heap Sort": heap_sort,
    "Merge Sort": merge_sort,
    "Quick Sort": quick_sort,
    "Counting Sort": counting_sort,
    "Radix Sort": radix_sort,
}

# Display name to lesson file id, so the picker and the Learn panel agree.
SORT_LESSON_IDS = {
    "Bubble Sort": "bubble_sort",
    "Selection Sort": "selection_sort",
    "Insertion Sort": "insertion_sort",
    "Merge Sort": "merge_sort",
    "Quick Sort": "quick_sort",
    "Heap Sort": "heap_sort",
    "Counting Sort": "counting_sort",
    "Radix Sort": "radix_sort",
}

SORT_PICK_NOTES = {
    "Bubble Sort": "Swap neighbours until nothing is out of order.",
    "Selection Sort": "Find the smallest, place it, repeat.",
    "Insertion Sort": "Slide each value back into a sorted prefix.",
    "Merge Sort": "Split, sort the halves, merge them back.",
    "Quick Sort": "Partition around a pivot, then recurse.",
    "Heap Sort": "Build a heap, pull the largest off the top.",
    "Counting Sort": "Count each value, then write them back in order.",
    "Radix Sort": "Bucket by the ones digit, then by the tens.",
}

SEARCH_ALGORITHMS = {
    "linear_search": linear_search,
    "binary_search": binary_search,
    "jump_search": jump_search,
}

SEARCH_PICKER = [
    ("linear_search", "Linear Search", "Check every value until you find it."),
    ("binary_search", "Binary Search", "Halve a sorted list over and over."),
    ("jump_search", "Jump Search", "Jump ahead in blocks, then scan one."),
]

# Dictionary of graph algorithms
graph_algo_dict = {
    "bfs": "bfs",
    "dfs": "dfs",
    "dijkstra": "dijkstra",
    "prim": "prim",
    "kruskal": "kruskal",
    "floyd_warshall": "floyd_warshall",
    "bellman_ford": "bellman_ford",
    "topological_sort": "topological_sort",
    "astar": "astar"
}

# The Graphs picker, shared by the graph page and the A* grid page: the id,
# the name shown, and one line on what it does.
GRAPH_PICKER = [
    ("bfs", "BFS", "Explore one ring at a time."),
    ("dfs", "DFS", "Follow one path to its end."),
    ("dijkstra", "Dijkstra", "Cheapest route with weights."),
    ("prim", "Prim", "Grow one tree by cheapest edge."),
    ("kruskal", "Kruskal", "Take cheap edges, skip loops."),
    ("floyd_warshall", "Floyd-Warshall", "Every pair at once."),
    ("bellman_ford", "Bellman-Ford", "Survives negative edges."),
    ("topological_sort", "Topological Sort", "Order tasks so every arrow points forward."),
    ("astar", "A* on a grid", "Shortest path, steered towards the goal."),
]

# The suggested beginner order, one entry per algorithm: lesson id, name,
# the page and query that open it, and one line on what it does. /learn lists
# it in full and Home's "Start here" shows its first few, so the two pages
# cannot disagree; every count on either page is worked out from the
# registries above, never written by hand. The complexity figures on /learn
# come from the lesson files themselves (static/js/learnfigures.js).
LEARN_ORDER = [
    ("linear_search", "Linear Search", "searching_page", "algorithm=linear_search",
     "Check every item until you find it."),
    ("binary_search", "Binary Search", "searching_page", "algorithm=binary_search",
     "Halve a sorted list over and over."),
    ("jump_search", "Jump Search", "searching_page", "algorithm=jump_search",
     "Jump ahead in blocks, then scan the one that can hold it."),
    ("bubble_sort", "Bubble Sort", "sorting_page", "algorithm=Bubble+Sort",
     "Swap neighbours until nothing is out of order."),
    ("selection_sort", "Selection Sort", "sorting_page", "algorithm=Selection+Sort",
     "Find the smallest, place it, repeat."),
    ("insertion_sort", "Insertion Sort", "sorting_page", "algorithm=Insertion+Sort",
     "Slide each value back into a sorted prefix."),
    ("merge_sort", "Merge Sort", "sorting_page", "algorithm=Merge+Sort",
     "Split, sort the halves, merge them back."),
    ("quick_sort", "Quick Sort", "sorting_page", "algorithm=Quick+Sort",
     "Partition around a pivot, then recurse."),
    ("heap_sort", "Heap Sort", "sorting_page", "algorithm=Heap+Sort",
     "Build a heap, pull the largest off the top."),
    ("counting_sort", "Counting Sort", "sorting_page", "algorithm=Counting+Sort",
     "Count each value, then write them back in order. No comparisons."),
    ("radix_sort", "Radix Sort", "sorting_page", "algorithm=Radix+Sort",
     "Bucket by the ones digit, then by the tens. No comparisons."),
    ("bfs", "Breadth-First Search", "graph_page", "algo=bfs",
     "Explore a network one ring at a time."),
    ("dfs", "Depth-First Search", "graph_page", "algo=dfs",
     "Follow one path as far as it goes, then back up."),
    ("topological_sort", "Topological Sort", "graph_page", "algo=topological_sort",
     "Order tasks so every arrow points forward, or find the cycle."),
    ("dijkstra", "Dijkstra's Algorithm", "graph_page", "algo=dijkstra",
     "Cheapest route when edges have lengths."),
    ("astar", "A* Search", "graph_page", "algo=astar",
     "Dijkstra steered towards a goal, on a grid you draw."),
    ("prim", "Prim's Algorithm", "graph_page", "algo=prim",
     "Grow one tree outward by the cheapest edge."),
    ("kruskal", "Kruskal's Algorithm", "graph_page", "algo=kruskal",
     "Take cheap edges that do not close a loop."),
    ("bellman_ford", "Bellman-Ford", "graph_page", "algo=bellman_ford",
     "Shortest paths that survive negative edges."),
    ("floyd_warshall", "Floyd-Warshall", "graph_page", "algo=floyd_warshall",
     "Shortest path between every pair at once."),
]

# How many of the first entries Home's "Start here" shows.
START_HERE_COUNT = 6


def algorithm_counts():
    """Every count the Home and /learn pages print, from the registries."""
    counts = {"sorting": len(sorting_algo_dict), "searching": len(SEARCH_ALGORITHMS),
              "graphs": len(GRAPH_PICKER), "total": len(LEARN_ORDER)}
    assert counts["total"] == counts["sorting"] + counts["searching"] + counts["graphs"]
    return counts


def deep_links():
    """The pages that open on one algorithm, for the sitemap: each is a different
    page to a reader and to a search engine."""
    links = ["/sorting?algorithm=%s" % name.replace(" ", "+") for name in sorting_algo_dict]
    links += ["/searching?algorithm=%s" % key for key, _name, _note in SEARCH_PICKER]
    links += ["/graph?algo=%s" % key for key, _name, _note in GRAPH_PICKER]
    return links
