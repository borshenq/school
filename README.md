# school

 > 如何啟動圖書系統
✦ 這是一個基於 Django 框架開發的圖書管理系統。您可以依照以下步驟啟動：


  1. 激活虛擬環境 (Virtual Environment)
  首先，您需要進入專案目錄並激活已有的虛擬環境：
   1 source venv/bin/activate


  2. 安裝依賴套件 (選用)
  如果您是第一次在目前的環境運行，建議先確保所有套件已安裝：
   1 pip install -r requirements.txt

  3. 啟動開發伺服器
  使用 Django 的 manage.py 工具來啟動伺服器：
   1 python manage.py runserver


  4. 訪問系統
  伺服器啟動後，終端機通常會顯示如下資訊：
  Starting development server at http://127.0.0.1:8000/


  請打開瀏覽器並輸入 http://127.0.0.1:8000/ 即可進入系統。
