import requests
import xml.etree.ElementTree as ET
import time


class SecForm():
    base_url = "https://www.sec.gov/cgi-bin/browse-edgar?"

    def __init__(self, user_agent="SecForm/0.1"):
        self.headers = {'User-Agent': user_agent}
        pass
    
    def test_function(self):
        res = requests.get("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=100&output=atom", headers=self.headers)
        return res



if __name__ == "__main__":
    time_start = time.time()
    sec_wrapper = SecForm()
    res = sec_wrapper.test_function()
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(res.content)
    entries = root.findall('.//atom:entry', namespaces=namespace)

    for entry in entries:
        title = entry.find('atom:title', namespaces=namespace).text
        link = entry.find(".//atom:link[@rel='alternate']", namespaces=namespace).get('href')
        summary = entry.find('atom:summary', namespaces=namespace).text
        updated = entry.find('atom:updated', namespaces=namespace).text

        print("Title:", title)
        print("Link:", link)
        print("Summary:", summary)
        print("Updated:", updated)
        print("\n")
    
    time_end = time.time()
    print(f"Time elapsed: {time_end - time_start}\nEntries scrapped {len(entries)}", )