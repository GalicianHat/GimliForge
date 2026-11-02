"""Start the browser app by default; keep the command-line report mode."""
import sys
from src.gimliforge import main as cli_main
from src.webapp import main as web_main

if __name__ == "__main__":
    if any(option in sys.argv[1:] for option in ("-f", "--file", "--check", "--pdf", "-o", "--output")):
        raise SystemExit(cli_main())
    web_main()
