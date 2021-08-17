from abc import ABCMeta, abstractmethod

class base_downloader(object):
    __metaclass__ = ABCMeta

    def __init__(self, homepage, filter_data_file, bool_download, result_save_path):
        """
        use homepage information, get all target markdown file list
        store the list in self.md_list and return it.
        """
        self.homepage = homepage
        self.filter_data_file = filter_data_file
        self.bool_download = bool_download
        self.result_save_path = result_save_path
        self.md_list = []
        self.all_pdparams_urls_filtered = set(()) #set((key, url))
        self.models = [] #PDModelInfo list

    @abstractmethod
    def get_markdown_file_list(self):
        """
        use homepage information, get all target markdown files and
        store these filepath to self.md_list, then return it.
        """
        return self.md_list

    @abstractmethod
    def get_all_pdparams_info_by_markdown_file(self):
        """
        loop process markdown file in the self.md_list to
        get all target pdparams file link, and use a key to map it.
        store these information in
        self.all_pdparams_urls_filtered = set((key, url))
        then return it.
        """
        return self.all_pdparams_urls_filtered

    @abstractmethod
    def pdparams_filter_and_download(self):
        """
        process the self.all_pdparams_urls_filtered
        combine these information and data file to get
        a result model list store to self.models and write it to file,
        download depend on bool_download param
        then return self.models
        """
        return self.models


    def run(self):
        self.get_markdown_file_list()
        self.get_all_pdparams_info_by_markdown_file()
        self.pdparams_filter_and_download()
