import cx_Oracle

class DatabaseManager:
    def __init__(self):
        # TODO: 본인의 Oracle DB 환경에 맞게 수정하세요.
        self.username = 'C##BANK_ADMIN' 
        self.password = '1234'
        
        # 호스트, 포트, SID(또는 서비스명)로 DSN(Data Source Name) 생성
        # 예: 로컬호스트(127.0.0.1), 기본포트(1521), 서비스명(XE)
        self.dsn = cx_Oracle.makedsn('localhost', 1521, service_name='XE')

    def get_connection(self):
        """DB 커넥션 객체를 반환합니다."""
        try:
            return cx_Oracle.connect(user=self.username, password=self.password, dsn=self.dsn)
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            print(f"[DB 연결 에러] 코드: {error.code}, 메시지: {error.message}")
            raise

    # ---------------------------------------------------------
    # 회원가입 / 로그인 쿼리 예시 (AccountManagerSystem에서 호출)
    # ---------------------------------------------------------
    
    def insert_customer(self, user_id, name, email, phone, address):
        """새로운 고객을 DB에 등록합니다. (요구사항: 회원가입)"""
        sql = """
            INSERT INTO Customer (customer_id, name, email, phone, address) 
            VALUES (:1, :2, :3, :4, :5)
        """
        # with문을 사용하면 작업 완료 시 커넥션과 커서가 자동으로 닫힙니다.
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    # 파이썬 변수를 바인딩하여 쿼리 실행
                    cursor.execute(sql, (user_id, name, email, phone, address))
                    conn.commit() # 데이터베이스에 확정
                    return True
                except cx_Oracle.IntegrityError:
                    print("[!] 이미 존재하는 아이디이거나 이메일이 중복되었습니다.")
                    return False

    def get_customer(self, user_id):
        """고객 ID로 정보를 조회합니다. (요구사항: 로그인 검증용)"""
        sql = "SELECT customer_id, name, email, phone, address FROM Customer WHERE customer_id = :1"
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id,))
                row = cursor.fetchone() # 한 건만 조회
                
                if row:
                    # 결과를 딕셔너리 형태로 반환하여 다루기 쉽게 만듭니다.
                    return {
                        'customer_id': row[0],
                        'name': row[1],
                        'email': row[2],
                        'phone': row[3],
                        'address': row[4]
                    }
                return None
    
    def execute_transfer(self, from_account, to_account, amount):

        # 1. 금액 검증(요구사항 10번)
        if amount <= 0:
            return False, "이체 금액은 0원보다 커야 합니다."
        
        sql_check_lock = "SELECT balance FROM Account WHERE account_num = :1 FOR UPDATE"
        sql_update_bal = "UPDATE Account SET balance = balance + :1 WHERE account_num = :2"
        sql_insert_tx = """
            INSERT INTO "TRANSACTION" (account_num, tr_type, amount, other_account, balance_after)
            VALUES (:1, :2, :3, :4, :5)
        """
        # oracle에서 transaction은 시스템 내부 예약어이므로, 테이블로 인식시키기위해서 ""를 써준다

        # cx_Oracle 커넥션 가져오기
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 2. 출금 계좌 확인 및 Lock
            cursor.execute(sql_check_lock, (from_account,))
            row = cursor.fetchone()
            if not row:
                return False, "출금 계좌를 찾을 수 없습니다."
            
            current_balance = row[0]

            # 3. 잔액 검증
            if current_balance < amount:
                return False, "잔액이 부족하여 이체가 취소되었습니다."
            
            # 4. 입금 계좌 존재 여부 및 Lock
            cursor.execute(sql_check_lock, (to_account,))
            to_row = cursor.fetchone()
            if not to_row:
                return False, "입금 대상 계좌가 존재하지 않아 작업이 취소됩니다."
            to_balance = to_row[0]

            # 트랜잭션 시작
            
            # 1. 출금 처리
            new_from_bal = current_balance - amount
            cursor.execute(sql_update_bal, (-amount, from_account))
            cursor.execute(sql_insert_tx, (from_account, 'WITHDRAWAL', amount, to_account, new_from_bal))

            # 2. 입금 처리
            new_to_bal = to_balance + amount
            cursor.execute(sql_update_bal, (amount, to_account))
            cursor.execute(sql_insert_tx, (to_account, 'DEPOSIT', amount, from_account))

            # 모든 작업이 정상적으로 끝났을 때만 DB에 반영
            conn.commit()
            return True, "계좌 이체가 성공적으로 완료되었습니다."
        
        except cx_Oracle.DatabaseError as e:
            # 중간에 오류가 발생하면 무조건 롤백하여 자금 증발 방지
            conn.rollback()
            return False, f"시스템 오류로 모든 작업이 취소되었습니다. 사유: {e}"
        
        finally:
            cursor.close()
            conn.close()
    
    def create_account(self, account_info):
        """새로운 계좌 생성"""

        # 1. 초기 입금액 검증
        if account_info['balance'] < 1000:
            return False, "최초 생성 시 입금액은 1000원 이상이어야 합니다."
        
        # 2. 허용된 은행인지 확인
        allowed_banks = {'001': '우리', '002': '국민', '003': '신한', '004': '기업'}
        if account_info['bank_code'] not in allowed_banks:
            return False, "제공하지 않은 은행입니다."
        
        sql_insert_acc = """
            insert into Account (account_num, customer_id, bank_code, alias, balance, account_type)
            values (:1, :2, :3, :4, :5, :6)
        """

        sql_insert_tx = """
            insert into "transsaction" (account_num, tr_type, amount, balance_after, description)
            values (:1, 'deposit', :2, :3, '계좌 개설 초기 입금')
        """

        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 3. 계좌 등록
            cursor.execute(sql_insert_acc, (
                account_info['account_num'],
                account_info['customer_id'],
                account_info['bank_code'],
                account_info['alias'],
                account_info['balance'],
                account_info['account_type']
            ))
        
            # 4. 최초 입금 내역 기록
            cursor.execute(sql_insert_tx, (
                account_info['account_num'],
                account_info['balance'],
                account_info['balance']
            ))

            conn.commit()
            return True, "계좌가 성공적으로 등록되었습니다."
    
        except cx_Oracle.IntegrityError:
            conn.rollback()
            return False, "이미 등록된 계좌번호입니다."
        except cx_Oracle.DatabaseError as e:
            conn.rollback()
            return False, f"DB 오류 발생: {e}"
        finally:
            conn.close()
    
    def update_account_alias(self, account_num, customer_id, new_alias):
        """계좌 별칭 수정"""

        # 1. 현재 계좌 상태 및 기존 별칭 조회(본인 계좌인지 확인)
        sql_select = "select alias from Account where account_num = :1 and customer_id = :2"

        # 2. 별칭 업데이트
        sql_update = "update Account set alias = :1 where account_num = :2"

        # 3. 변경 이력 기록 
        sql_history = """
            insert into AccountHistory (account_num, action_type, before_value, after_value)
            values (:1, '별칭변경', :2, :3)
        """

        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 계좌 소유주 및 현재 별칭 확인
            cursor.execute(sql_select, (account_num, customer_id))
            row = cursor.fetchone()

            if not row:
                return False, "본인 소유의 계좌를 찾을 수 없거나 계좌번호가 잘못되었습니다."
            
            current_alias = row[0]

            # 기존 별칭과 중복 검사
            if current_alias == new_alias:
                return False, f"이미 '{new_alias}'로 설정되어 있습니다. 다른 별칭을 입력해주세요."
            
            # 업데이트 및 이력 저장 실행
            cursor.execute(sql_update, (new_alias, account_num))
            cursor.execute(sql_history, (account_num, current_alias, new_alias))

            conn.commit()
            return True, f"별칭이 '{current_alias}'에서 '{new_alias}'로 변경되었습니다."
        
        except cx_Oracle.DatabaseError as e:
            conn.rollback()
            return False, f"DB 시스템 오류: {e}"
        finally:
            cursor.close()
            conn.close()
    
    def search_accounts(self, customer_id, search_type="ALL", keyword=""):
        """계좌 다목적 검색"""

        # 고객의 계좌 정보와 은행명을 가져옴
        base_sql = """
            select b.bank_name, a.account_num, a.alias, a.balance, a.account_type, a.status
            from Account a
            join Bank b on a.bank_code = b.bank_code
            where a.customer_id = :1
        """

        params = [customer_id]

        # 조건에 따른 where 절 추가
        if search_type == "account_num":
            base_sql += " and a.account_num like '%' || :2 || '%'"
            params.append(keyword)
        elif search_type == "alias":
            base_sql += " and a.alias like '%' || :2 || '%'"
            params.append(keyword)
        elif search_type == "bank":
            base_sql += " and b.bank_name like '%' || :2 || '%'"
            params.append(keyword)
        
        # 최신 계좌가 위로 오도록 정렬
        base_sql += " order by a.created_at desc"

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(base_sql, params)

                # 컬럼명 가져오기
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

                return [dict(zip(columns, row)) for row in rows]
    
    # 관리자 전용 기능
    
    def get_all_customers(self):
        """전체 사용자 목록 조회"""

        sql = "select customer_id, name, email, phone, to_char(created_at, 'YYYY-MM-DD') from Customer order by created_at desc"

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                colums = ['customer_id', 'name', 'email', 'phone', 'created_at']
                return [dict(zip(colums, row)) for row in cursor.fetchall()]
        
    def admin_update_customer(self, customer_id, email, phone, address):
        """특정 사용자 정보 수정 (update)"""
        sql = "update Customer set email = :1, phone = :2, address = :3 where customer_id = :4"

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, (email, phone, address, customer_id))
                    # rowcount로 실제 업데이터된 행이 있는지 확인
                    if cursor.rowcount == 0:
                        return False, "해당 id의 사용자를 찾을 수 없습니다."
                    conn.commit()
                    return True, f"'{customer_id}' 사용자의 정보가 수정되었습니다."
                except cx_Oracle.DatabaseError as e:
                    conn.rollback()
                    return False, f"수정 실패: {e}"
    
    def admin_delete_customer(self, customer_id):
        """특정 사용자 강제 삭제"""

        # 최고 관리자는 삭제할 수 없도록 방어 로직 추가
        if customer_id.lower() == 'admin':
            return False, "최고 관리자 계정은 삭제할 수 없습니다."
        
        sql = "delete from Customer where customer_id = :1"

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, (customer_id,))
                    if cursor.rowcount == 0:
                        return False, "해당 id의 사용자를 찾을 수 없습니다."
                    conn.commit()
                    return True, f"'{customer_id}' 사용자가 시스템에서 삭제 되었습니다."
                except cx_Oracle.IntegrityError:
                    # 계좌나 거래내역이 있는 사용자일 경우
                    conn.rollback()
                    return False, "이 사용자는 보유 중인 계좌나 거래 내역이 있어 삭제할 수 없습니다.(계좌 먼저 해지해주세요)"
                except cx_Oracle.DatabaseError as e:
                    conn.rollback()
                    return False, f"삭제 중 오류 발생: {e}"
                
                    