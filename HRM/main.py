"""
Điểm nhập chính cho ứng dụng HRM Employee Manager

Khởi động ứng dụng ở chế độ GUI hoặc console tùy thuộc vào môi trường.
"""

from .gui_app import GUIApp
from .console_app import ConsoleApp


def main():
    """Hàm chính"""
    # Tạo instance GUI
    gui_app = GUIApp()

    # Kiểm tra xem GUI có khả dụng không
    if hasattr(gui_app, 'root'):
        # Chạy chế độ GUI
        gui_app.run()
    else:
        # Chạy chế độ console
        console_app = ConsoleApp()
        console_app.run()


if __name__ == "__main__":
    main()