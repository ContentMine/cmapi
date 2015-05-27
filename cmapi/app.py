
import os, requests, json, uuid, inspect
from functools import wraps
from datetime import datetime

from flask import Flask, request, make_response, current_app, abort, redirect
from flask.ext.login import LoginManager, current_user, login_user

from cmapi import settings, processors
from cmapi.translator import Translator as translator

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)
    # parent directory
    here = os.path.dirname(os.path.abspath( __file__ ))
    config_path = os.path.join(os.path.dirname(here), 'app.cfg')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)
    login_manager.setup_app(app)
    if app.config.get('WITH_ES',False):
        if requests.head(app.config['FACT_API']).status_code != 200:
            requests.post(app.config['FACT_API'])
            requests.put(app.config['MAPPING_URL'], json.dumps(app.config['MAPPING']))
    return app

app = create_app()

@login_manager.user_loader
def load_account_for_login_manager(userid):
    # TODO should actually get a user somehow here or return anonymous user
    # connect to separate CL user auth tool
    return {}

'''
TODO: auth against CL accounts system - get user, their rights on this service, and the group they are in
then get details about this service from the CL services system - to work out what the user is allowed to do

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = models.Account.pull(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values or 'api_key' in request.headers:
        apik = request.values['api_key'] if 'api_key' in request.values else request.headers['api_key']
        res = models.Account.query(q='api_key:"' + apik + '"')['hits']['hits']
        if len(res) == 1:
            user = models.Account.pull(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)
'''


@app.errorhandler(404)
def page_not_found(e):
    return 'File Not Found', 404

@app.errorhandler(401)
def page_not_found(e):
    return 'Unauthorised', 401
        
        
def rjson(f):
    # wraps output as a JSON response, with JSONP if necessary
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs)) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            res = f(*args, **kwargs)
            if not isinstance(res,dict) and not isinstance(res,list): res = [i for i in str(res).split('\n') if len(i) > 0]
            resp = make_response( json.dumps( res, sort_keys=True ) )
            resp.mimetype = "application/json"
            return resp
    return decorated_function

# add checks once account auth in place    

@app.route('/', methods=['GET','POST'])
@app.route('/<procname>', methods=['GET','POST'])
@app.route('/<procname>/meta')
@rjson
def proc(procname=None):
    if procname is None:
        return {
            "title": "ContentMine API",
            "version": "0.2",
            "README": "ContentMine can retrieve PDF, HTML, XML documents from URLs and store metadata about the articles contained in those documents, then it can normalise the documents and extract facts by processing the normalised document with more processors. Append a processor name from the list below to the API url to learn more about each available route. Extracted facts can be explored at the /fact route.",
            "processors": [name.lower() for name, obj in inspect.getmembers(processors) if inspect.isclass(obj) and name != 'Processor'],
            "routes": ["fact"]
        }
    elif request.path.endswith('meta'):
        pr = getattr(processors, procname[0].capitalize() + procname[1:].lower() )
        return pr().meta()
    else:
        pr = getattr(processors, procname[0].capitalize() + procname[1:].lower() )
        params = request.json if request.json else request.values
        params = {k:params[k] for k in params.keys()}
        return pr().run(**params)
    
    
    
# provide access to facts ------------------------------------------------------
@app.route('/fact', methods=['GET','POST'])
@app.route('/fact/<ident>', methods=['GET','POST'])
@rjson
def factdirect(ident=None):
    if ident is not None:
        try:
            f = requests.get(app.config['FACT_API'] + ident)
            rec = f.json()['_source']
        except:
            abort(404)
    else:
        rec = {}
    if request.method == 'GET':
        if ident is not None:
            return rec
        else:
            return '' # instructions
    elif request.method in ['PUT','POST']:
        inp = {}
        if request.json:
            for k in request.json.keys():
                if k.lower() not in ['submit','api_key']:
                    inp[k] = request.json[k]
        else:
            for k, v in request.values.items():
                if k.lower() not in ['submit','api_key']:
                    inp[k] = v
        if request.method == 'PUT':
            rec = inp
        else:
            for k in inp.keys():
                rec[k] = inp[k]
        if 'id' not in rec: rec['id'] = uuid.uuid4().hex
        rec['updated_date'] = datetime.now().strftime("%Y-%m-%d %H%M")
        if 'created_date' not in rec:
            rec['created_date'] = datetime.now().strftime("%Y-%m-%d %H%M")
        # TODO: save user doing this action
        return requests.post(app.config['FACT_API'] + rec['id'], data=json.dumps(rec))


@app.route('/fact/query', methods=['GET','POST'])
@rjson
def fquery():
    # NOTE tried streaming response with context here through requests but it was very slow
    if request.method == 'GET':
        return requests.get(app.config['FACT_API'] + '_search?' + "&".join([k + '=' + request.args[k] for k in request.args.keys()])).json()
    elif request.method == 'POST':
        params = request.json if request.json else request.values
        params = {k:params[k] for k in params.keys()}
        return requests.post(app.config['FACT_API'] + '_search', data=json.dumps(params)).json()
    

@app.route('/fact/daily')
@rjson
def factdaily():
    # TODO: this should be a filtered query
    qry = {
        'query': {
            'range': {
                'created_date': {
                    'gte': datetime.now().strftime("%Y-%m-%d")
                }
            }
        },
        'sort': [{"created_date.exact":{"order":"desc"}}]
    }
    r = requests.post(app.config['FACT_API'] + '_search', data=json.dumps(qry))
    # TODO: decide if any control keys should be removed before displaying facts
    return [i['_source'] for i in r.json().get('hits',{}).get('hits',[])]
    

    


@app.route('/processit')
@rjson
def processit():
    if url:
        pass
    elif urls:
        pass
    elif cid:
        pass
    elif cids:
        pass
    elif query:
        pass
    # check each url in the catalogue
    # check each id in the catalogue
    # or if a query get the list of IDs from that query
    # if already there, look to see if we have files on disk for them
    # if not on disk try to retrieve them either directly or with quickscrape
    # if not on disk try to retrieve them either directly or with quickscrape
    # otherwise just grab what is at the url directly
    # run the rest of the specified plugins
    

# queue up article metadata records that need processing -----------------------
@app.route('/process')
@rjson
def process():
    return {}

@app.route('/process/assign')
@rjson
def assign():
    vals = request.json if request.json else request.values
    if 'ids' in vals:
        if ',' in vals['ids']:
            vl = vals['ids'].split(',')
        elif '[' not in vals['ids']:
            vl = [vals['ids']]
        else:
            vl = vals['ids']
        resp = make_response( json.dumps( current_user.assign(ids=vl) ) )
        resp.mimetype = "application/json"
        return resp
    else:
        abort(404)
        
@app.route('/process/assigned')
@rjson
def assigned():
    return current_user.assigned

@app.route('/process/unassign')
@rjson
def unassign():
    current_user.unassign()
    return []

@app.route('/process/next')
@rjson
def next():
    res = models.Catalogue.query(q={
        'query': {
            'filtered': {
                'filter': {
                    'missing': {
                        'field': 'assigned_to'
                    }
                }
            }
        },
        'sort': {'created_date': 'desc'},
        'size': 1
    })
    try:
        rec = res['hits']['hits'][0]['_source']
        if request.method == 'POST' or request.values.get('haveit',False):
            current_user.assign(ids=[rec['id']])
        return rec
    except:
        abort(404)


@app.route('/receive', methods=['GET','POST'])
@app.route('/receive/<processor>/<tag>', methods=['GET','POST'])
@rjson
def receive(processor=None,tag=None):
    if request.method == 'GET':
        return {'howto': 'POST a results file from one of the AMI processors to an extension of this URL, extended with the processor you used, and a tag to identify the fact group you wish to put the results into'}
    elif request.method == 'POST':
        if processor is None or tag is None:
            return redirect('/receive')
        else:
            try:
                fl = request.files['file']
                t = translator(processor=processor)
                results = t.translate(fl)
                for res in results:
                    res['set'] = tag
                    res['processor'] = processor
                    requests.post('http://contentmine.org/api/fact', data=json.dumps(res))
            except:
                abort(404)
    else:
        abort(404)
        

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])

