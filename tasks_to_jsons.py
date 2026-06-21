#!/usr/bin/env python3
"""Export Microsoft TODO tasks (pffexport output) into human-readable JSON.

For now this is a skeleton: it walks the input directory, finds every task,
and prints the task names. It writes nothing yet.
"""

import sys
from pathlib import Path
from typing import Iterator, Optional

from tap import Tap


class Args(Tap):
    input_dir: Path   # pffexport output directory to read tasks from
    output_dir: Path  # destination directory for per-task JSON files (must not exist)

    def configure(self) -> None:
        self.add_argument('input_dir')
        self.add_argument('output_dir')


def iter_task_dirs(root: Path) -> Iterator[Path]:
    """Yield every task directory under root (a dir containing a Task.txt)."""
    for task_file in sorted(root.rglob('Task.txt')):
        yield task_file.parent


def read_subject(task_dir: Path) -> Optional[str]:
    """Return the Subject value from a task's Task.txt, or None if absent."""
    text = (task_dir / 'Task.txt').read_text(encoding='utf-8', errors='replace')
    for line in text.splitlines():
        if line.startswith('Subject:'):
            return line.split(':', 1)[1].strip()
    return None


def main() -> None:
    args = Args().parse_args()

    if not args.input_dir.is_dir():
        sys.exit(f'error: input dir does not exist or is not a directory: {args.input_dir}')

    if args.output_dir.exists():
        sys.exit(f'error: output dir already exists, refusing to overwrite: {args.output_dir}')

    for task_dir in iter_task_dirs(args.input_dir):
        subject = read_subject(task_dir)
        print(subject if subject is not None else f'<no subject> ({task_dir})')


if __name__ == '__main__':
    main()
