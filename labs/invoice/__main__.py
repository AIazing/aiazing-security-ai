"""Start both fixtures locally; reset and stop from the controller terminal."""

import argparse
import json

from .control import InvoiceLab


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vulnerable-port", type=int, default=8765)
    parser.add_argument("--fixed-port", type=int, default=8766)
    args = parser.parse_args()
    if any(not 0 <= port <= 65535 for port in (args.vulnerable_port, args.fixed_port)):
        parser.error("Ports must be between 0 and 65535; 0 selects an available port.")
    try:
        with InvoiceLab(args.vulnerable_port, args.fixed_port) as lab:
            print(json.dumps(lab.urls, indent=2), flush=True)
            print("Local synthetic lab. Commands: reset, quit. Ctrl-C also stops.", flush=True)
            while True:
                try:
                    command = input("> ").strip().lower()
                except EOFError:
                    break
                if command in ("quit", "exit"):
                    break
                if command == "reset":
                    lab.reset()
                    print("Seed restored; all sessions invalidated.", flush=True)
                elif command:
                    print("Commands: reset, quit", flush=True)
    except KeyboardInterrupt:
        pass
    except OSError as error:
        parser.exit(1, "Could not start the local lab: {}\n".format(error))


if __name__ == "__main__":
    main()
