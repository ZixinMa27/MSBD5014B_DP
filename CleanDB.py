import argparse
import psycopg2

def DropTables(database_name):
    try:
        connection = psycopg2.connect(user="postgres",
                                port="5432",
                                database= database_name)

        cursor = connection.cursor()
        
        # SQL query drop tables
        relations = ["REGION", "NATION", "SUPPLIER", "CUSTOMER", "PART", "PARTSUPP", "ORDERS", "LINEITEM"]
        for element in reversed(relations):
            command = "DROP TABLE " + element.lower() + ";"
            cursor.execute(command)
        print("Table drop successfully in PostgreSQL ")
        connection.commit()
        connection.close()
        
    except (Exception, psycopg2.Error) as error:
        print("Error during DropTables", error)

    
def main():
    parser = argparse.ArgumentParser(description="Drop tables in a database")
    parser.add_argument("database_name", type=str, help= "Name of the database")
    args = parser.parse_args()
    
    DropTables(args.database_name)


if __name__ == "__main__":
    main()