#!/Library/Frameworks/Python.framework/Versions/3.10/bin/python3
import time
import glob
import os
import requests
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from fake_useragent import UserAgent
from threading import Lock
from bs4 import BeautifulSoup as BS
from termcolor import colored

#TODO: make this into a class

#functions
def progress(start_str:str, prog:int, total:int) -> None:
    """
    Displays status of task
    """
    percent = 100 * float(prog/total) if prog < total else 100
    color   = "yellow" if prog < total else "green"
    end     = "\r"

    #format percent to be 7 characters every time (important for formatting)
    percent_str = f"{float(percent):.2f}"
    percent_str = percent_str + "%" + (" " * (7 - len(percent_str) - 1))

    #start generating printable string -- includes start_str, percent_str, and the progress bar
    start_str += f" {prog}/{total}"
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

def get_all_ips(session:requests.Session) -> list:
    """
    Get last page index on proxy list site
    """
    total_ips = 0
    headers   = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0","Accept-Language": "en-US,en;q=0.5","Accept": "*/*"}
    next_page = True
    l_str= "\rGetting New Proxies"
    end = "\r"
    ip_master_list = []
    with session:
        while next_page:
            try:
                url             = f"https://hidemy.name/en/proxy-list/?start={total_ips}"
                res             = session.get(url, headers=headers, timeout=10)
                ip_master_list += get_ips_on_page(res)
                soup            = BS(res.text, "html.parser")
                li_next_arr     = soup.find("li", {"class": "next_array"})

                if li_next_arr:
                    total_ips += 64
                else:
                    next_page = False
                    break
            
            except Exception as e:
                print(e)
                break
            finally:
                print(f"{l_str} | Total Pages: {total_ips // 64}; Total Proxies: {total_ips}",end=end)

    return ip_master_list

def get_ips_on_page(response:requests.Response) -> list:
    """
    Gets IP addresses from the given response's HTML
    """
    ip_list = []
    soup = BS(response.text, "html.parser")

    ip_table = soup.find_all("tr")
    del ip_table[0]
    
    for row in ip_table:
        tds   = row.find_all("td")
        
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

async def _test_ips(start_str:str, ip_dict:dict, n:int, num_lock:Lock) -> list:
    check_url = "http://httpbin.org/ip"
    proxy = f"{ip_dict['ip']}:{ip_dict['port']}"
    types = ip_dict["type"].replace(" ", "").split(",")
    r_sesh_json_responses = []
    for _type in types:
        _type = _type.replace('s','') if _type == "https" else _type
        proxy_connector = ProxyConnector.from_url(f"{_type}://{proxy}")
        async with aiohttp.ClientSession(connector=proxy_connector, timeout=aiohttp.ClientTimeout(total=15)) as session:
            try:
                headers = {"User-Agent": UserAgent().random}
                r_sesh = await session.get(check_url, headers=headers)
                r_sesh_json = await r_sesh.json()
                r_sesh_json_responses.append(f"{_type}\t{r_sesh_json['origin']}\t{ip_dict['port']}")
            except Exception as e:
                r_sesh_json_responses.append(f"fail\t{str(e)}")
    with num_lock:
        global prog
        prog += 1
        progress(f"{start_str} (IPs:{n})", prog, n)

    return r_sesh_json_responses

async def test_ips(master_list:list) -> list:
    """
    Tests the IP addresses in the provided list
    """
    global prog
    prog = 0

    num_lock = Lock()
    tasks    = [asyncio.create_task(_test_ips("Testing Proxies", ip_dict, len(master_list), num_lock)) for ip_dict in master_list]
    ips      = await asyncio.gather(*tasks)

    clear_terminal(0)
    return ips

async def test_old_ips() -> list:
    """
    Tests the old IP addresses already saved
    """
    #get old proxies from files and put in master_list
    master_list = []
    for file_name in glob.glob("*proxy_servers.txt"):
        with open(file_name, "r", encoding="utf-8") as f:
            for line in f.readlines():
                _type, ip, port = line.strip().split("\t")
                ip_dict = {"ip": ip, "port": port, "type": _type}
                master_list.append(ip_dict)

    global prog
    prog = 0

    num_lock = Lock()
    tasks    = [asyncio.create_task(_test_ips("Testing Old Proxies", ip_dict, len(master_list), num_lock)) for ip_dict in master_list]
    ips      = await asyncio.gather(*tasks)

    #reset the proxy_server files
    for file_name in glob.glob("*proxy_servers.txt"):
        with open(file_name, "w", encoding="utf-8") as f:
            f.write("")

    clear_terminal(0)
    return ips

def remove_logs(file_names:list) -> None:
    for file_name in file_names:
        if glob.glob(file_name):
            os.remove(file_name)

def combine_ip_lists(old_ips:list | None, new_ips:list | None) -> list:
    all_ips = []
    if old_ips and new_ips:       all_ips = old_ips + new_ips
    elif old_ips and not new_ips: all_ips = old_ips
    elif new_ips and not old_ips: all_ips = new_ips

    return all_ips

def save_ips(all_ips:list) -> None:
    """
    Saves working proxies to files
    """
    print("Saving proxies",flush=True,end="\r")
    clear_terminal()
    for ip_list in all_ips:
        for ip in ip_list:
            _type = ip.split('\t')[0]
            if _type == "fail":
                with open(f"log.txt", "a") as f:
                    f.write(ip + '\n')
            else:
                with open(f"new_my_{_type}_proxy_servers.txt", "a") as f:
                    f.write(ip + '\n')
    clear_terminal(0)

async def main() -> None:
    """
    Driver code
    """
    try:
        #remove old log files
        remove_logs(["log.txt"])

        #test old IPs
        old_ips = await test_old_ips()

        #get new IPs and add them to a list
        ip_master_list = get_all_ips(requests.Session())

        #test new IPs
        new_ips = await test_ips(ip_master_list)

        #save ips
        save_ips(combine_ip_lists(old_ips,new_ips))

    except Exception as e:
        print(e)

if __name__ == "__main__":
    prog = 0
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"(Finished in {round(end_time - start_time, 2)} seconds)",end="\r")
    clear_terminal(5)
