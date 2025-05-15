from db_operations import DatabaseOperations

def test_database():
    db = DatabaseOperations()
    
    # ���Բ�ѯ�����鼮
    with db.connection.cursor() as cursor:
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        print("\n=== �����鼮 ===")
        for book in books:
            print(f"����: {book['book_name']}")
            print(f"����: {book['book_author']}")
            print(f"����: {book['book_rating']}")
            print("---")
            
        # ���Բ�ѯ����
        if books:
            first_book_id = books[0]['book_id']
            cursor.execute("SELECT * FROM book_comments WHERE book_id = %s", (first_book_id,))
            comments = cursor.fetchall()
            print(f"\n=== �鼮 {books[0]['book_name']} ������ ===")
            for comment in comments:
                print(f"�û�: {comment['comment_username']}")
                print(f"����: {comment['comment_rating']}")
                print(f"����: {comment['comment_content'][:50]}...")  # ֻ��ʾǰ50���ַ�
                print("---")
    
    db.close()

if __name__ == "__main__":
    test_database() 