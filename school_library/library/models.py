from django.db import models
from datetime import date, timedelta

class Book(models.Model):
    # --- 主鍵替換為館藏登錄號 ---
    id = models.CharField(max_length=10, primary_key=True, verbose_name="館藏登錄號")
    
    # 基礎資訊
    title = models.CharField(max_length=200, verbose_name="書名")
    author = models.CharField(max_length=100, verbose_name="作者", blank=True, null=True)
    isbn = models.CharField(max_length=20, verbose_name="ISBN", blank=True, null=True)
    category = models.CharField(max_length=50, default="未分類", verbose_name="分類")
    ebook_url = models.URLField(null=True, blank=True, verbose_name="電子書連結")
    
    # --- 專業書目欄位擴充 ---
    classification_no = models.CharField(max_length=50, verbose_name="分類號", blank=True, null=True)
    author_no = models.CharField(max_length=50, verbose_name="作者號", blank=True, null=True)
    edition = models.CharField(max_length=50, verbose_name="版本", blank=True, null=True)
    language = models.CharField(max_length=20, verbose_name="語言別", blank=True, null=True)       # B13
    pub_place = models.CharField(max_length=50, verbose_name="出版地", blank=True, null=True)      # B09
    publisher = models.CharField(max_length=100, verbose_name="出版社", blank=True, null=True)
    publish_year = models.CharField(max_length=50, verbose_name="出版年", blank=True, null=True)
    price = models.CharField(max_length=50, verbose_name="價格", blank=True, null=True)
    series = models.CharField(max_length=200, verbose_name="集叢項", blank=True, null=True)       # B24
    subjects = models.CharField(max_length=200, verbose_name="主題項", blank=True, null=True)      # B26
    notes = models.TextField(verbose_name="附註項", blank=True, null=True)
    
    # --- 專業館藏欄位擴充 ---
    bib_id = models.CharField(max_length=50, verbose_name="書目識別號", blank=True, null=True)
    status = models.CharField(max_length=50, default="館內架上", verbose_name="館藏狀態")
    circulation_type = models.CharField(max_length=50, verbose_name="流通別", blank=True, null=True)
    data_type = models.CharField(max_length=50, verbose_name="資料別", blank=True, null=True)
    special_no = models.CharField(max_length=50, verbose_name="特藏號", blank=True, null=True)
    volume_no = models.CharField(max_length=50, verbose_name="冊次號", blank=True, null=True)
    copy_no = models.CharField(max_length=50, verbose_name="複本號", blank=True, null=True)
    shelf_no = models.CharField(max_length=50, verbose_name="排架號", blank=True, null=True)
    location = models.CharField(max_length=100, verbose_name="館藏地", blank=True, null=True)
    source_type = models.CharField(max_length=50, verbose_name="來源別", blank=True, null=True)
    donor = models.CharField(max_length=100, verbose_name="捐贈者", blank=True, null=True)
    attachment = models.CharField(max_length=200, verbose_name="附件", blank=True, null=True)
    added_date = models.CharField(max_length=50, verbose_name="新增日期", blank=True, null=True)
    # -------------------------------

    copy_number = models.IntegerField(default=1, verbose_name="系統複本序號")
    is_available = models.BooleanField(default=True, verbose_name="可借用")
    is_reserved = models.BooleanField(default=False, verbose_name="預約保留中")

    def __str__(self):
        return f"{self.title} ({self.id})"

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

    @property
    def fine_amount(self):
        # 逾期一天罰 5 元
        if self.is_overdue:
            days = (date.today() - self.due_date).days
            return days * 5
        elif self.return_date and self.return_date > self.due_date:
            days = (self.return_date - self.due_date).days
            return days * 5
        return 0

class Reservation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="預約書籍")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="預約學生")
    reserve_date = models.DateField(auto_now_add=True, verbose_name="預約日期")
    is_active = models.BooleanField(default=True, verbose_name="預約有效")

    class Meta:
        ordering = ['reserve_date']
