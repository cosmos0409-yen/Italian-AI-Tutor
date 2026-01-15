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
*   建議使用虛擬環境 (Virtual Environment)。

### 2. 安裝依賴套件
下載專案後，在終端機執行：

```bash
pip install -r requirements.txt
```

### 3. 設定 API Key
本程式使用 Google Gemini API，請先前往 [Google AI Studio](https://aistudio.google.com/) 申請免費的 API Key。
首次執行程式時，在 "Settings" 分頁輸入您的 Key 即可 (會自動儲存至 `config_italian.json`)。

### 4. 啟動程式

```bash
python Italian.py
```

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
