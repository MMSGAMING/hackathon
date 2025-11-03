import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_historical_data(days=30):
    data = []
    for day in range(days):
        date = datetime.now() - timedelta(days=days - day)
        is_weekend = date.weekday() >= 5
        for hour in range(24):
            if is_weekend:
                base_occ = 0.15
            elif hour < 8 or hour > 18:
                base_occ = 0.1
            elif 8 <= hour < 12:
                base_occ = 0.7
            elif 12 <= hour < 13:
                base_occ = 0.4
            else:
                base_occ = 0.65
            occupancy = base_occ + np.random.normal(0, 0.08)
            occupancy = max(0, min(1, occupancy))
            base_temp = 20 + 4 * np.sin(hour * np.pi / 12)
            temperature = base_temp + occupancy * 2 + np.random.normal(0, 0.5)
            humidity = 40 + 20 * np.sin(hour * np.pi / 12) + occupancy * 10 + np.random.normal(0, 2)
            humidity = max(20, min(80, humidity))
            data.append({'hour': hour, 'day_of_week': date.weekday(), 'temperature': round(temperature, 2), 'humidity': round(humidity, 2), 'occupancy': round(occupancy, 3)})
    return pd.DataFrame(data)

def save_training_data():
    df = generate_historical_data(days=60)
    df.to_csv('data/training_data.csv', index=False)
    print(f"✓ Generated {len(df)} training samples")
    return df

if __name__ == '__main__':
    save_training_data()
