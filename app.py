from flask import Flask, render_template, jsonify, request
import numpy as np
from datetime import datetime, timedelta
import os

from train_model import EnergyModel
from optimizer import EnergyOptimizer
from simulate import generate_historical_data

app = Flask(__name__, template_folder='templates', static_folder='static')

model = EnergyModel()
current_mode = 'normal'
optimization_enabled = True

@app.before_request
def initialize_model():
    global model
    if model.model is None:
        if not model.load('models/rf_model.pkl'):
            print("Training new model...")
            model.train()
            model.save('models/rf_model.pkl')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        'model_status': 'trained' if model.model else 'untrained',
        'model_accuracy': model.model_accuracy,
        'training_samples': model.training_samples,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    result = model.predict_occupancy(
        hour=data.get('hour', 10),
        day_of_week=data.get('day_of_week', 2),
        temperature=data.get('temperature', 22),
        humidity=data.get('humidity', 45)
    )
    optimization = EnergyOptimizer.optimize_schedule(result['occupancy'])
    return jsonify({**result, **optimization})

@app.route('/api/schedule/24h', methods=['GET'])
def schedule_24h():
    mode = request.args.get('mode', 'normal')
    predictions = []
    for hour in range(24):
        if mode == 'weekend':
            base_occ = 0.15 + (0.2 if 10 <= hour <= 18 else 0)
        elif mode == 'peak':
            base_occ = 0.6 if 8 <= hour <= 18 else 0.15
        else:
            if 8 <= hour < 12:
                base_occ = 0.7
            elif 12 <= hour < 13:
                base_occ = 0.4
            elif 13 <= hour < 18:
                base_occ = 0.65
            else:
                base_occ = 0.1
        noise = np.random.normal(0, 0.05)
        pred = max(0, min(1, base_occ + noise))
        predictions.append(pred)
    schedule = EnergyOptimizer.calculate_24h_schedule(predictions)
    return jsonify(schedule)

@app.route('/api/baseline/24h', methods=['GET'])
def baseline_24h():
    baseline = [{'hour': h, 'time_slot': f"{h:02d}:00 - {(h+1)%24:02d}:00", 'hvac_mode': 'FULL', 'hvac_power': 3.5, 'lights_mode': 'FULL', 'lights_power': 1.5, 'total_energy': 7.0, 'savings_percent': 0} for h in range(24)]
    return jsonify(baseline)

@app.route('/api/energy/comparison', methods=['GET'])
def energy_comparison():
    optimized = EnergyOptimizer.calculate_24h_schedule([0.1, 0.15, 0.2, 0.3, 0.65, 0.7, 0.75, 0.7, 0.6, 0.5, 0.4, 0.3, 0.35, 0.6, 0.65, 0.4, 0.25, 0.15, 0.12, 0.1, 0.08, 0.08, 0.09, 0.1])
    baseline = [{'hour': h, 'total_energy': 7.0} for h in range(24)]
    comparison = EnergyOptimizer.calculate_energy_savings(baseline, optimized)
    return jsonify({'baseline_24h': [7.0] * 24, 'optimized_24h': [s['total_energy'] for s in optimized], 'comparison': comparison})

@app.route('/api/features', methods=['GET'])
def feature_importance():
    return jsonify(model.get_feature_importance())

@app.route('/api/retrain', methods=['POST'])
def retrain():
    data = generate_historical_data(days=45)
    metrics = model.train(data)
    model.save('models/rf_model.pkl')
    return jsonify({'status': 'success', 'message': 'Model retrained', 'metrics': metrics})

@app.route('/api/rooms', methods=['GET'])
def rooms_status():
    rooms = [
        {'id': 1, 'name': 'Conference A', 'occupancy': 0.2, 'temperature': 21.5, 'hvac': 'ECO'},
        {'id': 2, 'name': 'Open Office', 'occupancy': 0.65, 'temperature': 22.0, 'hvac': 'FULL'},
        {'id': 3, 'name': 'Conference B', 'occupancy': 0.1, 'temperature': 20.5, 'hvac': 'OFF'},
        {'id': 4, 'name': 'Server Room', 'occupancy': 0.0, 'temperature': 18.0, 'hvac': 'ECO'},
        {'id': 5, 'name': 'Lobby', 'occupancy': 0.4, 'temperature': 22.5, 'hvac': 'FULL'},
        {'id': 6, 'name': 'Break Room', 'occupancy': 0.3, 'temperature': 21.0, 'hvac': 'ECO'},
    ]
    return jsonify(rooms)

@app.route('/api/metrics/daily', methods=['GET'])
def daily_metrics():
    return jsonify({'total_energy_kwh': 156.8, 'baseline_kwh': 168.0, 'energy_saved_kwh': 11.2, 'savings_percent': 6.7, 'co2_saved_kg': 5.6, 'cost_saved_rupees': 84.0, 'occupancy_avg': 0.38, 'temperature_avg': 21.8, 'optimized_energy': 5.8})

if __name__ == '__main__':
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    print("🚀 EcoSense Backend Starting...")
    print("📍 Visit http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
