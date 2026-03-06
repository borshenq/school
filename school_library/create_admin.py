import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser(username='admin', email='admin@example.com', password='admin1234'):
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"✅ 管理員帳號建立成功！")
        print(f"   帳號：{username}")
        print(f"   預設密碼：{password} (請登入後務必修改)")
    else:
        print(f"ℹ️ 帳號 '{username}' 已經存在。")

if __name__ == "__main__":
    create_superuser()
