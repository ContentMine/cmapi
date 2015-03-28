
'''
A contentmine processor template
At the bottom the Processor object type is defined, the main task of it is run()
Other classes should inherit from the Processor object template, and overwrite 
_cmd to show what command they need to run.
Then they can optionally overwrite before, after, store and save - do actions corresponding to the run
By default before, after, store and save are executed by run, but they can be disabled on any default run call
by sending before=False etc
However of course the default action of these methods is pass. So unless they are overwritten in the defined processors 
with something useful, nothing would happen anyway.
Processors can also overwrite run if necessary
Each processor class should be able to be called and return output and delete anything it put on disk by default
It can also be programmed using the available overwriteable methods to store the stuff it put on disk somewhere else

Make sure to use class names that start with one upper case letter and the rest lower case.
'''

import uuid, subprocess, os, shutil, json, requests
from lxml import etree


class Processor(object):
    _output = {
        "usage": [
            "Called with no arguments, this route returns the usage instructions of the underlying codebase.",
            "Arguments can be passed as GET URL parameters, or as a JSON object via POST.",
            "Single-letter short versions or full-named versions of arguments can be used.",
            "If single-letter arguments lack a preceding -, it will be automatically added. For full-named arguments, preceding -- will be added if not supplied.",
            "Do not provide any output parameters - these are controlled by the API server.",
            "Similarly any paramaters telling the software where to find any local files it should expect will be handled by the API server.",
            "Output files will be saved to a folder and a URL will be provided for access to them.",
            "Any direct output from the executed command will be returned in the response object, which is always a successful return of JSON content.",
            "If a Catalogue ID (a cid) is available for a work being processed, it can be passed as the cid or --cid parameter. It will then be used to identify catalogue records and storage directories where necessary, so input parameters can be skipped."
        ]
    }
    
    @property
    def output(self):
        return self._output

    @classmethod
    def _cmd(cls, **kwargs):
        cls._output['command'] = []
        for key in kwargs.keys():
            if not key.startswith('-'): k = '-' + key
            if len(key) > 2: k = '-' + k
            cls._output['command'].append(k)
            cls._output['command'].append(kwargs[key])
    
    @classmethod
    def before(cls, **kwargs):
        pass
    
    @classmethod
    def after(cls, **kwargs):
        pass
            
    @classmethod
    def run(cls, before=True,after=True,store=True,save=True,**kwargs):
        # check for dodgy characters in the kwargs
        if 'callback' in kwargs: del kwargs['callback']
        if '_' in kwargs: del kwargs['_']
        for k in kwargs.keys():
            if ';' in k or ';' in kwargs[k]:
                cls._output['errors'] = ['Sorry, illegal character found in args.']
                return cls._output
        if before: cls.before(**kwargs)
        cls._cmd(**kwargs)
        try:
            p = subprocess.Popen(cls._output['command'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cls._output['output'], cls._output['errors'] = p.communicate()
        except Exception, e:
            cls._output['output'] = {}
            cls._output['errors'] = [str(e)]
        if after: cls.after(**kwargs)
        if not isinstance(cls._output['errors'],dict) and not isinstance(cls._output['errors'],list):
            cls._output['errors'] = [i for i in cls._output['errors'].split('\n') if len(i) > 0]
        if not isinstance(cls._output['output'],dict) and not isinstance(cls._output['output'],list) and '\n' in cls._output['output']:
            cls._output['output'] = [i for i in cls._output['output'].split('\n') if len(i) > 0]
        return cls._output

    

        
class Quickscrape(Processor):
    @classmethod
    def _cmd(cls, **kwargs):
        cls._output['command'] = ['/usr/bin/quickscrape']
        if len(kwargs) > 0:
            for key in kwargs.keys():
                if not key.startswith('-'): k = '-' + key
                if len(key) > 2: k = '-' + k
                if k not in ['-d','--scraperdir','-o','--output','-f','--outformat']:
                    cls._output['command'].append(k)
                    cls._output['command'].append(kwargs[key])
            cls._output['command'].append('--scraperdir')
            cls._output['command'].append('/home/cloo/dev/contentmine/src/journal-scrapers/scrapers/')
            cls._output['command'].append('--output')
            cls._output['command'].append('/home/cloo/qstmp/')
            cls._output['command'].append('--outformat')
            cls._output['command'].append('bibjson')
        else:
            cls._output['command'].append('--help')


    @classmethod
    def after(cls, **kwargs):
        turl = kwargs.get('u',kwargs.get('-u',kwargs.get('--url',kwargs.get('url',None))))
        if turl is not None:
            slug = turl.replace('://','_').replace('/','_').replace(':','')
            cls._output['cid'] = kwargs.get('cid',uuid.uuid4().hex)
            cls._output['store'] = 'http://store.cottagelabs.com/' + cls._output['cid']
            cls._output['files'] = []
            tmpdir = '/home/cloo/qstmp/' + slug
            outdir = '/home/cloo/storage_service/public/' + cls._output['cid']
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            for fl in os.listdir(tmpdir):
                shutil.copy(os.path.join(tmpdir, fl), outdir)
                cls._output['files'].append(cls._output['store'] + '/' + fl)
            shutil.rmtree(tmpdir)

        
        

class Norma(Processor):
    @classmethod
    def _cmd(cls, **kwargs):
        cls._output['command'] = ['norma']
        if len(kwargs.keys()) > 0 and '-x' not in kwargs.keys() and 'xsl' not in kwargs.keys() and '--xsl' not in kwargs.keys() and 'x' not in kwargs.keys():
            cls._output['command'].append('--xsl')
            cls._output['command'].append('/org/xmlcml/norma/pubstyle/nlm/toHtml.xsl')
        for key in kwargs.keys():
            if not key.startswith('-'): k = '-' + key
            if len(key) > 2: k = '-' + k
            if k == '--cid':
                cls._output['cid'] = kwargs[key]
                cls._output['command'].append('-q')
                cls._output['command'].append('/home/cloo/storage_service/public/' + str(kwargs[key]))
                cls._output['command'].append('--input')
                cls._output['command'].append('/home/cloo/storage_service/public/' + str(kwargs[key]) + '/fulltext.html')
                cls._output['command'].append('--output')
                cls._output['command'].append('/home/cloo/storage_service/public/' + str(kwargs[key]) + '/scholarly.html')
            else:
                cls._output['command'].append(k)
                cls._output['command'].append(kwargs[key])



            
class Amiregex(Processor):
    @classmethod
    def _cmd(cls, **kwargs):
        cls._output['command'] = ['/usr/bin/ami2-regex']
        # if regex and no -g make it this /opt/contentmine/src/site/portality/ami-regexes/concatenated.xml
        for key in kwargs.keys():
            if not key.startswith('-'): k = '-' + key
            if len(key) > 2: k = '-' + k
            cls._output['command'].append(k)
            cls._output['command'].append(kwargs[key])
    
    @classmethod
    def after(cls, **kwargs):
        pass
        '''cls._output['facts'] = []
        results_file = /home/cloo/storage_service/public/ + cmd + '_results.xml'

        ns = etree.FunctionNamespace("http://www.xml-cml.org/ami")
        ns.prefix = "zf"
        tree = etree.parse(results_file)
        hits = tree.xpath('//zf:hit')
        for hit in hits:
            doc = {}
            doc["pre"] = hit.get("pre")
            doc["fact"] = hit.get("word")
            doc["post"] = hit.get("post")
            cls._output['facts'].append(doc)
        
        shutil.move('target/fulltext.xml/results.xml', storagedirectory + '/' + cmd + '_results.xml')'''

        
class Amiwords(Processor):
    @classmethod
    def _cmd(cls, **kwargs):
        cls._output['command'] = ['/usr/bin/ami2-words']
        for key in kwargs.keys():
            if not key.startswith('-'): k = '-' + key
            if len(key) > 2: k = '-' + k
            cls._output['command'].append(k)
            cls._output['command'].append(kwargs[key])

            
class Retrieve(Processor):
    @classmethod
    def _cmd(cls, **kwargs):
        cls._output['command'] = ['wget']
        if len(kwargs) > 0:
            cls._output['cid'] = kwargs.get('cid',uuid.uuid4().hex)
            cls._output['store'] = 'http://store.cottagelabs.com/' + cls._output['cid']
            storedir = '/home/cloo/storage_service/public/' + cls._output['cid']
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            if 'url' in kwargs.keys():
                cls._output['command'].append(kwargs[key])
                cls._output['command'].append('-o')
                cls._output['command'].append(storedir + '/' + kwargs['url'].split('/')[-1])
            
    @classmethod
    def after(cls, **kwargs):
        turl = kwargs.get('u',kwargs.get('-u',kwargs.get('--url',kwargs.get('url',None))))
        if turl is not None:
            cls._output['files'] = []
            storedir = '/home/cloo/storage_service/public/' + cls._output['cid']
            for fl in os.listdir(storedir):
                if fl.endswith('.pdf'):
                    try:
                        pcmd = [
                            'pdftotext',
                            os.path.join(storedir, fl),
                            os.path.join(storedir, fl).replace('.pdf','.txt')
                        ]
                        p = subprocess.Popen(pcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        cls._output['output'], cls._output['errors'] = p.communicate()
                    except Exception, e:
                        cls._output['output'] = {}
                        cls._output['errors'] = [str(e)]
            for fl in os.listdir(storedir):
                cls._output['files'].append(cls._output['store'] + '/' + fl)

                