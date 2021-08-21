import os
import sys
import re
import csv
from pathlib import Path
from bs4 import BeautifulSoup
import markdown
import requests

from common import PDModelInfo
import base_downloader
from downloader_helper import download_pdparams, scrape_pdparams

class paddleclas_downloader(base_downloader.base_downloader):
    def __init__(self, homepage, filter_data_file, bool_download, result_save_path):
        super().__init__(homepage, filter_data_file, bool_download, result_save_path)

    def get_markdown_file_list(self):
        self.md_list.append(self.homepage)
        return self.md_list

    def get_all_pdparams_info_by_markdown_file(self):
        for md_file in self.md_list:
            tracks = scrape_pdparams(md_file)
            for track in tracks:
                track_url = '{}'.format(track['href'])
                track_title = track.text.strip().replace('/', '-')
                self.all_pdparams_urls_filtered.add((track_title, track_url))

        return self.all_pdparams_urls_filtered

    def pdparams_filter_and_download(self):
        with open(self.filter_data_file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                config_yaml = row[1]
                config_yaml = ''.join(config_yaml.split()) # remove all whitespace
                config_base = os.path.basename(config_yaml)
                config_base = os.path.splitext(config_base)[0]
                pdprams_url = ''

                for (track_title, track_url) in self.all_pdparams_urls_filtered:
                    # search title for the first chance
                    if re.match(config_base+'$', track_title):
                        pdprams_url = track_url
                        #print(config_yaml, track_title, pdprams_url)
                        break

                if not pdprams_url:
                    # search title for second chance
                    for (track_title, track_url) in self.all_pdparams_urls_filtered:
                        if re.search(config_base, track_url):
                            pdprams_url = track_url
                            break

                # if still fail, throw exception to check scrapy rules.
                if not pdprams_url:
                    print('failed to get pdparams for {} {}'.format(row[0], config_yaml))

                self.models.append(PDModelInfo(row[0], config_yaml, pdprams_url))

            # write file and download
            if not os.path.exists(self.result_save_path):
                os.makedirs(self.result_save_path)

            result_file_name = os.path.join(self.result_save_path, "paddleclas_full.csv")
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

    filter_file_path = os.path.join(dirname, "../data/paddleclas.csv")
    result_path_save_path = os.path.join(dirname, "./result/paddleclas_result") 
        
    downloader = paddleclas_downloader("https://github.com/PaddlePaddle/PaddleClas/blob/release/2.2/docs/zh_CN/models/models_intro.md", filter_file_path, bool_download, result_path_save_path)
    downloader.run()
