#!/usr/bin/env python3
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.app_controller import AppController

def main():
    controller = AppController()
    sys.exit(controller.run())

if __name__ == "__main__":
    main()
