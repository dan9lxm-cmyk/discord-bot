import subprocess
import time
import sys

while True:
    try:
        print("🚀 Запуск бота...")
        subprocess.run(["python", "bot.py"])
    except KeyboardInterrupt:
        print("👋 Остановка")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        time.sleep(5)