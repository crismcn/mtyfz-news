import requests

access_token = "102_CuyA04G-qS3pP50FNKu3YpP7ZsbzwKaunlcnDGQGpZ4voYNhY1smJR3G5PbPPQ-51Pv6-25WzPyErKRTLZAh-P15q1Vtawrw7eNjFU4rYYK0qnputE5p7k_PaFQHNIaAIAVBW"

url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"

files = {
    "media": open("assets/generated/2026-03-16/01-1-5-women-rejoin-iranian-soccer-squad-in-malaysia-after-abando-9f9d9944bcbf.jpg", "rb")
}

res = requests.post(url, files=files)

# {media_id, url}
print(res.json())