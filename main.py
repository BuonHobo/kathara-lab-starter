from pathlib import Path
import sys
from topology.wizard import configure_topology



if __name__ == "__main__":
    if len(sys.argv)!=3:
        print(f"Usage: {sys.argv[0]} <config directory> <target directory>")
        exit(1)

    config = Path(sys.argv[1])
    target = Path(sys.argv[2])

    configure_topology(config, target)

