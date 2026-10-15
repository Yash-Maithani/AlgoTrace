# Algorithm Visualizer - Quick Reference Guide

## 🚀 Project Overview
**Algorithm Visualizer v2.1** is an interactive Flask web application for learning algorithms through visual animations.

## 📊 Key Statistics
- **10+ Algorithms**: 6 Sorting + 4 Graph algorithms
- **3000+ Lines of Code**: Python, HTML, CSS, JavaScript
- **Modern Tech Stack**: Flask, D3.js, CSS3 animations
- **Educational Focus**: Students, educators, developers

## 🎯 Main Features

### Sorting Algorithms
1. **Bubble Sort** - O(n²) - Educational favorite
2. **Selection Sort** - O(n²) - Simple selection
3. **Insertion Sort** - O(n²) - Incremental building
4. **Heap Sort** - O(n log n) - Heap structure
5. **Merge Sort** - O(n log n) - Divide & conquer
6. **Quick Sort** - O(n log n) avg - Pivot-based

**Features:**
- Speed control: 1-200 range with ultra-fast animations
- Real-time stats: Comparisons and swaps
- Input methods: Random (5-100 elements) or manual
- Controls: Play, Pause, Reset

### Graph Algorithms
1. **BFS** - Breadth-First Search for level traversal
2. **DFS** - Depth-First Search for deep exploration
3. **Dijkstra** - Shortest path in weighted graphs
4. **Prim** - Minimum Spanning Tree construction

**Features:**
- Interactive graph input (2-26 nodes)
- Color-coded visualization states
- Random graph generation
- Step-by-step animation

## 🔧 Quick Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Installation
```bash
# 1. Navigate to project directory
cd PBL2

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run application
python app.py

# 6. Open browser
# Navigate to http://localhost:5002
```

## 🎨 Recent Enhancements (v2.1)

### Speed Control Enhancement
- **Doubled speed range**: 1-200 (from 1-100)
- **Smart tooltips**: "Slow" → "Default" → "⚡Lightning"
- **Exponential scaling**: Ultra-fast 10ms animations
- **Adaptive transitions**: Smooth high-speed performance

### Graph Visualization Fixes
- **UI cleanup**: Removed unnecessary legend box
- **Canvas management**: Robust clearCanvas() implementation
- **Artifact prevention**: Proper SVG element handling
- **Button fixes**: Restored "Generate Random Graph" functionality

## 🗂️ Project Structure
```
PBL2/
├── app.py                    # Main Flask app (458 lines)
├── requirements.txt          # Dependencies
├── sorting_algorithms/       # 6 sorting implementations
├── templates/               # 13 HTML templates
│   ├── sorting.html         # Sorting visualizer
│   ├── graph_base.html      # Graph algorithms (2729 lines)
│   └── ...
├── static/
│   ├── styles.css          # Main stylesheet (755 lines)
│   └── js/                 # JavaScript modules
├── project_documentation/   # Documentation folder
└── tests/                  # Unit tests
```

## 🌐 API Endpoints
- `GET /` - Landing page
- `GET /sorting` - Sorting visualizer
- `GET /graph?algo=bfs` - Graph algorithms
- `POST /run_bfs` - Execute BFS
- `POST /run_dfs` - Execute DFS
- `POST /run_dijkstra` - Execute Dijkstra
- `POST /run_prim` - Execute Prim
- `POST /generate_random_graph` - Random graph generation

## 🎯 Educational Value

### Target Audience
- **Students**: Computer science algorithm courses
- **Educators**: Visual teaching aids and demonstrations
- **Self-learners**: Independent algorithm study
- **Interview prep**: Hands-on algorithm practice

### Learning Benefits
- **Visual understanding**: Step-by-step algorithm execution
- **Performance metrics**: Real-time comparisons and swaps
- **Interactive experimentation**: Custom input testing
- **Complexity analysis**: Big O notation examples

## 📈 Performance Specs
- **Sorting**: 5-100 elements, 60fps animations
- **Graphs**: 2-26 nodes, up to 325 edges
- **Speed range**: 10ms - 1200ms intervals
- **Browser support**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## 🔮 Future Roadmap

### Planned Algorithms
- **Floyd-Warshall**: All-pairs shortest paths
- **Kruskal's MST**: Union-Find visualization
- **Topological Sort**: Directed graph ordering
- **A* Search**: Intelligent pathfinding

### Advanced Features
- **Comparison mode**: Side-by-side algorithms
- **Export tools**: Images, videos, data
- **User accounts**: Progress tracking
- **PWA support**: Offline functionality

## 🛠️ Technical Highlights

### Backend (Flask)
- RESTful API design
- JSON data exchange
- Modular route handling
- Algorithm implementations

### Frontend
- Responsive CSS Grid
- D3.js graph rendering
- ES6+ JavaScript
- Smooth CSS animations

### Performance
- Optimized DOM manipulation
- Efficient SVG rendering
- Memory-conscious design
- Cross-browser compatibility

## 📋 Documentation Files

This documentation package includes:

1. **Project_Summary.md** - Detailed markdown documentation
2. **Algorithm_Visualizer_Documentation.html** - Formatted HTML version
3. **Algorithm_Visualizer_Documentation.txt** - Plain text backup
4. **Quick_Reference.md** - This quick reference guide
5. **generate_docs.py** - Documentation generator script

## 💡 Usage Tips

### For Students
- Start with Bubble Sort to understand basic concepts
- Use speed control to follow algorithm steps
- Try different input sizes to see performance differences
- Compare stable vs unstable sorting algorithms

### For Educators
- Use in classroom for live demonstrations
- Assign different algorithms for comparison
- Discuss time/space complexity while visualizing
- Create custom test cases for specific scenarios

### For Developers
- Study implementation details in source code
- Extend with additional algorithms
- Customize visualizations for specific needs
- Use as interview preparation tool

---

**Quick Links:**
- 🌐 **Launch App**: `python app.py` → http://localhost:5002
- 📖 **Full Docs**: Algorithm_Visualizer_Documentation.html
- 🔧 **Setup**: Follow installation steps above
- 🚀 **GitHub**: Ready for version control and sharing

**Version**: 2.1 | **Framework**: Flask | **Last Updated**: 2025
