from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.list_books, name='list_books'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/export/', views.export_books, name='export_books'),
    path('books/import/', views.import_books, name='import_books'),
    path('students/', views.list_students, name='list_students'),
    path('students/import/', views.import_students, name='import_students'),
    path('students/<int:student_id>/history/', views.student_history, name='student_history'),
    path('students/<int:student_id>/card/', views.student_card, name='student_card'),
    path('loans/', views.list_loans, name='list_loans'),
    path('loans/borrow/', views.borrow_book, name='borrow_book'),
    path('loans/return/<int:loan_id>/', views.return_book, name='return_book'),
    path('api/isbn/<str:isbn>/', views.get_book_info, name='get_book_info'),
]
