import argparse
import psycopg2
import os

def CreateTables(database_name):
    try:
        connection = psycopg2.connect(user="postgres",
                                    password="Aa123456",
                                    host="localhost",
                                    port="5432",
                                    database=database_name)

        cursor = connection.cursor()
        
        # SQL query to create a new table
        # TPC-H/dbgen/dss.ddl 
        sql_commands = ['''CREATE TABLE NATION  ( N_NATIONKEY  INTEGER NOT NULL,
                            N_NAME       CHAR(25) NOT NULL,
                            N_REGIONKEY  INTEGER NOT NULL,
                            N_COMMENT    VARCHAR(152));''',

                        '''CREATE TABLE REGION  ( R_REGIONKEY  INTEGER NOT NULL,
                            R_NAME       CHAR(25) NOT NULL,
                            R_COMMENT    VARCHAR(152));''',

                        '''CREATE TABLE PART  ( P_PARTKEY     INTEGER NOT NULL,
                            P_NAME        VARCHAR(55) NOT NULL,
                            P_MFGR        CHAR(25) NOT NULL,
                            P_BRAND       CHAR(10) NOT NULL,
                            P_TYPE        VARCHAR(25) NOT NULL,
                            P_SIZE        INTEGER NOT NULL,
                            P_CONTAINER   CHAR(10) NOT NULL,
                            P_RETAILPRICE DECIMAL(15,2) NOT NULL,
                            P_COMMENT     VARCHAR(23) NOT NULL );''',

                        '''CREATE TABLE SUPPLIER ( S_SUPPKEY     INTEGER NOT NULL,
                            S_NAME        CHAR(25) NOT NULL,
                            S_ADDRESS     VARCHAR(40) NOT NULL,
                            S_NATIONKEY   INTEGER NOT NULL,
                            S_PHONE       CHAR(15) NOT NULL,
                            S_ACCTBAL     DECIMAL(15,2) NOT NULL,
                            S_COMMENT     VARCHAR(101) NOT NULL);''',

                        '''CREATE TABLE PARTSUPP ( PS_PARTKEY     INTEGER NOT NULL,
                            PS_SUPPKEY     INTEGER NOT NULL,
                            PS_AVAILQTY    INTEGER NOT NULL,
                            PS_SUPPLYCOST  DECIMAL(15,2)  NOT NULL,
                            PS_COMMENT     VARCHAR(199) NOT NULL );''',

                        '''CREATE TABLE CUSTOMER ( C_CUSTKEY     INTEGER NOT NULL,
                            C_NAME        VARCHAR(25) NOT NULL,
                            C_ADDRESS     VARCHAR(40) NOT NULL,
                            C_NATIONKEY   INTEGER NOT NULL,
                            C_PHONE       CHAR(15) NOT NULL,
                            C_ACCTBAL     DECIMAL(15,2)   NOT NULL,
                            C_MKTSEGMENT  CHAR(10) NOT NULL,
                            C_COMMENT     VARCHAR(117) NOT NULL);''',

                        '''CREATE TABLE ORDERS  ( O_ORDERKEY       INTEGER NOT NULL,
                            O_CUSTKEY        INTEGER NOT NULL,
                            O_ORDERSTATUS    CHAR(1) NOT NULL,
                            O_TOTALPRICE     DECIMAL(15,2) NOT NULL,
                            O_ORDERDATE      DATE NOT NULL,
                            O_ORDERPRIORITY  CHAR(15) NOT NULL,  
                            O_CLERK          CHAR(15) NOT NULL, 
                            O_SHIPPRIORITY   INTEGER NOT NULL,
                            O_COMMENT        VARCHAR(79) NOT NULL);''',

                        '''CREATE TABLE LINEITEM ( L_ORDERKEY    INTEGER NOT NULL,
                            L_PARTKEY     INTEGER NOT NULL,
                            L_SUPPKEY     INTEGER NOT NULL,
                            L_LINENUMBER  INTEGER NOT NULL,
                            L_QUANTITY    DECIMAL(15,2) NOT NULL,
                            L_EXTENDEDPRICE  DECIMAL(15,2) NOT NULL,
                            L_DISCOUNT    DECIMAL(15,2) NOT NULL,
                            L_TAX         DECIMAL(15,2) NOT NULL,
                            L_RETURNFLAG  CHAR(1) NOT NULL,
                            L_LINESTATUS  CHAR(1) NOT NULL,
                            L_SHIPDATE    DATE NOT NULL,
                            L_COMMITDATE  DATE NOT NULL,
                            L_RECEIPTDATE DATE NOT NULL,
                            L_SHIPINSTRUCT CHAR(25) NOT NULL,
                            L_SHIPMODE     CHAR(10) NOT NULL,
                            L_COMMENT      VARCHAR(44) NOT NULL);''']

                        
        # Execute a command: this creates new tables
        for command in sql_commands:
            cursor.execute(command)
        print("Table created successfully")
        connection.commit()
        connection.close()

    except (Exception, psycopg2.Error) as error:
        print("Error during CreateTables", error)


def AddKeys(database_name):
    try:
        connection = psycopg2.connect(user="postgres",
                                    password="Aa123456",
                                    host="localhost",
                                    port="5432",
                                    database=database_name)

        cursor = connection.cursor()
        
        # SQL query add keys 
        # TPC-H/dbgen/dss.ri
        sql_commands = ["ALTER TABLE REGION ADD PRIMARY KEY (R_REGIONKEY);",
                        "ALTER TABLE NATION ADD PRIMARY KEY (N_NATIONKEY);",
                        "ALTER TABLE SUPPLIER ADD PRIMARY KEY (S_SUPPKEY);",
                        "ALTER TABLE CUSTOMER ADD PRIMARY KEY (C_CUSTKEY);",
                        "ALTER TABLE PART ADD PRIMARY KEY (P_PARTKEY);",
                        "ALTER TABLE PARTSUPP ADD PRIMARY KEY (PS_PARTKEY,PS_SUPPKEY);",
                        "ALTER TABLE ORDERS ADD PRIMARY KEY (O_ORDERKEY);",
                        "ALTER TABLE LINEITEM ADD PRIMARY KEY (L_ORDERKEY,L_LINENUMBER);",
                        "ALTER TABLE NATION ADD FOREIGN KEY (N_REGIONKEY) references REGION;",
                        "ALTER TABLE SUPPLIER ADD FOREIGN KEY (S_NATIONKEY) references NATION;",
                        "ALTER TABLE CUSTOMER ADD FOREIGN KEY (C_NATIONKEY) references NATION;",
                        "ALTER TABLE PARTSUPP ADD FOREIGN KEY (PS_SUPPKEY) references SUPPLIER;",
                        "ALTER TABLE PARTSUPP ADD FOREIGN KEY (PS_PARTKEY) references PART;",
                        "ALTER TABLE ORDERS ADD FOREIGN KEY (O_CUSTKEY) references CUSTOMER;",
                        "ALTER TABLE LINEITEM ADD FOREIGN KEY (L_ORDERKEY) references ORDERS;",
                        "ALTER TABLE LINEITEM ADD FOREIGN KEY (L_PARTKEY,L_SUPPKEY) references PARTSUPP;"]
        
        # Execute a command: this add PK and FK to tables
        for command in sql_commands:
            cursor.execute(command)
        print("Keys added successfully")
        
        connection.commit()
        connection.close()

    except (Exception, psycopg2.Error) as error:
        print("Error during AddKeys", error)

            
def AddData(database_name, data_scale):
    try:
        connection = psycopg2.connect(user="postgres",
                                    password="Aa123456",
                                    host="localhost",
                                    port="5432",
                                    database=database_name)

        cursor = connection.cursor()
        
        # SQL query add data 
        relations = ["REGION", "NATION", "SUPPLIER", "CUSTOMER", "PART", "PARTSUPP", "ORDERS", "LINEITEM"]
        for element in relations:
            file_path =  'Data/_' + data_scale + '/' + element.lower() +".csv"
            data = open(file_path, 'r')
            cursor.copy_from(data, element.lower(), sep='|')
            
        print("Data added successfully in PostgreSQL ")
        connection.commit()
        connection.close()

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

    

def main():
    parser = argparse.ArgumentParser(description="Set up tables in a database")
    parser.add_argument("database_name", type=str, help= "Name of the database")
    parser.add_argument("data_scale", type=str, help= "scale of the dataset")
    args = parser.parse_args()

    CreateTables(args.database_name)
    AddKeys(args.database_name)
    AddData(args.database_name, args.data_scale)


if __name__ == "__main__":
    main()