import os
import django
import io
import csv
import sys

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
django.setup()

from library.models import Book

def import_bib_data(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")
        return

    print(f"🚀 開始從 {file_path} 匯入書目資料 (B04 結構)...")
    count = 0
    skipped = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        
        # 跳過前兩行標題 (B04... 與 書目識別號...)
        next(reader) 
        next(reader)

        for row in reader:
            if len(row) < 2:
                continue
            
            # 根據您貼出的順序對應 (0-based index)
            # 0: B04 書目識別號 -> 作為 ID (因為這份表沒 B01)
            # 1: B03 書名
            # 4: B05 分類號
            # 5: B07 作者
            # 6: B06 作者號
            # 7: B08 版本
            # 9: B09 出版地
            # 10: B10 出版社
            # 11: B12 出版年
            # 13: B16 價格
            # 14: B02 ISBN
            # 21: B25 附註項
            
            bib_id = row[0].strip()
            title = row[1].strip()
            
            # 檢查 ID 是否已存在
            if Book.objects.filter(id=bib_id).exists():
                skipped += 1
                continue

            # 建立書籍資料
            Book.objects.create(
                id=bib_id, # 直接用書目識別號當 ID
                bib_id=bib_id,
                title=title,
                classification_no=row[4].strip() if len(row) > 4 else "",
                author=row[5].strip() if len(row) > 5 else "",
                author_no=row[6].strip() if len(row) > 6 else "",
                edition=row[7].strip() if len(row) > 7 else "",
                publisher=row[10].strip() if len(row) > 10 else "",
                publish_year=row[11].strip() if len(row) > 11 else "",
                price=row[13].strip() if len(row) > 13 else "",
                isbn=row[14].strip() if len(row) > 14 else "",
                notes=row[21].strip() if len(row) > 21 else "",
                status="館內架上",
                is_available=True
            )
            count += 1
            if count % 100 == 0:
                print(f"已處理 {count} 筆...")

    print(f"\n🎉 匯入完成！成功：{count} 筆, 跳過：{skipped} 筆。")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "bib_data.txt"
    import_bib_data(target_file)
