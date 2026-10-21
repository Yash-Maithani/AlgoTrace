"""A random connected graph for the Random button on the graph pages.

A random spanning tree first, so every node is reached, then extra edges
between pairs not yet joined. Weights are whole numbers from 1 to 20.
Called by POST /generate_random_graph with the counts already checked.
"""
import random


def random_connected_graph(num_nodes, num_edges):
    # Generate nodes (A, B, C, ...)
    nodes = [chr(ord('A') + i) for i in range(num_nodes)]

    # First, create a spanning tree to ensure connectivity
    edges = []
    used_nodes = [nodes[0]]
    remaining_nodes = nodes[1:]

    while remaining_nodes:
        # Pick a random used node and a random remaining node
        u = random.choice(used_nodes)
        v = remaining_nodes.pop(random.randint(0, len(remaining_nodes) - 1))
        weight = random.randint(1, 20)
        edges.append([u, v, weight])
        used_nodes.append(v)

    # Add additional random edges if needed
    edge_set = {tuple(sorted([e[0], e[1]])) for e in edges}

    while len(edges) < num_edges:
        u = random.choice(nodes)
        v = random.choice(nodes)

        if u != v:  # No self-loops
            edge_key = tuple(sorted([u, v]))
            if edge_key not in edge_set:
                weight = random.randint(1, 20)
                edges.append([u, v, weight])
                edge_set.add(edge_key)

    return nodes, edges
