"""
Sorting Algorithm Routes
"""
from flask import Blueprint, render_template, request, jsonify
from services.algorithm_service import SortingService

sorting_bp = Blueprint('sorting', __name__, url_prefix='/sorting')
sorting_service = SortingService()


@sorting_bp.route('/', methods=['GET', 'POST'])
def sorting_page():
    """Main sorting page"""
    if request.method == 'POST':
        return handle_sorting_request()
    
    # GET request - display the form
    selected_algo = request.args.get('algorithm', 'Bubble Sort')
    available_algorithms = sorting_service.get_available_algorithms()
    
    if selected_algo not in available_algorithms:
        selected_algo = available_algorithms[0] if available_algorithms else "Bubble Sort"
    
    return render_template(
        "sorting.html",
        sorting_algorithms=available_algorithms,
        selected_algo=selected_algo,
        data=[],
        steps=[],
        input_method="random",
        manual_input="",
        size=30,
        error="",
        info=None
    )


@sorting_bp.route('/api/visualize', methods=['POST'])
def api_visualize():
    """API endpoint for sorting visualization"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        algorithm = data.get('algorithm')
        array_data = data.get('data')
        
        if not algorithm or not array_data:
            return jsonify({'error': 'Algorithm and data are required'}), 400
        
        result = sorting_service.visualize_algorithm(algorithm, array_data)
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@sorting_bp.route('/api/algorithms', methods=['GET'])
def api_get_algorithms():
    """Get available sorting algorithms"""
    try:
        algorithms = []
        for algo_name in sorting_service.get_available_algorithms():
            info = sorting_service.get_algorithm_info(algo_name)
            algorithms.append(info)
        
        return jsonify({'algorithms': algorithms})
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def handle_sorting_request():
    """Handle sorting form submission"""
    try:
        selected_algo = request.form.get("algorithm", "Bubble Sort")
        input_method = request.form.get("input_method", "random")
        size = 30
        manual_input = ""
        error = ""
        data = []
        
        # Generate or parse input data
        if input_method == "random":
            try:
                size = int(request.form.get("size", 30))
                data = sorting_service.generate_random_data(size)
            except ValueError as e:
                error = str(e)
        
        elif input_method == "manual":
            manual_input = request.form.get("manual_input", "")
            try:
                data = sorting_service.parse_manual_input(manual_input)
            except ValueError as e:
                error = str(e)
        
        # Execute algorithm if no errors
        result = None
        if not error and data:
            try:
                result = sorting_service.visualize_algorithm(selected_algo, data)
            except ValueError as e:
                error = str(e)
        
        # Prepare template data
        template_data = {
            "sorting_algorithms": sorting_service.get_available_algorithms(),
            "selected_algo": selected_algo,
            "data": data,
            "steps": result['steps'] if result else [],
            "input_method": input_method,
            "manual_input": manual_input,
            "size": size,
            "error": error,
            "info": {
                'swaps': result['stats']['swaps'] if result else 0,
                'comparisons': result['stats']['comparisons'] if result else 0,
                'stable': 'Yes' if result and result['stable'] else 'No',
                'time_complexity': result['time_complexity'] if result else {},
                'space_complexity': result['space_complexity'] if result else '',
                'description': result['description'] if result else ''
            } if result else None
        }
        
        return render_template("sorting.html", **template_data)
        
    except Exception as e:
        # Handle unexpected errors
        return render_template(
            "sorting.html",
            sorting_algorithms=sorting_service.get_available_algorithms(),
            selected_algo="Bubble Sort",
            data=[],
            steps=[],
            input_method="random",
            manual_input="",
            size=30,
            error=f"An unexpected error occurred: {str(e)}",
            info=None
        )
