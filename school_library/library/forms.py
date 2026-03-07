import re
from django import forms
from .models import Book, Student

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'id', 'bib_id', 'title', 'author', 'isbn', 
            'classification_no', 'publisher', 'category', 'ebook_url'
        ]
        labels = {
            'id': '館藏登錄號 (10位文字)',
        }

    def clean_id(self):
        book_id = self.cleaned_data.get('id')
        # 檢查是否重複
        if Book.objects.filter(id=book_id).exists():
            raise forms.ValidationError("此館藏登錄號已存在！")
        return book_id

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        if not isbn: return isbn
        # 移除橫線
        isbn = isbn.replace('-', '')
        # 驗證 ISBN 格式 (10 或 13 位數字)
        if isbn and not re.match(r'^\d{10}(\d{3})?$', isbn):
            raise forms.ValidationError("ISBN 格式錯誤！必須為 10 或 13 位數字。")
        return isbn

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'student_id', 'grade']

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id').upper()
        # 驗證學號格式，例如 S 開頭後接 3-5 位數字 (可根據實際校規調整)
        if not re.match(r'^S\d{3,5}$', student_id):
            raise forms.ValidationError("學號格式錯誤！必須為 S 開頭後接數字 (例如: S001)。")
        
        # 檢查是否重複 (排除目前的實體以利未來編輯功能)
        if Student.objects.filter(student_id=student_id).exclude(id=self.instance.id if self.instance else None).exists():
            raise forms.ValidationError("此學號已存在，請確認是否輸入正確。")
        
        return student_id
