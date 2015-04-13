
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

import uuid, subprocess, os, shutil, json, requests, time
from lxml import etree
from flask import current_app


class Processor(object):
    def __init__(self):
        self.output = {
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
    
    def _cmd(self, **kwargs):
        self.output['command'] = []
        for key in kwargs.keys():
            k = key
            if not key.startswith('-'): k = '-' + k
            if len(key) > 2: k = '-' + k
            self.output['command'].append(k)
            self.output['command'].append(kwargs[key])
    
    def before(self, **kwargs):
        pass
    
    def after(self, **kwargs):
        pass
    
    def meta(self):
        return {} # a method to return any metadata that may be needed by UI to build user options
        
    def run(self, before=True,after=True,store=True,save=True,**kwargs):
        # check for dodgy characters in the kwargs
        if 'callback' in kwargs: del kwargs['callback']
        if '_' in kwargs: del kwargs['_']
        for k in kwargs.keys():
            if ';' in k or ';' in kwargs[k]:
                self.output['errors'] = ['Sorry, illegal character found in args.']
                return self.output
        if before: self.before(**kwargs)
        self._cmd(**kwargs)
        try:
            p = subprocess.Popen(self.output['command'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.output['output'], self.output['errors'] = p.communicate()
        except Exception, e:
            self.output['output'] = {}
            self.output['errors'] = [str(e)]
        if after: self.after(**kwargs)
        if not isinstance(self.output['errors'],dict) and not isinstance(self.output['errors'],list):
            self.output['errors'] = [i for i in self.output['errors'].split('\n') if len(i) > 0]
        if not isinstance(self.output['output'],dict) and not isinstance(self.output['output'],list) and '\n' in self.output['output']:
            self.output['output'] = [i for i in self.output['output'].split('\n') if len(i) > 0]
        return self.output

    

        
class Quickscrape(Processor):
    def _cmd(self, **kwargs):
        self.output['command'] = ['quickscrape']
        if len(kwargs) > 0:
            for key in kwargs.keys():
                k = key
                if not key.startswith('-'): k = '-' + k
                if len(key) > 2: k = '-' + k
                if k not in ['-d','--scraperdir','-o','--output','-f','--outformat']:
                    self.output['command'].append(k)
                    self.output['command'].append(kwargs[key])
            self.output['command'].append('--scraperdir')
            self.output['command'].append(current_app.config['QS_JS_DIR'])
            self.output['command'].append('--output')
            self.output['command'].append(current_app.config['QS_TMP_DIR'])
            self.output['command'].append('--outformat')
            self.output['command'].append('bibjson')
        else:
            self.output['command'].append('--help')


    def after(self, **kwargs):
        turl = kwargs.get('u',kwargs.get('-u',kwargs.get('--url',kwargs.get('url',None))))
        if turl is not None:
            slug = turl.replace('://','_').replace('/','_').replace(':','')
            self.output['cid'] = kwargs.get('cid',uuid.uuid4().hex)
            self.output['store'] = 'http://store.cottagelabs.com/' + self.output['cid']
            self.output['files'] = []
            tmpdir = current_app.config['QS_TMP_DIR'] + slug
            outdir = current_app.config['STORAGE_DIR'] + self.output['cid']
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            for fl in os.listdir(tmpdir):
                shutil.copy(os.path.join(tmpdir, fl), outdir)
                self.output['files'].append(self.output['store'] + '/' + fl)
                '''if fl == 'bib.json':
                    try:
                        self.output['bibjson'] = json.load(open(tmpdir + '/' + fl))
                    except:
                        pass'''
            shutil.rmtree(tmpdir)

        
        

class Norma(Processor):
    def _cmd(self, **kwargs):
        self.output['command'] = ['norma']
        if len(kwargs.keys()) > 0 and 'x' not in kwargs.keys() and '-x' not in kwargs.keys() and 'xsl' not in kwargs.keys() and '--xsl' not in kwargs.keys() and 'x' not in kwargs.keys():
            #self.output['command'].append('--xsl')
            #self.output['command'].append('/org/xmlcml/norma/pubstyle/nlm/toHtml.xsl')
            self.output['command'].append('-x')
            self.output['command'].append('nlm2html')
        for key in kwargs.keys():
            k = key
            if not key.startswith('-'): k = '-' + k
            if len(key) > 2: k = '-' + k
            if k == '--cid':                            
                self.output['cid'] = kwargs[key]
                self.output['command'].append('-q')
                self.output['command'].append(current_app.config['STORAGE_DIR'] + str(kwargs[key]))
                self.output['command'].append('--input')
                self.output['command'].append('fulltext.xml')
                self.output['command'].append('--output')
                self.output['command'].append('scholarly.html')
            else:
                self.output['command'].append(k)
                self.output['command'].append(kwargs[key])

    def after(self, **kwargs):
        if kwargs.get('cid',False):
            self.output['store'] = 'http://store.cottagelabs.com/' + self.output['cid']
            self.output['files'] = []
            dr = current_app.config['STORAGE_DIR'] + self.output['cid']
            listfiles = os.listdir(dr)
            for fl in listfiles:
                if 'scholarly.html' not in listfiles and fl.lower().endswith('.html'):
                    shutil.copy(os.path.join(dr, fl), os.path.join(dr, 'scholarly.html'))
                    self.output['transposed'] = fl
                    self.output['shtml'] = self.output['store'] + '/scholarly.html'
                self.output['files'].append(self.output['store'] + '/' + fl)
            if 'scholarly.html' in listfiles:
                self.output['shtml'] = self.output['store'] + '/scholarly.html'

'''how many -x are there? is there a list? - look in stylesheetbyname.xml
/norma/src/main/resources ... /org/xmlcml/norma/pubstyle/stylesheetByName.xml
<stylesheetList>
  <stylesheet name="nlm2html">/org/xmlcml/norma/pubstyle/nlm/toHtml.xsl</stylesheet>
  <stylesheet name="bmc2html">/org/xmlcml/norma/pubstyle/bmc/xml2html.xsl</stylesheet>
  <stylesheet name="hind2xml">/org/xmlcml/norma/pubstyle/hindawi/groupMajorSections.xsl</stylesheet>
</stylesheetList>'''

            
class Amiregex(Processor):
    def meta(self):
        # TODO: this should be set by app config...
        r = {'regexes':[]}
        try:
            for fl in os.listdir(current_app.config['REGEXES_DIR']):
                r['regexes'].append(fl.replace('.xml',''))
        except:
            pass
        return r
        
    def _cmd(self, **kwargs):
        self.output['command'] = ['/usr/bin/ami2-regex']
        if 'r.r' not in kwargs.keys() and '-r.r' not in kwargs.keys() and '--r.regex' not in kwargs.keys():
            self.output['command'].append('-r.r')
            self.output['command'].append(current_app.config['REGEXES_DIR'] + 'concatenated.xml')
            self.output['regex'] = 'concatenated'
        for key in kwargs.keys():
            k = key
            if not key.startswith('-'): k = '-' + k
            if len(key) > 2 and key != '-r.r': k = '-' + k
            if k == '--cid':
                self.output['cid'] = kwargs[key]
                self.output['command'].append('-q')
                self.output['command'].append(current_app.config['STORAGE_DIR'] + str(kwargs[key]))
                self.output['command'].append('--input')
                self.output['command'].append('scholarly.html')
                #self.output['command'].append('--output')
                #self.output['command'].append('results')
            elif k in ['-r.r','--r.regex']:
                self.output['command'].append('-r.r')
                if kwargs[key].startswith('http'):
                    self.output['command'].append(kwargs[key])
                else:
                    self.output['command'].append(current_app.config['REGEXES_DIR'] + kwargs[key] + '.xml')
                self.output['regex'] = kwargs[key]
            else:
                self.output['command'].append(k)
                self.output['command'].append(kwargs[key])
            
            
    def after(self, **kwargs):
        self.output['facts'] = []
        if 'cid' in self.output:
            results_file = current_app.config['STORAGE_DIR'] + self.output['cid'] + '/results/regex/' + self.output['regex'] + '/results.xml'
            #ns = etree.FunctionNamespace("http://www.xml-cml.org/ami")
            #ns.prefix = "zf"
            counter = 0
            success = False
            while counter < 4 and not success:
                try:
                    tree = etree.parse(results_file)
                    #results = tree.xpath('//zf:result')
                    results = tree.xpath('//result')
                    for result in results:
                        doc = {}
                        doc["pre"] = result.get("pre")
                        doc["fact"] = result.get("value0")
                        doc["post"] = result.get("post")
                        self.output['facts'].append(doc)
                    success = True
                except:
                    counter += 1
                    time.sleep(10)
        self.output['factcount'] = len(self.output['facts'])

        
class Amispecies(Processor):
    def _cmd(self, **kwargs):
        self.output['command'] = ['/usr/bin/ami2-species']
        for key in kwargs.keys():
            k = key
            if not key.startswith('-'): k = '-' + k
            if len(key) > 2: k = '-' + k
            if k == '--cid':
                self.output['cid'] = kwargs[key]
                self.output['command'].append('-q')
                self.output['command'].append(current_app.config['STORAGE_DIR'] + str(kwargs[key]))
                self.output['command'].append('--input')
                self.output['command'].append('scholarly.html')
                self.output['command'].append('--sp.species')
                self.output['command'].append('--context')
                self.output['command'].append('35')
                self.output['command'].append('50')
                self.output['command'].append('--sp.type')
                self.output['command'].append('binomial')
                self.output['command'].append('genus')
                self.output['command'].append('genussp')
            else:
                self.output['command'].append(k)
                self.output['command'].append(kwargs[key])

    def after(self, **kwargs):
        self.output['facts'] = []
        if 'cid' in self.output:
            for tp in ['binomial','genus','genussp']:
                results_file = current_app.config['STORAGE_DIR'] + self.output['cid'] + '/results/species/' + tp + '/results.xml'
                counter = 0
                success = False
                while counter < 4 and not success:
                    try:
                        tree = etree.parse(results_file)
                        results = tree.xpath('//result')
                        for result in results:
                            doc = {}
                            doc["pre"] = result.get("pre")
                            doc["exact"] = result.get("exact")
                            doc["fact"] = result.get("name")
                            doc["post"] = result.get("post")
                            doc["name"] = result.get("name")
                            self.output['facts'].append(doc)
                        success = True
                    except:
                        counter += 1
                        time.sleep(10)
        self.output['factcount'] = len(self.output['facts'])

        
'''        
class Amiword(Processor):
    def _cmd(self, **kwargs):
        self.output['command'] = ['/usr/bin/ami2-word']
        for key in kwargs.keys():
            k = key
            if not key.startswith('-'): k = '-' + k
            if len(key) > 2: k = '-' + k
            if k == '--cid':
                self.output['cid'] = kwargs[key]
                self.output['command'].append('-q')
                self.output['command'].append(current_app.config['STORAGE_DIR'] + str(kwargs[key]))
                self.output['command'].append('--input')
                self.output['command'].append('scholarly.html')
            else:
                self.output['command'].append(k)
                self.output['command'].append(kwargs[key])

                                
class Amisequence(Processor):
    def _cmd(self, **kwargs):
        self.output['command'] = ['/usr/bin/ami2-sequence']
        for key in kwargs.keys():
            k = key
            if not key.startswith('-'): k = '-' + k
            if len(key) > 2: k = '-' + k
            if k == '--cid':
                self.output['cid'] = kwargs[key]
                self.output['command'].append('-q')
                self.output['command'].append(current_app.config['STORAGE_DIR'] + str(kwargs[key]))
                self.output['command'].append('--input')
                self.output['command'].append('scholarly.html')
            else:
                self.output['command'].append(k)
                self.output['command'].append(kwargs[key])

                
class Amiidentifier(Processor):
    def _cmd(self, **kwargs):
        self.output['command'] = ['/usr/bin/ami2-identifier']
        for key in kwargs.keys():
            k = key
            if not key.startswith('-'): k = '-' + k
            if len(key) > 2: k = '-' + k
            if k == '--cid':
                self.output['cid'] = kwargs[key]
                self.output['command'].append('-q')
                self.output['command'].append(current_app.config['STORAGE_DIR'] + str(kwargs[key]))
                self.output['command'].append('--input')
                self.output['command'].append('scholarly.html')
            else:
                self.output['command'].append(k)
                self.output['command'].append(kwargs[key])
'''

            
class Retrieve(Processor):
    def _cmd(self, **kwargs):
        self.output['command'] = ['curl']
        if len(kwargs) > 0:
            self.output['cid'] = kwargs.get('cid',uuid.uuid4().hex)
            self.output['store'] = 'http://store.cottagelabs.com/' + self.output['cid']
            storedir = current_app.config['STORAGE_DIR'] + self.output['cid']
            if not os.path.exists(storedir):
                os.makedirs(storedir)
            self.output['command'].append('-X')
            self.output['command'].append('GET')
            if 'url' in kwargs.keys():
                self.output['command'].append(kwargs['url'])
                self.output['command'].append('-o')
                self.output['command'].append(storedir + '/' + kwargs['url'].split('/')[-1])
            
    def after(self, **kwargs):
        turl = kwargs.get('url',None)
        if turl is not None:
            fn = turl.split('/')[-1]
            self.output['files'] = []
            self.output['retrieved'] = self.output['store'] + '/' + fn
            storedir = current_app.config['STORAGE_DIR'] + self.output['cid']
            if fn.lower().endswith('pdf'):
                try:
                    pcmd = [
                        'pdftotext',
                        '-nopgbrk',
                        os.path.join(storedir, fn),
                        os.path.join(storedir, 'unpdf.txt')
                    ]
                    p = subprocess.Popen(pcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.output['output'], self.output['errors'] = p.communicate()
                    if len(self.output['errors']) == 0:
                        self.output['unpdf'] = self.output['store'] + '/unpdf.txt'
                except Exception, e:
                    self.output['output'] = {}
                    self.output['errors'] = [str(e)]
                    print self.output
            txt = None
            time.sleep(5)
            flsa = os.listdir(storedir)
            for fy in flsa:
                if fy.endswith('.txt'): txt = fy
            if txt is not None:
                xfer = True
                for fa in flsa:
                    if fy.endswith('.html'): xfer = False
                if xfer:
                    new = '<html><head></head><body><p>'
                    content = open(os.path.join(storedir, txt),'r')
                    outofpara = False
                    for line in content.readlines():
                        if len(line.strip().rstrip('\n')) == 0:
                            if not outofpara:
                                new += '</p>\n\n'
                                outofpara = True
                        else:
                            if outofpara:
                                new += '<p>'
                                outofpara = False
                            new += line.rstrip('\n')
                    content.close()
                    new += '</p></body></html>'
                    nf = open(storedir + '/fulltext.html','w')
                    nf.write(new)
                    nf.close()
                    self.output['txt2html'] = storedir + '/fulltext.html'
            fls = os.listdir(storedir)
            for f in fls:
                if 'fulltext.pdf' not in fls and f.lower().endswith('.pdf'):
                    shutil.copy(os.path.join(storedir, f), os.path.join(storedir, 'fulltext.pdf'))
                if 'fulltext.html' not in fls and f.lower().endswith('.html'):
                    shutil.copy(os.path.join(storedir, f), os.path.join(storedir, 'fulltext.html'))
                if 'fulltext.xml' not in fls and f.lower().endswith('.xml'):
                    shutil.copy(os.path.join(storedir, f), os.path.join(storedir, 'fulltext.xml'))
            for fl in os.listdir(storedir):
                self.output['files'].append(self.output['store'] + '/' + fl)

                