#!/usr/bin/env python3
import sys

def format_evidence(log_paths):
    print("# Evidence Summary\n")
    for path in log_paths:
        print(f"## File: {path}")
        try:
            with open(path, "r") as f:
                content = f.read()
                print("```text\n" + content[:500] + ("..." if len(content)>500 else "") + "\n```\n")
        except Exception as e:
            print(f"Error reading {path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 format_evidence.py <log_file1> <log_file2> ...")
        sys.exit(1)
    format_evidence(sys.argv[1:])
