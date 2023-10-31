import requests

user_agent = "SecForm/0.1"
headers = {'User-Agent': user_agent}

class SecForm():
    def __init__():
        pass


if __name__ == "__main__":
    res = requests.get("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=320&count=1000&output=atom", headers=headers)
    #parse XML response
    print(res.text)

