from pathlib import Path
import json
import datetime
import requests


class CloudVisionCounter:
    # 月1,000枚でエラー
    def __init__(self, nm):
        self.jp = Path(__file__).parent / 'accounts' / nm / 'counts.json'
        self.j = json.loads(self.jp.read_text())
        now = datetime.datetime.now()
        self.curkey = now.strftime('%Y-%m')
        if self.curkey not in self.j['counts']:
            self.j['counts'][self.curkey] = 0
            js = json.dumps(self.j, indent=4)
            self.jp.write_text(js)
        self.max = 1000 - 100

    def cur_count(self):
        if self.j['counts'][self.curkey] >= self.max:
            raise ValueError('Limit')
        return self.j['counts'][self.curkey]

    def increase(self):
        self.j = json.loads(self.jp.read_text())
        self.j['counts'][self.curkey] += 1
        js = json.dumps(self.j, indent=4)
        self.jp.write_text(js)
        if self.j['counts'][self.curkey] >= self.max:
            raise ValueError('Limit')

    def as_str(self):
        return '{}/{}'.format(self.cur_count(), self.max)


class CVCounterOnline:
    # 月1,000枚でエラー
    def __init__(self, name, gas_url):
        self.name = name
        self.gas_url = gas_url
        now = datetime.datetime.now()
        self.month = now.strftime('%Y-%m')
        r = requests.get(self.gas_url)
        print(r)
        self.j = r.json()
        self.max = 1000 - 100

    def cur_count(self):
        if self.name not in self.j:
            return 0
        if self.month not in self.j[self.name]:
            return 0
        c = self.j[self.name][self.month]
        print(f'{self.name} - {self.month}: {c}/{self.max}')
        if c >= self.max:
            raise ValueError('Limit')
        return c

    def increase(self):
        r = requests.post(
            self.gas_url,
            {
                'name': self.name,
                'month': self.month,
                'issueCount': 1
            }
        )
        print(r)
        self.j = r.json()
        if self.j[self.name][self.month] >= self.max:
            raise ValueError('Limit')

    def add_issue_count(self, ic):
        r = requests.post(
            self.gas_url,
            {
                'name': self.name,
                'month': self.month,
                'issueCount': ic
            }
        )
        print(r)
        self.j = r.json()
        if self.j[self.name][self.month] >= self.max:
            raise ValueError('Limit')

    def as_str(self):
        return '{}/{}'.format(self.cur_count(), self.max)


def main():
    """Main."""
    # counter = CloudVisionCounter('deathofrk@gmail.com')
    # print(counter.cur_count())
    # print(counter.j['counts'])
    # print(counter.j)
    # counter.increase()
    # print(counter.cur_count())

    counter = CVCounterOnline('yeti0001@gmail.com')
    print(counter.cur_count())
    print(counter.j)
    counter.add_issue_count(10)
    print(counter.j)


if __name__ == '__main__':
    main()
