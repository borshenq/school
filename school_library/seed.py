from main import SessionLocal, Book, Student, engine, Base

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 新增書籍
books = [
    Book(title="哈利波特：神秘的魔法石", author="J.K. 羅琳", isbn="9789573317241"),
    Book(title="小王子", author="安東尼·德·聖-艾修伯里", isbn="9789573318000"),
    Book(title="福爾摩斯探案全集", author="亞瑟·柯南·道爾", isbn="9789573319000"),
    Book(title="神奇樹屋：恐龍谷大冒險", author="瑪麗·波·奧斯本", isbn="9789573320000")
]

# 新增學生
students = [
    Student(name="張小明", student_id="S001", grade="三年一班"),
    Student(name="李小華", student_id="S002", grade="三年二班"),
    Student(name="王大為", student_id="S003", grade="四年一班")
]

db.add_all(books)
db.add_all(students)
db.commit()
db.close()
print("測試資料已建立！")
