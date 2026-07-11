        # Optional physical measurements
        def safe_float(value):
            """Safely convert to float if present"""
            return float(value) if value is not None else None

        mass = safe_float(raw_data.get('mass'))
        mass_err = safe_float(raw_data.get('mass_uncertainty'))
        temperature = safe_float(raw_data.get('temperature'))
        temp_err = safe_float(raw_data.get('temperature_uncertainty'))
        column_density = safe_float(raw_data.get('column_density'))
        col_err = safe_float(raw_data.get('column_density_uncertainty'))

        # Filament properties
        filament_width = safe_float(raw_data.get('filament_width'))
        width_err = safe_float(raw_data.get('filament_width_uncertainty'))
        filament_length = safe_float(raw_data.get('filament_length'))
        length_err = safe_float(raw_data.get('filament_length_uncertainty'))