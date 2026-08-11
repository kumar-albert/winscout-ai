import sys

from src.agent import chat, run_agent

if __name__ == "__main__":
    if "--chat" in sys.argv:
        chat()
    else:
        print(run_agent())
