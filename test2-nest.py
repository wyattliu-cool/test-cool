import warnings
# 先导入依赖再过滤警告
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import requests
import json
import os

# ====================== 配置（UBC NEST区域）======================
ACCESS_TOKEN = "MLY|37502893796024230|8e58cb51905c54f8ccc0d4dfc1e2d26c"
# UBC AMS The Nest 周边范围 west,south,east,north
BBOX = "-123.2460,49.2620,-123.2380,49.2680"
SAVE_FOLDER = "./ubc_nest_mapillary_images"
API_URL = "https://graph.mapillary.com/images"
# =================================================================

# 创建保存文件夹
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

all_features = []
next_cursor = None
download_count = 0
fail_count = 0

print("=== 开始抓取 UBC NEST 周边街景列表 ===")
while True:
    params = {
        "access_token": ACCESS_TOKEN,
        "bbox": BBOX,
        "fields": "id,geometry,thumb_256_url,captured_at"
    }
    if next_cursor:
        params["after"] = next_cursor

    resp = requests.get(API_URL, params=params, timeout=30)
    data = resp.json()
    image_list = data.get("data", [])

    if not image_list:
        break

    for item in image_list:
        img_id = item["id"]
        img_url = item.get("thumb_256_url")
        geometry = item["geometry"]

        feat = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "image_id": img_id,
                "img_url": img_url,
                "capture_time": item.get("captured_at")
            }
        }
        all_features.append(feat)

        if not img_url:
            print(f"[{img_id}] 无缩略图链接，跳过")
            fail_count += 1
            continue

        save_path = os.path.join(SAVE_FOLDER, f"{img_id}.jpg")
        if os.path.exists(save_path):
            print(f"[{img_id}] 文件已存在，跳过")
            download_count += 1
            continue

        # 下载图片
        try:
            img_resp = requests.get(img_url, timeout=15)
            if img_resp.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(img_resp.content)
                download_count += 1
                print(f"✅ 已下载: {img_id}.jpg")
            else:
                print(f"❌ [{img_id}] 链接失效 {img_resp.status_code}")
                fail_count += 1
        except Exception as e:
            print(f"❌ [{img_id}] 网络异常: {str(e)}")
            fail_count += 1

    # 分页
    paging = data.get("paging", {})
    next_cursor = paging.get("cursors", {}).get("after")
    if not next_cursor:
        break
    print("\n==== 加载下一页数据 ====\n")

# 导出点位GeoJSON
geojson_path = os.path.join(SAVE_FOLDER, "nest_image_index.geojson")
geojson_data = {"type": "FeatureCollection", "features": all_features}
with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump(geojson_data, f, ensure_ascii=False, indent=2)

print("\n==================== 任务完成 ====================")
print(f"✅ 成功下载图片：{download_count} 张")
print(f"❌ 失败/无链接：{fail_count} 张")
print(f"📁 图片目录：{os.path.abspath(SAVE_FOLDER)}")
print(f"🗺️ GIS点位文件：{geojson_path}")