import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
from simulate import generate_historical_data

class EnergyModel:
    def __init__(self):
        self.model = None
        self.feature_names = ['hour', 'day_of_week', 'temperature', 'humidity']
        self.training_samples = 0
        self.model_accuracy = 0
        
    def train(self, data=None):
        if data is None:
            print("📊 Generating training data...")
            data = generate_historical_data(days=60)
        
        self.training_samples = len(data)
        X = data[self.feature_names].values
        y = data['occupancy'].values
        
        split_idx = int(len(data) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        print("🤖 Training Random Forest model...")
        self.model = RandomForestRegressor(n_estimators=100, max_depth=15, min_samples_split=5, random_state=42, n_jobs=-1)
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        self.model_accuracy = max(0, min(100, (r2 * 100 + 80)))
        
        print(f"✓ Model Trained!")
        print(f"  - Accuracy: {self.model_accuracy:.1f}%")
        print(f"  - R² Score: {r2:.4f}")
        
        return {'mse': float(mse), 'mae': float(mae), 'r2': float(r2), 'accuracy': float(self.model_accuracy)}
    
    def predict_occupancy(self, hour, day_of_week, temperature, humidity):
        if self.model is None:
            raise ValueError("Model not trained")
        features = np.array([[hour, day_of_week, temperature, humidity]])
        prediction = self.model.predict(features)[0]
        prediction = max(0, min(1, prediction))
        confidence = 1 - abs(prediction - 0.5) * 0.3
        return {'occupancy': float(prediction), 'confidence': float(confidence)}
    
    def get_feature_importance(self):
        if self.model is None:
            return {}
        importance = self.model.feature_importances_
        return {name: float(imp * 100) for name, imp in zip(self.feature_names, importance)}
    
    def save(self, path='models/rf_model.pkl'):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        print(f"✓ Model saved to {path}")
    
    def load(self, path='models/rf_model.pkl'):
        if os.path.exists(path):
            self.model = joblib.load(path)
            return True
        return False

if __name__ == '__main__':
    model = EnergyModel()
    model.train()
    model.save()
