import json

def initialize_database(filename="state.json"):
    initial_data = {
        "chunks": [],
        "chapters": []
    }
    save_state_to_json(initial_data, filename)

def save_state_to_json(data, filename="state.json"):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)


def load_state_from_json(filename="state.json"):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        # Initialize the database if the file doesn't exist
        initialize_database(filename)
        return {
            "chunks": [],
            "chapters": []
        }


# On application startup
saved_state = load_state_from_json()
if saved_state:
    # Continue processing or handle as needed

