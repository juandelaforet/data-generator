#!/usr/bin/python

import sys
import os
import csv
import time
import datetime
import random
import elasticsearch
import elasticsearch.helpers

REQUEST_BODY = {"settings": {"number_of_shards": 1, "number_of_replicas": 0}}

PRINT_SUMMARY_INDEX = 'user_prints_daily_summary'

EVENT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

ES_HOST = {"host": "192.168.56.101", "port": 9200}

es = elasticsearch.Elasticsearch(hosts=[ES_HOST])

base_directory = '/opt/data-generator'
users_file = base_directory + '/reference_data/USERS.ent.csv'

with open(users_file, 'rb') as f:
    csv_reader = csv.reader(f)
    next(csv_reader)
    user_list = list(csv_reader)


for i in range(len(user_list)):
    for z in range(1, 7):
        summary_date = datetime.datetime.today() + datetime.timedelta(days=-z)
        earliest_time = (datetime.datetime.strptime((summary_date.strftime("%Y-%m-%d") + " 09:00:00") , "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=random.randint(1,120))).strftime(EVENT_DATE_FORMAT)
        latest_time = (datetime.datetime.strptime((summary_date.strftime("%Y-%m-%d") + " 17:00:00") , "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=random.randint(1,120))).strftime(EVENT_DATE_FORMAT)

        printed_pages = random.randint(0,50)
        direct_prints = random.randint(0,printed_pages)
        pull_prints = random.randint(0,printed_pages-direct_prints)

        es.index(index=PRINT_SUMMARY_INDEX,
                 doc_type=PRINT_SUMMARY_INDEX+"_record",
                 body={'badge_number': user_list[i][0],
                       'summary_date': summary_date.strftime("%Y-%m-%d"),
                       'earliest_print': earliest_time,
                       'latest_print': latest_time,
                       'total_prints': (direct_prints + pull_prints),
                       'total_pages': printed_pages,
                       'total_direct_prints': direct_prints,
                       'total_pull_prints': pull_prints})

