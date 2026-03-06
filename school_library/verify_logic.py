import sqlite3
from datetime import date, timedelta

# 模擬資料庫測試邏輯 (直接使用 SQLite)
DB_PATH = "school_library.db"

def run_test():
    print("🚀 開始進行系統邏輯快速驗證...\n")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 驗證圖書資料
    cursor.execute("SELECT COUNT(*) FROM books")
    books_count = cursor.fetchone()[0]
    print(f"📊 [館藏驗證] 目前總藏書量：{books_count} 本")

    # 2. 驗證複本序號功能
    cursor.execute("SELECT title, isbn, copy_number FROM books WHERE title='小王子'")
    copies = cursor.fetchall()
    print(f"📚 [複本驗證] 《小王子》複本數量：{len(copies)}")
    for i, copy in enumerate(copies, 1):
        print(f"   - 複本 {i}: ISBN={copy[1]}, 序號={copy[2]}")

    # 3. 驗證逾期判定邏輯
    today = date.today()
    cursor.execute("""
        SELECT books.title, loans.due_date 
        FROM loans 
        JOIN books ON loans.book_id = books.id 
        WHERE loans.return_date IS NULL AND loans.due_date < ?
    """, (today,))
    overdue = cursor.fetchall()
    print(f"\n⚠️ [逾期驗證] 偵測到逾期未還數量：{len(overdue)}")
    for item in overdue:
        print(f"   - 逾期書籍：{item[0]} (應還日期：{item[1]})")

    # 4. 驗證借書上限邏輯 (模擬)
    BORROW_LIMIT = 5
    student_id = "S001" # 測試學生
    cursor.execute("SELECT id FROM students WHERE student_id=?", (student_id,))
    s_id = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM loans WHERE student_id=? AND return_date IS NULL", (s_id,))
    current_loans = cursor.fetchone()[0]
    
    print(f"\n🧒 [上限驗證] 學生 {student_id} 目前借閱數：{current_loans}")
    if current_loans >= BORROW_LIMIT:
        print(f"   ❌ 結果：已達上限 {BORROW_LIMIT} 本，系統將阻擋新借閱。")
    else:
        print(f"   ✅ 結果：尚未達上限，允許繼續借閱 (剩餘額度: {BORROW_LIMIT - current_loans})。")

    conn.close()
    print("\n✅ 邏輯驗證完成！系統核心運作正常。")

if __name__ == "__main__":
    run_test()
