import argparse
import os
import pprint
import re
import requests
from bs4 import BeautifulSoup as bs
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import smtplib
from datetime import datetime
import config
import urllib.parse as urlparse

BASE_URL = 'https://courses.students.ubc.ca/'

regex_dept = re.compile(r'&dept=([A-Z]+)')
regex_section = re.compile(r'&section=((\d|[A-Z])+)')
regex_course = re.compile(r'&course=((\d|[A-Z])+)')


def fetch_args():
    parser = argparse.ArgumentParser(description='UBC Registration Scrawler',
                                     usage='find a remaining seat for a course.')
    parser.add_argument('--year', help='', type=int, default=datetime.now().year)
    parser.add_argument('--term', help='W or S', default='W')
    parser.add_argument('--filter', type=bool, default=False)
    parser.add_argument('--email', type=bool, default=False)
    subparsers = parser.add_subparsers(help='Choose one of the commands to run.', dest='subparser')
    course_parser = subparsers.add_parser('course', help='search course by course')
    course_parser.add_argument('--dept', help='search course by dept', default=None)
    course_parser.add_argument('--course', help='', default=None)
    section_parser = subparsers.add_parser('section', help='search course by section')
    section_parser.add_argument('--dept', help='', default=None)
    section_parser.add_argument('--course', help='', default=None)
    section_parser.add_argument('--section', help='', default=None)
    dept_parser = subparsers.add_parser('dept', help='search course by dept')
    dept_parser.add_argument('--dept', help='', default=None)

    return parser.parse_args()


def send_email(info, email):
    msg = MIMEMultipart()
    msg['From'] = config.credentials["username"]
    msg['To'] = email
    msg['Subject'] = "Python email"
    msg.attach(MIMEText(info, 'plain'))
    try:
        server = smtplib.SMTP(host='smtp.gmail.com', port=587)
        server.starttls()
        server.login(config.credentials["username"], config.credentials["password"])
        server.sendmail(email, email, msg.as_string())
    except:
        raise


def run():
    args = fetch_args()
    result = None
    searcher = Searcher(args.year, args.term)
    if args.subparser == 'course':
        result = searcher.search_course_by_info(args.dept, args.course)
    elif args.subparser == 'section':
        result = searcher.section_watch_by_info(args.dept, args.course, args.section)
    elif args.subparser == 'dept':
        result = searcher.search_dept_by_info(args.dept)

    if args.filter:
        result = list(get_registerable(result))
    pprint.pprint(result)
    if args.email:
        send_email(json.dumps(result), args.email)


def get_registerable(course_dicts):
    result = []
    for course in course_dicts:
        for key, val in course.items():
            if val['General Seats Remaining'] > 0:
                result.append(course)
    return result


class Searcher(object):

    def __init__(self, year, term):
        self.year = year
        self.term = term

    @staticmethod
    def get_soup(url):
        return bs(requests.request('GET', url).content, 'html.parser')

    @staticmethod
    def parse_page_sections(soup):
        sections = soup.select('.section1')
        sections.extend(soup.select('.section2'))
        return sections

    def parse_page_urls(self, soup, type=None):
        urls = []
        sections = self.parse_page_sections(soup)
        is_lecture = 'Activity' in soup.select('tr')[0].text
        for section in sections:
            if is_lecture and section.select('td')[2].text not in ['Lecture', 'Web-Oriented Course']:
                continue
            if section.a:
                urls.append(urlparse.urljoin(BASE_URL, section.a['href']))
                # if type:
                #     urls.append(self.get_url(self.parse_info(section.a['href']), type))
                # else:
                #     urls.append(section.a['href'])
        return urls

    def get_url(self, info, type):
        if type == 'dept':
            return BASE_URL + 'cs/courseschedule?tname=subj-department&sessyr={}&sesscd={}&dept={}&' \
                              '&pname=subjarea'.format(self.year,
                                                       self.term,
                                                       info['dept'])
        elif type == 'section':
            return BASE_URL + 'cs/courseschedule?sesscd={}&pname=subjarea&tname=subj-section&' \
                              'sessyr={}&course={}&section={}&dept={}'.format(self.year,
                                                                              self.term,
                                                                              info['course'],
                                                                              info['section'],
                                                                              info['dept'])
        elif type == 'course':
            return BASE_URL + 'cs/courseschedule?tname=subj-course&sessyr={}&sesscd={}&dept={}&' \
                              'course={}&pname=subjarea'.format(self.year,
                                                                self.term,
                                                                info['dept'],
                                                                info['course'])

    @staticmethod
    def parse_info(url):
        dept = regex_dept.search(url)
        section = regex_section.search(url)
        course = regex_course.search(url)
        result = {}
        result['dept'] = dept.group(1) if dept else ''
        result['course'] = course.group(1) if course else ''
        result['section'] = section.group(1) if section else ''
        return result

    def search_whole(self):
        whole_soup = self.get_soup(
            os.path.join(BASE_URL, 'cs/courseschedule?tname=subj-all-departments&sessyr=2019&sesscd=S&pname=subjarea'))
        whole_urls = self.parse_page_urls(whole_soup)
        for whole_url in whole_urls:
            self.search_dept(whole_url)

    def search_dept(self, url):
        result = []
        dept_soup = bs(requests.request('GET', url).content, 'html.parser')
        course_urls = self.parse_page_urls(dept_soup)
        for course_url in course_urls:
            dept_info = self.parse_info(course_url)
            result.extend(self.search_course(self.get_url(dept_info, 'course')))
        return [elem for elem in result if elem]

    def search_course(self, url):
        result = []
        page = requests.request('GET', url).content
        course_soup = bs(page, 'html.parser')
        section_urls = self.parse_page_urls(course_soup, 'section')
        for section_url in section_urls:
            section_info = self.parse_info(section_url)
            section_status = self.section_watch(section_url)
            if section_status:
                result.append({' '.join(section_info.values()): section_status})
        return result

    def section_watch(self, url):
        result = {}
        content = requests.request('GET', url).content
        soup = bs(content, 'html.parser')
        try:
            summary = soup.select('table')[3].text
            result['General Seats Remaining'] = int(re.search(r'General Seats Remaining:(\d+)', summary).group(1))
            result['Restricted Seats Remaining'] = int(
                re.search(r'Restricted Seats Remaining\*?:(\d+)', summary).group(1))
            result['Currently Registered'] = int(re.search(r'Currently Registered\*?:(\d+)', summary).group(1))
            return result
        except Exception:
            return None

    def search_dept_by_info(self, dept):
        info = {'dept': dept}
        url = self.get_url(info, 'dept')
        return self.search_dept(url)

    def search_course_by_info(self, dept, course):
        info = {'dept': dept,
                'course': course}
        url = self.get_url(info, 'course')
        return self.search_course(url)

    def section_watch_by_info(self, dept, course, section):
        info = {
            'dept': dept,
            'section': section,
            'course': course
        }
        url = self.get_url(info, 'section')
        return self.section_watch(url)


if __name__ == '__main__':
    run()