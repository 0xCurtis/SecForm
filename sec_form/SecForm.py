import requests
import xml.etree.ElementTree as ET
import time

class SecForm():
    base_url = "https://www.sec.gov/cgi-bin/browse-edgar?"

    def __init__(self, user_agent="SecForm/0.1"):
        self.headers = {'User-Agent': user_agent}
        self.namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        pass

    def scrape_transaction(self, transaction):
        transactionAmounts = transaction.find('transactionAmounts', namespaces=self.namespace)
        transactionShares = transactionAmounts.find('transactionShares', namespaces=self.namespace).find('value', namespaces=self.namespace).text 
        transactionPricePerShare = transactionAmounts.find('transactionPricePerShare', namespaces=self.namespace).find('value', namespaces=self.namespace).text
        postTransactionAmounts = transaction.find('postTransactionAmounts', namespaces=self.namespace)
        sharesOwnedFollowingTransaction = postTransactionAmounts.find('sharesOwnedFollowingTransaction', namespaces=self.namespace).find('value', namespaces=self.namespace).text
        return {
            "transactionShares": transactionShares,
            "transactionPricePerShare": transactionPricePerShare,
            "sharesOwnedFollowingTransaction": sharesOwnedFollowingTransaction
        }

    def detail_entries(self, entrie_list):
        entries_dicts = []
        try:
            for entry in entrie_list:
                url = entry['link'].replace("-index.htm", ".txt")
                res = requests.get(url, headers=self.headers)
                content = res.content.decode('utf-8')
                start = content.find("<XML>")
                end = content.find("</XML>")
                xml = content[start+6:end]
                root = ET.fromstring(xml)
                if root.find('.//derivativeTable', namespaces=self.namespace) is not None:
                    continue
                issuer = root.find('.//issuer', namespaces=self.namespace)
                issuerCik = issuer.find('issuerCik', namespaces=self.namespace).text
                issuerName = issuer.find('issuerName', namespaces=self.namespace).text
                issuerTradingSymbol = issuer.find('issuerTradingSymbol', namespaces=self.namespace).text
                nonDerivativeTable = root.find('.//nonDerivativeTable', namespaces=self.namespace)
                transcation_list = []
                for nonDerivativeTransaction in nonDerivativeTable.findall('nonDerivativeTransaction', namespaces=self.namespace):
                    transcation_list.append(self.scrape_transaction(nonDerivativeTransaction))
                
                security_transaction = {
                    "issuerCik": issuerCik,
                    "issuerName": issuerName,
                    "Ticker": issuerTradingSymbol,
                    "Transactions":  transcation_list
                }
                entries_dicts.append(security_transaction)
        except Exception:
            with open("error.xml", "w") as f:
                f.write(xml)
        return entries_dicts

    def parse_entries(self, entries):
        entries_list = []

        for entry in entries:
            title = entry.find('atom:title', namespaces=self.namespace).text
            if not title.endswith("(Reporting)"):
                continue
            link = entry.find(".//atom:link[@rel='alternate']", namespaces=self.namespace).get('href')
            summary = entry.find('atom:summary', namespaces=self.namespace).text
            updated = entry.find('atom:updated', namespaces=self.namespace).text
            date = summary.split("<b>")[1].split("</b>")[1]
            acc_no = summary.split("<b>")[2].split("</b>")[1]
            entries_list.append({'link': link, 'updated': updated, 'date': date, 'acc_no': acc_no})
        return entries_list

    def get_last_fillings(self, start=0, count=100, current_list=[], type=4, owner="include"):
        try:
            url = f"{self.base_url}action=getcurrent&type={type}&owner={owner}&start={start}&count=100&output=atom"
            res = requests.get(url, headers=self.headers)
            root = ET.fromstring(res.content)
            entries = root.findall('.//atom:entry', namespaces=self.namespace)
            current_list.extend(entries)
            if count > 100:
                print("Page left : ", count/100)
                return self.get_last_fillings(start+100, count-100, current_list)
            return self.parse_entries(current_list)[:count]
        except ET.ParseError as e:
            print(e)
            return self.parse_entries(current_list)
        except Exception as e:
            print(e)
            return self.parse_entries(current_list)

if __name__ == "__main__":
    #used to pretty print the result
    import json

    start_time = time.time()
    sec_wrapper = SecForm()
    res = sec_wrapper.get_last_fillings(start=0, count=20)
    result = sec_wrapper.detail_entries(res)
    for r in result:
        print(json.dumps(r,sort_keys=True, indent=4))
    print("Time taken: ", time.time() - start_time)

    