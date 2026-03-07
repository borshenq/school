import os
import django
import datetime
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
django.setup()

from library.models import Book, Student, Loan

# 清空現有資料
print("🧹 清空現有資料...")
Loan.objects.all().delete()
Book.objects.all().delete()
Student.objects.all().delete()

# 1. 產生 10 筆圖書資料 (包含分類與電子書)
books_data = [
    {"title": "哈利波特：神秘的魔法石", "author": "J.K. 羅琳", "isbn": "9789573317241", "category": "文學", "ebook_url": "https://books.google.com.tw/books?id=f_Y3DAAAQBAJ"},
    {"title": "小王子", "author": "聖修伯里", "isbn": "9789573318000", "category": "文學", "ebook_url": "https://小王子電子書.tw"},
    {"title": "十萬個為什麼：人體奧秘", "author": "科普小組", "isbn": "9789573320001", "category": "科普", "ebook_url": None},
    {"title": "神奇樹屋：恐龍谷大冒險", "author": "瑪麗·波·奧斯本", "isbn": "9789573320002", "category": "兒童文學", "ebook_url": None},
    {"title": "屁屁偵探：消失的午餐", "author": "Troll", "isbn": "9789573320003", "category": "繪本", "ebook_url": None},
    {"title": "名偵探柯南 100", "author": "青山剛昌", "isbn": "9789573320004", "category": "漫畫", "ebook_url": None},
    {"title": "科學實驗王：電與磁", "author": "Gomdori co.", "isbn": "9789573320005", "category": "科普", "ebook_url": None},
    {"title": "查理與巧克力工廠", "author": "羅德·達爾", "isbn": "9789573320006", "category": "兒童文學", "ebook_url": "https://charlie-factory.com"},
    {"title": "國語辭典", "author": "教育部", "isbn": "9789573320007", "category": "工具書", "ebook_url": "https://dict.revised.moe.edu.tw/"},
    {"title": "台灣歷史故事", "author": "歷史研究室", "isbn": "9789573320008", "category": "歷史", "ebook_url": None},
]

# 增加複本 (測試複本功能)
books_data.append({"title": "小王子", "author": "聖修伯里", "isbn": "9789573318000", "category": "文學", "ebook_url": None})

print("📚 建立書籍資料...")
for b in books_data:
    existing_copies = Book.objects.filter(isbn=b["isbn"]).count()
    Book.objects.create(
        title=b["title"],
        author=b["author"],
        isbn=b["isbn"],
        category=b["category"],
        ebook_url=b.get("ebook_url"),
        copy_number=existing_copies + 1
    )

# 2. 產生 10 筆學生資料
students_data = [
    {"name": "張小明", "student_id": "S001", "grade": "一年一班"},
    {"name": "李小華", "student_id": "S002", "grade": "一年二班"},
    {"name": "王大為", "student_id": "S003", "grade": "二年一班"},
    {"name": "林美玲", "student_id": "S004", "grade": "二年二班"},
    {"name": "陳阿土", "student_id": "S005", "grade": "三年一班"},
    {"name": "黃雅婷", "student_id": "S006", "grade": "三年二班"},
    {"name": "郭子維", "student_id": "S007", "grade": "四年一班"},
    {"name": "蔡依玲", "student_id": "S008", "grade": "四年二班"},
    {"name": "周杰倫", "student_id": "S009", "grade": "五年一班"},
    {"name": "林俊傑", "student_id": "S010", "grade": "六年一班"},
]

print("🧑 建立學生資料...")
for s in students_data:
    Student.objects.create(**s)

# 3. 產生一些借閱紀錄 (包含正常與逾期)
print("📖 建立借閱紀錄...")
s1 = Student.objects.get(student_id="S001")
s2 = Student.objects.get(student_id="S002")
# 改用 ISBN 查詢，避免因 ID 不連續導致錯誤
b1 = Book.objects.filter(isbn="9789573317241").first() # 哈利波特
b2 = Book.objects.filter(isbn="9789573320001").first() # 十萬個為什麼

# 逾期紀錄 (借出日為 20 天前)
Loan.objects.create(
    book=b1,
    student=s1,
    loan_date=date.today() - timedelta(days=20),
    due_date=date.today() - timedelta(days=6)
)
b1.is_available = False
b1.save()

# 正常借閱 (今日借出)
Loan.objects.create(
    book=b2,
    student=s2,
    loan_date=date.today(),
    due_date=date.today() + timedelta(days=14)
)
b2.is_available = False
b2.save()

print("✅ 10 筆測試資料已成功匯入 Django 資料庫 (db.sqlite3)！")
print("包含：圖書、學生、正常借閱以及 1 筆逾期紀錄。")
