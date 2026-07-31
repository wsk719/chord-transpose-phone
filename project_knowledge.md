# 專案知識庫

## 2026-07-31 — 掃描件被誤判成文字譜 ＋ ♯ 被 OCR 讀成字母（A/C♯、F♯m 抓不到）
測試檔：讚美之泉《我全然獻上》五線譜掃描 1732×2420 JPG。**兩個獨立根因，第一個影響大得多。**
- **根因 1：`isStaff` 誤判**。原判準「dens>0.25 && run>0.5 的列數 ≥10」對這張只算出 **6 列** → 走文字譜路徑、譜線完全沒遮罩 → 整頁只抓到 2 個假和弦（`E`×2）。原因是掃描/JPEG 雜訊把譜線咬斷，最長連續段只到全寬 0.59（譜線本身也才佔全寬 ~0.70），過不了 0.5 的**絕對**門檻。
  - 修法：加第二判準 `run>0.3 && run>=dens*0.75`，即「這列的墨水有多集中在同一段」。真譜線的主段占該列墨量 ~0.95；簡譜節拍底線/歌詞列是很多短段，比值只有 0.04–0.3（合成資料實測），所以不會回歸 2026-07-31 早先修好的「簡譜被誤判成五線譜」。本檔 staffRows 6 → **23**。
  - 教訓：**掃描件不要用「佔全寬比例」這種絕對門檻**，要用形狀/比例特徵（連續性 = run/dens）。
- **根因 2：♯ 記號的 OCR 讀法**。tesseract 對本檔 ♯ 的實際輸出：`F♯m→Fem`、`D/F♯→D/Fi`、`A/C♯→A/C#`（少數正確）/`AICE`/`AICK`/`Alct`。
  - 修法 `sharpenToken()`：把「音名 `[A-Ga-g]` 後面緊接 1–2 個像♯的字元 `[eEiIltTkKhHfF4+xX]`，且後面是字尾/`/`/m/數字/sus/add/dim/aug/maj」換成 `#`，再回 `correctCore` 驗證。`AICE→AIC#`→（既有的 I→/ 規則）→`A/C#`。
  - **這個修正很積極**（`Get→G#`、`Fit→F#`、`Gem→G#m`、`Bee→B#`），所以**刻意不放進 `correctToken` 一般路徑**，只在兩處救援：`detectFrom` 內該行已有 ≥2 個確認和弦時（沿用字高比對 `h<=lh*1.6`），以及 `sparseCorrect`（本來就限定和弦列高度帶）。歌詞行湊不到 2 個和弦，救援不會啟動。
  - 既有的 `fails` 救援門檻維持 ≥3；♯ 救援用 ≥2（實測第 8 小節那行 OCR 只認得出 D、Bm 兩個）。
- **成效（同一張圖）**：舊版真實路徑 2 個假和弦 → 新版 36 個偵測，含 `A/C#`×3、`F#m`、`D/F#`、`D/A`、`G/A`、`E7` 等。
- **驗證管線（可重複）**：Python(PIL/numpy) 重現 `rowStats`＋遮罩前處理 → `tesseract --psm 3 tsv` → node 用 `new Function` 把 HTML 裡的 `correctCore/correctToken/sharpenToken/detectFrom` 原始碼**直接抽出來跑**（detectFrom 依賴 `scale`/`isStaff`，用工廠函式注入）→ 34 項斷言（♯ 案例、歌詞行必須 0 和弦、18 項既有誤讀修正不得退化）。舊版跑同一份測試只失敗新增的 3 個 ♯ 案例，證明無回歸。

## 2026-07-31 — 顯示縮放（不受原圖解析度影響）
- 問題：`#imgCanvas` 原本靠 `max-width:100%;height:auto` 決定畫面大小 → 大圖被壓到容器寬、小圖維持原尺寸，完全被來源解析度綁死。
- 作法：CSS 改 `max-width:none` + `margin:0 auto`，畫面大小改由 JS 明確設 `canvas.style.width/height = canvas.width/height × viewZoom`（**只改 CSS 顯示尺寸，canvas 位圖與 bbox 座標一律維持原圖像素**，所以 OCR/轉調/下載 PNG、PDF 完全不受影響）。
- 狀態機 `zoomMode`：`fitW`(符合寬度) / `fitP`(符合整頁) / `free`(手動)。`fitZoom()` 用 `canvasWrap.clientWidth`（扣 padding/border）與 `min(computed maxHeight, 75vh)` 算比例；`free` 以外的模式在 `renderImage()`、換頁、`window.resize` 時自動重算。載入完成後預設 `fitW`。
- 縮放入口：控制列 −/＋（×1.25 / ×0.8）、符合寬度、符合整頁、100%，以及 `canvasWrap` 上的 **Ctrl/⌘＋滾輪**（需 `{passive:false}` 才能 `preventDefault`）。滾輪縮放以游標為錨點：`scrollLeft=(scrollLeft+ax)*k-ax`。範圍 5%–800%。
- **座標容差要跟著 viewZoom 換算**：`canvasPos()` 本來就用 `canvas.width/rect.width` 所以自動正確，但寫死的像素門檻不會 —— 拖曳判定 `3px → 3/viewZoom`、`hitTest` 手把 `10/viewZoom`、框身容差 `5/viewZoom`。否則縮到 30% 時 1 螢幕 px = 3 圖 px，點一下就被判成拖曳。
- 驗證：抽 `<script>` 跑 `node --check`；另用 jsdom 載入頁面、stub `getContext`、灌入假 `canvas.width/height` 與 `clientWidth`，實測 3000px 大圖 fitW=30%、fitP=14%，400px 小圖 fitW=225%（會放大，符合預期）。

## 2026-07-31 — 簡譜被誤判為五線譜 → 最後一行和弦被遮罩塗掉
- 症狀（2.我唯一渴望.pdf）：最後一行和弦完全辨識不到。原因鏈：簡譜的節拍底線讓「密度>25% 的列」達 21 列（門檻 10）→ 誤判為五線譜 → 譜線遮罩把「密度>12%」的列塗白 → 最後一行和弦最寬最粗，自己的字身列超過 12% 被攔腰塗掉，OCR 前字就沒了。其他和弦行密度不夠高所以倖存 → 只有最後一行消失。
- 修法：`rowStats` 對每列同時算 dens（密度）與 run（**最長連續墨水段**佔寬比）。五線譜判定改為 `dens>0.25 && run>0.5`：真譜線是整行連續的（run≈0.8+），簡譜底線是斷段（此檔最高 0.52 僅 2 列，遠低於門檻 10）。遮罩內部邏輯不動（只有真五線譜才會進去），把 `rowDensity` 改名 `rowStats` 後遮罩取 `.dens`。
- 順手新增誤讀修正（皆通過 22 案例回歸測試）：`Gm/7→Gm7`（上標7前多讀出斜線；C/7 本非合法和弦無衝突）、`_Bb/C→Bb/C`（前導/尾隨 `_` 列入可剝除雜訊）、`Bom/F→Bbm/F`（♭讀成 o，限 [A-G]o 後接 m 形）。
- 驗證管線（無瀏覽器）：pdftoppm 依工具同樣縮放產圖 → Python 重現 rowStats/遮罩 → tesseract CLI 出 TSV → node 直接 eval HTML 內核心邏輯段跑 detectFrom 等價邏輯。CLI 是 tesseract 4、瀏覽器是 tesseract.js 5，結果近似但非完全相同。

## 2026-07-31 — 手動標註框拖曳/縮放＋全域字級
- 標註框資料結構：`pages[i].dets[] = {text, chord, bbox:{x0,y0,x1,y1}, on, manual?}`，座標為**原圖像素座標**；畫面顯示經 CSS 縮放，事件座標須乘 `canvas.width / getBoundingClientRect().width` 轉回。
- 互動改用 pointer events（`onpointerdown/move/up/cancel` + `setPointerCapture`）：位移 ≤3px 視為點擊（保留原本排除/刪除/補和弦行為），>3px 且按在綠框上才進入拖曳。點擊與拖曳共用同一組事件，不能再用 `onclick`（會與拖曳衝突）。
- 綠框縮放：右下角手把 `(x1+3, y1+3)`，以左上角為錨等比例縮放，最小 0.25 倍；改為統一字級後，縮放只影響覆蓋範圍，不再影響字級。
- 全域字級 `#imgFont`（range 50–300%）：**全頁統一字級**。`baseFontH(p)` 取「非手動框」框高中位數（無則取全部、再無則 `img.width/45`），`fs = baseFontH × fscale` 在迴圈外算一次，所有標註（OCR 藍框＋手動綠框）共用 → 滑桿一動全部一起變且大小一致。
  - 舊作法 `fs = 各框自己的 h × fscale` 會讓每個和弦字級不同（OCR bbox 高度本來就參差），且 while 迴圈按框寬縮字更放大差異；已整個移除該縮字迴圈（統一字級下按框寬縮字會破壞一致性）。
  - cover 模式的遮蓋矩形改為「原 bbox ∪ 實際文字範圍」：`ry0 = min(y0-3, base-fs)`、`rx1 = max(x1+3, x0+textWidth+3)`（`base = y1 - h×0.1`），否則字級調大後文字會溢出白底、原和弦露出來。
- `#imgCanvas` 需加 `touch-action:none`，否則觸控拖曳會被瀏覽器捲動吃掉。
- `handleR()` 用 function declaration（hoisting），因 `paintPage` 定義位置在它之前。
- 驗證方式：抽出 `<script>` 內容跑 `node --check`。
