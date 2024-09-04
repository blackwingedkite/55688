import re
import os

def split_text(text, chunk_size):
    chunks = []
    current_chunk = ""
    for char in text:
        current_chunk += char
        if len(current_chunk) >= chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = ""
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def merge_chunk_content_new(txt_pages_dict, chunk_size=500):
    chunks = []
    text = "".join([page["text"] for page in txt_pages_dict])

    patterns = [
    (r'<table.*?>.*?</table>', 'table'),
    (r'image \d+:.*?end of image \d+', 'image'),
    # (r'<(div|p|h[1-6]).*?>.*?</\1>', 'html'),
    (r'ocr table \d+:.*?end of ocr table \d+:', 'ocr_table'),
    (r'single table \d+:.*?end of single table \d+', 'single_table'),
    ]

    # 在文本中找到所有匹配的模式
    matches = []
    for pattern, type in patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            matches.append((match.start(), match.end(), type, match.group()))
            matches.sort(key=lambda x: x[0])
    start_checkpoint = []
    end_checkpoint = []
    for i in matches:
        start_checkpoint.append(i[0])
        end_checkpoint.append(i[1])
        print(i)
        #(2725, 2924, 'image', 'image 0.........)
        #(4258, 5027, 'table', '<table> ...)
        #(8941, 9900, 'single_table', 'single table 0...)
        #(8964, 9874, 'table', '<table ............)
    chunk_start = 0
    chunk_end = 0
    match_item = 0
    while True:
        if match_item < len(matches):
            if chunk_start + chunk_size >= len(text):
                print(str(chunk_start)+ " "+str(len(text)) )
                print("SHOULD END HERE")
                chunks.append(text[chunk_start:])
                break
            elif chunk_start + chunk_size <= start_checkpoint[match_item]:
                chunk_end = chunk_start + chunk_size
                print(str(chunk_start)+ " "+str(chunk_end))
                chunks.append(text[chunk_start:chunk_end])
                chunk_start = chunk_end
            elif chunk_start + chunk_size > start_checkpoint[match_item]:
                chunks.append(text[chunk_start:start_checkpoint[match_item]])
                print(str(chunk_start)+ " "+str(start_checkpoint[match_item]))
                chunks.append(text[start_checkpoint[match_item]:end_checkpoint[match_item]])
                print(str(start_checkpoint[match_item])+ " "+str(end_checkpoint[match_item]))
                chunk_start = end_checkpoint[match_item]
                chunk_end = end_checkpoint[match_item]
                match_item += 1
        else:
            if chunk_start + chunk_size >= len(text):
                print(str(chunk_start)+ " "+str(len(text)) )
                print("SHOULD END HERE")
                chunks.append(text[chunk_start:])
                break
            else:
                chunk_end = chunk_start + chunk_size
                print(str(chunk_start)+ " "+str(chunk_end))
                chunks.append(text[chunk_start:chunk_end])
                chunk_start = chunk_end


    # table還好，但我希望image自己一人一個chunk，這樣如果取到相關的image時可以對應到真實相片路徑
    # 合併相鄰的chunks
    merged_chunks = []
    for i in range(len(chunks) - 1):
        if ("end of image" in chunks[i]) and ("end of image" not in chunks[i+1]):
            merged_chunks.append(chunks[i])
            merged_chunks.append(chunks[i+1])
        elif ("end of image" in chunks[i]) and ("end of image" in chunks[i+1]):
            merged_chunks.append(chunks[i])
        else:
            merged_chunks.append(chunks[i] + chunks[i+1])
        if i==(len(chunks)-2) and ("end of image" in chunks[i+1]):
            merged_chunks.append(chunks[i+1])


    now_page = 0
    chunk_page = list()
    print("Number of merged chunks:", len(merged_chunks))
    print("Number of pages in txt_pages_dict:", len(txt_pages_dict))
    for chunk in merged_chunks:
        inner_dict = {"chunk": chunk, "start_page": "", "end_page":""}

        #first_content = 有可能的第一頁的內容
        #last_content = 有可能的最後一頁的內容
        #content = 這之間的內容（可能跨多頁）
        first_content = txt_pages_dict[now_page]["text"]
        content = first_content
        last_content = ""
        forward_step = 0
        page_loc = []
        while now_page < len(txt_pages_dict): #從第一頁到最後一頁
            if (chunk in last_content) and (chunk not in first_content):
                #所有的內容不在原本這頁了，但是在下一頁．這之後就完全忽略前一頁的內容
                now_page += 1
                page_loc.append(now_page +1)
                break
            elif (chunk in content):
                #跨多頁的內容（含第一頁到最後一頁）會在這裡處理
                end_page = now_page + forward_step
                for step in range(now_page, end_page+1):
                    page_loc.append(step+1)
                if last_content != "":
                    now_page = now_page + forward_step - 1
                break # 找到 chunk 所在的頁面後退出循環
            else:
                #如果在目前的content找不到，就往下一頁找
                forward_step += 1
                #如果已經到最後一頁了，就不再往下找
                if now_page + forward_step >= len(txt_pages_dict):
                    break
                last_content = txt_pages_dict[now_page+forward_step]["text"]
                content += last_content
        print(page_loc)
        if len(page_loc) == 0:
            page_txt = "Not Found"
            inner_dict["start_page"] = page_txt
            inner_dict["end_page"] = page_txt
        else:
            inner_dict["start_page"] = page_loc[0]
            inner_dict["end_page"] = page_loc[-1] #不是-1是因為後面還有一個空格
        chunk_page.append(inner_dict)
        print(str(inner_dict["start_page"]) + " " + str(inner_dict["end_page"]))
        print("===================================")
    return merged_chunks, chunk_page

with open("咒術迴戰_parse-1.txt",encoding="utf-8") as file:
    content = file.read()
doc_list = content.split("自由的百科全書")
index = 1
txt_page = []
for output_text in doc_list:
    output_dict = {
        "page": index,
        "text": output_text
    }
    txt_page.append(output_dict)
    index += 1
print(len(txt_page))
merge_chunk_content_new(txt_page, chunk_size=500)
