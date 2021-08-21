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

class paddleseg_downloader(base_downloader.base_downloader):
    def __init__(self, homepage, filter_data_file, bool_download, result_save_path):
        super().__init__(homepage, filter_data_file, bool_download, result_save_path)

    def get_markdown_file_list(self):
        self.md_list = Path(self.homepage).glob('**/*.md')
        return self.md_list

    def get_filter_list_from_data_file(self, data_file):
        self.all_filters = []
        with open(data_file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                config_yaml = row[1]
                config_yaml = ''.join(config_yaml.split()) # remove all whitespace
                config_base = os.path.basename(config_yaml)
                config_base = os.path.splitext(config_base)[0]
                self.all_filters.append(config_base)

    def get_all_pdparams_info_by_markdown_file(self):
        self.get_filter_list_from_data_file(self.filter_data_file)
        for md_file in self.md_list:
            with open(md_file, 'r') as f:
                text = f.read()
                html_text = markdown.markdown(text)

                soup = BeautifulSoup(html_text, 'html.parser')

                tracks_pdparams = soup.find_all('a', attrs={'href': re.compile(r'\.pdparams$')})
                if len(list(tracks_pdparams))>0:
                    for track in tracks_pdparams:
                        pdparams_url = '{}'.format(track['href'])
                        for filter_text in self.all_filters:
                            pattern = re.compile(r".*%s.*" %filter_text)
                            if pattern.match(pdparams_url):
                                self.all_pdparams_urls_filtered.add((filter_text, pdparams_url))
                                # print(filter_text, pdparams_url)
        return self.all_pdparams_urls_filtered


    def download_pdparams_file(self, file_name,  pdparams_url):
        if not os.path.exists(self.result_save_path):
            os.makedirs(self.result_save_path)

        if self.bool_download:
            file_name = os.path.join(self.result_save_path, file_name)
            # print(file_name)
            print('Downloading: {} {}'.format(file_name, pdparams_url))
            # Download the track
            r = requests.get(pdparams_url, allow_redirects=True)
            with open(file_name, 'wb') as f:
                f.write(r.content)


    def pdparams_filter_and_download(self):
        with open(self.filter_data_file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            #combine
            for row in reader:
                count = 0
                for (filter_text, pdparams_url) in self.all_pdparams_urls_filtered:
                    pattern = re.compile(r".*%s.*" %filter_text)
                    if pattern.match(row[1]):
                        count = count + 1
                        config_yaml = row[1]
                        config_yaml = ''.join(config_yaml.split()) # remove all whitespace'
                        self.models.append(PDModelInfo(row[0], config_yaml, pdparams_url))
                        #download
                        file_name = '{}.pdparams'.format(filter_text)
                        if count > 1:
                            file_name = '{}_{}.pdparams'.format(filter_text, count)

                        self.download_pdparams_file(file_name, pdparams_url)

                if not count:
                    print('failed to get pdparams for {} {}'.format(row[0], row[1]))
                    # self.models.append(PDModelInfo(row[0], row[1], "null"))

        #write file
        result_file_name = os.path.join(self.result_save_path, "paddleseg_full.csv")
        with open(result_file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(self.models)

        return self.models

if __name__ == "__main__":
    dirname = os.path.dirname(sys.argv[0])
    bool_download = 0
    if not dirname:
        dirname = ""
    if len(sys.argv) > 1:
        bool_download = 1

    filter_file_path = os.path.join(dirname, "../data/paddleseg.csv")
    result_path_save_path = os.path.join(dirname, "./result/paddleseg_result") 

    downloader = paddleseg_downloader("/home/huzhaoyang/Working/PaddleSeg", filter_file_path, bool_download, result_path_save_path)
    downloader.run()
