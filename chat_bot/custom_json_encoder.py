from decimal import Decimal
from datetime import datetime, date
from json import JSONEncoder
import numpy as np 



import numpy as np  # ✅ Add this import at the top

class CustomEncoder(JSONEncoder):
    def default(self, obj):
        # ✅ Handle numpy integer types
        if isinstance(obj, np.integer):
            return int(obj)
        # ✅ Handle numpy floating point types
        elif isinstance(obj, np.floating):
            return float(obj)
        # ✅ Handle numpy arrays
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        # ✅ Handle Decimal
        elif isinstance(obj, Decimal):
            return str(obj)
        # ✅ Handle datetime and date
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        # ✅ Handle lists
        elif isinstance(obj, list):
            return [self.default(item) for item in obj]
        # ✅ Handle tuples
        elif isinstance(obj, tuple):
            return tuple(self.default(item) for item in obj)
        # ✅ Handle dicts
        elif isinstance(obj, dict):
            return {key: self.default(value) for key, value in obj.items()}
        # Default fallback
        return super().default(obj)

# Last version of the custom encoder
# class CustomEncoder(JSONEncoder):
#     def default(self, obj):
#         # Check and convert Decimal objects
#         if isinstance(obj, Decimal):
#             return str(obj)  # Convert Decimal to string to avoid loss of precision
#         # Check and convert datetime objects
#         elif isinstance(obj, (datetime, date)):  # Handle both datetime and date objects
#             return obj.isoformat()
#         # Recursively apply conversion logic to iterable types
#         elif isinstance(obj, list):
#             return [self.default(item) for item in obj]
#         elif isinstance(obj, tuple):
#             return tuple(self.default(item) for item in obj)
#         elif isinstance(obj, dict):
#             return {key: self.default(value) for key, value in obj.items()}
#         # Fall back to the default method for other types
#         return JSONEncoder.default(self, obj)

def transform_data(data):
    encoder = CustomEncoder()
    
    # Extract headers and rows from the input
    headers, rows = data
    
    # Transform each row by applying the encoder where necessary
    transformed_rows = []
    for row in rows:
        # Encode each item in the row as necessary
        transformed_row = [encoder.default(item) if isinstance(item, Decimal) else item for item in row]
        transformed_rows.append(transformed_row)
    
    # Wrap both headers and rows in their own lists to match the desired format
    return [headers, [transformed_rows]]

# # Sample data
# data = (['player_id', 'non_penalty_goals'], [(66, Decimal('23'))])

# # Apply the transformation
# transformed_data = transform_data(data)

# print(transformed_data)