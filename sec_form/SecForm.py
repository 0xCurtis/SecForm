import requests
import xml.etree.ElementTree as ET
import time
import argparse

CREATOR_SIGNATURE = r"""
   _____ ______ _____    ______ ____  _____  __  __   __      _____  __ 
  / ____|  ____/ ____|  |  ____/ __ \|  __ \|  \/  |  \ \    / / _ \/_ |
 | (___ | |__ | |       | |__ | |  | | |__) | \  / |   \ \  / / | | || |
  \___ \|  __|| |       |  __|| |  | |  _  /| |\/| |    \ \/ /| | | || |
  ____) | |___| |____   | |   | |__| | | \ \| |  | |     \  / | |_| || |
 |_____/|______\_____|  |_|    \____/|_|  \_\_|  |_|      \/   \___(_)_|
                                                                              

    Mail : curtis1337wastaken@protonmail.com
    X/Twitter : https://twitter.com/Curtisuke (@curtisuke)
    Github : https://github.com/0xCurtis
"""

class SecForm():
    base_url = "https://www.sec.gov/cgi-bin/browse-edgar?"
    headers = {'User-Agent': "SEC Form /0.1.0 (by @curtisuke)"}
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}

    def scrape_transaction(self, transaction : ET.Element) -> dict:
        """
        This function takes a transaction element from the xml scrapped in detail_entries and returns a dictionary containing the details of the transaction

        Args:
            transaction (ET.Element): transaction element
        
        Returns:
            dict: dictionary containing the details of the transaction
        """
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

    def scrape_issuer(self, issuer : ET.Element) -> dict:
        """
        This function takes an issuer element from the xml scrapped in detail_entries and returns a dictionary containing the details of the issuer

        Args:
            issuer (ET.Element): issuer element
        
        Returns:
            dict: dictionary containing the details of the issuer
        """
        issuerCik = issuer.find('issuerCik', namespaces=self.namespace).text
        issuerName = issuer.find('issuerName', namespaces=self.namespace).text
        issuerTradingSymbol = issuer.find('issuerTradingSymbol', namespaces=self.namespace).text
        return {
            "issuerCik": issuerCik,
            "issuerName": issuerName,
            "issuerTradingSymbol": issuerTradingSymbol
        }

    def detail_entries(self, entrie_list : list[dict]) -> list[dict]:
        """
        This function takes a list of entries and returns a list of dictionaries containing the details of the entries

        Args:
            entrie_list (list[dict]): list of entries (scraped from get_last_fillings)

        Returns:
            list[dict]: list of dictionaries containing the details of the entries
        """
        entries_dicts = []
        for entry in entrie_list:
            try:
                url = entry['link'].replace("-index.htm", ".txt")
                content = requests.get(url, headers=self.headers).content.decode('utf-8')
                start = content.find("<XML>")
                end = content.find("</XML>")
                xml = content[start+6:end]
                root = ET.fromstring(xml)
                if root.find('.//derivativeTable', namespaces=self.namespace) is not None:
                    continue
                
                nonDerivativeTable = root.find('.//nonDerivativeTable', namespaces=self.namespace)
                transcation_list = []
                for nonDerivativeTransaction in nonDerivativeTable.findall('nonDerivativeTransaction', namespaces=self.namespace):
                    transcation_list.append(self.scrape_transaction(nonDerivativeTransaction))
                issuer = root.find('.//issuer', namespaces=self.namespace)                
                security_transaction = {
                    **self.scrape_issuer(issuer),
                    "Transactions":  transcation_list
                }
                entries_dicts.append(security_transaction)
            except Exception:
                with open("error.xml", "w") as f:
                    f.write(xml)
        
        return entries_dicts

    def parse_entries(self, entries: list[ET.Element]) -> list[dict]:
        """
        This function takes a list of entries and returns a list of dictionaries containing the details of the entries

        Args:
            entries (list[ET.Element]): list of entries (scraped from get_last_fillings)
        
        Returns:
            list[dict]: list of dictionaries containing the details of the entries
        """
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
            entries_list.append({'link': link.strip(), 'updated': updated.strip(), 'date': date.strip(), 'acc_no': acc_no.strip(), 'title': title.strip()})
        
        return entries_list

    def get_last_fillings(self, start=0, count=100, current_list=[], type=4, owner="include") -> list[dict]:
        """
        This function is used to get the last fillings from the sec website it can be from any forms but in the current state of the code it is used to get form 4

        Args:
            start (int, optional): start index. Defaults to 0.
            count (int, optional): number of fillings to return. Defaults to 100.
            current_list (list, optional): list of entries. Defaults to [].
            type (int, optional): type of fillings. Defaults to 4.
            owner (str, optional): owner of the fillings. Defaults to "include".
        
        Returns:
            list[dict]: list of dictionaries containing the details of the entries
        """
        try:
            url = f"{self.base_url}action=getcurrent&type={type}&owner={owner}&start={start}&count=100&output=atom"
            res = requests.get(url, headers=self.headers)
            root = ET.fromstring(res.content)
            entries = root.findall('.//atom:entry', namespaces=self.namespace)
            current_list.extend(entries)
            if count > 100:
                return self.get_last_fillings(start+100, count-100, current_list)
            return self.parse_entries(current_list)[:count]
        except ET.ParseError as e:
            print(e)
            return self.parse_entries(current_list)
        except Exception as e:
            print(e)
            return self.parse_entries(current_list)

if __name__ == "__main__":
    # Parse the arguments for the cli version
    parser = argparse.ArgumentParser(description="Get the last daily fillings from the sec website")
    parser.add_argument("--start", type=int, default=0, help="Starting index (eg : 50 will skip the 50 last fillings)")
    parser.add_argument("--count", type=int, default=100, help="Number of fillings to return")
    parser.add_argument("--type", type=str, default="4", help="Type of fillings")
    parser.add_argument('--sign', action='store_true')
    parser.add_argument('--no-sign', dest='sign', action='store_false')
    parser.add_argument('--details', action='store_true', help="Get the details of the fillings or only the fillings list")
    parser.add_argument('--no-details', dest='details', action='store_false')
    parser.set_defaults(sign=False, details=False)
    args = parser.parse_args()
    # if no-sign is set as True print the creator signature
    if args.sign:
        print(CREATOR_SIGNATURE)
    # Create the object and get the last fillings
    sec_form = SecForm()
    last_fillings = sec_form.get_last_fillings(args.start, args.count, type=args.type)
    # Get the details of the fillings
    if args.details:
        details = sec_form.detail_entries(last_fillings)
        print(details)
    else:
        for filling in last_fillings:
            print(f"{filling['title']}\n\t- {filling['date']}\n\t- {filling['acc_no']}\n\t- {filling['link']}\n\n")
        print("Total fillings : ", len(last_fillings))