# iPAS AIoT應用工程師（初級）學科備考專案

為 Nelson 準備 115 年（2026/10/31）iPAS 經濟部產業人才能力鑑定「AIoT應用工程師」初級學科考試所製作的學習教材。

## 考試範圍
- 考科一【初級-學科】AIoT 基礎概論（75 分鐘，單選題）
- 考科二【初級-學科】物聯網系統與應用（75 分鐘，單選題）
- 每科 70 分及格；或平均 70 分且每科不低於 60 分。
- 官方範圍與來源整理：`summary.md`；官方原始檔：根目錄的 brochure_*、guide_subject1_*、credit_exemption*、page_* 等。

## 讀書計畫（每天 30 分鐘，已整體延後一天）
D1 10/19 AI 基礎與 AIoT 案例｜D2 10/20 物聯網架構與無線技術｜D3 10/21 MQTT/CoAP/REST/Modbus/OPC UA/MTConnect｜D4 10/22 中介軟體平台與資安隱私｜D5 10/23 感測器、訊號、UART/I2C/SPI｜D6 10/24 考科一模擬考 A｜D7 10/25 考科一模擬考 B＋錯題｜D8 10/26 考科二系統架構與故障排除｜D9 10/27 資安、硬體 I/O、開源授權｜D10 10/28 雲端數據收集、JSON/XML、資料庫｜D11 10/29 智慧製造 OEE/精實/MES/成本｜10/30 D12 考科二模擬考＋聽 D13 總複習。

## 結構
- `study/`：互動學習網頁與講義
  - `src/`：每日講義（md）與題目（txt），每段標註官方評鑑內容代碼
  - `build.py` + `template.html` → `index.html`（單檔、離線、localStorage 存進度）
  - `make_pdf.py` + `print_template.html` → `講義.pdf`
  - `test_ui.py`：headless UI 測試
- `audio/`：有聲教材
  - `scripts/`：v1 講稿（edge-tts zh-TW-HsiaoChenNeural）
  - `scripts_v2/`：v2 生動版講稿（多範例、口訣、考題陷阱）
  - `v2/`：v2 音檔以 Higgsfield ElevenLabs v4（Hana preset c25f78a0-714e-42af-8da3-a399cef94968）錄製
  - `tts.py`：edge-tts 重新產生 v1 音檔
- `site/`：部署用，另一個 repo → https://github.com/collective353bot/ipas-aiot-study ，GitHub Pages：https://collective353bot.github.io/ipas-aiot-study/

## 注意事項
- 考科二沒有官方學習指引，內容依簡章評鑑內容與能力指標逐條對應，一般技術知識標「補充」。
- 官方學習指引有數題答案與解析矛盾（如 5.2 第 5、7、8 題），講義已更正並以 ⚠️ 標示。
- 題目皆為原創或「改編自官方學習指引」，非考古題。
- 部署時先 `unset GITHUB_TOKEN`（環境變數 token 無效，改用 gh 登入）。
