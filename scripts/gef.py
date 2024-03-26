#!/usr/bin/env python3

import os
import sys
import time
import fcntl
import select
import threading
import queue
import tty, termios

input_queue = queue.Queue()

def clear_screen():
    print("\033c", end="")

def move_cursor_up(n=1):
    """ move up n lines on cursor """
    print(f"\033[{n}A", end="", flush=True)

def move_cursor_down(n=1):
    """ move down n lines on cursor """
    print(f"\033[{n}B", end="", flush=True)

def move_cursor_right(n=1):
    """ move right n lines on cursor """
    print(f"\033[{n}C", end="")

def save_cursor_position():
    print("\033[s", end='', flush=True)

def restore_cursor_position():
    print("\033[u", end='', flush=True)

def rewrite_line(new_text):
    """rewrite this line"""
    print(f"\r\033[K{new_text}", end="")

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def input_listener(input_queue):
    """Press 'q' to exit"""
    move_cursor_down(9)
    print("Press 'q' to exit: ", end='')
    save_cursor_position()
    move_cursor_up(10)
    while True:
        ch = getch()
        input_queue.put(ch)
        if ch.lower() == 'q':
            break
        time.sleep(0.5)

def client(file_name):
    current_data = [""] * 20

    mmap_fd = os.open(file_name, os.O_RDONLY | os.O_NONBLOCK)
    try:
        print("\n" * (len(current_data) - 1))
        while True:
            try:
                os.lseek(mmap_fd, 0, os.SEEK_SET)
                data = os.read(mmap_fd, 2048).decode('utf-8')
            except BlockingIOError:
                # if no any data, just wait
                time.sleep(1)
                continue

            if not data:
                break

            updates = data.strip().split("\n")
            move_cursor_up(len(current_data))

            for i, line in enumerate(updates):
                os.lseek(mmap_fd, i * 192, os.SEEK_SET)
                if line != current_data[i]:
                    current_data[i] = line
                    rewrite_line(line)  # only update changed line
                else:
                    rewrite_line(current_data[i])

                if i < len(updates) - 1:
                    print()

            restore_cursor_position()
            if not input_queue.empty():
                ch = input_queue.get()
                if ch is not None and ch.lower() == 'q':
                    break
            time.sleep(0.5)
    finally:
        os.close(mmap_fd)

def view_regs():
    mmap_file = os.path.expanduser('~/.gef/shared_view')
    while not os.path.exists(mmap_file):
        time.sleep(1)
    client(mmap_file)

def view_backtrace():
    print("todo")

def main():
    if len(sys.argv) != 3:
        print("Usage: gef view <regs|bt|backtrace>")
        return

    input_thread = threading.Thread(target=input_listener, args=(input_queue,))
    input_thread.start()

    command, subcommand = sys.argv[1:3]
    if command == "view":
        if subcommand == "regs":
            view_regs()
        elif subcommand in ("bt", "backtrace"):
            view_backtrace()
        else:
            print("Unknown view subcommand.")
            print("Usage: gef view <regs|bt|backtrace>")
    else:
        print("Unknown command.")
        print("Usage: gef view <regs|bt|backtrace>")
    # wait child exit
    input_thread.join()
    return

if __name__ == "__main__":
    clear_screen()
    main()
