# __snapshots__

此資料夾的 baseline 截圖目前**暫時廢棄**，圖片先行留存。

**背景：**
原 `test_functional.py` 中的 `TestVisualRegression` 使用 `assert_snapshot` 做 pixel-level 比對，
baseline 存放於此。重構後該測試改為 `save_screenshot` 存檔不比對（截圖輸出至 `screenshots/dlt/vr_reference/`），
原因是各人螢幕解析度不同，pixel 比對無法跨環境穩定運作。

**現況：**
- 目前無任何測試引用這裡的 PNG
- 圖片保留供未來參考，若後續導入視覺測試服務（如 Percy / Applitools）可作為參考素材

**可刪除時機：**
確認不再需要這些 baseline 時，整個資料夾可直接刪除。
