# Algorithm Visualizer 🎯

A comprehensive Flask-based web application for visualizing sorting and graph algorithms with interactive animations and step-by-step execution.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.3+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### Sorting Algorithms

All six are implemented in `sorting_algorithms/` and selectable from the UI. Each was
verified against Python's `sorted()` across 400+ randomised cases plus empty,
single-element, duplicate, already-sorted and reverse-sorted inputs.

- **Bubble Sort** — adjacent comparisons and swaps
- **Selection Sort** — repeated minimum selection
- **Insertion Sort** — element-by-element insertion
- **Heap Sort** — heap construction and extraction
- **Merge Sort** — divide and conquer
- **Quick Sort** — pivot selection and partitioning

### Graph Algorithms

All seven now have a template, a `graph_algo_dict` entry in `app.py` and a
server-side `/run_*` endpoint:

- **Breadth-First Search (BFS)** — level-by-level traversal
- **Depth-First Search (DFS)** — deep exploration paths
- **Dijkstra's Algorithm** — shortest path finding
- **Prim's Algorithm** — minimum spanning tree
- **Kruskal's Algorithm** — MST via Union-Find; yields a spanning forest on disconnected input
- **Floyd-Warshall** — all-pairs shortest paths with path reconstruction
- **Bellman-Ford** — shortest paths over negative weights, with negative-cycle detection

All seven animate end to end in the browser. Every graph page is rendered from
`templates/graph_base.html`, which holds the whole D3 visualizer and switches on
the algorithm the route passed it; each child template contributes only its
`{% block extra_content %}` information panel.

### Known Issues

- `bfs.html`, `dfs.html`, `dijkstra.html` and `prim.html` each still carry a
  complete standalone HTML document after their `{% endblock %}`. Jinja discards
  everything outside a block, so none of it is served — the four pages work
  because `graph_base.html` drives them, not because of those tails. They are
  dead code and safe to delete; they were left in place because the pages render
  correctly with or without them. `kruskal.html`, `floyd_warshall.html` and
  `bellman_ford.html` have had theirs removed.
- `static/js/graph-visualizer.js` is loaded by no page. It is a canvas renderer
  that needs a `<canvas>` element `graph_base.html` never creates, and the only
  reference to it is the `<script>` tag in the discarded tail of `bfs.html`
  above. Wiring it in would mean running a second renderer alongside the base's
  D3 one, so it was left unreferenced rather than revived.
- BFS, DFS and Dijkstra never call `displayResults()` on their `final` step, so
  those three pages animate and report the outcome in the status panel but leave
  the result panel below the graph empty. The `bfs`, `dfs` and `dijkstra`
  branches of `displayResults()` exist and are unused. Kruskal, Prim,
  Floyd-Warshall and Bellman-Ford do fill it.
- Sorting embeds every animation step into the HTML response, so large array
  sizes produce very large pages. There is no server-side clamp.
- `/run_prim` raises `KeyError` when given hand-written JSON in which a node
  appears only as a neighbour and has no key of its own. `/run_bellman_ford`
  handles that case; `/run_prim` has not been changed.
- Several files are unreachable: no route renders `templates/base.html`,
  `index.html`, `error.html`, `sorting_new.html` or `bellman_ford_new.html`, and
  nothing imports `app_new.py`.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**
   ```bash
   cd /path/to/algorithm-visualizer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```
   or
   ```bash
   flask run
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Explore the algorithms!**
   - Choose **Sorting** for array sorting visualizations
   - Choose **Graph** for graph algorithm demonstrations

## 🎮 How to Use

### Sorting Algorithms

1. **Select an Algorithm**: Choose from Bubble Sort, Quick Sort, etc.
2. **Input Data**: 
   - **Random Array**: Specify size (1-1000 elements)
   - **Manual Input**: Enter comma-separated integers (e.g., `64,34,25,12,22,11,90`)
3. **Run Visualization**: Watch the step-by-step sorting process
4. **View Statistics**: See comparisons, swaps, and complexity information

### Graph Algorithms (Prim Example)

1. **Choose an Algorithm**: Append `?algo=prim` to `/graph` (or `bfs`, `dfs`, `dijkstra`)
2. **Provide a Graph**: Paste one in the input panel, or click a Quick Demo button
3. **Run Algorithm**: Click "Visualize Algorithm"
4. **Step Through**: Use play, pause and reset to walk the animation

## 🏗️ Project Architecture

```
📦 algorithm-visualizer/
├── 📁 sorting_algorithms/   # The sorting implementations app.py actually uses
│   ├── bubble_sort.py
│   ├── selection_sort.py
│   ├── insertion_sort.py
│   ├── heap_sort.py
│   ├── merge_sort.py
│   └── quick_sort.py
├── 📁 algorithms/           # Incomplete OOP refactor; not imported by app.py
│   ├── base.py
│   ├── 📁 sorting/          # bubble, quick, selection only
│   └── 📁 graph/            # empty
├── 📁 routes/              # Blueprints; registered only by app_new.py
│   ├── sorting_routes.py
│   └── graph_routes.py
├── 📁 services/            # Service layer; imported only by routes/
│   └── algorithm_service.py
├── 📁 templates/
│   ├── landing.html          # Served at /
│   ├── sorting.html          # Served at /sorting
│   ├── graph_base.html       # Parent of the graph pages; holds the D3 engine
│   ├── bfs.html … bellman_ford.html  # All seven; each is an info panel over graph_base
│   ├── base.html             # Unused; only sorting_new.html extends it
│   └── index.html, sorting_new.html, bellman_ford_new.html, error.html
├── 📁 static/
│   ├── styles.css            # Main stylesheet
│   └── 📁 js/               # common.js, graph-visualizer.js — not loaded by any live page
├── 📁 tests/
│   └── test_kruskal.py       # Covers /run_kruskal; needs pytest installed
├── app.py                   # Entry point — the one in Quick Start above
├── app_new.py               # Alternative blueprint entry point; needs flask-cors
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## 🔧 Technical Details

### Algorithm Flow: UI → Server → Animation

1. **User Input**: User selects algorithm and provides data via web interface
2. **Frontend Processing**: JavaScript validates input and sends AJAX request
3. **Backend Execution**: Flask routes call service layer algorithms
4. **Step Generation**: Algorithms return visualization steps as JSON
5. **Animation Rendering**: Frontend animates steps using Canvas/SVG

### API Endpoints

Routes registered by `app.py`, the entry point used in Quick Start above:

| Method | Route | Purpose |
| --- | --- | --- |
| GET, POST | `/` | Landing page |
| GET, POST | `/sorting` | Sorting visualizer page and run |
| GET | `/graph` | Graph visualizer page; `?algo=` takes any of the seven keys in `graph_algo_dict` |
| POST | `/run_bfs` | Execute BFS traversal |
| POST | `/run_dfs` | Execute DFS traversal |
| POST | `/run_dijkstra` | Execute Dijkstra's algorithm |
| POST | `/run_prim` | Execute Prim's algorithm |
| POST | `/run_kruskal` | Execute Kruskal's MST algorithm |
| POST | `/run_floyd_warshall` | Execute Floyd-Warshall all-pairs shortest paths |
| POST | `/run_bellman_ford` | Execute Bellman-Ford shortest paths |
| POST | `/generate_random_graph` | Generate a connected random graph |

Request bodies are not uniform. `visualize()` in `graph_base.html` picks the
shape per algorithm:

- `/run_bfs`, `/run_dfs`, `/run_dijkstra`, `/run_prim`, `/run_bellman_ford` take
  `{"graph": {...}, "start": "A"}`, where `graph` is an adjacency object.
- `/run_kruskal` and `/run_floyd_warshall` take
  `{"nodes": ["A", ...], "edges": [["A", "B", 3], ...]}`.

Responses are a JSON array of `[action, ...]` animation steps ending in a
`["final", ...]` step — except `/run_bellman_ford`, which returns an object
with `steps`, `has_negative_cycle`, `distances` and `iterations`.

Unreachable distances are sent as the string `"∞"`, not a float. JSON has no
infinity literal, and `json.dumps(float("inf"))` emits a bare `Infinity` token
that `JSON.parse` rejects. The front end never does arithmetic on a distance it
receives; `isUnreachable()` in `graph_base.html` is the single place that
recognises the sentinel.

The blueprint API — `/sorting/api/visualize`, `/sorting/api/algorithms`,
`/graph/api/bfs`, `/graph/api/dfs`, `/graph/api/dijkstra` — is defined in `routes/`
and registered only by `app_new.py`, which is **not** the entry point documented above.
`app_new.py` also imports `flask-cors`; it is listed in `requirements.txt` but must be
installed or the module fails to import.

## 🧪 Testing

Run the test suite to verify algorithm correctness:

```bash
# Install pytest if not already installed
pip install pytest pytest-flask

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_kruskal.py -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Adding New Algorithms

1. **Create Algorithm Class**: Inherit from `SortingAlgorithm` or `GraphAlgorithm`
2. **Implement Required Methods**: `visualize()`, `get_name()`, `get_description()`, etc.
3. **Add to Service**: Register in the appropriate service class
4. **Create Template**: Add HTML template for visualization
5. **Write Tests**: Add test cases in the `tests/` directory

## 👤 Author

**Yash Maithani**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Algorithms inspired by classic computer science textbooks
- Visualization techniques adapted from educational platforms
- Flask framework for robust web development
- D3.js and Canvas API for interactive graphics

---

**Built with ❤️ for computer science education and algorithm visualization**
