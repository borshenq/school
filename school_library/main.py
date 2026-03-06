from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey, or_, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import date, timedelta
import os
import csv
import io
import httpx

# --- 設定 ---
BORROW_LIMIT = 5

# --- 資料庫設定 ---
DATABASE_URL = "sqlite:///./school_library.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 資料表模型 ---
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)
    isbn = Column(String)
    category = Column(String, default="未分類")
    ebook_url = Column(String, nullable=True)
    copy_number = Column(Integer, default=1)
    is_available = Column(Boolean, default=True)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    student_id = Column(String, unique=True)
    grade = Column(String)

class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    loan_date = Column(Date, default=date.today)
    due_date = Column(Date)
    return_date = Column(Date, nullable=True)

Base.metadata.create_all(bind=engine)

# --- FastAPI 應用 ---
app = FastAPI()
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 路由 ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    books_count = db.query(Book).count()
    loans_active = db.query(Loan).filter(Loan.return_date == None).count()
    overdue_count = db.query(Loan).filter(Loan.return_date == None, Loan.due_date < date.today()).count()
    error = request.query_params.get("error")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "books_count": books_count,
        "loans_active": loans_active,
        "overdue_count": overdue_count,
        "error": error
    })

# --- Google Books API ---
@app.get("/api/isbn/{isbn}")
async def get_book_info(isbn: str):
    async with httpx.AsyncClient() as client:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        response = await client.get(url)
        data = response.json()
        if "items" in data:
            book_info = data["items"][0]["volumeInfo"]
            return {
                "title": book_info.get("title", ""),
                "author": ", ".join(book_info.get("authors", [])),
                "category": book_info.get("categories", ["未分類"])[0]
            }
        else:
            raise HTTPException(status_code=404, detail="找不到資料")

# --- 圖書管理 ---
@app.get("/books", response_class=HTMLResponse)
async def list_books(request: Request, q: str = None, cat: str = None, db: Session = Depends(get_db)):
    query = db.query(Book)
    if q:
        query = query.filter(or_(Book.title.contains(q), Book.author.contains(q), Book.isbn.contains(q)))
    if cat:
        query = query.filter(Book.category == cat)
    books = query.all()
    categories = [c[0] for c in db.query(Book.category).distinct().all()]
    return templates.TemplateResponse("books.html", {"request": request, "books": books, "search_query": q, "current_cat": cat, "categories": categories})

@app.post("/books/add")
async def add_book(title: str = Form(...), author: str = Form(...), isbn: str = Form(...), category: str = Form("未分類"), ebook_url: str = Form(None), db: Session = Depends(get_db)):
    existing_copies = db.query(Book).filter(Book.isbn == isbn).count()
    new_book = Book(title=title, author=author, isbn=isbn, category=category, ebook_url=ebook_url if ebook_url else None, copy_number=existing_copies + 1)
    db.add(new_book)
    db.commit()
    return RedirectResponse(url="/books", status_code=303)

@app.post("/books/delete/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book and book.is_available:
        db.delete(book)
        db.commit()
    return RedirectResponse(url="/books", status_code=303)

@app.get("/books/export")
async def export_books(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "書名", "作者", "ISBN", "分類", "電子書連結", "複本序號", "可借用"])
    for b in books:
        writer.writerow([b.id, b.title, b.author, b.isbn, b.category, b.ebook_url, b.copy_number, b.is_available])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode("utf-8-sig")), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=books.csv"})

@app.post("/books/import")
async def import_books(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    decoded = content.decode("utf-8-sig").splitlines()
    reader = csv.DictReader(decoded)
    for row in reader:
        existing_copies = db.query(Book).filter(Book.isbn == row["ISBN"]).count()
        new_book = Book(title=row["書名"], author=row["作者"], isbn=row["ISBN"], category=row.get("分類", "未分類"), ebook_url=row.get("電子書連結") if row.get("電子書連結") else None, copy_number=existing_copies + 1)
        db.add(new_book)
    db.commit()
    return RedirectResponse(url="/books", status_code=303)

# --- 學生管理 ---
@app.get("/students", response_class=HTMLResponse)
async def list_students(request: Request, db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return templates.TemplateResponse("students.html", {"request": request, "students": students})

@app.post("/students/add")
async def add_student(name: str = Form(...), student_id: str = Form(...), grade: str = Form(...), db: Session = Depends(get_db)):
    new_student = Student(name=name, student_id=student_id, grade=grade)
    db.add(new_student)
    db.commit()
    return RedirectResponse(url="/students", status_code=303)

@app.get("/students/{id}/history", response_class=HTMLResponse)
async def student_history(id: int, request: Request, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student: raise HTTPException(status_code=404)
    loans = db.query(Loan).filter(Loan.student_id == student.id).order_by(Loan.loan_date.desc()).all()
    history = [{"book_title": db.query(Book).filter(Book.id == l.book_id).first().title, "loan_date": l.loan_date, "due_date": l.due_date, "return_date": l.return_date, "is_returned": l.return_date is not None} for l in loans]
    return templates.TemplateResponse("student_history.html", {"request": request, "student": student, "history": history})

@app.get("/students/{id}/card", response_class=HTMLResponse)
async def student_card(id: int, request: Request, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student: raise HTTPException(status_code=404)
    return templates.TemplateResponse("student_card.html", {"request": request, "student": student})

@app.get("/students/export")
async def export_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["學號", "姓名", "班級"])
    for s in students: writer.writerow([s.student_id, s.name, s.grade])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode("utf-8-sig")), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=students.csv"})

@app.post("/students/import")
async def import_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    decoded = content.decode("utf-8-sig").splitlines()
    reader = csv.DictReader(decoded)
    for row in reader:
        if not db.query(Student).filter(Student.student_id == row["學號"]).first():
            new_student = Student(name=row["姓名"], student_id=row["學號"], grade=row["班級"])
            db.add(new_student)
    db.commit()
    return RedirectResponse(url="/students", status_code=303)

# --- 借還書 ---
@app.get("/loans", response_class=HTMLResponse)
async def list_loans(request: Request, db: Session = Depends(get_db)):
    active_loans = db.query(Loan).filter(Loan.return_date == None).all()
    display_loans = []
    today = date.today()
    for l in active_loans:
        book = db.query(Book).filter(Book.id == l.book_id).first()
        student = db.query(Student).filter(Student.id == l.student_id).first()
        display_loans.append({"id": l.id, "book_title": f"{book.title} (複本 {book.copy_number})", "student_name": student.name, "student_id": student.student_id, "loan_date": l.loan_date, "due_date": l.due_date, "is_overdue": l.due_date < today})
    return templates.TemplateResponse("loans.html", {"request": request, "loans": display_loans})

@app.post("/loans/borrow")
async def borrow_book(book_id: int = Form(...), student_id: str = Form(...), db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not book or not book.is_available or not student: return RedirectResponse(url="/?error=not_found", status_code=303)
    if db.query(Loan).filter(Loan.student_id == student.id, Loan.return_date == None).count() >= BORROW_LIMIT:
        return RedirectResponse(url=f"/?error=limit_reached&limit={BORROW_LIMIT}", status_code=303)
    new_loan = Loan(book_id=book.id, student_id=student.id, due_date=date.today() + timedelta(days=14))
    book.is_available = False
    db.add(new_loan)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/loans/return/{loan_id}")
async def return_book(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if loan:
        loan.return_date = date.today()
        db.query(Book).filter(Book.id == loan.book_id).first().is_available = True
        db.commit()
    return RedirectResponse(url="/loans", status_code=303)

# --- 統計與掃描 ---
@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    today = date.today()
    stats = [{"date": (today - timedelta(days=i)).strftime("%m/%d"), "count": db.query(Loan).filter(Loan.loan_date == (today - timedelta(days=i))).count()} for i in range(6, -1, -1)]
    return stats

@app.get("/stats", response_class=HTMLResponse)
async def show_stats(request: Request): return templates.TemplateResponse("stats.html", {"request": request})

@app.get("/scan", response_class=HTMLResponse)
async def scan_page(request: Request): return templates.TemplateResponse("scan.html", {"request": request})
