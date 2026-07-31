import requests
import time
import json
import os

ACCESS_TOKEN = "MLY|37502893796024230|8e58cb51905c54f8ccc0d4dfc1e2d26c"
BBOX = "-123.251,49.240,-123.203,49.278"
SAVE_FOLDER = "./mapillary_download"

os.makedirs(SAVE_FOLDER, exist_ok=True)

def fetch_all_image_meta(bbox, token):
    endpoint = "https://graph.mapillary.com/images"
    params = {
        "access_token": token,
        "bbox": bbox,
        "fields": "id,captured_at,geometry,compass_angle,is_pano",
        "limit":200
    }
    all_meta = []
    while True:
        resp = requests.get(endpoint, params=params, timeout=25)
        resp.raise_for_status()
        js = resp.json()
        data = js.get("data",[])
        if not data:
            break
        all_meta.extend(data)
        next_url = js.get("paging",{}).get("next")
        if not next_url:
            break
        endpoint = next_url
        params = {}
        time.sleep(0.75)
    return all_meta

def download_single_img(image_id, token, out_path):
    info_url = f"https://graph.mapillary.com/{image_id}"
    r1 = requests.get(info_url, params={"access_token":token,"fields":"thumb_2048_url"},timeout=15)
    img_url = r1.json()["thumb_2048_url"]
    img_bin = requests.get(img_url,timeout=30).content
    with open(out_path,"wb") as f:
        f.write(img_bin)

if __name__ == "__main__":
    meta_data = fetch_all_image_meta(BBOX,ACCESS_TOKEN)
    print(f"该区域一共获取街景：{len(meta_data)} 张")
    meta_path = os.path.join(SAVE_FOLDER,"meta.json")
    with open(meta_path,"w",encoding="utf‑8")as f:
        json.dump(meta_data,f,ensure_ascii=False,indent=2)

    
    for idx,item in enumerate(meta_data[:10]):
        iid = item["id"]
        save_file = os.path.join(SAVE_FOLDER,f"{iid}.jpg")
        print(f"正在下载第{idx+1}张，id={iid}")
        try:
            download_single_img(iid,ACCESS_TOKEN,save_file)
        except Exception as e:
            print(f"下载失败 {iid} ：{e}")
        time.sleep(1.2)