import os, copy

from io import BytesIO

from typing import Dict, List

from multiprocessing import Process

from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

from requests import Response
import requests

import time


class ChapterJson:

    def __init__(self, response: Response):
        
        jsonlike = response.json()["readableProduct"]

        self.title = jsonlike["title"]
        self.is_public = jsonlike["isPublic"]
        self.inner_id = jsonlike["number"]

        self.pages_list = jsonlike["pageStructure"]["pages"] if self.is_public else []

        self.next_chapter_url = (jsonlike["nextReadableProductUri"] 
            if "nextReadableProductUri" in jsonlike else None)
        self.prev_chapter_url = (jsonlike["prevReadableProductUri"]
            if "prevReadableProductUri" in jsonlike else None)


def image_recovery(image_list: List[JpegImageFile]) -> List[JpegImageFile]:

    frag_wid, frag_hei = [208, 296]
    new_image_list: List[JpegImageFile] = []

    for image in image_list:

        new_image = copy.copy(image)

        for j in range(4):
            for k in range(4):
                new_image.paste(image.crop((frag_wid*j, frag_hei*k, frag_wid*(j+1), frag_hei*(k+1))), (frag_wid*k, frag_hei*j))
                new_image.paste(image.crop((frag_wid*k, frag_hei*j, frag_wid*(k+1), frag_hei*(j+1))), (frag_wid*j, frag_hei*k))

        new_image_list.append(new_image)

    return new_image_list


def shonenjump_parser(chapter_url: str, destination: str, dir_name: str) -> int:

    start_time = time.time()

    if not os.path.isdir(destination):
        print("Error: directory does not exist")
        return -1

    q_for_execution: List[Process] = []
    process_list: List[[Process, int]] = []

    workers_number = 4

    is_worker_busy_list = []
    for _ in range(workers_number):
        is_worker_busy_list.append(False)

    prev_chapter_url, next_chapter_url, pages_list, inner_id, is_public = _parse_performer(chapter_url + ".json")

    destination += f"/{dir_name}"

    if not os.path.isdir(destination):
        os.makedirs(destination)

    if is_public:
        q_for_execution.append(Process(target=convert_to_pdf, args=(pages_list, destination + "/chapter-" + str(inner_id) + ".pdf")))

    process_arbitrage(q_for_execution, process_list, is_worker_busy_list)

    left_end = False
    right_end = False

    if prev_chapter_url is not None:
        task_1 = _parse_performer(prev_chapter_url + ".json", direction="left")
    else:
        left_end = True

    if next_chapter_url is not None:
        task_2 = _parse_performer(next_chapter_url + ".json", direction="right")
    else:
        right_end = True

    while True:

        if not left_end:
            prev_chapter_url, _, pages_list, inner_id, is_public = task_1
        if is_public and not left_end:
            q_for_execution.append(Process(target=convert_to_pdf, args=(pages_list, destination + "/chapter-" + str(inner_id) + ".pdf")))
        
        left_end = True if prev_chapter_url is None else False
        if not left_end:
            task_1 = _parse_performer(prev_chapter_url + ".json", direction="left")
            print(prev_chapter_url)
    
        if not right_end:
            _, next_chapter_url, pages_list, inner_id, is_public = task_2
        if is_public and not right_end:
            q_for_execution.append(Process(target=convert_to_pdf, args=(pages_list, destination + "/chapter-" + str(inner_id) + ".pdf")))

        right_end = True if next_chapter_url is None else False
        if not right_end:
            task_2 = _parse_performer(next_chapter_url + ".json", direction="right")
            print(next_chapter_url)

        process_arbitrage(q_for_execution, process_list, is_worker_busy_list)
        
        if left_end and right_end:
            print(f"indexing is over: {time.time() - start_time}")
            break

    while len(q_for_execution) != 0:
        process_arbitrage(q_for_execution, process_list, is_worker_busy_list)

    [(process[0].join() if process is not None else None) for process in process_list]

    return 0


def _parse_performer(ful_url: str, direction: str = None) -> ( str, str, List[Dict[int, List[Dict[str, str]]]], int, bool):

    HEADERS: Dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    raw_json: Response = requests.get(ful_url, headers=HEADERS)
    chapter_json = ChapterJson(raw_json)

    return (chapter_json.prev_chapter_url, chapter_json.next_chapter_url, chapter_json.pages_list, chapter_json.inner_id, chapter_json.is_public)


def process_arbitrage(q_for_execution: List[Process], process_list: List[[Process, int]], is_worker_busy_list: List[bool]) -> None:

    for i in range(len(process_list)):
        if process_list[i] is None:
            continue

        if not process_list[i][0].is_alive() and len(process_list) != 0:
            is_worker_busy_list[process_list[i][1]] = False
            process_list[i] = None

    for i in range(len(is_worker_busy_list)):
        if not is_worker_busy_list[i] and len(q_for_execution) != 0:
            is_worker_busy_list[i] = True
            tmp = q_for_execution.pop()
            tmp.start()
            process_list.append((tmp, i))


def convert_to_pdf(pages_list: List[Dict[int, List[Dict[str, str]]]], path_and_name: str):

    images: List[JpegImageFile] = []

    for page in pages_list:

        if page["type"] != "main":
            continue

        cur_image = requests.get(page["src"])
        images.append(Image.open(BytesIO(cur_image.content)))

    recovered_images: List[JpegImageFile] = image_recovery(images)

    pdf = canvas.Canvas(path_and_name, pagesize=letter)
    pdf.setPageSize((836, 1200))

    for image in recovered_images:
        pdf.drawImage(ImageReader(image), 0, 0)
        pdf.showPage()

    pdf.save()











# import os, copy, asyncio

# from io import BytesIO

# from typing import Dict, List

# from multiprocessing import Process

# from PIL import Image
# from PIL.JpegImagePlugin import JpegImageFile

# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.utils import ImageReader

# from requests import Response
# import requests

# import time


# class ChapterJson:

#     def __init__(self, response: Response):
        
#         jsonlike = response.json()["readableProduct"]

#         self.title = jsonlike["title"]
#         self.is_public = jsonlike["isPublic"]
#         self.inner_id = jsonlike["number"]

#         self.pages_list = jsonlike["pageStructure"]["pages"] if self.is_public else []

#         self.next_chapter_url = (jsonlike["nextReadableProductUri"] 
#             if "nextReadableProductUri" in jsonlike else None)
#         self.prev_chapter_url = (jsonlike["prevReadableProductUri"]
#             if "prevReadableProductUri" in jsonlike else None)


#     @staticmethod
#     def image_recovery(image_list: List[JpegImageFile]) -> List[JpegImageFile]:

#         frag_wid, frag_hei = [208, 296]
#         new_image_list: List[JpegImageFile] = []

#         for image in image_list:

#             new_image = copy.copy(image)

#             for j in range(4):
#                 for k in range(4):
#                     new_image.paste(image.crop((frag_wid*j, frag_hei*k, frag_wid*(j+1), frag_hei*(k+1))), (frag_wid*k, frag_hei*j))
#                     new_image.paste(image.crop((frag_wid*k, frag_hei*j, frag_wid*(k+1), frag_hei*(j+1))), (frag_wid*j, frag_hei*k))

#             new_image_list.append(new_image)

#         return new_image_list


# async def shonenjump_parser(chapter_url: str, destination: str) -> int:

#     SEARCH_URL: str = "https://shonenjumpplus.com/episode/"

#     start_time = time.time()

#     if not os.path.isdir(destination):
#         print("Error: directory does not exist")
#         return -1

#     q_for_execution: List[Process] = []
#     process_list: List[[Process, int]] = []

#     workers_number = 4

#     is_worker_busy_list = []
#     for _ in range(workers_number):
#         is_worker_busy_list.append(False)

#     task_result = await asyncio.create_task(_parse_performer(chapter_url + ".json"))

#     destination += f"/{task_result[3]}"

#     if not os.path.isdir(destination):
#         os.makedirs(destination)

#     p = Process(target=convert_to_pdf, args=(task_result[2], destination + "/chapter-" + str(task_result[3]) + ".pdf"))
#     q_for_execution.append(p)

#     process_arbitrage(q_for_execution, process_list, is_worker_busy_list)

#     left_end = False
#     right_end = False

#     task_1 = asyncio.create_task(_parse_performer(task_result[0] + ".json", direction="left"))
#     task_2 = asyncio.create_task(_parse_performer(task_result[1] + ".json", direction="right"))

#     while True:

#         prev_chapter_url, _, pages_list, inner_id = await task_1
#         left_end = True if prev_chapter_url is None else False
#         q_for_execution.append(Process(target=convert_to_pdf, args=(pages_list, destination + "/chapter-" + str(inner_id) + ".pdf")))
#         if not left_end:
#             task_1 = asyncio.create_task(_parse_performer(prev_chapter_url + ".json", direction="left"))
#             print(prev_chapter_url)
    
#         _, next_chapter_url, pages_list, inner_id = await task_2
#         right_end = True if next_chapter_url is None else False
#         q_for_execution.append(Process(target=convert_to_pdf, args=(pages_list, destination + "/chapter-" + str(inner_id) + ".pdf")))
#         if not right_end:
#             task_2 = asyncio.create_task(_parse_performer(next_chapter_url + ".json", direction="right"))
#             print(next_chapter_url)


#         process_arbitrage(q_for_execution, process_list, is_worker_busy_list);
        
#         if left_end and right_end:
#             print(f"indexing is over: {time.time() - start_time}")
#             break

#     return 0


# async def _parse_performer(ful_url: str, direction: str = None) -> ( str, str, List[Dict[int, List[Dict[str, str]]]], int):

#     HEADERS: Dict[str, str] = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
#     }
    
#     raw_json: Response = requests.get(ful_url, headers=HEADERS)
#     chapter_json = ChapterJson(raw_json)

#     return (chapter_json.prev_chapter_url, chapter_json.next_chapter_url, chapter_json.pages_list, chapter_json.inner_id)


# def process_arbitrage(q_for_execution: List[Process], process_list: List[[Process, int]], is_worker_busy_list: List[bool]) -> None:

#     for i in range(len(process_list)):
#         if process_list[i] is None:
#             continue

#         if not process_list[i][0].is_alive() and len(process_list) != 0:
#             is_worker_busy_list[process_list[i][1]] = False
#             process_list[i] = None

#     for i in range(len(is_worker_busy_list)):
#         if not is_worker_busy_list[i] and len(q_for_execution) != 0:
#             is_worker_busy_list[i] = True
#             tmp = q_for_execution.pop()
#             tmp.start()
#             process_list.append((tmp, i))

#     return (q_for_execution, process_list)



# def convert_to_pdf(pages_list: List[Dict[int, List[Dict[str, str]]]], path_and_name: str):

#     images: List[JpegImageFile] = []

#     for page in pages_list:

#         if page["type"] != "main":
#             continue

#         cur_image = requests.get(page["src"])
#         images.append(Image.open(BytesIO(cur_image.content)))

#     recovered_images: List[JpegImageFile] = ChapterJson.image_recovery(images)

#     pdf = canvas.Canvas(path_and_name, pagesize=letter)
#     pdf.setPageSize((836, 1200))

#     for image in recovered_images:
#         pdf.drawImage(ImageReader(image), 0, 0)
#         pdf.showPage()

#     pdf.save()










# from typing import Dict, List

# from io import BytesIO

# import copy, os

# from multiprocessing import Process

# import requests, time

# from bs4 import BeautifulSoup

# from PIL import Image
# from PIL.JpegImagePlugin import JpegImageFile

# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.utils import ImageReader


# searchurl: str = "https://shonenjumpplus.com/episode/"
# headers: Dict[str, str] = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
# }


# def imgrecovery(imglist: List[JpegImageFile]) -> List[JpegImageFile]:

#     frag_wid, frag_hei = [208, 296]
#     newimglist: List[JpegImageFile] = []

#     for img in imglist:

#         newimg = copy.copy(img)

#         for j in range(4):
#             for k in range(4):
#                 newimg.paste(img.crop((frag_wid*j, frag_hei*k, frag_wid*(j+1), frag_hei*(k+1))), (frag_wid*k, frag_hei*j))
#                 newimg.paste(img.crop((frag_wid*k, frag_hei*j, frag_wid*(k+1), frag_hei*(j+1))), (frag_wid*j, frag_hei*k))

#         newimglist.append(newimg)

#     return newimglist


# def chapterparser(chapid: str, pages: List[str], pathandname: str) -> None:

#     images: List[JpegImageFile] = []

#     for i in range(0, len(pages)):

#         curpage = pages[i]

#         if curpage["type"] != "main":
#             continue

#         curimg = requests.get(curpage["src"])
#         images.append(Image.open(BytesIO(curimg.content)))

#     imgforpdf: List[JpegImageFile] = imgrecovery(images)

#     pdf = canvas.Canvas(pathandname, pagesize=letter)
#     pdf.setPageSize((836, 1200))

#     for img in imgforpdf:
#         pdf.drawImage(ImageReader(img), 0, 0)
#         pdf.showPage()

#     pdf.save()

#     print(f"Chapter {chapid} is done")

#     return None


# def allchaptersparser(stpoint: str, tarpath: str) -> None:
    
#     processes: List[Process] = []
#     indexed: List[str] = []

#     start_time = time.time()

#     for arrow in ["prevReadableProductUri", "nextReadableProductUri"]:

#         epid: str = stpoint

#         while True:
        
#             print(f"current: {epid}")
        
#             gottenjson: requests.Response = requests.get(searchurl + epid + ".json", headers=headers)

#             if (sc := gottenjson.status_code) != 200:
#                 print(f"Page get error! (status code: {sc}, episode id: {epid})")
#                 break

#             epjson = gottenjson.json()

#             chapinfo: Dict[str, str] = {
#                 "isPublic": "False",
#                 "title": "unknown",
#                 "number": "0"
#             }

#             for jsonkey in chapinfo.keys():

#                 try:
#                     chapinfo[jsonkey] = str(epjson["readableProduct"][jsonkey])

#                 except KeyError:
#                     print(f"Key error! (key \"{jsonkey}\" not found)")
#                     break

#             line_wid = len(line_cont := f"{chapinfo["title"]}, ep: {chapinfo["number"]}, is_pub: {chapinfo["isPublic"]}")
#             print(line_cont + "\n" + "=" * line_wid)

#             if os.path.exists(pathandname := tarpath + f"/chapter-{chapinfo["number"]}.pdf"):
#                 if (fulid := epjson["readableProduct"][arrow]) is not None:
#                     epid = fulid.split("/")[-1]
#                 else:
#                     break

#                 continue

#             if epid not in indexed and chapinfo["isPublic"] == "True":

#                 curproc = Process(
#                     target=chapterparser, 
#                     args=(chapinfo["number"], epjson["readableProduct"]["pageStructure"]["pages"], pathandname)
#                 )

#                 processes.append(curproc)
#                 curproc.start()

#                 indexed.append(epid)

#             if (fulid := epjson["readableProduct"][arrow]) is not None:
#                 epid = fulid.split("/")[-1]
#             else:
#                 break

#     print(f"indexing is over: {time.time() - start_time}")

#     for aproc in processes:
#         aproc.join()















# from typing import List

# from io import BytesIO

# import copy, os

# import requests

# from bs4 import BeautifulSoup

# from PIL import Image
# from PIL.JpegImagePlugin import JpegImageFile

# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.utils import ImageReader


# search_domain: str = "https://shonenjumpplus.com/episode/"
# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
# }


# def recovery_images(imglist: List[JpegImageFile]) -> List[JpegImageFile]:

#     frag_wid, frag_hei = [208, 296]
#     newimglist: List[JpegImageFile] = []

#     for img in imglist:

#         newimg = copy.copy(img)

#         for j in range(4):
#             for k in range(4):
#                 newimg.paste(img.crop((frag_wid*j, frag_hei*k, frag_wid*(j+1), frag_hei*(k+1))), (frag_wid*k, frag_hei*j))
#                 newimg.paste(img.crop((frag_wid*k, frag_hei*j, frag_wid*(k+1), frag_hei*(j+1))), (frag_wid*j, frag_hei*k))

#         newimglist.append(newimg)

#     return newimglist


# def chain_title_parsing(episode_id: str, target_path: str, fromside: str = None) -> None:

#     ep_id = episode_id.split("/")[-1]
#     print(f"current: {ep_id}")
#     page = requests.get(search_domain + episode_id + ".json", headers=headers)

#     if (sc := page.status_code) != 200:
#         print(f"Page get error! (status_code: {sc}, episode_id: {episode_id})")
#         return None


#     episode_json = page.json()

#     is_pub = False
#     title = "unknown"
#     chapter = 0
#     for k in ["isPublic", "title", "number"]:

#         try:
#              param = episode_json["readableProduct"][k]

#              if k == "isPublic":
#                  is_pub = param
#              elif k == "title":
#                  title = param
#              elif k == "number":
#                  chapter = param

#         except KeyError:
#              print(f"Key error! (key \"{k}\" not found)")
#              return None

#     line_wid = len(line_cont := f"{title}, ep: {chapter}, is_pub: {is_pub}")
#     print(line_cont + "\n" + "=" * line_wid)

#     chain = []
#     for side in ["prevReadableProductUri", "nextReadableProductUri"]:
#         if (adjacent := episode_json["readableProduct"][side]) is not None and (fromside == side or fromside is None):
#             chain.append(adjacent.split("/")[-1])

#     for mem in chain:
#         chain_title_parsing(mem, target_path, side)

#     if not is_pub or os.path.exists(target_path := target_path + f"/chapter-{chapter}.pdf"):
#         return None

#     else:
#         pages = episode_json["readableProduct"]["pageStructure"]["pages"]

#         images: List[JpegImageFile] = []

#         for i in range(0, len(pages)):

#             cur_page = pages[i]

#             if cur_page["type"] != "main":
#                 continue

#             cur_img = requests.get(cur_page["src"])
#             images.append(Image.open(BytesIO(cur_img.content)))

#         images_for_pdf: List[JpegImageFile] = recovery_images(images)

#         pdf = canvas.Canvas(target_path, pagesize=letter)
#         pdf.setPageSize((836, 1200))

#         for img in images_for_pdf:
#             pdf.drawImage(ImageReader(img), 0, 0)
#             pdf.showPage()

#         pdf.save()

#         print(f"Chapter {chapter} is done")


# # def run():
# #    chain_title_parsing("13933686331661632099", "/Users/humac/Downloads/oshinoko")
