#!/bin/bash
scrapy crawl -a config="$1" -a output="$2" curse_spider
