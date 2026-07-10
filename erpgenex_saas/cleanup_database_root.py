import frappe

def cleanup_database_root():
    """Clean up database using root credentials"""
    try:
        # Get root password
        from erpgenex_saas.services.password_manager import PasswordManager
        password_manager = PasswordManager()
        root_password = password_manager.get_mariadb_root_password()
        
        print(f"Root Password: {root_password}")
        
        # Connect as root and drop the database
        import pymysql
        
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password=root_password,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Drop the database
        db_name = "_9cb93f3c707a2132"
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            print(f"Dropped database: {db_name}")
        except Exception as e:
            print(f"Failed to drop database: {str(e)}")
        
        # Drop the user
        try:
            cursor.execute(f"DROP USER IF EXISTS `{db_name}`@`%`")
            cursor.execute(f"DROP USER IF EXISTS `{db_name}`@`localhost`")
            print(f"Dropped user: {db_name}")
        except Exception as e:
            print(f"Failed to drop user: {str(e)}")
        
        # Flush privileges
        cursor.execute("FLUSH PRIVILEGES")
        
        cursor.close()
        connection.close()
        
        print("Cleanup completed")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
