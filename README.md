# 🇮🇹 Italian Speaking Practice (Parla Italiano)

一個專為義大利文學習者設計的跨平台口說練習應用程式 (Windows/macOS)。
結合 Google Gemini AI、Edge TTS 與即時語音識別，提供身臨其境的角色扮演對話體驗。

![Italian App Screenshot](assets/screenshot_placeholder.png)
*(請自行將截圖放置於 assets 資料夾)*

## ✨ 主要功能 (Features)

*   **多角色扮演**: 可選擇不同個性的 AI 導師 (如：親切家教、嚴格老師、路人、店員)。
    *   **自定義頭像**: 您可以將自己的圖片放入 `assets/avatars` 資料夾，但請務必使用 **`.png`** 副檔名。
*   **真實情境模擬**: 包含旅遊、購物、餐廳點餐、商務等多種情境。
*   **跨平台支援**: 完美支援 **Windows** 與 **macOS**，解決了字體與路徑兼容性問題。
*   **智能分析報告**: 
    *   練習結束後，AI 會分析您的 **文法**、**詞彙** 與 **自然度**。
    *   可將分析報告匯出為 **PDF** (Windows 自動使用微軟正黑體，macOS 自動偵測系統字體)。
*   **雙語翻譯**: 可隨時切換顯示繁體中文翻譯。

## 🛠️ 安裝與執行 (Installation)
### 1. 環境需求
*   Python 3.10 或更高版本。
*   (macOS) 需要安裝 PortAudio。

### 2. 安裝步驟 (Windows)
1.  **安裝 Python**: 前往 [python.org](https://www.python.org/) 下載並安裝。
2.  **開啟終端機 (CMD/PowerShell)**，進入專案資料夾。
3.  **安裝套件**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **執行程式**:
    ```bash
    python Italian.py
    ```

### 3. 安裝步驟 (macOS) - 詳細教學
macOS 使用者建議使用 Homebrew 來管理環境，以確保音訊套件 `PortAudio` 能正常運作。

#### Step A: 安裝 Homebrew (如果尚未安裝)
打開 Terminal (終端機)，貼上以下指令並按 Enter：
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Step B: 安裝 Python 與 PortAudio
此程式需要 `portaudio` 支援錄音功能 (PyAudio/SoundDevice 依賴此套件)。
```bash
brew install python
brew install portaudio
```

#### Step C: 建立虛擬環境 (建議)
為了避免套件衝突，建議建立專屬的虛擬環境：
```bash
# 進入本專案資料夾 (假設您下載到了 Downloads)
cd ~/Downloads/Italian-AI-Tutor

# 建立環境
python3 -m venv venv

# 啟動環境
source venv/bin/activate
```

#### Step D: 安裝依賴套件
```bash
pip install -r requirements.txt
```

#### Step E: 執行程式
```bash
python3 Italian.py
```

### 4. 設定 API Key
本程式使用 Google Gemini API，請先前往 [Google AI Studio](https://aistudio.google.com/) 申請免費的 API Key。
首次執行程式時，在 "Settings" 分頁輸入您的 Key 即可 (會自動儲存至 `config_italian.json`)。

## 🚀 操作說明 (User Guide)

### 1. 初始設定 (Settings)
*   啟動程式後，請先至 **Settings** 分頁。
*   輸入 **Gemini API Key** (必填)。
*   選擇您的目標語言、角色 (Persona)、等級 (Level) 與情境 (Scenario)。
*   確認 **Microphone** 與 **Voice** 設定正確。
*   點擊 **Save Settings** 儲存設定。

### 2. 開始練習 (Practice)
*   切換至 **Practice** 分頁。
*   點擊 **Start (Inizia)** 按鈕開始對話。
*   程式具備 **語音活動偵測 (VAD)** 功能，您只需自然說話，程式會自動錄音並回覆。
*   若需結束練習，請點擊 **Stop (Ferma)**。

### 3. 查看報告 (Report)
*   練習結束後，AI 會自動生成學習分析報告 (需在設定中開啟 Generate Report)。
*   切換至 **Report** 分頁查看內容。
*   點擊 **Export PDF** 可將報告匯出保存。

## 📂 專案結構

```
/
├── assets/             # 圖片資源 (Avatars)
├── temp/               # 暫存音訊檔 (自動生成)
├── Italian.py          # 主程式碼
├── requirements.txt    # 套件依賴列表
├── Reference.md        # 參考文件
├── config_italian.json # 設定檔 (自動生成，請勿上傳至 Github)
└── README.md           # 說明文件
```

## ⚠️ 注意事項

*   **麥克風權限**: 在 macOS 上首次執行時，終端機可能會請求麥克風存取權限，請選擇允許。
*   **字體問題**: PDF 匯出功能已內建字體 fallback 機制，若匯出的 PDF 中文字顯示異常，請檢查系統是否有 Arial Unicode 或 Heiti 字體。

## 🤝 貢獻
歡迎提交 Pull Request 或 Issue 來協助改進這個專案！

---
**License**: MIT
