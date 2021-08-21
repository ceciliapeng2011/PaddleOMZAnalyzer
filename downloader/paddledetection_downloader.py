import os
import sys
import re
import csv
from pathlib import Path
from bs4 import BeautifulSoup
import markdown
import requests

from common import PDModelInfo
from downloader_helper import download_pdparams, scrape_pdparams
import base_downloader

class paddledetection_downloader(base_downloader.base_downloader):
    def __init__(self, homepage, filter_data_file, bool_download, result_save_path):
        super().__init__(homepage, filter_data_file, bool_download, result_save_path)

    def get_markdown_file_list(self):
        self.md_list = Path(self.homepage).glob('**/*.md')
        return self.md_list

    def get_all_pdparams_info_by_markdown_file(self):
        count_pdparams = 0
        for md_file in self.md_list:
            with open(md_file, 'r') as f:
                text = f.read()
                html_text = markdown.markdown(text)

                soup = BeautifulSoup(html_text, 'html.parser')

                tracks_pdparams = soup.find_all('a', attrs={'href': re.compile(r'\.pdparams$')}, string=re.compile(r'^((?!\().)*$'))

                if len(list(tracks_pdparams))>0:
                    # debugging
                    tracks_ymls = soup.find_all('a', attrs={'href': re.compile(r'\.yml$|\.yaml$')}, string=re.compile(r'^((?!\().)*$')) # either yml or yaml
                    # print(md_file, len(list(tracks_pdparams)), len(tracks_ymls))
                    count_pdparams += len(list(tracks_pdparams))

                    for track in tracks_pdparams:
                        track_config = track.findNext('a', attrs={'href': re.compile(r'\.yml$|\.yaml$')}, string=re.compile(r'^((?!\().)*$'))
                        if track_config is None:
                            continue # ignore

                        configs_url = '{}'.format(track_config['href'])
                        pdparams_url = '{}'.format(track['href'])
                        self.all_pdparams_urls_filtered.add((configs_url, pdparams_url))
        # print(len(self.all_pdparams_urls_filtered), count_pdparams)
        return self.all_pdparams_urls_filtered

    def pdparams_filter_and_download(self):
        with open(self.filter_data_file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                config_yaml = row[1] # configs/.../*.yml
                config_yaml = ''.join(config_yaml.split()) # remove all whitespace'
                # print(config_yaml)

                cur_pdprams_url = ''

                # find the best matcher which is highly possible to be the correct config yml.
                for (config_url, pdprams_url) in self.all_pdparams_urls_filtered:
                      if re.search(config_yaml+'$', config_url):
                        cur_pdprams_url = pdprams_url
                        self.models.append(PDModelInfo(row[0], config_yaml, cur_pdprams_url)) # possible more than one pdparams matches config yml , e.g. slim

                # second chance, to match basename only
                if not cur_pdprams_url:
                    config_base = os.path.basename(config_yaml)
                    for (config_url, pdprams_url) in self.all_pdparams_urls_filtered:
                        # print(config_yaml, config_url, re.match(config_yaml, config_url))
                        if re.search(config_base, config_url):
                            cur_pdprams_url = pdprams_url
                            self.models.append(PDModelInfo(row[0], config_yaml, cur_pdprams_url))

                # if still fail, throw exception to check scrapy rules.
                if not cur_pdprams_url:
                    print('failed to get pdparams for {}, {}'.format(row[0], config_yaml))
                    continue

            # write file and download
            if not os.path.exists(self.result_save_path):
                os.makedirs(self.result_save_path)

            result_file_name = os.path.join(self.result_save_path, "paddledet_full.csv")
            with open(result_file_name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerows(self.models)

            # download
            if self.bool_download:
                for m in self.models:
                    download_pdparams(m.pdparams, self.result_save_path)

        return self.models

if __name__ == "__main__":
    dirname = os.path.dirname(sys.argv[0])
    bool_download = 0
    if not dirname:
        dirname = ""
    if len(sys.argv) > 1:
        bool_download = 1

    filter_file_path = os.path.join(dirname, "../data/paddledet.csv")
    result_path_save_path = os.path.join(dirname, "./result/paddledet_result") 

    downloader = paddledetection_downloader("/home/huzhaoyang/Working/PaddleDetection", filter_file_path, bool_download, result_path_save_path)
    downloader.run()
