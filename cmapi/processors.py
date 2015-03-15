
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
            "Any direct output from the executed command will be returned in the response object, which is always a successful return of JSON content."
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
                    cls._output['command'].append('/home/cloo/repl/apps/contentmine/src/journal-scrapers/scrapers/')
                    cls._output['command'].append('--output')
                    cls._output['command'].append('/home/cloo/storage_service/public')
                    cls._output['command'].append('--outformat')
                    cls._output['command'].append('bibjson')
        else:
            cls._output['command'].append('--help')


    @classmethod
    def after(cls, **kwargs):
        pass
        # look for a record with these details already present
        '''slug = url.replace('://','_').replace('/','_').replace(':','')
        rec = json.load(open(outputdirectory + '/' + slug + '/bib.json','r'))

        # move output to correct storage location
        for fl in os.listdir(outputdirectory + '/' + slug):
            shutil.copy(os.path.join(outputdirectory + '/' + slug, fl), outputdirectory)
        shutil.rmtree(outputdirectory + '/' + slug)'''

        
        

class Norma(Processor):
    @classmethod
    def _cmd(cls, **kwargs):
        cls._output['command'] = ['norma']
        # if no -x make it this
        # '/opt/contentmine/src/norma/src/main/resources/org/xmlcml/norma/pubstyle/nlm/toHtml.xsl'
        for key in kwargs.keys():
            if not key.startswith('-'): k = '-' + key
            if len(key) > 2: k = '-' + k
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
        # read the results and transform to object
        '''facts = []
        results_file = outputdirectory + '/' + cmd + '_results.xml'

        ns = etree.FunctionNamespace("http://www.xml-cml.org/ami")
        ns.prefix = "zf"
        tree = etree.parse(results_file)
        hits = tree.xpath('//zf:hit')
        for hit in hits:
            doc = {}
            doc["pre"] = hit.get("pre")
            doc["fact"] = hit.get("word")
            doc["post"] = hit.get("post")
            facts.append(doc)
                
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

            
