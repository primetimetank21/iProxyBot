import requests
import glob
from threading import Thread, Lock
from bs4 import BeautifulSoup as BS
import time

#functions
def get_last_page(session):
    total_ips = 0
    headers   = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0","Accept-Language": "en-US,en;q=0.5","Accept": "*/*"}
    next_page = True
    with session:
        while next_page:
            try:
                url         = f"https://hidemy.name/en/proxy-list/?start={total_ips}"
                res         = session.get(url, headers=headers, timeout=10)
                soup        = BS(res.text, "html.parser")
                li_next_arr = soup.find("li", {"class": "next_array"})

                if li_next_arr:
                    total_ips += 64
                else:
                    next_page = False
                    break
            
            except Exception as e:
                print(e)
                break

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

def _test_IPs(IP, lock):
    try:
        # IP = { "ip":   ip, "port": port, "type": _type}

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
        print(f"    {IP['ip']:>15} => {response.json()}", flush=True)
    except:
        pass

def test_IPs(master_list):
    print("Testing Proxies...")
    my_threads = []
    lock = Lock()
    for ip in master_list:
        ip_thread        = Thread(target=_test_IPs, args=(ip,lock))
        my_threads.append(ip_thread)
    return my_threads

def test_old_IPs():
    print("Testing old proxies...")
    master_list = []

    #get old proxies from files and put in master_list
    for file_name in glob.glob("*.txt"):
        with open(file_name, "r") as f:
            for line in f.readlines():
                _type, ip, port = line.strip().split("\t")
                ip_dict = {"ip": ip, "port": port, "type": _type}
                master_list.append(ip_dict)
    
    threads = test_IPs(master_list)
    for t in threads:
        t.start()
    for t in threads:
        t.join()

def save_proxies(proxies_dict):
    print("Saving proxies...")
    for _type in proxies_dict.keys():
            with open(f"new_my_{_type}_proxy_servers.txt", "w") as f:
                for ip in proxies_dict[_type]:
                    f.write(f"{ip}\n")
            print(f"    Done with {_type}")

def main():
    try:
        with requests.Session() as session:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0","Accept-Language": "en-US,en;q=0.5","Accept": "*/*"}

            print("Getting last page...")
            last_page = get_last_page(session)
            print(f"    Total Pages:\t{last_page // 64}")
            print(f"    Total Proxies:\t{last_page}")
            ip_master_list = []

            #get IPs from site
            print("Getting new proxies...")
            for page in range(0,last_page+1,64):
                try:
                    url             = f"https://hidemy.name/en/proxy-list/?start={page}"
                    res             = session.get(url, headers=headers)
                    ip_master_list += get_IPs(res)
                    page           += 64

                except Exception as e:
                    print(e)

        #test IPs and add store working IPs
        threads = test_IPs(ip_master_list)
        for t in threads: t.start()
        for t in threads: t.join()

        #test old proxies
        test_old_IPs()

        #saving successful proxies
        save_proxies(working_IPs)

        print("Program finished successfully")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    working_IPs = {}
    start = time.time()
    main()
    end   = time.time()
    print(f"(Finished in {round(end - start, 2)} seconds)")
