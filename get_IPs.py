#!/Library/Frameworks/Python.framework/Versions/3.10/bin/python3
import requests
import glob
import time
from random import randint
from threading import Thread, Lock
from bs4 import BeautifulSoup as BS
from termcolor import colored

#functions
def progress(start_str, prog, total):
    if prog > total: return
    percent = 100 * float(prog/total) if prog <= total else 100
    color   = "yellow" if prog < total else "green"
    end     = "\r" if percent < 100 else "\n"
    bar     = colored("=" * int(percent), color) + " " * (100 - int(percent))
    print(f"\r{start_str:<33}|{bar}| {percent:.2f}%",end=end)

def get_last_page(session):
    total_ips = 0
    headers   = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0","Accept-Language": "en-US,en;q=0.5","Accept": "*/*"}
    next_page = True
    end = "\n"
    with session:
        while next_page:
            try:
                url         = f"https://hidemy.name/en/proxy-list/?start={total_ips}"
                res         = session.get(url, headers=headers, timeout=10)
                soup        = BS(res.text, "html.parser")
                li_next_arr = soup.find("li", {"class": "next_array"})

                if li_next_arr:
                    total_ips += 64
                    end = "\r"
                else:
                    next_page = False
                    end = "\n"
                    break
            
            except Exception as e:
                print(e)
                break
            finally:
                l = len("\rGetting last page")
                print("\rGetting last page" + " "*(34-l)+"|" + f"\tTotal Pages:\t{total_ips // 64}; Total Proxies:\t{total_ips}",end=end)
                # print(f"\n    Total Proxies:\t{total_ips}",end=end)

    # print(f"\r    Total Pages:\t{total_ips // 64}\t|\tTotal Proxies:\t{total_ips}",end=end)
    return total_ips

def get_IPs(response):
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

def _test_IPs(start_str,master_list, lock, num_lock):
    while True:
        try:
            # IP = { "ip":   ip, "port": port, "type": _type}
            with num_lock:
                global idx
                IP = master_list[idx]
                idx += 1
                if idx > len(master_list): return
            check_url = "http://httpbin.org/ip"
            types     = IP["type"].replace(" ", "").split(",")
            proxy     = f"{IP['ip']}:{IP['port']}"
            response  = requests.get(check_url, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=15)
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
                # progress(f"{start_str} (IPs:{len(master_list)})",prog,len(master_list))
                progress(f"{start_str} (IPs:{len(master_list)})",prog,len(master_list))

def create_IP_threads(start_str, master_list):
    my_threads = []
    lock       = Lock()
    num_lock   = Lock()
    for _ in range(randint(100,300)):
        ip_thread = Thread(target=_test_IPs, args=(start_str,master_list,lock,num_lock))
        my_threads.append(ip_thread)
    return my_threads

def test_IPs(master_list):
    # print("Testing Proxies...",flush=True)
    my_threads = create_IP_threads("Testing Proxies",master_list)
    global prog
    global idx
    prog,idx = 0,0

    for t in my_threads: t.start()
    for t in my_threads: t.join()

def test_old_IPs():
    # print("Testing old proxies...",flush=True)
    global prog
    global idx
    prog,idx = 0,0

    #get old proxies from files and put in master_list
    master_list = []
    for file_name in glob.glob("*.txt"):
        with open(file_name, "r") as f:
            for line in f.readlines():
                _type, ip, port = line.strip().split("\t")
                ip_dict = {"ip": ip, "port": port, "type": _type}
                master_list.append(ip_dict)
    
    my_threads = create_IP_threads("Testing Old Proxies",master_list)

    for t in my_threads: t.start()
    for t in my_threads: t.join()

def save_proxies(proxies_dict):
    print("Saving proxies",flush=True)
    for _type in proxies_dict.keys():
            with open(f"new_my_{_type}_proxy_servers.txt", "w") as f:
                # print(f"    Saving {_type}...",end="")
                for i,ip in enumerate(proxies_dict[_type]):
                    f.write(f"{ip}\n")
                    progress(f"    Saving {_type}",i+1,len(proxies_dict[_type]))
            # print(f"    Done with {_type}")

def main():
    try:
        with requests.Session() as session:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0","Accept-Language": "en-US,en;q=0.5","Accept": "*/*"}

            # print("Getting last page")
            last_page = get_last_page(session)
            # print(f"    Total Pages:\t{last_page // 64}")
            # print(f"    Total Proxies:\t{last_page}")
            ip_master_list = []

            #get IPs from site
            # print("Getting new proxies...",flush=True)
            for page in range(0,last_page+2,64):
                try:
                    url             = f"https://hidemy.name/en/proxy-list/?start={page}"
                    res             = session.get(url, headers=headers)
                    ip_master_list += get_IPs(res)
                    # page           += 64

                except Exception as e:
                    print(e)
                finally:
                    progress("Getting New Proxies",page,last_page+1)
            progress("Getting New Proxies",100,100)
            # print()


        #test IPs and add store working IPs
        test_IPs(ip_master_list)
        # print()

        #test old proxies
        test_old_IPs()
        # print()

        #saving successful proxies
        save_proxies(working_IPs)

        print("Program finished successfully")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    working_IPs = {}
    prog,idx = 0,0
    start = time.time()
    main()
    end   = time.time()
    print(f"(Finished in {round(end - start, 2)} seconds)")
