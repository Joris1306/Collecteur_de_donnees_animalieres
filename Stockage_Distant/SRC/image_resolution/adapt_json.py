import os
import json
import sys


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <input_json>")
        sys.exit(1)

    try:
        input_json = sys.argv[1]

        # cle1 = 'predictions'
        with open(input_json, "r") as f:
            data = json.load(f)

        # print(data)
        # print(type(data))
        for i,(cle,val) in enumerate(data.items()):
            if i != 0 or cle != 'predictions':
                raise Exception("Error")
            
            for item in val:
                # print(item)
                # print(type(item))
                for key, value in item.items():
                    if key != 'filepath':
                        continue
                    value = value.split('/')[1]
                    print(f"item[{key}] = {value}")
                    item[key] = value

        print(data)
        with open(f"adapted_{input_json}", "w") as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
