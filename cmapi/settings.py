# ========================
# MAIN SETTINGS

# make this something secret in your overriding app.cfg
SECRET_KEY = "default-key"

# contact info
ADMIN_NAME = "Cottage Labs"
ADMIN_EMAIL = "sysadmin@cottagelabs.com"

# service info
SERVICE_NAME = "ContentMine API"
HOST = "0.0.0.0"
DEBUG = True
PORT = 5111
ES_HOST = "http://gateway:9200/"
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
