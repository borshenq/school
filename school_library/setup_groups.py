import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from library.models import Book, Student, Loan

def setup():
    # 1. 建立「一般管理員」群組 (Staff)
    staff_group, _ = Group.objects.get_or_create(name='一般管理員')
    
    # 取得相關權限
    book_ct = ContentType.objects.get_for_model(Book)
    student_ct = ContentType.objects.get_for_model(Student)
    loan_ct = ContentType.objects.get_for_model(Loan)

    staff_perms = [
        'view_book', 'add_book', 'change_book',
        'view_student', 'add_student', 'change_student',
        'view_loan', 'add_loan', 'change_loan'
    ]
    
    for perm_code in staff_perms:
        perm = Permission.objects.get(codename=perm_code)
        staff_group.permissions.add(perm)

    # 2. 建立「系統管理員」群組 (Manager)
    manager_group, _ = Group.objects.get_or_create(name='系統管理員')
    # 系統管理員擁有所有權限 (包含 delete)
    all_perms = Permission.objects.filter(content_type__in=[book_ct, student_ct, loan_ct])
    for perm in all_perms:
        manager_group.permissions.add(perm)

    print("✅ 權限群組初始化完成：'一般管理員' 與 '系統管理員'")

if __name__ == "__main__":
    setup()
