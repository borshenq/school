import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
django.setup()

from django.contrib.auth.models import User, Group

def create_users():
    # 確保群組已存在 (再次呼叫確保安全)
    staff_group = Group.objects.get(name='一般管理員')
    manager_group = Group.objects.get(name='系統管理員')

    users_to_create = [
        {
            "username": "admin",
            "password": "password123",
            "email": "admin@example.com",
            "is_superuser": True,
            "is_staff": True,
            "group": None,
            "desc": "超級管理員 (擁有所有權限)"
        },
        {
            "username": "manager",
            "password": "password123",
            "email": "manager@example.com",
            "is_superuser": False,
            "is_staff": True,
            "group": manager_group,
            "desc": "系統管理員 (可刪除與匯入)"
        },
        {
            "username": "staff",
            "password": "password123",
            "email": "staff@example.com",
            "is_superuser": False,
            "is_staff": True,
            "group": staff_group,
            "desc": "一般管理員 (僅能借還書與新增)"
        }
    ]

    print("🚀 開始建立測試帳號...")
    for u in users_to_create:
        user, created = User.objects.get_or_create(username=u['username'], email=u['email'])
        if created:
            user.set_password(u['password'])
            user.is_superuser = u['is_superuser']
            user.is_staff = u['is_staff']
            user.save()
            if u['group']:
                user.groups.add(u['group'])
            print(f"✅ 已建立：{u['username']} ({u['desc']})")
        else:
            print(f"ℹ️ 帳號 '{u['username']}' 已經存在。")

if __name__ == "__main__":
    create_users()
    print("\n🎉 測試帳號建立完畢！")
    print("-" * 30)
    print("帳號資訊 (密碼皆為: password123):")
    print("1. admin   - 完整權限")
    print("2. manager - 系統管理員權限")
    print("3. staff   - 一般管理員權限")
    print("-" * 30)
