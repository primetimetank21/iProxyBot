import requests, threading
from bs4 import BeautifulSoup as BS

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

def _test_IPs(IP):
    try:
        # IP = { "ip":   ip, "port": port, "type": _type}

        check_url = "http://httpbin.org/ip"
        types     = IP["type"].replace(" ", "").split(",")
        proxy     = f"{IP['ip']}:{IP['port']}"
        response  = requests.get(check_url, proxies={"http": proxy, "https": proxy}, timeout=10)
        types     = IP["type"].replace(" ", "").split(",")

        global working_IPs

        for t in types:
            if t not in working_IPs:
                working_IPs[t] = []
            working_IPs[t].append(f"{t}\t{IP['ip']}\t{IP['port']}")
        print(f"    {IP['ip']:>15} => {response.json()}")

    except:
        pass

def test_IPs(master_list):
    print("Testing Proxies...")
    my_threads = []
    for ip in master_list:
        ip_thread = threading.Thread(target=_test_IPs, args=(ip,))
        my_threads.append(ip_thread)
    return my_threads


with requests.Session() as session:
    headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0","Accept-Language": "en-US,en;q=0.5","Accept": "*/*"}

    print("Getting last page...")
    last_page = get_last_page(session)
    print(f"    Total Pages:\t{last_page // 64}")
    print(f"    Total Proxies:\t{last_page}")
    ip_master_list = []

    #get IPs from site
    print("Getting Proxies...")
    for page in range(0,last_page+1,64):
        try:
            url             = f"https://hidemy.name/en/proxy-list/?start={page}"
            res             = session.get(url, headers=headers)
            ip_master_list += get_IPs(res)
            page           += 64

        except Exception as e:
            print(e)

#test IPs and add store working IPs
working_IPs = {}
threads = test_IPs(ip_master_list)

for t in threads:
    t.start()
for t in threads:
    t.join()

#save successful IPs

#TODO
#add function to test if old proxies work; delete them if they don't
print("Saving proxies...")
for _type in working_IPs.keys():
    compare_list = []
    with open(f"new_my_{_type}_proxy_servers.txt", "r") as f:
        for line in f.readlines():
            line = line.strip().replace(" ", "\t")
            compare_list.append(line)

    print(f"    Working on {_type}...")
    compare_list = list(set(compare_list))

    for ip in working_IPs[_type]:
        if ip not in compare_list:
            compare_list.append(ip)

    with open(f"new_my_{_type}_proxy_servers.txt", "w") as f:
        for ip in compare_list:
            f.write(f"{ip}\n")
    print(f"    Done with {_type}")

print("Program finished successfully")