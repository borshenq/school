from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Book, Student, Loan
from django.db.models import Q
from datetime import date, timedelta
import csv, io, httpx

BORROW_LIMIT = 5

def home(request):
    books_count = Book.objects.count()
    loans_active = Loan.objects.filter(return_date__isnull=True).count()
    overdue_count = Loan.objects.filter(return_date__isnull=True, due_date__lt=date.today()).count()
    error = request.GET.get('error')
    limit = request.GET.get('limit')
    return render(request, 'library/index.html', {
        'books_count': books_count,
        'loans_active': loans_active,
        'overdue_count': overdue_count,
        'error': error,
        'limit': limit
    })

def list_books(request):
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')
    books = Book.objects.all()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q))
    if cat:
        books = books.filter(category=cat)
    categories = Book.objects.values_list('category', flat=True).distinct()
    return render(request, 'library/books.html', {
        'books': books, 'search_query': q, 'categories': categories, 'current_cat': cat
    })

@login_required
def add_book(request):
    if request.method == 'POST':
        isbn = request.POST['isbn']
        existing_count = Book.objects.filter(isbn=isbn).count()
        Book.objects.create(
            title=request.POST['title'],
            author=request.POST['author'],
            isbn=isbn,
            category=request.POST.get('category', '未分類'),
            ebook_url=request.POST.get('ebook_url') or None,
            copy_number=existing_count + 1
        )
    return redirect('list_books')

@login_required
def borrow_book(request):
    if request.method == 'POST':
        book_id = request.POST['book_id']
        student_id = request.POST['student_id']
        book = get_object_or_404(Book, id=book_id)
        student = Student.objects.filter(student_id=student_id).first()
        
        if not book.is_available or not student:
            return redirect('/?error=not_found')
        
        active_loans = Loan.objects.filter(student=student, return_date__isnull=True).count()
        if active_loans >= BORROW_LIMIT:
            return redirect(f'/?error=limit_reached&limit={BORROW_LIMIT}')
        
        Loan.objects.create(book=book, student=student, due_date=date.today() + timedelta(days=14))
        book.is_available = False
        book.save()
    return redirect('home')

@login_required
def return_book(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    loan.return_date = date.today()
    loan.save()
    loan.book.is_available = True
    loan.book.save()
    return redirect('list_loans')

@login_required
def list_loans(request):
    loans = Loan.objects.filter(return_date__isnull=True)
    return render(request, 'library/loans.html', {'loans': loans})

@login_required
def list_students(request):
    students = Student.objects.all()
    return render(request, 'library/students.html', {'students': students})

@login_required
def import_books(request):
    if request.method == 'POST' and request.FILES.get('file'):
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        for row in reader:
            isbn = row['ISBN']
            existing_count = Book.objects.filter(isbn=isbn).count()
            Book.objects.create(
                title=row['書名'], author=row['作者'], isbn=isbn,
                category=row.get('分類', '未分類'), ebook_url=row.get('電子書連結') or None,
                copy_number=existing_count + 1
            )
    return redirect('list_books')

@login_required
def import_students(request):
    if request.method == 'POST' and request.FILES.get('file'):
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        for row in reader:
            if not Student.objects.filter(student_id=row['學號']).exists():
                Student.objects.create(name=row['姓名'], student_id=row['學號'], grade=row['班級'])
    return redirect('list_students')

@login_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.is_available:
        book.delete()
    return redirect('list_books')

async def get_book_info(request, isbn):
    # 此 API 開放給前端抓取資料，不需要登入
    async with httpx.AsyncClient() as client:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        response = await client.get(url)
        data = response.json()
        if "items" in data:
            info = data["items"][0]["volumeInfo"]
            return JsonResponse({
                "title": info.get("title", ""),
                "author": ", ".join(info.get("authors", [])),
                "category": info.get("categories", ["未分類"])[0]
            })
    return JsonResponse({"error": "Not Found"}, status=404)

def export_books(request):
    # 匯出資料通常也建議受保護
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['ID', '書名', '作者', 'ISBN', '分類', '電子書連結'])
    for b in Book.objects.all():
        writer.writerow([b.id, b.title, b.author, b.isbn, b.category, b.ebook_url])
    return response

@login_required
def student_history(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    loans = Loan.objects.filter(student=student).order_by('-loan_date')
    return render(request, 'library/student_history.html', {'student': student, 'loans': loans})

@login_required
def student_card(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'library/student_card.html', {'student': student})
