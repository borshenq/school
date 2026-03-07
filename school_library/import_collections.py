import os
import django
import io
import csv
import sys

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
django.setup()

from library.models import Book

def import_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")
        return

    print(f"🚀 開始從 {file_path} 匯入館藏資料...")
    count = 0
    skipped = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        # 支援 Tab 分隔格式
        reader = csv.reader(f, delimiter='\t')

        for row in reader:
            if len(row) < 3:
                continue
            
            # 欄位對應 (B01, B04, B03, B53, ...)
            acc_no = row[0].strip()
            bib_id = row[1].strip()
            title = row[2].strip()
            status = row[3].strip()
            
            # 預防某些欄位缺失的情形
            data_type = row[5].strip() if len(row) > 5 else ""
            copy_no = row[8].strip() if len(row) > 8 else ""
            shelf_no = row[9].strip() if len(row) > 9 else ""
            added_date = row[14].strip() if len(row) > 14 else ""

            # 檢查是否已存在
            if Book.objects.filter(id=acc_no).exists():
                skipped += 1
                continue

            # 建立書籍資料
            Book.objects.create(
                id=acc_no,
                title=title,
                bib_id=bib_id,
                status=status,
                data_type=data_type,
                copy_no=copy_no,
                shelf_no=shelf_no,
                added_date=added_date,
                is_available=(status == "館內架上")
            )
            count += 1

    print(f"\n🎉 匯入完成！成功：{count} 筆, 跳過：{skipped} 筆。")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "books_data.txt"
    import_from_file(target_file)
