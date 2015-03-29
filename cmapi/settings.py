# ========================
# MAIN SETTINGS

# make this something secret in your overriding app.cfg
SECRET_KEY = "default-key"

# contact info
ADMIN_NAME = "Cottage Labs"
ADMIN_EMAIL = "sysadmin@cottagelabs.com"

# processors files info
STORAGE_DIR = '/home/cloo/storage_service/public/'
QS_JS_DIR = '/home/cloo/dev/contentmine/src/journal-scrapers/scrapers/'
QS_TMP_DIR = '/home/cloo/qstmp/'
REGEXES_DIR = '/home/cloo/dev/contentmine/src/ami-regexes/'

#STORAGE_DIR = '/Users/one/sdir/'
#QS_JS_DIR = '/Users/one/Code/contentmine/src/journal-scrapers/scrapers/'
#QS_TMP_DIR = '/Users/one/qstmp/'

# service info
SERVICE_NAME = "ContentMine API"
HOST = "0.0.0.0"
DEBUG = True
PORT = 5111
WITH_ES = True
ES_HOST = "http://localhost:9200/"
ES_DB = "contentmine"
ES_TYPE = "fact"
FACT_API = ES_HOST + ES_DB + '/' + ES_TYPE + '/'
MAPPING_URL = ES_HOST + ES_DB + '/_mapping/' + ES_TYPE
MAPPING = {
    "fact" : {
        "properties": {
            "created_date": {
                "type": "date",
                "format" : "yyyy-MM-dd mmss||date_optional_time"
            },
            "updated_date": {
                "type": "date",
                "format" : "yyyy-MM-dd mmss||date_optional_time"
            }
        },
        "date_detection": False,
        "dynamic_templates" : [
            {
                "dates" : {
                    "path_match" : "date.*",
                    "mapping" : {
                        "type" : "multi_field",
                        "fields" : {
                            "{name}" : {"type" : "date"},
                            "format" : "yyyy-MM-dd mmss||date_optional_time"
                        }
                    }
                }
            },
            {
                "default" : {
                    "match" : "*",
                    "match_mapping_type": "string",
                    "mapping" : {
                        "type" : "string",
                        "fields" : {
                            "exact" : {"type" : "{dynamic_type}", "index" : "not_analyzed", "store" : "yes"}
                        }
                    }
                }
            }
        ]
    }
}
