import os
import time
from termcolor import colored

def progress(start_str, prog, total):
    """
    Displays status of task
    """
    if prog < total:
        percent = 100 * float(prog/total)
        color   = "yellow"
        end     = "\r"
    else:
        percent = 100
        color   = "green"
        end     = "\n"

    #format percent to be 7 characters every time (important for formatting)
    percent_str = f"{float(percent):.2f}"
    percent_str = percent_str + "%" + (" " * (7 - len(percent_str) - 1))

    #start generating printable string -- includes start_str, percent_str, and the progress bar
    printable_str  = f"\r{start_str:<33} {percent_str} "
    printable_str += "|"

    #create progress bar string
    bar_limit      = WIDTH - len(printable_str) - 2  #'2' comes from the '|' chars
    prog_bar_limit = int(bar_limit * percent * .01)
    prog_bar       = colored("=" * prog_bar_limit, color) + (" " * (bar_limit - prog_bar_limit))
    printable_str += prog_bar

    #finish generating printable string
    printable_str += "|"

    print(printable_str,end=end,flush=True)

# def old_progress(start_str, prog, total):
#     if prog > total: return
#     percent = 100 * float(prog/total) if prog <= total else 100
#     color   = "yellow" if prog < total else "green"
#     end     = "\r" if percent < 100 else "\n"
#     bar     = colored("=" * int(percent), color) + " " * (100 - int(percent))
#     print(f"\r{start_str:<33}|{bar}| {percent:.2f}%",end=end)

if __name__ == "__main__":
    term_size = os.get_terminal_size()
    WIDTH     = term_size.columns
    arr       = list(range(0,10000))
    progress("Nums", 0, len(arr))
    for i,num in enumerate(arr):
        sq = num**2
        arr[i] = sq
        progress("Nums", i+1, len(arr))
        time.sleep(0.0005)
    print("Done")