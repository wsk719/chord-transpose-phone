# 專案知識庫

## 2026-07-31 — 手動標註框拖曳/縮放＋全域字級
- 標註框資料結構：`pages[i].dets[] = {text, chord, bbox:{x0,y0,x1,y1}, on, manual?}`，座標為**原圖像素座標**；畫面顯示經 CSS 縮放，事件座標須乘 `canvas.width / getBoundingClientRect().width` 轉回。
- 互動改用 pointer events（`onpointerdown/move/up/cancel` + `setPointerCapture`）：位移 ≤3px 視為點擊（保留原本排除/刪除/補和弦行為），>3px 且按在綠框上才進入拖曳。點擊與拖曳共用同一組事件，不能再用 `onclick`（會與拖曳衝突）。
- 綠框縮放：右下角手把 `(x1+3, y1+3)`，以左上角為錨等比例縮放，最小 0.25 倍。字級由框高推導（`fs = h × fscale`），覆蓋矩形＝bbox，所以框放大 → 覆蓋範圍與字一起變大。
- 全域字級 `#imgFont`（range 50–300%）：`paintPage` 中 `fs = h × fscale`，同時把「字寬自動縮小」上限乘上 fscale，否則調大字級會被 while 迴圈縮回去。
- `#imgCanvas` 需加 `touch-action:none`，否則觸控拖曳會被瀏覽器捲動吃掉。
- `handleR()` 用 function declaration（hoisting），因 `paintPage` 定義位置在它之前。
- 驗證方式：抽出 `<script>` 內容跑 `node --check`。
