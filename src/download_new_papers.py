# encoding: utf-8
import os
import tqdm
from bs4 import BeautifulSoup as bs
import urllib.request
import json
import datetime
import pytz
import requests
from pypdf import PdfReader, errors


def _download_new_papers(field_abbr):
    NEW_SUB_URL = f'https://arxiv.org/list/{field_abbr}/new'  # https://arxiv.org/list/cs/new
    page = urllib.request.urlopen(NEW_SUB_URL)
    soup = bs(page)
    content = soup.body.find("div", {'id': 'content'})

    # find the first h3 element in content
    h3 = content.find("h3").text   # e.g: New submissions for Wed, 10 May 23
    date = h3.replace("New submissions for", "").strip()

    dt_list = content.dl.find_all("dt")
    dd_list = content.dl.find_all("dd")
    arxiv_base = "https://arxiv.org/abs/"

    assert len(dt_list) == len(dd_list)
    new_paper_list = []
    for i in tqdm.tqdm(range(len(dt_list))):
        paper = {}
        paper_number = dt_list[i].text.strip().split(" ")[2].split(":")[-1]
        paper['main_page'] = arxiv_base + paper_number
        paper['pdf'] = arxiv_base.replace('abs', 'pdf') + paper_number

        paper['title'] = dd_list[i].find("div", {"class": "list-title mathjax"}).text.replace("Title: ", "").strip()
        paper['authors'] = dd_list[i].find("div", {"class": "list-authors"}).text \
                            .replace("Authors:\n", "").replace("\n", "").strip()
        paper['subjects'] = dd_list[i].find("div", {"class": "list-subjects"}).text.replace("Subjects: ", "").strip()
        paper['abstract'] = dd_list[i].find("p", {"class": "mathjax"}).text.replace("\n", " ").strip()
        new_paper_list.append(paper)


    #  check if ./data exist, if not, create it
    if not os.path.exists("./data"):
        os.makedirs("./data")

    # save new_paper_list to a jsonl file, with each line as the element of a dictionary
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date = date.strftime("%a, %d %b %y")
    with open(f"./data/{field_abbr}_{date}.jsonl", "w") as f:
        for paper in new_paper_list:
            f.write(json.dumps(paper) + "\n")


def get_papers(field_abbr, limit=None):
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date = date.strftime("%a, %d %b %y")
    if not os.path.exists(f"./data/{field_abbr}_{date}.jsonl"):
        _download_new_papers(field_abbr)
    results = []
    with open(f"./data/{field_abbr}_{date}.jsonl", "r") as f:
        for i, line in enumerate(f.readlines()):
            if limit and i == limit:
                return results
            results.append(json.loads(line))
    return results


def read_paper(title, pdf_url):
    if not os.path.exists("papers"):
        os.mkdir("papers")

    try:
        paper_pdf_filename = f"papers/{title}.pdf"
        paper_pdf_file = open(paper_pdf_filename, "wb")

        # Fetch the PDF content from the provided URL
        response = requests.get(pdf_url)
        response.raise_for_status()  # Check for any request errors
        
        # Save the PDF content to a file (Optional)
        paper_pdf_file.write(response.content)
        paper_pdf_file.close()
        
        # Read text from the downloaded PDF
        pdf_reader = PdfReader(paper_pdf_filename)
        print(len(pdf_reader.pages))
        print()
        
        # Extract text from each page
        pdf_text = ''
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            pdf_text += page.extract_text()

        # os.remove(paper_pdf_filename)
        # print(f"File '{title}' has been deleted.")
        return pdf_text
    
    except errors.PyPdfError as e:
        print("Error reading the PDF:", e)
        return None


if __name__ == "__main__":
    # Provide the URL of the PDF file
    pdf_url = 'https://arxiv.org/pdf/2312.04567'  # Replace this with your PDF URL
    text_from_pdf = read_paper('sample', pdf_url)

    if text_from_pdf:
        print("Text extracted from the PDF:")
        print(text_from_pdf)

