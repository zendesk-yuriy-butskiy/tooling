import json
import sys


def parse_json_and_print_values(json_str, *keys):
    if not json_str.strip():  # Check if the input is empty or whitespace only
        return  # Ignore empty lines

    try:
        # Parse the JSON string into a dictionary
        data = json.loads(json_str)

        # Collect the values corresponding to each key in keys
        values = [str(data[key]) for key in keys if key in data]

        # Print the values separated by space
        print(' - '.join(values))

    except json.JSONDecodeError as e:
        # Silently ignore lines that are not valid JSON
        print(f"Warning, not a JSON string: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)


# Example usage:
if __name__ == "__main__":
    # Let's assume the remaining arguments are the keys
    # Example usage in a pipeline:
    # echo '{"level": "info", "message": "This is a log message", "timestamp": "2023-04-01T12:00:00Z"}' |\
    # python script.py message timestamp

    if len(sys.argv) < 2:
        print("Usage: echo '<json_string>' | python script.py <key1> <key2> ... <keyN>", file=sys.stderr)
        sys.exit(1)

    keys = sys.argv[1:]

    # Read JSON string from stdin
    for line in sys.stdin:
        parse_json_and_print_values(line, *keys)
