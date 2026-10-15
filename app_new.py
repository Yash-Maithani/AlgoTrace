"""
Flask Application - Algorithm Visualizer
Clean, modular entry point for the application
"""
from flask import Flask, render_template, redirect, url_for
from flask_cors import CORS
from routes.sorting_routes import sorting_bp
from routes.graph_routes import graph_bp


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Enable CORS for API routes
    CORS(app, resources={
        r"/sorting/api/*": {"origins": "*"},
        r"/graph/api/*": {"origins": "*"}
    })
    
    # Register blueprints
    app.register_blueprint(sorting_bp)
    app.register_blueprint(graph_bp)
    
    # Main routes
    @app.route("/")
    def index():
        """Landing page"""
        return render_template("landing.html")
    
    @app.route("/sorting")
    def sorting_redirect():
        """Redirect to sorting blueprint"""
        return redirect(url_for('sorting.sorting_page'))
    
    @app.route("/graph")
    def graph_redirect():
        """Redirect to graph blueprint"""
        return redirect(url_for('graph.graph_page'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", 
                             error_code=404, 
                             error_message="Page not found"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template("error.html", 
                             error_code=500, 
                             error_message="Internal server error"), 500
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
