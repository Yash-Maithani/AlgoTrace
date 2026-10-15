// Common Graph Visualization Utilities
// Fixes: Double weights, Node overlap, Responsive expansion

class GraphVisualizer {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Configuration options
        this.options = {
            nodeRadius: options.nodeRadius || 25,
            minRadius: options.minRadius || 100,
            maxRadius: options.maxRadius || Math.min(this.canvas.width, this.canvas.height) * 0.4,
            animationSpeed: options.animationSpeed || 400,
            ...options
        };
        
        // State management
        this.nodes = [];
        this.edges = [];
        this.nodePositions = new Map();
        this.isAnimating = false;
        this.currentLayout = null;
        
        // Initialize canvas
        this.initCanvas();
    }
    
    initCanvas() {
        // Enable high DPI rendering
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);
        
        // Set canvas style
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        
        // Enable smooth rendering
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
    }
    
    // Calculate optimal layout for given number of nodes
    calculateLayout(nodeCount) {
        const canvasWidth = this.canvas.width / (window.devicePixelRatio || 1);
        const canvasHeight = this.canvas.height / (window.devicePixelRatio || 1);
        
        let radius, centerX, centerY;
        
        if (nodeCount <= 6) {
            radius = this.options.minRadius;
        } else if (nodeCount <= 12) {
            radius = this.options.minRadius * 1.3;
        } else if (nodeCount <= 20) {
            radius = this.options.minRadius * 1.6;
        } else {
            radius = this.options.maxRadius;
        }
        
        // Ensure radius fits in canvas
        radius = Math.min(radius, this.options.maxRadius);
        centerX = canvasWidth / 2;
        centerY = canvasHeight / 2;
        
        return { radius, centerX, centerY, nodeCount };
    }
    
    // Get node position with multi-circle support for large graphs
    getNodePosition(nodeIndex, layout) {
        const { radius, centerX, centerY, nodeCount } = layout;
        
        if (nodeCount <= 20) {
            // Single circle layout
            const angle = (2 * Math.PI / nodeCount) * nodeIndex;
            return {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle)
            };
        } else {
            // Multi-circle layout for large graphs
            const nodesPerCircle = 12;
            const circleIndex = Math.floor(nodeIndex / nodesPerCircle);
            const nodeInCircle = nodeIndex % nodesPerCircle;
            const circleRadius = radius * (0.5 + circleIndex * 0.3);
            const angle = (2 * Math.PI / nodesPerCircle) * nodeInCircle;
            
            return {
                x: centerX + circleRadius * Math.cos(angle),
                y: centerY + circleRadius * Math.sin(angle)
            };
        }
    }
    
    // Update nodes and recalculate positions with animation
    async updateNodes(nodes, edges = null) {
        if (this.isAnimating) return;
        
        this.nodes = [...nodes];
        if (edges) this.edges = [...edges];
        
        const newLayout = this.calculateLayout(this.nodes.length);
        const oldPositions = new Map(this.nodePositions);
        
        // Calculate new positions
        const newPositions = new Map();
        this.nodes.forEach((node, index) => {
            newPositions.set(node, this.getNodePosition(index, newLayout));
        });
        
        // Animate to new positions if layout changed significantly
        if (this.shouldAnimate(newLayout)) {
            await this.animateLayoutChange(oldPositions, newPositions);
        } else {
            this.nodePositions = newPositions;
            this.currentLayout = newLayout;
            this.draw();
        }
    }
    
    shouldAnimate(newLayout) {
        if (!this.currentLayout) return false;
        
        // Animate if radius changed significantly or node count changed
        const radiusChange = Math.abs(newLayout.radius - this.currentLayout.radius);
        const nodeCountChange = newLayout.nodeCount !== this.currentLayout.nodeCount;
        
        return radiusChange > 20 || nodeCountChange;
    }
    
    async animateLayoutChange(oldPositions, newPositions) {
        this.isAnimating = true;
        const duration = this.options.animationSpeed;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out)
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            
            // Interpolate positions
            const interpolatedPositions = new Map();
            this.nodes.forEach(node => {
                const oldPos = oldPositions.get(node) || newPositions.get(node);
                const newPos = newPositions.get(node);
                
                interpolatedPositions.set(node, {
                    x: oldPos.x + (newPos.x - oldPos.x) * easedProgress,
                    y: oldPos.y + (newPos.y - oldPos.y) * easedProgress
                });
            });
            
            this.nodePositions = interpolatedPositions;
            this.draw();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.isAnimating = false;
                this.nodePositions = newPositions;
            }
        };
        
        requestAnimationFrame(animate);
        
        // Return promise that resolves when animation completes
        return new Promise(resolve => {
            setTimeout(resolve, duration);
        });
    }
    
    // Clear canvas properly
    clear() {
        const canvasWidth = this.canvas.width / (window.devicePixelRatio || 1);
        const canvasHeight = this.canvas.height / (window.devicePixelRatio || 1);
        this.ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    }
    
    // Draw edges with weight labels (fixes double weight issue)
    drawEdges(highlightedEdges = [], edgeColors = {}) {
        const drawnWeights = new Set(); // Prevent duplicate weight labels
        
        this.edges.forEach(edge => {
            const fromPos = this.nodePositions.get(edge.from || edge.u);
            const toPos = this.nodePositions.get(edge.to || edge.v);
            
            if (!fromPos || !toPos) return;
            
            const isHighlighted = highlightedEdges.some(he => 
                (he.from === edge.from && he.to === edge.to) ||
                (he.from === edge.to && he.to === edge.from) ||
                (he.u === edge.u && he.v === edge.v) ||
                (he.u === edge.v && he.v === edge.u)
            );
            
            // Edge styling
            this.ctx.strokeStyle = edgeColors[edge.id] || (isHighlighted ? '#ff6d00' : '#888');
            this.ctx.lineWidth = isHighlighted ? 4 : 2;
            
            // Draw edge line
            this.ctx.beginPath();
            this.ctx.moveTo(fromPos.x, toPos.x);
            this.ctx.lineTo(toPos.x, toPos.y);
            this.ctx.stroke();
            
            // Draw weight label (prevent duplicates)
            if (edge.weight !== undefined && edge.weight !== null) {
                const edgeKey = `${Math.min(fromPos.x, toPos.x)}-${Math.min(fromPos.y, toPos.y)}-${edge.weight}`;
                
                if (!drawnWeights.has(edgeKey)) {
                    drawnWeights.add(edgeKey);
                    
                    const midX = (fromPos.x + toPos.x) / 2;
                    const midY = (fromPos.y + toPos.y) / 2;
                    
                    // Weight background
                    this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                    this.ctx.fillRect(midX - 12, midY - 8, 24, 16);
                    
                    // Weight text
                    this.ctx.font = 'bold 12px Arial';
                    this.ctx.fillStyle = isHighlighted ? '#e65100' : '#333';
                    this.ctx.fillText(edge.weight.toString(), midX, midY);
                }
            }
        });
    }
    
    // Draw nodes with proper state colors
    drawNodes(nodeStates = {}, nodeColors = {}) {
        this.nodes.forEach(node => {
            const pos = this.nodePositions.get(node);
            if (!pos) return;
            
            const state = nodeStates[node] || 'default';
            let nodeColor = nodeColors[node];
            
            if (!nodeColor) {
                switch (state) {
                    case 'visited': nodeColor = '#4caf50'; break;
                    case 'processing': nodeColor = '#ff9800'; break;
                    case 'queued': nodeColor = '#2196f3'; break;
                    case 'current': nodeColor = '#e91e63'; break;
                    case 'mst': nodeColor = '#ff6d00'; break;
                    default: nodeColor = '#f44336';
                }
            }
            
            // Node shadow
            this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
            this.ctx.shadowBlur = 4;
            this.ctx.shadowOffsetX = 2;
            this.ctx.shadowOffsetY = 2;
            
            // Draw node
            this.ctx.beginPath();
            this.ctx.arc(pos.x, pos.y, this.options.nodeRadius, 0, 2 * Math.PI);
            this.ctx.fillStyle = nodeColor;
            this.ctx.fill();
            
            // Clear shadow for border
            this.ctx.shadowColor = 'transparent';
            this.ctx.shadowBlur = 0;
            this.ctx.shadowOffsetX = 0;
            this.ctx.shadowOffsetY = 0;
            
            // Node border
            this.ctx.strokeStyle = '#222';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
            
            // Node label
            this.ctx.font = 'bold 16px Arial';
            this.ctx.fillStyle = '#fff';
            this.ctx.fillText(node.toString(), pos.x, pos.y);
        });
    }
    
    // Main draw method
    draw(nodeStates = {}, edgeHighlights = [], nodeColors = {}, edgeColors = {}) {
        this.clear();
        this.drawEdges(edgeHighlights, edgeColors);
        this.drawNodes(nodeStates, nodeColors);
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GraphVisualizer;
}
