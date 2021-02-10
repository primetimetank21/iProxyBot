import requests, grequests
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

def test_IPs(master_list):
    print("Testing Proxies...")
    check_url   = "http://httpbin.org/ip"
    working_IPs = {}

    for index, ip in enumerate(master_list):
        try:
            # ip = {
            #         "ip":   ip,
            #         "port": port,
            #         "type": _type
            #     }
            print(f"    Request {index+1}")

            types    = ip["type"].replace(" ", "").split(",")
            proxy    = f"{ip['ip']}:{ip['port']}"
            response = requests.get(check_url, proxies={"http":proxy, "https":proxy}, timeout=10)
            types    = ip["type"].replace(" ", "").split(",")

            for t in types:
                if t not in working_IPs:
                    working_IPs[t] = []
                working_IPs[t].append(f"{t} {ip['ip']} {ip['port']}")
            print(f"        {response.status_code} => {response.json()}")

        except:
            # print(e)
            try:
                print(f"        {response.status_code} => Not available")
            except:
                print(f"         Not available")
    
    return working_IPs


with requests.Session() as session:
    headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0",
               "Accept-Language": "en-US,en;q=0.5",
               "Accept": "*/*"
    }

    print("Getting last page...")
    last_page      = get_last_page(session)
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

#test IPs
#incorporate threading at this part -- definitely will speed up the process
working_IPs = test_IPs(ip_master_list)

#save successful IPs
print("Saving proxies...")
for _type in working_IPs.keys():
    with open(f"new_my_{_type}_proxy_servers.txt","a") as f:
        for ip in working_IPs[_type]:
            f.write(f"{ip}\n")

print("Done")
