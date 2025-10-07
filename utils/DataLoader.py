# 最后要delete，合并到dataset
import os
import json
import urllib.request
from tqdm import tqdm

# 1. 设置路径
json_path = r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\Scrum-interviews.json"
save_dir = r"F:\Work\Debate\MultiAgentDabateDataAnnotation\Data\orgin\Scrum-interviews"
os.makedirs(save_dir, exist_ok=True)

# 2. 读取 JSON 文件
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. 解析所有文件链接 (.xlsx 和 .pdf)
file_entries = data.get("files", {}).get("entries", {})
download_list = []

for fname, meta in file_entries.items():
    if fname.endswith(".xlsx") or fname.endswith(".pdf"):
        url = meta.get("links", {}).get("content")
        if url:
            download_list.append((fname, url))

print(f"发现 {len(download_list)} 个可下载文件")


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


# 4. 下载函数
def download_file(filename, url):
    try:
        print(f"\n📥 开始下载: {filename}")
        full_path = os.path.join(save_dir, filename)
        with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=filename, ncols=100) as t:
            urllib.request.urlretrieve(
                url, full_path,
                reporthook=t.update_to
            )
        print(f"✅ 已保存: {filename}")
    except Exception as e:
        print(f"❌ 下载失败 {filename}: {e}")


# 5. 批量下载
if __name__ == "__main__":
    for fname, url in download_list:
        download_file(fname, url)
