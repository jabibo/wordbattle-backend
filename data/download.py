import requests


def download_files(url_list, save_directory):
    for url in url_list:
        file_name = url.split("/")[-1]
        response = requests.get(url)
        with open(f"{save_directory}/{file_name}", "wb") as file:
            file.write(response.content)

save_dir = "./data/raw/"

url_list =[
    'https://clarin.bbaw.de:8088/fedora/objects/dwds:2/datastreams/xml/content'
    ,'http://wortschatz.uni-leipzig.de/Papers/top10000de.txt'
    ,'http://www1.ids-mannheim.de/fileadmin/kl/derewo/derewo-v-ww-bll-320000g-2012-12-31-1.0.zip'
    ,'http://www1.ids-mannheim.de/fileadmin/kl/derewo/DeReKo-2014-II-MainArchive-STT.100000.freq.7z'
    ,'http://www1.ids-mannheim.de/fileadmin/kl/derewo/derewo-v-ww-bll-250000g-2011-12-31-0.1.zip'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2015_3M.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2014_3M.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2010_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2009_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2008_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2007_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2006_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2005_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2004_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2003_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2002_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_2001_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_1999_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_1998_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_1997_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_1996_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_news_1995_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_web_2002_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_wikipedia_2014_3M.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_wikipedia_2010_1M-text.tar.gz'
    ,'http://corpora2.informatik.uni-leipzig.de/downloads/deu_wikipedia_2007_1M-text.tar.gz'
    ]             
download_files(url_list, save_dir)