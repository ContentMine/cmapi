from lxml import etree

class Translator(object):
    
    def __init__(self, processor):
        self.processor = processor
        
    def translate(self, fl):
        return getattr(self, '_%s' % self.processor)(fl)
        
    def _amispecies(self, fl):
        output = []
        tree = etree.parse(fl)
        results = tree.xpath('//result')
        for result in results:
            doc = {}
            doc["pre"] = result.get("pre")
            doc["exact"] = result.get("exact")
            doc["fact"] = result.get("match")
            doc["post"] = result.get("post")
            doc["name"] = result.get("name")
            output.append(doc)
        return output

    def _amiidentifier(self, fl):
        output = []
        tree = etree.parse(fl)
        results = tree.xpath('//result')
        for result in results:
            doc = {}
            doc["pre"] = result.get("pre")
            doc["fact"] = result.get("exact")
            doc["post"] = result.get("post")
            output.append(doc)
        return output

    def _amiregex(self, fl):
        output = []    
        tree = etree.parse(fl)
        #results = tree.xpath('//zf:result')
        results = tree.xpath('//result')
        for result in results:
            doc = {}
            doc["pre"] = result.get("pre")
            doc["fact"] = result.get("value0")
            doc["post"] = result.get("post")
            output.append(doc)
        return output

    
