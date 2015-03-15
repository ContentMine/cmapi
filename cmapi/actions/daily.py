def daily(cid,tags=[]):
    # retrieve the catalogue record created by the daily journaltocs scrape
    print "getting catalogue record"
    try:
        rec = requests.get('http://localhost:9200/contentmine/catalogue/' + cid).json()['_source']
    except:
        return {"errors": "this ID does not exist in our catalogue"}
    
    d = '/opt/contentmine/src/site/portality/static/scraping/'
    outputdirectory = d + cid
    if not os.path.exists(outputdirectory): os.makedirs(outputdirectory)
    url = rec['link'][0]['url']

    # run quickscrape to get metadata

    # run norma to get a normalised version of the xml file ready for processing

    # run species

    # run regex (using a concatenated file of all current regexes, which needs produced somehow)

    # send facts to the index
    print "facts"
    if 'daily' not in tags: tags.append('daily')
    timestamp = datetime.now().strftime("%Y%m%d")
    if timestamp not in tags: tags.append(timestamp)
    for fact in facts:
        if getkeywords:
            fact['keywords'] = requests.get('http://cottagelabs.com/parser?blurb="' + fact['pre'] + ' ' + fact['fact'] + ' ' + fact['post'] + '"').json()
            time.sleep(0.05)
        # send the fact to the fact api
        fact['tags'] = tags
        fact['source'] = cid
        requests.post('http://localhost:9200/contentmine/fact', data=json.dumps(fact))



def getdailies():
    dy = datetime.now() - timedelta(days=1)
    fdy = dy.strftime("%Y-%m-%d %H%M")
    print "getting dailies since ", fdy
    q = {
        "query": {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "tags.exact": "daily"
                                }
                            },
                            {
                                "range": {
                                    "created_date": {
                                        "gte":  fdy
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        },
        "sort": [{"created_date": {"order":"desc"}}],
        "fields": [],
        "size": 1000000
    }    
    results = requests.post('http://localhost:9200/contentmine/catalogue/_search', data=json.dumps(q))

    print "ready to proces " + str(result in results.json().get('hits',{}).get('total',0)) + ' records.'
    for result in results.json().get('hits',{}).get('hits',[]):
        print "processing " + str(result['_id'])
        daily(result['_id'])

        
getdailies()
