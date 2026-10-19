# 雲端進度同步（Google Apps Script）

讀書 App 的進度會存到你自己 Google 雲端硬碟裡的一個試算表（工作表 `sync`）。

## 部署步驟
1. 到 Google 雲端硬碟新增一個 Google 試算表（例如命名 `ipas_aiot_sync`），選單 **擴充功能 → Apps Script**。
   （也可直接在 https://script.google.com 建立「新專案」；第一次寫入時會自動建立試算表 `ipas_aiot_sync`。）
2. 刪除編輯器裡預設的 `Code.gs` 內容，貼上本資料夾 **`Code.gs`** 的全部內容（已填好密鑰；此檔不進 git）。
   若只有 `Code.gs.template`，把 `__SECRET__` 換成 `secret.txt` 的內容（32 字元以上隨機字串）。
3. 按 💾 儲存。
4. 右上角 **部署 → 新增部署作業**，齒輪選 **網頁應用程式**：
   - 執行身分：**我**
   - 誰可以存取：**所有人**
   按「部署」，依提示授權（選帳號 → 進階 → 前往（不安全）→ 允許；這是你自己的腳本）。
5. 複製「網頁應用程式網址」（`https://script.google.com/macros/s/…/exec`）。
6. 測試：瀏覽器開 `<網址>?k=<SECRET>&op=get`，應看到 `{"ok":true,"data":null,"updatedAt":0}`。

## 在各裝置啟用
開啟設定連結（每台裝置一次）：

```
https://collective353bot.github.io/ipas-aiot-study/#/sync?u=<URL 編碼的網址>&k=<SECRET>
```

App 會把網址與密鑰存進該裝置 localStorage，並立刻把連結從網址列移除。也可在「設定 → 雲端自動同步」貼上連結或分別填網址與密鑰；已設定的裝置可按「複製設定連結」給其他裝置用。
連結內含密鑰，請勿公開分享。密鑰在 `#` 之後，不會傳給 GitHub Pages 伺服器。

## 更新程式碼
修改後要 **部署 → 管理部署作業 → ✏️ 編輯 → 版本：新版本 → 部署**，網址不變。（「新增部署作業」會產生新網址。）

## 換密鑰
改 `SECRET` 後以新版本重新部署，再用新設定連結重設每台裝置。

## 協定
POST（`text/plain` 內文，避免 CORS 預檢）`{"k":SECRET,"id":"default","op":"get"|"put","data":"<JSON 字串>"}`
→ `{"ok":true,"data":"…","updatedAt":ms}`。合併在用戶端完成（各項取較新、刪除用墓碑），伺服器只存最新合併結果。
