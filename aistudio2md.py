#!/usr/bin/env python3
"""
Export chat responses from Google AI Studio JSON export.

Usage:
    python export_chat.py --input exported.json --output ./chat-responses
    python export_chat.py --input exported.json --mode single --output chat.md
    python export_chat.py --input exported.json --separate --with-thinking
    python export_chat.py --input exported.json --separate --include-user
"""

import json
import os
import argparse
from pathlib import Path


def load_chunks(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('chunkedPrompt', {}).get('chunks', [])


def group_turns(chunks):
    turns = []
    current_turn = None

    for c in chunks:
        role = c.get('role')
        text = c.get('text', '')
        is_thought = c.get('isThought', False)

        if role == 'user':
            if current_turn is not None:
                turns.append(current_turn)
            current_turn = {'user': text, 'model': [], 'model_thought': []}
        elif role == 'model':
            if current_turn is None:
                current_turn = {'user': '', 'model': [], 'model_thought': []}
            if is_thought:
                current_turn['model_thought'].append(text)
            else:
                current_turn['model'].append(text)

    if current_turn is not None:
        turns.append(current_turn)

    return turns


def format_turn(turn, include_user=False, include_thinking=False):
    parts = []

    if include_user and turn['user']:
        parts.append(f"**User:**\n{turn['user']}\n")

    if include_thinking and turn['model_thought']:
        thought_text = '\n'.join(turn['model_thought'])
        parts.append(f"**Thinking:**\n{thought_text}\n")

    if turn['model']:
        model_text = ''.join(turn['model'])
        parts.append(f"**Model:**\n{model_text}")

    return '\n'.join(parts)


def export_single_file(turns, output_path, include_user=False, include_thinking=False):
    sections = []
    for i, turn in enumerate(turns, 1):
        sections.append(f"## Turn {i}\n\n{format_turn(turn, include_user, include_thinking)}")
    content = '\n\n---\n\n'.join(sections)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved single file: {output_path} ({len(content)} chars)")


def export_separate_files(turns, output_dir, include_user=False, include_thinking=False):
    os.makedirs(output_dir, exist_ok=True)
    for i, turn in enumerate(turns, 1):
        content = format_turn(turn, include_user, include_thinking)
        filepath = os.path.join(output_dir, f"response-{i:03d}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved {filepath} ({len(content)} chars)")


def main():
    parser = argparse.ArgumentParser(description='Export chat responses from Google AI Studio JSON')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file path')
    parser.add_argument('--output', '-o', required=True, help='Output file or directory path')
    parser.add_argument('--mode', '-m', choices=['single', 'separate'], default='separate',
                        help='Export mode: single file or separate files')
    parser.add_argument('--include-user', '-u', action='store_true',
                        help='Include user prompts in output')
    parser.add_argument('--include-thinking', '-t', action='store_true',
                        help='Include thinking sections in output')
    args = parser.parse_args()

    chunks = load_chunks(args.input)
    turns = group_turns(chunks)

    print(f"Found {len(turns)} turns")

    if args.mode == 'single':
        export_single_file(turns, args.output, args.include_user, args.include_thinking)
    else:
        export_separate_files(turns, args.output, args.include_user, args.include_thinking)

    print("Done")


if __name__ == '__main__':
    main()
