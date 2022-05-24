#!/Library/Frameworks/Python.framework/Versions/3.10/bin/python3
import time
import glob
import os
import requests
from random import randint
from threading import Thread, Lock
from typing import Dict
from bs4 import BeautifulSoup as BS
from termcolor import colored

#functions

def progress(start_str:str, prog:int, total:int) -> None:
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
        # end     = "\n" #might be causing issues
        end     = "\r" #might be causing issues

    #format percent to be 7 characters every time (important for formatting)
    percent_str = f"{float(percent):.2f}"
    percent_str = percent_str + "%" + (" " * (7 - len(percent_str) - 1))

    #start generating printable string -- includes start_str, percent_str, and the progress bar
    printable_str  = f"\r{start_str:<38} {percent_str} "
    printable_str += "|"

    #create progress bar string
    terminal_size  = os.get_terminal_size()
    width          = terminal_size.columns
    bar_limit      = width - len(printable_str) - 2  #'2' comes from the '|' chars
    prog_bar_limit = int(bar_limit * percent * .01)
    prog_bar       = colored("=" * prog_bar_limit, color) + (" " * (bar_limit - prog_bar_limit))
    printable_str += prog_bar

    #finish generating printable string
    printable_str += "|"

    print(printable_str,end=end,flush=True)

def clear_terminal(delay:float=0.5) -> None:
    """
    Clears text from the latest terminal line
    """
    width = os.get_terminal_size().columns
    time.sleep(delay)
    print(" " * width, end="\r")

def get_last_page(session:requests.Session) -> int:
    """
    Get last page index on proxy list site
    """
    total_ips = 0
    headers   = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0","Accept-Language": "en-US,en;q=0.5","Accept": "*/*"}
    next_page = True
    end = "\r"
    with session:
        while next_page:
            try:
                url         = f"https://hidemy.name/en/proxy-list/?start={total_ips}"
                res         = session.get(url, headers=headers, timeout=10)
                soup        = BS(res.text, "html.parser")
                li_next_arr = soup.find("li", {"class": "next_array"})

                if li_next_arr:
                    total_ips += 64
                    # end = "\r"
                else:
                    next_page = False
                    # end = "\n"
                    # end = "\r"
                    break
            
            except Exception as e:
                print(e)
                break
            finally:
                l = len("\rGetting last page")
                print("\rGetting last page" + " "*(37-l)+"|" + f"Total Pages: {total_ips // 64}; Total Proxies: {total_ips}",end=end)

    return total_ips

def get_ips(response:requests.Response) -> list:
    """
    Gets IP addresses from the given response's HTML
    """
    ip_list = []
    soup = BS(response.text, "html.parser")

    ip_table = soup.find_all("tr")
    del ip_table[0]
    
    for row in ip_table:
        tds     = row.find_all("td")
        
        ip    = tds[0].text.strip()
        port  = tds[1].text.strip()
        _type = tds[4].text.strip().lower()

        ip_dict = {
            "ip":   ip,
            "port": port,
            "type": _type
        }

        ip_list.append(ip_dict)

    return ip_list

def _test_ips(start_str:str, master_list:list, lock:Lock, num_lock:Lock) -> None:
    while True:
        try:
            # IP = { "ip": ip, "port": port, "type": _type}
            with num_lock:
                global idx
                IP = master_list[idx]
                idx += 1
                if idx >= len(master_list): return
            check_url = "http://httpbin.org/ip"
            proxy     = f"{IP['ip']}:{IP['port']}"
            # response  = requests.get(check_url, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=15)
            requests.get(check_url, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=15)
            types     = IP["type"].replace(" ", "").split(",")

            global working_IPs
            with lock:
                for t in types:
                    if t not in working_IPs:
                        working_IPs[t] = []
                    working_IPs[t].append(f"{t}\t{IP['ip']}\t{IP['port']}")
            # print(f"    {IP['ip']:>15} => {response.json()}", flush=True)
        except:
            if idx >= len(master_list): return
        finally:
            with num_lock:
                global prog
                prog += 1
                # progress(f"numIPs:{len(master_list)}",prog, len(master_list))
                progress(f"{start_str} (IPs:{len(master_list)})",prog,len(master_list))

def create_ip_threads(start_str:str, master_list:list) -> list:
    """
    Create threads to test all the IP addresses
    """
    my_threads = []
    lock       = Lock()
    num_lock   = Lock()
    for _ in range(randint(100,300)):
        ip_thread = Thread(target=_test_ips, args=(start_str,master_list,lock,num_lock))
        my_threads.append(ip_thread)
    return my_threads

def test_ips(master_list:list) -> None:
    """
    Tests the IP addresses in the provided list
    """
    my_threads = create_ip_threads("Testing Proxies",master_list)
    global prog
    global idx
    prog,idx = 0,0

    for t in my_threads: t.start()
    for t in my_threads: t.join()

def test_old_ips() -> None:
    """
    Tests the old IP addresses already saved
    """
    global prog
    global idx
    prog,idx = 0,0

    #get old proxies from files and put in master_list
    master_list = []
    for file_name in glob.glob("*proxy_servers.txt"):
        with open(file_name, "r", encoding="utf-8") as f:
            for line in f.readlines():
                _type, ip, port = line.strip().split("\t")
                ip_dict = {"ip": ip, "port": port, "type": _type}
                master_list.append(ip_dict)
    
    my_threads = create_ip_threads("Testing Old Proxies",master_list)

    for t in my_threads: t.start()
    for t in my_threads: t.join()

def save_proxies(proxies_dict:dict) -> None:
    """
    Saves working proxies to files
    """
    print("Saving proxies",flush=True,end="\r")
    clear_terminal()
    for _type in proxies_dict.keys():
            with open(f"new_my_{_type}_proxy_servers.txt", "w", encoding="utf-8") as f:
                for i,ip in enumerate(proxies_dict[_type]):
                    f.write(f"{ip}\n")
                    progress(f"Saving {_type}",i+1,len(proxies_dict[_type]))
            clear_terminal(0.5)

def main() -> None:
    """
    Driver code
    """
    try:
        with requests.Session() as session:
            headers = {"User-Agent": """Mozilla/5.0 (X11;Ubuntu; Linux x86_64; rv:84.0)\
                        Gecko/20100101 Firefox/84.0""",
                       "Accept-Language": "en-US,en;q=0.5",
                       "Accept": "*/*"}

            last_page = get_last_page(session)
            ip_master_list = []

            #get IPs from site
            for page in range(0,last_page+2,64):
                try:
                    url             = f"https://hidemy.name/en/proxy-list/?start={page}"
                    res             = session.get(url, headers=headers)
                    ip_master_list += get_ips(res)

                except Exception as e:
                    print(e)
                finally:
                    progress("Getting New Proxies",page+1,last_page+1)
            # progress("Getting New Proxies",100,100)

        #test IPs and add store working IPs
        test_ips(ip_master_list)

        #test old proxies
        test_old_ips()

        #saving successful proxies
        save_proxies(working_IPs)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    working_IPs:Dict[str,list] = {}
    prog,idx   = 0,0
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"(Finished in {round(end_time - start_time, 2)} seconds)",end="\r")
    clear_terminal(5)
