"""
Ứng dụng console cho HRM Employee Manager

Chứa các chức năng chế độ dòng lệnh.
"""

import os
import sys
from dotenv import load_dotenv
from data_manager import DataManager
from utils import format_display_value
from config import CONSOLE_MENU_OPTIONS


class ConsoleApp:
    """Ứng dụng console"""

    def __init__(self):
        self.data_manager = DataManager()

    def run(self):
        """Chạy ứng dụng ở chế độ console"""
        print("HRM Employee Manager - Console Mode")
        print("=" * 50)

        # Tải biến môi trường
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)

        # Lấy API key
        api_key = input("Enter your API key (press Enter to use from .env): ").strip()

        if not api_key:
            api_key = os.getenv('API_KEY')
            if api_key:
                print("Using API key from .env file")
            else:
                print("Error: API key is required!")
                sys.exit(1)

        print("Fetching employee data...")

        count, error = self.data_manager.fetch_employees(api_key)

        if error:
            print(f"Error: {error}")
            sys.exit(1)

        print(f"Successfully fetched {count} employees.")

        self.main_menu()

    def main_menu(self):
        """Menu chính"""
        while True:
            print("\n" + "=" * 50)
            print("HRM EMPLOYEE MANAGER - CONSOLE MENU")
            print("=" * 50)
            print(f"Total employees: {len(self.data_manager.df)} | Filtered: {len(self.data_manager.filtered_df)}")
            print("=" * 50)
            print("1. 🔍 Search employees (Fuzzy search)")
            print("2. 🔽 Filter by column")
            print("3. 📊 Sort by column")
            print("4. 📋 Display employees")
            print("5. 📈 Statistics")
            print("6. 📄 Export data")
            print("7. 🔄 Reset filters")
            print("8. ❌ Exit")
            print("=" * 50)

            choice = input("Choose an option (1-8): ").strip()

            if choice == '1':
                self.console_search()
            elif choice == '2':
                self.console_filter()
            elif choice == '3':
                self.console_sort()
            elif choice == '4':
                self.console_display()
            elif choice == '5':
                self.console_statistics()
            elif choice == '6':
                self.console_export()
            elif choice == '7':
                self.console_reset()
            elif choice == '8':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

    def console_search(self):
        """Chức năng tìm kiếm console"""
        print("\n🔍 FUZZY SEARCH")
        print("-" * 30)
        current_search = self.data_manager.search_text if self.data_manager.search_text else ""
        print(f"Current search: '{current_search}'")

        search_text = input("Enter search text (name, email, phone, code, position): ").strip()

        if search_text:
            self.data_manager.search_text = search_text
            self.data_manager.apply_filters()
            print(f"✅ Found {len(self.data_manager.filtered_df)} matching employees")
        else:
            self.data_manager.search_text = ""
            self.data_manager.apply_filters()
            print("✅ Search cleared")

    def console_filter(self):
        """Chức năng lọc console"""
        print("\n🔽 COLUMN FILTER")
        print("-" * 30)

        if self.data_manager.column_filters:
            print("Current filters:")
            for col, val in self.data_manager.column_filters.items():
                print(f"  {col}: {val}")
        else:
            print("No active filters")

        print("\nAvailable columns:")
        columns = {
            '1': ('name', 'Họ tên'),
            '2': ('email', 'Email'),
            '3': ('phone', 'Số điện thoại'),
            '4': ('code', 'Mã NV'),
            '5': ('position', 'Chức vụ'),
            '6': ('bank_name', 'Ngân hàng')
        }

        for key, (col, name) in columns.items():
            print(f"{key}. {name}")
        print("7. Clear all filters")
        print("8. Back to main menu")

        choice = input("Choose column to filter (1-8): ").strip()

        if choice == '8':
            return
        elif choice == '7':
            self.data_manager.column_filters = {}
            self.data_manager.apply_filters()
            print("✅ All filters cleared")
            return

        if choice in columns:
            col, name = columns[choice]
            print(f"\nFiltering by: {name}")

            unique_values = self.data_manager.df[col].dropna().unique()
            unique_values = sorted([str(v) for v in unique_values if v])

            if len(unique_values) <= 10:
                print("Available values:")
                for i, val in enumerate(unique_values[:10], 1):
                    print(f"{i}. {val}")
                print("11. Enter custom value")

                val_choice = input("Choose value or enter 11 for custom: ").strip()

                if val_choice == '11':
                    filter_val = input("Enter filter value: ").strip()
                elif val_choice.isdigit() and 1 <= int(val_choice) <= len(unique_values):
                    filter_val = unique_values[int(val_choice) - 1]
                else:
                    print("Invalid choice")
                    return
            else:
                filter_val = input("Enter filter value (partial match): ").strip()

            if filter_val:
                self.data_manager.column_filters[col] = filter_val.lower()
                self.data_manager.apply_filters()
                print(f"✅ Filter applied: {name} contains '{filter_val}'")
            else:
                if col in self.data_manager.column_filters:
                    del self.data_manager.column_filters[col]
                self.data_manager.apply_filters()
                print(f"✅ Filter for {name} cleared")

    def console_sort(self):
        """Chức năng sắp xếp console"""
        print("\n📊 SORT BY COLUMN")
        print("-" * 30)

        columns = {
            '1': ('name', 'Họ tên'),
            '2': ('email', 'Email'),
            '3': ('code', 'Mã NV'),
            '4': ('position', 'Chức vụ'),
            '5': ('stt', 'STT')
        }

        for key, (col, name) in columns.items():
            print(f"{key}. {name}")
        print("6. Back to main menu")

        choice = input("Choose column to sort by (1-6): ").strip()

        if choice == '6':
            return

        if choice in columns:
            col, name = columns[choice]

            print("Sort order:")
            print("1. Ascending (A-Z, 1-9)")
            print("2. Descending (Z-A, 9-1)")

            order_choice = input("Choose order (1-2): ").strip()

            if order_choice in ['1', '2']:
                ascending = order_choice == '1'

                try:
                    self.data_manager.filtered_df = self.data_manager.filtered_df.sort_values(by=col, ascending=ascending)
                    print(f"✅ Sorted by {name} ({'ascending' if ascending else 'descending'})")
                except Exception as e:
                    print(f"❌ Error sorting: {str(e)}")
            else:
                print("Invalid choice")

    def console_display(self):
        """Chức năng hiển thị console với phân trang"""
        print("\n📋 DISPLAY EMPLOYEES")
        print("-" * 30)

        if self.data_manager.filtered_df.empty:
            print("No employees to display")
            return

        print("Display options:")
        print("1. Show all employees")
        print("2. Show with pagination (10 per page)")
        print("3. Show specific columns")
        print("4. Back to main menu")

        choice = input("Choose display option (1-4): ").strip()

        if choice == '4':
            return

        all_cols = {}
        for i, col in enumerate(['stt'] + list(self.data_manager.df.columns), 1):
            all_cols[str(i)] = col

        display_cols = ['stt'] + list(self.data_manager.df.columns)[:5]

        if choice == '3':
            print("\nAvailable columns:")
            for key, col in all_cols.items():
                print(f"{key}. {col}")

            col_choice = input("Enter column numbers (comma-separated, e.g., 1,2,3): ").strip()

            try:
                selected_indices = [int(x.strip()) for x in col_choice.split(',')]
                display_cols = [all_cols[str(i)] for i in selected_indices if str(i) in all_cols]
                if not display_cols:
                    display_cols = ['stt'] + list(self.data_manager.df.columns)[:5]
            except:
                print("Invalid selection, using default columns")

        if choice == '1':
            print(f"\nShowing all {len(self.data_manager.filtered_df)} employees:")
            display_df = self.data_manager.filtered_df[display_cols].copy()

            for col in display_cols:
                if col in ['name', 'email', 'position']:
                    display_df[col] = display_df[col].astype(str).str.slice(0, 30)
                else:
                    display_df[col] = display_df[col].apply(lambda x: format_display_value(x, col)).str.slice(0, 30)

            print(display_df.to_string(index=False, max_colwidth=30))

        elif choice == '2':
            page_size = 10
            total_pages = (len(self.data_manager.filtered_df) + page_size - 1) // page_size

            current_page = 1

            while True:
                start_idx = (current_page - 1) * page_size
                end_idx = min(start_idx + page_size, len(self.data_manager.filtered_df))

                print(f"\nPage {current_page}/{total_pages} (showing {start_idx+1}-{end_idx} of {len(self.data_manager.filtered_df)})")

                page_df = self.data_manager.filtered_df[display_cols].iloc[start_idx:end_idx].copy()
                for col in display_cols:
                    if col in ['name', 'email', 'position']:
                        page_df[col] = page_df[col].astype(str).str.slice(0, 30)
                    else:
                        page_df[col] = page_df[col].apply(lambda x: format_display_value(x, col)).str.slice(0, 30)

                print(page_df.to_string(index=False, max_colwidth=30))

                if total_pages == 1:
                    break

                print("\nNavigation:")
                print("n. Next page")
                print("p. Previous page")
                print("g. Go to page")
                print("q. Quit display")

                nav_choice = input("Choose (n/p/g/q): ").strip().lower()

                if nav_choice == 'q':
                    break
                elif nav_choice == 'n' and current_page < total_pages:
                    current_page += 1
                elif nav_choice == 'p' and current_page > 1:
                    current_page -= 1
                elif nav_choice == 'g':
                    try:
                        page_num = int(input("Enter page number: ").strip())
                        if 1 <= page_num <= total_pages:
                            current_page = page_num
                        else:
                            print("Invalid page number")
                    except:
                        print("Invalid input")

    def console_statistics(self):
        """Chức năng thống kê console"""
        print("\n📈 STATISTICS")
        print("-" * 30)

        if self.data_manager.filtered_df.empty:
            print("No data to analyze")
            return

        print(f"Total employees: {len(self.data_manager.filtered_df)}")
        print(f"Original dataset: {len(self.data_manager.df)}")

        if 'position' in self.data_manager.filtered_df.columns:
            position_counts = self.data_manager.filtered_df['position'].value_counts()
            print(f"\n📊 Employees by position:")
            for pos, count in position_counts.head(10).items():
                print(f"  {pos}: {count}")

        if 'email' in self.data_manager.filtered_df.columns:
            email_domains = self.data_manager.filtered_df['email'].dropna().apply(lambda x: str(x).split('@')[-1] if '@' in str(x) else 'unknown')
            domain_counts = email_domains.value_counts()
            print(f"\n📧 Email domains:")
            for domain, count in domain_counts.head(5).items():
                print(f"  {domain}: {count}")

        if 'bank_name' in self.data_manager.filtered_df.columns:
            bank_counts = self.data_manager.filtered_df['bank_name'].value_counts()
            print(f"\n🏦 Bank distribution:")
            for bank, count in bank_counts.head(5).items():
                if bank and bank != 'nan':
                    print(f"  {bank}: {count}")

    def console_export(self):
        """Chức năng xuất console"""
        print("\n📄 EXPORT DATA")
        print("-" * 30)

        if self.data_manager.filtered_df.empty:
            print("No data to export")
            return

        print("Export options:")
        print("1. Export to CSV")
        print("2. Export to Excel")
        print("3. Export to JSON")
        print("4. Export with custom filename")
        print("5. Back to main menu")

        choice = input("Choose export option (1-5): ").strip()

        if choice == '5':
            return

        base_name = "employees"
        if choice == '4':
            base_name = input("Enter base filename (without extension): ").strip()
            if not base_name:
                base_name = "employees"

        format_map = {'1': 'CSV', '2': 'Excel', '3': 'JSON'}

        if choice in format_map:
            success, message = self.data_manager.export_data(format_map[choice], base_name)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")

    def console_reset(self):
        """Đặt lại tất cả bộ lọc và tìm kiếm"""
        self.data_manager.reset_filters()
        print("✅ All filters and search cleared")