#!/usr/bin/python

import csv
from elasticsearch import Elasticsearch

"""
VERSION : 1.0
AUTHOR  : John Smith
"""
CODE_VERSION = "1.0"
VERSION_DATE = "05/02/2018"

ES_HOST = {
    "host": "192.168.56.101",
    "port": 9200
}

request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
}

user_details_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "user_details_record": {
            "properties": {
                "badge_number": {"type": "integer"},
                "first_name": {"type": "keyword", "index": "true"},
                "middle_names": {"type": "keyword", "index": "true"},
                "surname": {"type": "keyword", "index": "true"},
                "job_title": {"type": "keyword", "index": "true"},
                "main_location": {"type": "keyword", "index": "true"},
                "phone": {"type": "keyword", "index": "true"},
                "smoker": {"type": "text"},
                "starter": {"type": "text"},
                "team": {"type": "keyword", "index": "true"},
                "email": {"type": "keyword", "index": "true"},
                "pki_details": {"type": "keyword", "index": "true"},
                "test_user": {"type": "text"}
            }
        }
    }
}

user_locations_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "user_locations_record": {
            "properties": {
                "badge_number": {"type": "integer"},
                "location": {"type": "keyword", "index": "true"},
                "from_date": {"type": "date", "index": "true"},
                "to_date": {"type": "date", "index": "true"},
                "current": {"type": "text"}
            }
        }
    }
}

email_body_text_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "email_body_text_record": {
            "properties": {
                "badge_number": {"type": "integer"},
                "original_text": {"type": "keyword", "index": "true"},
                "annotated_text": {"type": "keyword", "index": "true"},
                "match_score": {"type": "integer"},
                "match_details": {"type": "keyword", "index": "true"},
                "file_reference": {"type": "text"}
            }
        }
    }
}

user_terminals_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "user_terminals_record": {
            "properties": {
                "badge_number": {"type": "integer"},
                "location": {"type": "keyword", "index": "true"},
                "terminal": {"type": "keyword", "index": "true"},
                "from_date": {"type": "date", "index": "true"},
                "to_date": {"type": "date", "index": "true"},
                "current": {"type": "text"}
            }
        }
    }
}

user_phones_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "user_phones_record": {
            "properties": {
                "badge_number": {"type": "integer"},
                "location": {"type": "keyword", "index": "true"},
                "phone": {"type": "keyword", "index": "true"},
                "from_date": {"type": "date", "index": "true"},
                "to_date": {"type": "date", "index": "true"},
                "current": {"type": "text"}
            }
        }
    }
}

user_prints_daily_summary_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "user_prints_record": {
            "properties": {
                "badge_number": {"type": "integer"},
                "summary_date": {"type": "keyword", "index": "true"},
                "earliest_print": {"type": "date", "index": "true"},
                "latest_print": {"type": "date", "index": "true"},
                "total_prints": {"type": "integer"},
                "total_pages": {"type": "integer"},
                "total_direct_prints": {"type": "integer"},
                "total_pull_prints": {"type": "integer"}
            }
        }
    }
}

user_risks_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "user_risks_record": {
            "properties": {
                "badge_number": {"type": "integer"},
                "of_concern_hr": {"type": "text"},
                "of_concern_security": {"type": "text"},
                "score": {"type": "integer"}
            }
        }
    }
}

devices_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "devices_record": {
            "properties": {
                "device_id": {"type": "keyword"},
                "device_name": {"type": "keyword", "index": "true"},
                "device_type": {"type": "keyword", "index": "true"},
                "manufacturer": {"type": "keyword", "index": "true"},
                "serial_number": {"type": "keyword", "index": "true"},
                "asset_tag": {"type": "keyword", "index": "true"},
                "capacity": {"type": "integer"},
                "capacity_units": {"type": "keyword"}
            }
        }
    }
}

locations_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "locations_record": {
            "properties": {
                "location": {"type": "keyword", "index": "true"},
                "door_data": {"type": "boolean"},
                "latitude": {"type": "float"},
                "longitude": {"type": "float"}
            }
        }
    }
}

printers_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "printers_record": {
            "properties": {
                "location": {"type": "keyword", "index": "true"},
                "printer_name": {"type": "keyword", "index": "true"},
                "printer_type": {"type": "keyword", "index": "true"},
                "direct_or_pull": {"type": "keyword", "index": "true"}
            }
        }
    }
}

pki_details_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "pki_details_record": {
            "properties": {
                "badge_number": {"type": "integer", "index": "true"},
                "pki_details": {"type": "keyword", "index": "true"},
                "circus_role": {"type": "keyword", "index": "true"},
                "voyager_role": {"type": "keyword", "index": "true"},
                "structure_role": {"type": "keyword", "index": "true"}
            }
        }
    }
}

citrix_servers_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "citrix_servers_record": {
            "properties": {
                "server_name": {"type": "keyword", "index": "true"},
                "location": {"type": "keyword", "index": "true"},
                "max_sessions": {"type": "integer", "index": "false"}
            }
        }
    }
}

citrix_sessions_request_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "citrix_sessions_record": {
            "properties": {
                "session_name": {"type": "keyword", "index": "true"},
                "location": {"type": "keyword", "index": "true"},
                "citrix_server": {"type": "keyword", "index": "true"}
            }
        }
    }
}

reference_data_directory = "/opt/data-generator/reference_data/"

# USER DETAILS
users_fp = open(reference_data_directory + "USERS.ent.csv", 'rb')
csv_file_object = csv.reader(users_fp)

header = csv_file_object.next()
header = [item.lower() for item in header]

bulk_data = []

for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
        data_dict[header[i]] = row[i]
    op_dict = {
        "index": {
            "_index": 'user_details',
            "_type": 'user_details_record',
            "_id": data_dict['badge_number']
        }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('user_details'):
    es.indices.delete(index='user_details')

es.indices.create(index='user_details', body=user_details_request_body)
es.bulk(index='user_details', body=bulk_data, refresh=True)

users_fp.close()
# USER DETAILS

# USER RISKS
risks_fp = open(reference_data_directory + "USER_RISKS.ent.csv", 'rb')
csv_file_object = csv.reader(risks_fp)

header = csv_file_object.next()
header = [item.lower() for item in header]

bulk_data = []

for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
        data_dict[header[i]] = row[i]
    op_dict = {
        "index": {
            "_index": 'user_risks',
            "_type": 'user_risks_record',
            "_id": data_dict['badge_number']
        }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('user_risks'):
    es.indices.delete(index='user_risks')

es.indices.create(index='user_risks', body=user_risks_request_body)
es.bulk(index='user_risks', body=bulk_data, refresh=True)

risks_fp.close()
# USER RISKS

# DEVICES
devices_fp = open(reference_data_directory + "DEVICES.ent.csv", 'rb')
csv_file_object = csv.reader(devices_fp)

header = csv_file_object.next()
header = [item.lower() for item in header]

bulk_data = []

for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
        data_dict[header[i]] = row[i]
    op_dict = {
        "index": {
            "_index": 'devices',
            "_type": 'devices_record',
            "_id": data_dict['device_id']
        }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('devices'):
    es.indices.delete(index='devices')

es.indices.create(index='devices', body=devices_request_body)
es.bulk(index='devices', body=bulk_data, refresh=True)

devices_fp.close()
# DEVICES

# LOCATIONS
locations_fp = open(reference_data_directory + "LOCATIONS.ent.csv", 'rb')
csv_file_object = csv.reader(locations_fp)

header = csv_file_object.next()
header = [item.lower() for item in header]

bulk_data = []

for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
        data_dict[header[i]] = row[i]
    op_dict = {
        "index": {
            "_index": 'locations',
            "_type": 'locations_record',
            "_id": data_dict['location']
        }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('locations'):
    es.indices.delete(index='locations')

es.indices.create(index='locations', body=locations_request_body)
es.bulk(index='locations', body=bulk_data, refresh=True)

locations_fp.close()
# LOCATIONS

# PRINTERS
printers_fp = open(reference_data_directory + "PRINTERS.ent.csv", 'rb')
csv_file_object = csv.reader(printers_fp)

header = csv_file_object.next()
header = [item.lower() for item in header]

bulk_data = []

for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
        data_dict[header[i]] = row[i]
    op_dict = {
        "index": {
            "_index": 'printers',
            "_type": 'printers_record',
            "_id": data_dict['printer_name']
        }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('printers'):
    es.indices.delete(index='printers')

es.indices.create(index='printers', body=printers_request_body)
es.bulk(index='printers', body=bulk_data, refresh=True)

printers_fp.close()
# PRINTERS

# PKI_DETAILS
pki_details_fp = open(reference_data_directory + "PKI.ent.csv", 'rb')
csv_file_object = csv.reader(pki_details_fp)

header = csv_file_object.next()
header = [item.lower() for item in header]

bulk_data = []

for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
        data_dict[header[i]] = row[i]
    op_dict = {
        "index": {
            "_index": 'pki_details',
            "_type": 'pki_details_record',
            "_id": data_dict['badge_number']
        }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('pki_details'):
    es.indices.delete(index='pki_details')

es.indices.create(index='pki_details', body=pki_details_request_body)
es.bulk(index='pki_details', body=bulk_data, refresh=True)

printers_fp.close()
# PKI_DETAILS

# CITRIX_SERVERS
citrix_servers_fp = open(reference_data_directory + "CITRIX_SERVERS.ent.csv", 'rb')
csv_file_object = csv.reader(citrix_servers_fp)

header = csv_file_object.next()
header = [item.lower() for item in header]

bulk_data = []

for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
        data_dict[header[i]] = row[i]
    op_dict = {
        "index": {
            "_index": 'citrix_servers',
            "_type": 'citrix_servers_record',
            "_id": data_dict['server_name']
        }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('citrix_servers'):
    es.indices.delete(index='citrix_servers')

es.indices.create(index='citrix_servers', body=citrix_servers_request_body)
es.bulk(index='citrix_servers', body=bulk_data, refresh=True)

citrix_servers_fp.close()
# CITRIX_SERVERS

# CITRIX_SESSIONS
citrix_sessions_fp = open(reference_data_directory + "CITRIX_SESSIONS.ent.csv", 'rb')
csv_file_object = csv.reader(citrix_sessions_fp)

header = csv_file_object.next()
header = [item.lower() for item in header]

bulk_data = []

for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
        data_dict[header[i]] = row[i]
    op_dict = {
        "index": {
            "_index": 'citrix_sessions',
            "_type": 'citrix_sessions_record',
            "_id": data_dict['session_name']
        }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

es = Elasticsearch(hosts=[ES_HOST])

if es.indices.exists('citrix_sessions'):
    es.indices.delete(index='citrix_sessions')

es.indices.create(index='citrix_sessions', body=citrix_sessions_request_body)
es.bulk(index='citrix_sessions', body=bulk_data, refresh=True)

citrix_sessions_fp.close()
# CITRIX_SESSIONS

es.indices.create(index='user_locations', body=user_locations_request_body)
es.indices.create(index='user_terminals', body=user_terminals_request_body)
es.indices.create(index='user_phones', body=user_phones_request_body)
es.indices.create(index='user_prints_daily_summary', body=user_prints_daily_summary_request_body)
es.indices.create(index='email_body_text', body=email_body_text_request_body)

