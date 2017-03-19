import scrapy
from io import BytesIO
from shutil import rmtree
from os import path, getcwd
from subprocess import call
from zipfile import ZipFile
from time import localtime, strftime

_debug_mode_ = False

class QuotesSpider(scrapy.Spider):
	name = "curse_spider"
	handle_httpstatus_list = [302]
	
	def time_stamp(self): return strftime("[%H:%M:%S]", localtime())

	def dprint(self, data='', force=False):
		if data == '': return
		global _debug_mode_
		if (force == True) or (_debug_mode_ ==True): print(self.time_stamp() + " - " + data)

	def fatality(self, finishingmove):
		self.dprint(finishingmove, True)
		raise

	def start_requests(self):
		cfile = getattr(self, 'config', None)
		apath = getattr(self, 'output', None)
		if ((apath is None) or (not path.isdir(apath))): self.fatality('Error: Output path does not exist!')
		self.odir = path.abspath(apath)
		urls = []
		self.dprint('Reading config file: ' + cfile, True)
		try:
			cdata = open(cfile)
			for conf in cdata:
				if (conf[:4] == 'http'):
					urls.append(conf[:-1])
			cdata.close()
		except: raise
		for url in urls:
			self.dprint("Found addon URL: " + url)
			yield scrapy.Request(url, self.parse, dont_filter=True)			
			
	def parse(self, response):
		if (response.status >= 300) and (response.status < 400):
			redir = response.css('a::attr(href)').extract_first()
			self.dprint("Found redirect: " + redir)
			yield scrapy.Request(redir, self.parse, dont_filter=True)
		elif response.status == 200:
			if response.url[-4:].lower() == '.zip':
				dfile = path.join(self.odir, response.url.split("/")[-1])
				self.dprint("Found zip file: " + dfile)
				z = ZipFile(BytesIO(response.body))
				self.dprint('Testing: ' + dfile)
				if z.testzip() is not None: self.fatality('Error: ' + dfile + ' is corrupted!')
				self.dprint("Extracting: " + dfile + " -> " + self.odir)
				z.extractall(self.odir)
				z.close()
				self.dprint('Finished: ' + dfile + ' -> ' + self.odir, True)
			else:
				dlink = response.css('div.countdown a::attr(data-href)').extract_first()
				self.dprint("Found download link: " + dlink)
				yield scrapy.Request(dlink, self.parse)
		
