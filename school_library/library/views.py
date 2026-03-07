from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from .models import Book, Student, Loan, Reservation
from .forms import BookForm, StudentForm
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import csv
import io
import httpx

BORROW_LIMIT = 5
PER_PAGE = 10

@login_required
def home(request):
    books_count = Book.objects.count()
    loans_active = Loan.objects.filter(return_date__isnull=True).count()
    overdue_count = Loan.objects.filter(return_date__isnull=True, due_date__lt=date.today()).count()
    return render(request, 'library/index.html', {
        'books_count': books_count,
        'loans_active': loans_active,
        'overdue_count': overdue_count,
    })

@login_required
def list_books(request):
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')
    books_list = Book.objects.all().order_by('-id')
    if q:
        books_list = books_list.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q))
    if cat:
        books_list = books_list.filter(category=cat)
        
    paginator = Paginator(books_list, PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Book.objects.values_list('category', flat=True).distinct()
    
    return render(request, 'library/books.html', {
        'page_obj': page_obj, 
        'search_query': q, 
        'categories': categories, 
        'current_cat': cat
    })

@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            isbn = form.cleaned_data['isbn']
            existing_count = Book.objects.filter(isbn=isbn).count()
            book.copy_number = existing_count + 1
            book.save()
            messages.success(request, f"成功新增書籍：{book.title}")
        else:
            for field, error in form.errors.items():
                messages.error(request, f"書籍新增失敗 ({field}): {error[0]}")
    return redirect('list_books')

@permission_required('library.delete_book', raise_exception=True)
def delete_book(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        if book.is_available:
            book.delete()
            messages.success(request, "書籍已從館藏刪除。")
        else:
            messages.error(request, "無法刪除已借出的書籍。")
    return redirect('list_books')

@login_required
def list_students(request):
    q = request.GET.get('q', '')
    students_list = Student.objects.all().order_by('student_id')
    if q:
        students_list = students_list.filter(Q(name__icontains=q) | Q(student_id__icontains=q) | Q(grade__icontains=q))
        
    paginator = Paginator(students_list, PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'library/students.html', {'page_obj': page_obj, 'search_query': q})

@login_required
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"成功新增學生：{student.name} ({student.student_id})")
        else:
            for field, error in form.errors.items():
                messages.error(request, f"學生新增失敗 ({field}): {error[0]}")
    return redirect('list_students')

@permission_required('library.delete_student', raise_exception=True)
def delete_student(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        if not Loan.objects.filter(student=student, return_date__isnull=True).exists():
            student.delete()
            messages.success(request, "學生資料已刪除。")
        else:
            messages.error(request, "學生仍有書籍未歸還，無法刪除。")
    return redirect('list_students')

# API for Autocomplete
def api_search_students(request):
    q = request.GET.get('q', '')
    if len(q) < 1:
        return JsonResponse([], safe=False)
    students = Student.objects.filter(Q(name__icontains=q) | Q(student_id__icontains=q))[:10]
    results = [{"id": s.student_id, "label": f"{s.student_id} - {s.name} ({s.grade})"} for s in students]
    return JsonResponse(results, safe=False)

@login_required
def student_history(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    loans = Loan.objects.filter(student=student).order_by('-loan_date')
    history = []
    for l in loans:
        history.append({
            "book_title": l.book.title if l.book else "(書籍已從館藏移除)",
            "loan_date": l.loan_date,
            "due_date": l.due_date,
            "return_date": l.return_date,
            "is_returned": l.return_date is not None
        })
    return render(request, 'library/student_history.html', {'student': student, 'history': history})

@login_required
def student_card(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'library/student_card.html', {'student': student})

@login_required
def list_loans(request):
    active_loans = Loan.objects.filter(return_date__isnull=True).select_related('book', 'student')
    display_loans = []
    today = date.today()
    for l in active_loans:
        display_loans.append({
            "id": l.id,
            "book_title": f"{l.book.title} (複本 {l.book.copy_number})",
            "student_name": l.student.name,
            "student_id": l.student.student_id,
            "loan_date": l.loan_date,
            "due_date": l.due_date,
            "is_overdue": l.due_date < today,
            "fine_amount": l.fine_amount
        })
    return render(request, 'library/loans.html', {'loans': display_loans})

@login_required
def borrow_book(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        student_id = request.POST.get('student_id')
        
        book = Book.objects.filter(id=book_id).first()
        student = Student.objects.filter(student_id=student_id).first()
        
        if not book:
            messages.error(request, "借書失敗：找不到該書籍 ID。")
            return redirect('home')
        if not student:
            messages.error(request, f"借書失敗：找不到學號 {student_id} 的學生。")
            return redirect('home')
        
        # Check reservation
        if book.is_reserved:
            first_res = Reservation.objects.filter(book=book, is_active=True).first()
            if first_res and first_res.student != student:
                messages.error(request, "借書失敗：此書目前保留給預約者。")
                return redirect('home')

        if not book.is_available and not book.is_reserved:
            messages.error(request, f"借書失敗：書籍《{book.title}》已被借出。")
            return redirect('home')
        
        current_loans = Loan.objects.filter(student=student, return_date__isnull=True).count()
        if current_loans >= BORROW_LIMIT:
            messages.error(request, f"借書失敗：學生 {student.name} 已達到借書上限 ({BORROW_LIMIT} 本)。")
            return redirect('home')
            
        Loan.objects.create(book=book, student=student, due_date=date.today() + timedelta(days=14))
        
        # Update reservation status if this student had a reservation
        res = Reservation.objects.filter(book=book, student=student, is_active=True).first()
        if res:
            res.is_active = False
            res.save()
            
        book.is_available = False
        book.is_reserved = False
        book.save()
        messages.success(request, f"借書成功！《{book.title}》已借給 {student.name}，請於 {date.today() + timedelta(days=14)} 前歸還。")
        return redirect('home')
    return redirect('home')

@login_required
def return_book(request, loan_id):
    if request.method == 'POST':
        loan = get_object_or_404(Loan, id=loan_id)
        if not loan.return_date:
            loan.return_date = date.today()
            loan.save()
            
            # Check for active reservations
            res = Reservation.objects.filter(book=loan.book, is_active=True).first()
            if res:
                loan.book.is_reserved = True
                loan.book.is_available = False
                messages.success(request, f"歸還成功，此書已被預約保留。")
            else:
                loan.book.is_available = True
                loan.book.is_reserved = False
            loan.book.save()
            if not res:
                messages.success(request, f"歸還成功！《{loan.book.title}》已入庫。")
    return redirect('list_loans')

@permission_required('library.add_book', raise_exception=True)
def import_books(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            decoded_file = file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file)
            count = 0
            for row in reader:
                # 取得必要欄位
                book_id = row.get('館藏登錄號') or row.get('ID')
                if not book_id: continue
                
                title = row.get('書名')
                if not title: continue

                # 檢查是否已存在
                if Book.objects.filter(id=book_id).exists():
                    continue

                # 建立書籍資料
                Book.objects.create(
                    id=book_id,
                    bib_id=row.get('書目識別號'),
                    title=title,
                    author=row.get('作者'),
                    isbn=row.get('ISBN'),
                    category=row.get('分類', '未分類'),
                    status=row.get('館藏狀態', '館內架上'),
                    data_type=row.get('資料別'),
                    copy_no=row.get('複本號'),
                    shelf_no=row.get('排架號'),
                    added_date=row.get('新增日期'),
                    ebook_url=row.get('電子書連結'),
                    is_available=(row.get('可借用') == 'True' or row.get('館藏狀態') == '館內架上')
                )
                count += 1
            messages.success(request, f"成功匯入 {count} 筆書籍資料。")
        except Exception as e:
            messages.error(request, f"匯入失敗：{str(e)}")
    return redirect('list_books')

@login_required
def export_books(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books.csv"'
    response.write(u'\ufeff'.encode('utf8')) # BOM for Excel
    writer = csv.writer(response)
    writer.writerow([
        "館藏登錄號", "書目識別號", "書名", "作者", "ISBN", 
        "分類號", "作者號", "版本", "出版社", "出版年", "價格",
        "分類", "館藏狀態", "資料別", "複本號", "排架號", 
        "新增日期", "電子書連結", "可借用"
    ])
    for b in Book.objects.all():
        writer.writerow([
            b.id, b.bib_id, b.title, b.author, b.isbn, 
            b.classification_no, b.author_no, b.edition, b.publisher, b.publish_year, b.price,
            b.category, b.status, b.data_type, b.copy_no, b.shelf_no, 
            b.added_date, b.ebook_url, b.is_available
        ])
    return response

@login_required
def export_loans(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loans.csv"'
    response.write(u'\ufeff'.encode('utf8')) # BOM for Excel
    writer = csv.writer(response)
    writer.writerow(["借閱 ID", "館藏登錄號", "書名", "學生姓名", "學號", "借書日期", "應還日期", "歸還日期", "是否逾期"])
    
    loans = Loan.objects.all().select_related('book', 'student').order_by('-loan_date')
    for l in loans:
        writer.writerow([
            l.id,
            l.book.id,
            l.book.title,
            l.student.name,
            l.student.student_id,
            l.loan_date,
            l.due_date,
            l.return_date if l.return_date else "尚未歸還",
            "是" if l.is_overdue else "否"
        ])
    return response

@permission_required('library.add_student', raise_exception=True)
def import_students(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            decoded_file = file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file)
            count = 0
            for row in reader:
                sid = row['學號'].upper()
                if not Student.objects.filter(student_id=sid).exists():
                    Student.objects.create(name=row['姓名'], student_id=sid, grade=row['班級'])
                    count += 1
            messages.success(request, f"成功匯入 {count} 位學生資料。")
        except Exception as e:
            messages.error(request, f"匯入失敗：{str(e)}")
    return redirect('list_students')

@login_required
def export_students(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(["學號", "姓名", "班級"])
    for s in Student.objects.all():
        writer.writerow([s.student_id, s.name, s.grade])
    return response

# Stats & API
def get_stats_api(request):
    today = date.today()
    stats = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = Loan.objects.filter(loan_date=d).count()
        stats.append({"date": d.strftime("%m/%d"), "count": count})
    return JsonResponse(stats, safe=False)

@login_required
def smart_scan_api(request):
    """智慧掃描處理：自動判斷借書或還書"""
    code = request.GET.get('code', '').strip()
    if not code:
        return JsonResponse({"status": "error", "message": "無效的代碼"})

    # 1. 檢查是否為學生 (學號通常 S 開頭或特定格式)
    student = Student.objects.filter(student_id=code).first()
    if student:
        return JsonResponse({
            "status": "student",
            "name": student.name,
            "sid": student.student_id,
            "message": f"已讀取學生：{student.name}"
        })

    # 2. 檢查是否為書籍 (館藏登錄號)
    book = Book.objects.filter(id=code).first()
    if book:
        # 判定 A：如果書籍已被借出 -> 執行還書
        loan = Loan.objects.filter(book=book, return_date__isnull=True).first()
        if loan:
            loan.return_date = date.today()
            loan.save()
            book.is_available = True
            book.save()
            return JsonResponse({
                "status": "returned",
                "title": book.title,
                "message": f"歸還成功！書籍《{book.title}》已入庫。"
            })
        
        # 判定 B：如果是「館內架上」且有指定學生 -> 執行借書
        target_sid = request.GET.get('student_id')
        if target_sid:
            target_student = Student.objects.filter(student_id=target_sid).first()
            if target_student:
                # 檢查上限
                current_loans = Loan.objects.filter(student=target_student, return_date__isnull=True).count()
                if current_loans >= BORROW_LIMIT:
                    return JsonResponse({"status": "error", "message": f"失敗：{target_student.name} 已達借書上限"})
                
                # 執行借書
                Loan.objects.create(book=book, student=target_student, due_date=date.today() + timedelta(days=14))
                book.is_available = False
                book.save()
                return JsonResponse({
                    "status": "borrowed",
                    "title": book.title,
                    "message": f"借書成功！《{book.title}》已借給 {target_student.name}。"
                })
        
        return JsonResponse({
            "status": "book_info",
            "title": book.title,
            "available": book.is_available,
            "message": f"找到書籍：{book.title} (目前{'在館中' if book.is_available else '已借出'})"
        })

    return JsonResponse({"status": "error", "message": "找不到對應的學生或書籍資訊"})


@login_required
def show_stats(request):
    return render(request, 'library/stats.html')

@login_required
def scan_page(request):
    return render(request, 'library/scan.html')

def get_book_info(request, isbn):
    # Using synchronous httpx call inside sync view
    with httpx.Client() as client:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        try:
            response = client.get(url)
            data = response.json()
            if "items" in data:
                book_info = data["items"][0]["volumeInfo"]
                return JsonResponse({
                    "title": book_info.get("title", ""),
                    "author": ", ".join(book_info.get("authors", [])),
                    "category": book_info.get("categories", ["未分類"])[0]
                })
        except Exception:
            pass
    return JsonResponse({"error": "Not found"}, status=404)
