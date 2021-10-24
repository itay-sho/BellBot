import json


def load_secrets():
    with open('secrets.json') as f:
        secrets = json.loads(f.read())

    breakpoint()


def main():
    load_secrets()


if __name__ == '__main__':
    main()
