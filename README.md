# 和弦轉調工具

**線上使用：https://wsk719.github.io/chord-transpose-tool/**

上傳圖片／PDF 和弦譜 → OCR 辨識和弦 → 轉調並直接標註回譜面；也支援純文字譜轉調。
**全部在瀏覽器端執行，沒有後端，譜面檔案不會離開使用者的電腦。**

## 檔案結構

| 路徑 | 說明 |
|---|---|
| `和弦轉調工具.html` | **唯一的原始碼**，本機雙擊即可用（走 CDN 載入函式庫） |
| `build_site.py` | 產生部署版：`python build_site.py` |
| `docs/index.html` | 部署版（由上面產生，**請勿手改**） |
| `docs/vendor/` | 自帶的第三方函式庫（見下方清單） |
| `implementation_plan.md` | 當前需求與解法 |
| `project_knowledge.md` | 專案知識庫／踩坑紀錄 |

改功能請改 `和弦轉調工具.html`，然後跑一次 `python build_site.py`。

## 部署到 GitHub Pages

本專案已部署於 [wsk719/chord-transpose-tool](https://github.com/wsk719/chord-transpose-tool)（`main` 分支 `/docs`）。
要重新部署到別的 repo，步驟如下：

1. 把這個資料夾推到 GitHub 的**公開** repo（免費方案的 Pages 只支援公開 repo）。
2. repo → **Settings → Pages** → Source 選 **Deploy from a branch**，
   Branch 選 `main`、資料夾選 **`/docs`** → Save。
3. 等一兩分鐘，網址是 `https://<你的帳號>.github.io/<repo 名稱>/`。
4. 之後只要 `git push`，網站就會自動更新。

首次載入約需下載 18 MB（OCR 引擎 wasm ＋ 英文語言包），瀏覽器會快取，第二次之後就很快。

### 幾個限制要知道

- GitHub Pages 免費方案：站台 ≤ 1 GB、頻寬**軟**上限 100 GB/月、每小時 10 次建置。
- 服務條款明訂 **不得作為商業服務（SaaS）或電商網站**使用；這個工具免費給大家用沒問題。
- 想要更寬的頻寬可以改用 Cloudflare Pages（沒有頻寬上限），把 `docs/` 整個資料夾拖上去即可，不需要改任何程式碼。

## 自帶的第三方函式庫（`docs/vendor/`）

不用 CDN 的原因：CDN 被擋或掛掉時整個工具會失效，自帶比較穩，也不會把使用者的瀏覽紀錄送給第三方。

| 檔案 | 來源套件 | 版本 |
|---|---|---|
| `tesseract.min.js`, `worker.min.js` | `tesseract.js` | 5.x |
| `tesseract-core-simd-lstm.wasm(.js)`, `tesseract-core-lstm.wasm(.js)` | `tesseract.js-core` | 隨 tesseract.js 5.x |
| `eng.traineddata.gz` | `@tesseract.js-data/eng`（`4.0.0_best_int`） | — |
| `pdf.min.js`, `pdf.worker.min.js` | `pdfjs-dist` | 3.11.174 |
| `jspdf.umd.min.js` | `jspdf` | 2.5.1 |

`4.0.0_best_int` 與 SIMD-LSTM core 是 tesseract.js 在 `oem=1`（本工具的設定）下**原本就會抓的版本**，
所以自帶之後辨識結果與先前完全一致。

### 更新自帶函式庫

```bash
npm i tesseract.js@5 pdfjs-dist@3.11.174 jspdf@2.5.1 @tesseract.js-data/eng
cp node_modules/tesseract.js/dist/{tesseract.min.js,worker.min.js}                     docs/vendor/
cp node_modules/tesseract.js-core/tesseract-core{-simd,}-lstm.wasm{,.js}               docs/vendor/
cp node_modules/@tesseract.js-data/eng/4.0.0_best_int/eng.traineddata.gz               docs/vendor/
cp node_modules/pdfjs-dist/build/{pdf.min.js,pdf.worker.min.js}                        docs/vendor/
cp node_modules/jspdf/dist/jspdf.umd.min.js                                            docs/vendor/
python build_site.py
```

升級 pdf.js 版本時記得同步改 `build_site.py` 裡的版本字串（否則替換會失敗並中止，不會產出壞頁面）。

## 版權

- 程式碼為本專案自行撰寫；第三方函式庫各自依其授權（Apache-2.0 / MIT）散布，授權檔一併放在 `docs/vendor/`。
- **本工具不提供也不散布任何譜面**。使用者自行上傳的譜面只在自己的瀏覽器裡處理，請自行確認擁有合法使用權。
