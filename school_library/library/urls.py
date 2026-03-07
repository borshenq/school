from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.list_books, name='list_books'),
    path('books/add', views.add_book, name='add_book'), # 配合 FastAPI 表單 action="/books/add"
    path('books/delete/<str:book_id>', views.delete_book, name='delete_book'),
    path('books/export', views.export_books, name='export_books'),
    path('books/import', views.import_books, name='import_books'),
    
    path('students', views.list_students, name='list_students'),
    path('students/add', views.add_student, name='add_student'),
    path('students/delete/<int:student_id>', views.delete_student, name='delete_student'),
    path('students/export', views.export_students, name='export_students'),
    path('students/import', views.import_students, name='import_students'),
    path('students/<int:student_id>/history', views.student_history, name='student_history'),
    path('students/<int:student_id>/card', views.student_card, name='student_card'),
    
    path('loans', views.list_loans, name='list_loans'),
    path('loans/borrow', views.borrow_book, name='borrow_book'),
    path('loans/return/<int:loan_id>', views.return_book, name='return_book'),
    path('loans/export', views.export_loans, name='export_loans'),
    
    path('api/isbn/<str:isbn>', views.get_book_info, name='get_book_info'),
    path('api/scan', views.smart_scan_api, name='smart_scan_api'),
    path('api/stats', views.get_stats_api, name='get_stats_api'),
    path('api/students/search', views.api_search_students, name='api_search_students'),
    path('stats', views.show_stats, name='show_stats'),
    path('scan', views.scan_page, name='scan_page'),
]
