class EnergyOptimizer:
    HVAC_FULL = 3.5
    HVAC_ECO = 1.2
    HVAC_OFF = 0.1
    LIGHTS_FULL = 1.5
    LIGHTS_DIM = 0.4
    LIGHTS_OFF = 0.05
    SERVER_BASE = 2.0
    
    @staticmethod
    def optimize_schedule(predicted_occupancy):
        if predicted_occupancy < 0.15:
            hvac_mode = "OFF"
            hvac_power = EnergyOptimizer.HVAC_OFF
            lights_mode = "OFF"
            lights_power = EnergyOptimizer.LIGHTS_OFF
            savings_percent = 30
        elif predicted_occupancy < 0.40:
            hvac_mode = "ECO"
            hvac_power = EnergyOptimizer.HVAC_ECO
            lights_mode = "DIM"
            lights_power = EnergyOptimizer.LIGHTS_DIM
            savings_percent = 15
        else:
            hvac_mode = "FULL"
            hvac_power = EnergyOptimizer.HVAC_FULL
            lights_mode = "FULL"
            lights_power = EnergyOptimizer.LIGHTS_FULL
            savings_percent = 0
        
        total_energy = hvac_power + lights_power + EnergyOptimizer.SERVER_BASE
        return {'hvac_mode': hvac_mode, 'hvac_power': round(hvac_power, 2), 'lights_mode': lights_mode, 'lights_power': round(lights_power, 2), 'total_energy': round(total_energy, 2), 'savings_percent': savings_percent}
    
    @staticmethod
    def calculate_24h_schedule(predictions):
        schedule = []
        for hour, occupancy_pred in enumerate(predictions):
            optimization = EnergyOptimizer.optimize_schedule(occupancy_pred)
            schedule.append({'hour': hour, 'time_slot': f"{hour:02d}:00 - {(hour+1)%24:02d}:00", 'predicted_occupancy': round(occupancy_pred, 2), **optimization})
        return schedule
    
    @staticmethod
    def calculate_energy_savings(schedule_baseline, schedule_optimized):
        baseline_total = sum(s['total_energy'] for s in schedule_baseline)
        optimized_total = sum(s['total_energy'] for s in schedule_optimized)
        savings_kwh = baseline_total - optimized_total
        savings_percent = (savings_kwh / baseline_total * 100) if baseline_total > 0 else 0
        co2_per_kwh = 0.5
        co2_saved = savings_kwh * co2_per_kwh
        cost_per_kwh = 7.5
        cost_saved = savings_kwh * cost_per_kwh
        return {'baseline_energy': round(baseline_total, 2), 'optimized_energy': round(optimized_total, 2), 'energy_saved_kwh': round(savings_kwh, 2), 'savings_percent': round(savings_percent, 1), 'co2_saved_kg': round(co2_saved, 2), 'cost_saved_rupees': round(cost_saved, 2)}
