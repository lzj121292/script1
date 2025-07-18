import requests
import time
import bs4
import json
import csv
import os

class JobScraper:
    def __init__(self):
        self.api_url = 'https://pultegroup.wd1.myworkdayjobs.com/wday/cxs/pultegroup/PGI/jobs'
        self.detail_url_prefix = 'https://pultegroup.wd1.myworkdayjobs.com/en-US/PGI/details/'
        self.limit = 20
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0'
        }
        self.csv_file = 'job_list.csv'
        self.fieldnames = [
            'title', 'company_url', 'locations', 'post_date', 'bullet_fields',
            'date_posted', 'employment_type', 'description', 'address_country'
        ]

    def get_job_detail(self, full_url):
        headers = {
            'User-Agent': self.headers['User-Agent']
        }
        response = requests.get(full_url, headers=headers)
        response.encoding = 'utf-8'
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if 'datePosted' in data:
                    return data
            except Exception:
                continue
        return None

    def write_jobs_to_csv(self, jobs):
        with open(self.csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            for job in jobs:
                writer.writerow(job)
        print(f"已写入 {len(jobs)} 条到 {self.csv_file}")

    def get_job_list(self):
        offset = 0
        jobs = []
        payload = {
            'appliedFacets': {},
            'limit': self.limit,
            'offset': offset,
        }
        response = requests.post(self.api_url, json=payload, headers=self.headers)
        if response.status_code != 200:
            print("请求失败，状态码：", response.status_code)
            return
        data = response.json()
        total = data.get('total', 0)
        print(f"总职位数: {total}")

        while offset < total:
            payload['offset'] = offset
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            if response.status_code != 200:
                print(f"第{offset//self.limit+1}页请求失败，状态码：", response.status_code)
                break
            data = response.json()
            for job in data['jobPostings']:
                title = job.get('title')
                external_path = job.get('externalPath')
                job_id = external_path.split('/')[-1] if external_path else ''
                full_url = self.detail_url_prefix + job_id
                locations = job.get('locationsText')
                post_date = job.get('postedOn')
                bullet_fields = job.get('bulletFields')
                detail = self.get_job_detail(full_url)
                if detail:
                    date_posted = detail.get('datePosted')
                    employment_type = detail.get('employmentType')
                    description = detail.get('description')
                    address_country = detail.get('jobLocation', {}).get('address', {}).get('addressCountry')
                else:
                    date_posted = employment_type = description = address_country = None
                jobs.append({
                    'title': title,
                    'company_url': full_url,
                    'locations': locations,
                    'post_date': post_date,
                    'bullet_fields': bullet_fields,
                    'date_posted': date_posted,
                    'employment_type': employment_type,
                    'description': description,
                    'address_country': address_country
                })
            offset += self.limit
            time.sleep(3)
        self.write_jobs_to_csv(jobs)

if __name__ == '__main__':
    scraper = JobScraper()
    scraper.get_job_list()
