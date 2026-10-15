// Common utilities for graph and sorting visualizations

// Utility functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Debounce function for resize events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Color schemes for different algorithm states
const COLORS = {
    // Sorting colors
    SORTING: {
        DEFAULT: '#e3f2fd',
        COMPARING: '#ff9800',
        SWAPPING: '#f44336',
        SORTED: '#4caf50',
        PIVOT: '#9c27b0',
        MINIMUM: '#e91e63'
    },
    
    // Graph colors  
    GRAPH: {
        UNVISITED: '#f44336',     // Red
        QUEUED: '#2196f3',        // Blue  
        PROCESSING: '#ff9800',    // Orange
        VISITED: '#4caf50',       // Green
        MST: '#ff6d00',          // Deep Orange
        CURRENT: '#e91e63',      // Pink
        PATH: '#795548'          // Brown
    },
    
    // Edge colors
    EDGE: {
        DEFAULT: '#888',
        HIGHLIGHTED: '#ff6d00',
        MST: '#ff6d00',
        PATH: '#e53935'
    }
};

// Animation configurations
const ANIMATION = {
    FAST: 200,
    NORMAL: 500,
    SLOW: 1000,
    EASING: {
        EASE_OUT: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        EASE_IN_OUT: 'cubic-bezier(0.42, 0, 0.58, 1)',
        BOUNCE: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { sleep, debounce, COLORS, ANIMATION };
}
