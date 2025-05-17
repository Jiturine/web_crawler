from db_operations import DatabaseOperations


def test_database():
    db = DatabaseOperations()

    # 测试查询所有书籍
    with db.connection.cursor() as cursor:
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        print("\n=== 所有书籍 ===")
        for book in books:
            print(f"书名: {book['book_name']}")
            print(f"作者: {book['book_author']}")
            print(f"评分: {book['book_rating']}")
            print("---")

        # 测试查询评论
        if books:
            first_book_id = books[0]['book_id']
            cursor.execute(
                "SELECT * FROM book_comments WHERE book_id = %s", (first_book_id,))
            comments = cursor.fetchall()
            print(f"\n=== 书籍 {books[0]['book_name']} 的评论 ===")
            for comment in comments:
                print(f"用户: {comment['comment_username']}")
                print(f"评分: {comment['comment_rating']}")
                print(f"内容: {comment['comment_content'][:50]}...")  # 只显示前50个字符
                print("---")

    db.close()


if __name__ == "__main__":
    test_database()
