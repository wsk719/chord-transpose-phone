#!/usr/bin/env python3
"""把 ./和弦轉調工具.html 產生成可部署到 GitHub Pages 的 ./docs/index.html。

單一原始碼原則：只維護 和弦轉調工具.html，改完跑一次 `python build_site.py` 即可。
與原始檔的差異只有三件事：
  1. 三個外部 CDN <script> 改成 docs/vendor/ 底下自帶的函式庫。
  2. tesseract.js / pdf.js 的 worker 與 wasm 路徑改成同源絕對路徑
     （關鍵：worker 是用 blob URL 建立的，裡面的相對路徑會相對於網站根目錄解析，
       在 GitHub Pages 的專案頁 https://<user>.github.io/<repo>/ 底下會 404）。
  3. 頁面加上「檔案不會上傳」的隱私說明與版權提醒。
其餘邏輯完全不動。任何一個替換沒命中就直接失敗，避免產出壞掉的頁面。
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "和弦轉調工具.html"
OUT_DIR = ROOT / "docs"
OUT = OUT_DIR / "index.html"

# 每個 vendor 檔案的來源 npm 套件，供 README 與稽核用
VENDOR_FILES = [
    "tesseract.min.js", "worker.min.js",
    "tesseract-core-simd-lstm.wasm.js", "tesseract-core-simd-lstm.wasm",
    "tesseract-core-lstm.wasm.js", "tesseract-core-lstm.wasm",
    "eng.traineddata.gz",
    "pdf.min.js", "pdf.worker.min.js",
    "jspdf.umd.min.js",
]

REPLACEMENTS = [
    # 1. CDN → 自帶
    ('<script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>\n'
     '<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>\n'
     '<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>',
     '<script src="vendor/tesseract.min.js"></script>\n'
     '<script src="vendor/pdf.min.js"></script>\n'
     '<script src="vendor/jspdf.umd.min.js"></script>\n'
     '<script>\n'
     '  // vendor 目錄的同源絕對路徑（worker 用 blob URL 建立，相對路徑會解析錯）\n'
     '  const VENDOR=new URL("vendor/",location.href).href;\n'
     '</script>'),

    # 2a. pdf.js worker
    ("pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';",
     "pdfjsLib.GlobalWorkerOptions.workerSrc=VENDOR+'pdf.worker.min.js';"),

    # 2b. tesseract.js worker / wasm / 語言包
    #     langPath 給目錄，tesseract 會去抓 {langPath}/eng.traineddata.gz
    #     corePath 給目錄，tesseract 會依 SIMD 支援度自己選 -simd-lstm 或 -lstm
    ("const worker=await Tesseract.createWorker('eng',1,{logger:m=>{",
     "const worker=await Tesseract.createWorker('eng',1,{\n"
     "      workerPath:VENDOR+'worker.min.js', corePath:VENDOR, langPath:VENDOR,\n"
     "      logger:m=>{"),

    # 3. 隱私與版權說明
    ('  <span class="sub">圖片和弦譜 OCR 辨識標註轉調・文字譜轉調</span>\n</header>',
     '  <span class="sub">圖片和弦譜 OCR 辨識標註轉調・文字譜轉調</span>\n'
     '</header>\n\n'
     '<p class="notice">🔒 所有辨識與轉調都在<b>您自己的瀏覽器</b>中完成，'
     '譜面檔案不會上傳到任何伺服器，本站也沒有後端可以儲存它們。<br>'
     '⚠️ 請自行確認您對所處理的譜面擁有合法使用權；本工具不提供、不散布任何譜面內容。</p>'),
]

NOTICE_CSS = """  .notice{max-width:1100px;margin:0 auto 14px;padding:10px 14px;font-size:13px;line-height:1.7;
    color:var(--sub);background:#eef4ff;border:1px solid #d3e0f8;border-radius:10px}
  @media(max-width:768px){.notice{margin:0 8px 12px;padding:9px 11px;font-size:12px;line-height:1.6}}
</style>"""


def build() -> None:
    if not SRC.exists():
        sys.exit(f"找不到原始檔：{SRC}")
    html = SRC.read_text(encoding="utf-8")

    for old, new in REPLACEMENTS:
        if html.count(old) != 1:
            sys.exit(f"替換失敗（命中 {html.count(old)} 次，需正好 1 次）：{old[:60]}…")
        html = html.replace(old, new)

    if html.count("</style>") != 1:
        sys.exit("找不到唯一的 </style>，無法插入 .notice 樣式")
    html = html.replace("</style>", NOTICE_CSS)

    # 產出後不該再有任何外部 http(s) 資源
    external = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    if external:
        sys.exit("產出的頁面仍有外部資源：" + ", ".join(external))

    OUT_DIR.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    missing = [f for f in VENDOR_FILES if not (OUT_DIR / "vendor" / f).exists()]
    if missing:
        sys.exit("docs/vendor 缺少檔案：" + ", ".join(missing) + "\n（見 README 的「更新自帶函式庫」）")

    total = sum(p.stat().st_size for p in (OUT_DIR / "vendor").iterdir())
    print(f"✅ 產生 {OUT.relative_to(ROOT)}（{OUT.stat().st_size/1024:.0f} KB）"
          f"，vendor {total/1024/1024:.1f} MB / {len(VENDOR_FILES)} 個檔案")


if __name__ == "__main__":
    build()
