import json
import numpy as np

# Define a custom encoder class that can handle NumPy arrays and other data types
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.complex):
            return {"real": obj.real, "imag": obj.imag}
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.void):
            return obj.tolist()
        elif isinstance(obj, np.datetime64):
            return str(obj)
        elif isinstance(obj, np.timedelta64):
            return str(obj)
        return json.JSONEncoder.default(self, obj)