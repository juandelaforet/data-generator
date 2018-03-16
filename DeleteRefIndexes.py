#!/usr/bin/python

"""
VERSION : 1.0
AUTHOR  : John Smith
"""
CODE_VERSION = "1.0"
VERSION_DATE = "05/02/2018"

from elasticsearch import Elasticsearch

ES_HOST = {
    "host": "192.168.56.101",
    "port": 9200
}

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('user_details'):
    res = es.indices.delete(index='user_details')

if es.indices.exists('user_risks'):
    res = es.indices.delete(index='user_risks')

if es.indices.exists('printers'):
    res = es.indices.delete(index='printers')

if es.indices.exists('devices'):
    res = es.indices.delete(index='devices')

if es.indices.exists('locations'):
    res = es.indices.delete(index='locations')

if es.indices.exists('pki_details'):
    res = es.indices.delete(index='pki_details')

if es.indices.exists('citrix_servers'):
    res = es.indices.delete(index='citrix_servers')

if es.indices.exists('citrix_sessions'):
    res = es.indices.delete(index='citrix_sessions')

if es.indices.exists('user_locations'):
    res = es.indices.delete(index='user_locations')

if es.indices.exists('user_terminals'):
    res = es.indices.delete(index='user_terminals')

if es.indices.exists('email_body_text'):
    res = es.indices.delete(index='email_body_text')

if es.indices.exists('user_phones'):
    res = es.indices.delete(index='user_phones')

if es.indices.exists('user_prints_daily_summary'):
    res = es.indices.delete(index='user_prints_daily_summary')
