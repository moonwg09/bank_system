import sys
from db_manager import DatabaseManager

# 사용자 데이터를 담을 모델 클래스
class User:
    def __init__(self, user_id, password, email, address, name, is_admin=False):
        self.user_id = user_id
        self.password = password
        self.email = email
        self.address = address
        self.name = name
        self.is_admin = is_admin  # 관리자 여부 플래그

# 시스템 메인 컨트롤러 클래스
class AccountManagerSystem:
    def __init__(self):
        self.db = DatabaseManager() # DB 매니저 인스턴스화
        self.current_user = None 

    def sign_up(self):
        print("\n--- [회원가입] ---")
        user_id = input("아이디: ").strip()
        # (실제로는 비밀번호 테이블이나 컬럼이 별도로 필요합니다. 여기서는 간소화)
        name = input("이름: ").strip()
        email = input("이메일: ").strip()
        phone = input("전화번호(010-0000-0000): ").strip()
        address = input("주소: ").strip()
        
        if not all([user_id, name, email, phone]):
            print("[!] 필수 항목을 모두 입력해야 합니다.")
            return
            
        # DB에 Insert 요청
        is_success = self.db.insert_customer(user_id, name, email, phone, address)
        if is_success:
            print(f"\n[성공] {name}님, 회원가입이 완료되었습니다!")

    def login(self):
        print("\n--- [로그인] ---")
        user_id = input("아이디: ").strip()
        
        # DB에서 Select 요청
        user_data = self.db.get_customer(user_id)
        
        if user_data:
            self.current_user = user_data
            print(f"\n[로그인 성공] {user_data['name']}님 환영합니다.")
            self.user_menu()
        else:
            print("[!] 존재하지 않는 아이디입니다.")

    def display_main_menu(self):
        while True:
            print("\n" + "="*35)
            print("      통합계좌 관리 시스템      ")
            print("="*35)
            print("1. 로그인")
            print("2. 회원가입")
            print("3. 프로그램 종료")
            print("="*35)
            
            choice = input("메뉴 번호를 입력해주세요: ")
            
            if choice == '1':
                self.login()
            elif choice == '2':
                self.sign_up()
            elif choice == '3':
                print("시스템을 종료합니다. 감사합니다.")
                sys.exit()
            else:
                print("[!] 올바른 번호를 입력해주세요.")

    def sign_up(self):
        print("\n--- [회원가입] ---")
        user_id = input("아이디: ").strip()
        
        # 아이디 중복 검증
        if user_id in self.users:
            print("[!] 이미 존재하는 아이디입니다. 다른 아이디를 사용해주세요.")
            return

        password = input("비밀번호: ").strip()
        email = input("이메일: ").strip()
        address = input("주소: ").strip()
        name = input("이름: ").strip()
        
        # 빈 값 검증
        if not all([user_id, password, email, address, name]):
            print("[!] 모든 항목을 필수로 입력해야 합니다. 다시 시도해주세요.")
            return
            
        # 새로운 User 객체 생성 및 저장
        new_user = User(user_id, password, email, address, name)
        self.users[user_id] = new_user
        print(f"\n[성공] {name}님, 회원가입이 완료되었습니다! 로그인을 진행해주세요.")

    def login(self):
        print("\n--- [로그인] ---")
        user_id = input("아이디: ").strip()
        password = input("비밀번호: ").strip()
        
        user = self.users.get(user_id)
        
        # 계정 존재 여부 및 비밀번호 일치 검증
        if user and user.password == password:
            self.current_user = user
            
            # 관리자 여부에 따른 메뉴 분기
            if user.is_admin:
                print(f"\n[관리자 모드] {user.name}님 환영합니다.")
                self.admin_menu()
            else:
                print(f"\n[로그인 성공] {user.name}님 환영합니다.")
                self.user_menu()
        else:
            print("[!] 아이디 또는 비밀번호가 일치하지 않습니다.")

    def user_menu(self):
        # TODO: 2번~13번 요구사항(계좌 생성, 이체 등)을 구현할 영역
        print(">>> 일반 사용자 서비스 메뉴로 진입했습니다. (기능 구현 예정)")
        input("엔터를 누르면 로그아웃 후 메인으로 돌아갑니다...")
        self.current_user = None

    def admin_menu(self):
        # TODO: 14번 요구사항(사용자 CRUD)을 구현할 영역
        print(">>> 관리자 서비스 메뉴로 진입했습니다. (기능 구현 예정)")
        input("엔터를 누르면 로그아웃 후 메인으로 돌아갑니다...")
        self.current_user = None
    
    def transfer_menu(self):
        print("\n--- [계좌 이체] ---")
        from_account = input("출금할 내 계좌번호: ").strip()
        to_account = input("입금할 상대방 계좌번호: ").strip()

        try:
            amount = int(input("이체 금액: "))
        except ValueError:
            print("[!] 금액은 숫자로만 입력해주세요.")
            return
        
        # 자기 자신에게 이체 방지
        if from_account == to_account:
            print("[!] 동일한 계좌로는 이체할 수 없습니다.")
            return
        
        print("\n이체를 진행 중입니다. 잠시만 기다려주세요...")

        # DB 매니저의 이체 로직 호출
        success, message = self.db.execute_transfer(from_account, to_account, amount)

        if success:
            print(f"[성공] {message}")
        else:
            print(f"[실패] {message}")
    
    def create_account_menu(self):
        print("\n--- [신규 계좌 등록]---")
        print("1: 우리은행(001), 2: 국민은행(002), 3: 신한은행(003), 4: 기업은행(004)")

        bank_choice = input("은행 코드를 선택하세요: ").strip()
        acc_num = input("계좌번호 입력: ").strip()
        alias = input("계좌 별칭(선택): ").strip()
        acc_type = input("계좌 종류(예: 보통예금): ").strip()

        try:
            initial_deposit = int(input("초기 입금액(1000원 이상): "))
        except ValueError:
            print("[!] 금액은 숫자로 입력해야 합니다.")
            return
        
        # 데이터 패키징
        account_data = {
            'account_num': acc_num,
            'customer_id': self.current_user['customer_id'], #로그인 세션 정보 사용
            'bank_code': bank_choice,
            'alias': alias if alias else "기본 계좌",
            'balance': initial_deposit,
            'account_type': acc_type,
        }

        success, message = self.db.create_account(account_data)

        if success:
            print(f"\n[성공] {message}")
        else:
            print(f"\n[실패] {message}")
    
    def update_alias_menu(self):
        print("\n--- [계좌 별칭 수정]---")
        acc_num = input("별칭을 변경할 계좌변호: ").strip()
        new_alias = input("새로운 별칭 입력: ").strip()

        # 입력값 검증
        if not acc_num or not new_alias:
            print("[!] 계좌번호와 새로운 별칭을 모두 입력해야 합니다.")
            return

        # 현재 로그인된 사용자의 id를 함께 전달하여 보안 유지
        current_customer_id = self.current_user['customer_id']

        success, message = self.db.update_account_alias(acc_num, current_customer_id, new_alias)

        if success:
            print(f"\n[성공] {message}")
        else:
            print(f"\n[실패] {message}")


    def search_account_menu(self):
        print("\n--- [계좌 조회 및 검색] ---")
        print("1. 전체 내 계좌 조회")
        print("2. 계좌번호로 검색")
        print("3. 별칭으로 검색")
        print("4. 은행명으로 검색")

        choice = input("검색 조건을 선택하세요(1~4): ").strip()

        search_type = "ALL"
        keyword = ""

        if choice == '2':
            search_type = "ACCOUNT_NUM"
            keyword = input("검색할 계좌번호 입력: ").strip()
        elif choice == '3':
            search_type = "ALIAS"
            keyword = input("검색할 별칭 입력: ").strip()
        elif choice == '4':
            search_type = "BANK"
            keyword = input("검색할 은행명 입력: ").strip()
        elif choice != '1':
            print("[!] 잘못된 입력입니다. 전체 조회를 실행합니다.")
        
        # DB 매니저 호출 (현재 로그인한 사용자 id 전달)
        results = self.db.search_accounts(self.current_user['customer_id'], search_type, keyword)

        if not results:
            print("\n[안내] 검색 조건에 일치하는 계좌가 없습니다.")
            return
        #검색 결과 출력
        print(f"\n 총 {len(results)}개의 계좌가 검색되었습니다.")
        print("-"*70)

        for r in results:
            print(f"{r['BANK_NAME']:<10} | {r['ACCOUNT_NUM']:<15} | {r['ALIAS']:<12} | {r['BALANCE']:>12,} | {r['STATUS']}")
        
        print("-"*70)

    def admin_menu(self):
        while True:
            print("\n" + "="*35)
            print(f"   [관리자 모드] - 접속자: {self.current_user['name']}   ")
            print("="*35)
            print("1. 전체 사용자 조회")
            print("2. 사용자 정보 수정")
            print("3. 사용자 삭제")
            print("4. 로그아웃 (메인으로)")
            print("="*35)

            choice = input("원하시는 관리자 업무 번호를 선택하세요: ").strip()

            if choice == '1':
                self.admin_view_all_users()
            elif choice == '2':
                self.admin_edit_user()
            elif choice == '3':
                self.admin_remove_user()
            elif choice == '4':
                print("\n[안내] 관리자 계정에서 로그아웃합니다.")
                self.current_user = None
                break 
            else:
                print("[!] 올바른 번호를 입력해주세요.")
        
    def admin_view_all_users(self):
        users= self.db.get_all_customers()
        print(f"\n현재 가입된 전체 사용자 (총 {len(users)}명)")
        print("-" * 65)
        print(f"{'아이디':<15} | {'이름':<10} | {'전화번호':<15} | {'가입일'}")
        print("-" * 65)
        for u in users:
            print(f"{u['customer_id']:<15} | {u['name']:<10} | {u['phone']:<15} | {u['created_at']}")
        print("-" * 65)
    
    def admin_edit_user(self):
        print("\n--- [사용자 정보 수정] ---")
        target_id = input("수정할 사용자의 id를 입력하세요: ").strip()

        print("새로 반영할 정보를 입력하세요")
        new_email = input("새 이메일: ").strip()
        new_phone = input("새 전화번호: ").strip()
        new_address = input("새 주소: ").strip()

        if not all([new_email, new_phone, new_address]):
            print("[!] 모든 항목을 입력해야 합니다.")
            return
        
        success, msg = self.db.admin_update_customer(target_id, new_email, new_phone, new_address)
        print(f"[{'성공' if success else '실패'}] {msg}")

    def admin_remove_user(self):
        print("\n--- [사용자 강제 삭제] ---")
        print("주의: 계좌가 남아있는 사용자는 삭제할 수 없습니다.")
        target_id = input("삭제할 사용자의 ID를 입력하세요: ").strip()
        
        confirm = input(f"정말로 '{target_id}' 사용자를 삭제하시겠습니까? (Y/N): ").strip().upper()
        if confirm != 'Y':
            print("[안내] 삭제가 취소되었습니다.")
            return
            
        success, msg = self.db.admin_delete_customer(target_id)
        print(f"[{'성공' if success else '실패'}] {msg}")

# 프로그램 실행 진입점
if __name__ == "__main__":
    system = AccountManagerSystem()
    system.display_main_menu()