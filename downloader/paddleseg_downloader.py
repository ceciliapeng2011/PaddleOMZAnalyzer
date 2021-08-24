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

__dir__ = os.path.dirname(os.path.abspath(__file__))
class paddleseg_downloader(base_downloader.base_downloader):
    def __init__(self, homepage, filter_data_file, bool_download, result_save_path):
        super().__init__(homepage, filter_data_file, bool_download, result_save_path)

    def get_markdown_file_list(self):
        if not os.path.exists(self.homepage):
            print('ERROR: {} directory no exist.'.format(self.homepage))
            
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
                        #print(pdparams_url)
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
                    script_file_name = os.path.join(self.homepage, "contrib/HumanSeg/export_model/download_export_model.py")
                    print(script_file_name)
                    script_file = open(script_file_name, 'r') 
                    pattern = re.compile(r".*http.*.zip")
                    for line in script_file:
                        if pattern.match(line):
                            line = line.replace('"','')
                            line = line.replace(' ','')
                            line = line.replace('\n','')
                            line = line.replace(',','')
                            config_base = os.path.basename(line)
                            config_base = os.path.splitext(config_base)[0]
                            config_base = config_base.replace('_with_softmax','')
                            pattern_two = re.compile(r".*%s.*" %config_base)
                            if pattern_two.match(row[1]):
                                config_yaml = ''.join(row[1].split()) # remove all whitespace'
                                self.models.append(PDModelInfo(row[0], config_yaml, line))
                                file_name = '{}.zip'.format(config_base)
                                self.download_pdparams_file(file_name, line)
        #write file
        result_file_name = os.path.join(__dir__, "paddleseg_full.csv")
        with open(result_file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(self.models)

        return self.models

if __name__ == "__main__":
    seg_repo_path = os.path.abspath(os.path.join(__dir__, '../../PaddleSeg'))
    bool_download = 1

    filter_file_path = os.path.join(__dir__, "../data/paddleseg.csv")
    result_path_save_path = os.path.join(__dir__, "./paddleseg")

    downloader = paddleseg_downloader(seg_repo_path, filter_file_path, bool_download, result_path_save_path)
    downloader.run()
