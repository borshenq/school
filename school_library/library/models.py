from django.db import models
from datetime import date, timedelta

class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="書名")
    author = models.CharField(max_length=100, verbose_name="作者")
    isbn = models.CharField(max_length=20, verbose_name="ISBN")
    category = models.CharField(max_length=50, default="未分類", verbose_name="分類")
    ebook_url = models.URLField(null=True, blank=True, verbose_name="電子書連結")
    copy_number = models.IntegerField(default=1, verbose_name="複本序號")
    is_available = models.BooleanField(default=True, verbose_name="可借用")

    def __str__(self):
        return f"{self.title} (複本 {self.copy_number})"

class Student(models.Model):
    name = models.CharField(max_length=50, verbose_name="姓名")
    student_id = models.CharField(max_length=20, unique=True, verbose_name="學號")
    grade = models.CharField(max_length=20, verbose_name="班級")

    def __str__(self):
        return f"{self.name} ({self.student_id})"

class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="書籍")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="學生")
    loan_date = models.DateField(auto_now_add=True, verbose_name="借書日期")
    due_date = models.DateField(verbose_name="應還日期")
    return_date = models.DateField(null=True, blank=True, verbose_name="歸還日期")

    @property
    def is_overdue(self):
        if not self.return_date and self.due_date < date.today():
            return True
        return False
