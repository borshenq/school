import os
import django
import csv
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
django.setup()

from library.models import Book

def smart_import(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")
        return

    print(f"🚀 啟動智慧匯入：{file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # 先讀取標題列判斷格式
        first_line = f.readline()
        f.seek(0) # 回到開頭
        
        reader = csv.reader(f, delimiter='\t')
        headers = next(reader)
        
        # 跳過第二行說明文字
        next(reader) 

        count = 0
        skipped = 0

        # 判斷格式：B01 開頭為館藏表，B04 開頭為書目表
        is_collection_mode = headers[0] == "B01"
        
        for row in reader:
            if not row or len(row) < 2: continue
            
            try:
                if is_collection_mode:
                    # 館藏表模式 (B01, B04, B03, B53, ...)
                    book_id = row[0].strip()
                    bib_id = row[1].strip()
                    title = row[2].strip()
                    status = row[3].strip()
                    
                    book, created = Book.objects.update_or_create(
                        id=book_id,
                        defaults={
                            "bib_id": bib_id,
                            "title": title,
                            "status": status,
                            "data_type": row[5].strip() if len(row) > 5 else "",
                            "volume_no": row[7].strip() if len(row) > 7 else "",
                            "copy_no": row[8].strip() if len(row) > 8 else "",
                            "shelf_no": row[9].strip() if len(row) > 9 else "",
                            "added_date": row[14].strip() if len(row) > 14 else "",
                            "is_available": (status == "館內架上"),
                            "is_reserved": (status == "已被預約")
                        }
                    )
                    if created: count += 1
                    else: skipped += 1
                else:
                    # 書目表模式 (B04, B03, ...)
                    # 模式：更新所有具有相同 bib_id 的實體書
                    bib_id = row[0].strip()
                    
                    # 尋找所有屬於此書目的實體書
                    related_books = Book.objects.filter(bib_id=bib_id)
                    
                    update_data = {
                        "classification_no": row[4].strip() if len(row) > 4 else "",
                        "author": row[5].strip() if len(row) > 5 else "",
                        "author_no": row[6].strip() if len(row) > 6 else "",
                        "edition": row[7].strip() if len(row) > 7 else "",
                        "language": row[8].strip() if len(row) > 8 else "",
                        "pub_place": row[9].strip() if len(row) > 9 else "",
                        "publisher": row[10].strip() if len(row) > 10 else "",
                        "publish_year": row[11].strip() if len(row) > 11 else "",
                        "price": row[13].strip() if len(row) > 13 else "",
                        "isbn": row[14].strip() if len(row) > 14 else "",
                        "series": row[20].strip() if len(row) > 20 else "",
                        "notes": row[21].strip() if len(row) > 21 else "",
                        "subjects": row[22].strip() if len(row) > 22 else "",
                    }
                    
                    if related_books.exists():
                        related_books.update(**update_data)
                        count += related_books.count()
                    else:
                        # 如果找不到對應的實體書，建立一筆基礎紀錄 (ID 暫用 bib_id)
                        if not Book.objects.filter(id=bib_id).exists():
                            Book.objects.create(id=bib_id, bib_id=bib_id, title=row[1].strip(), **update_data)
                            count += 1
                        else:
                            skipped += 1
                count += 1
            except Exception as e:
                print(f"❌ 錯誤於行 {count+skipped+3}: {e}")

    print(f"\n🎉 匯入完成！模式：{'館藏(B01)' if is_collection_mode else '書目(B04)'}")
    print(f"成功：{count} 筆, 跳過：{skipped} 筆。")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        smart_import(sys.argv[1])
    else:
        print("請指定要匯入的檔案路徑。")
