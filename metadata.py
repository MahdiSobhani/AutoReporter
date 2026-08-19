import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
from utils import db_connecting, show_tables, space_used, ERD, timer, export ,df ,pd ,time

class MetaData:
    def __init__(self, counter, SourceID, Server, db, schema, table, Row, Size):
        self.counter = counter
        self.SourceID = SourceID
        self.Server = Server
        self.db = db
        self.schema = schema
        self.table = table
        self.Row = Row
        self.Size = Size

    def My_ThreadPool(self):
        total_tables ,CONCAT = len(df),[]
        try:
            print(f'{self.counter} Reading... {self.table}')
            con = db_connecting(self.Server, self.db)
            
            sample_data = pd.read_sql(f'SELECT top(1) * FROM [{self.schema}].[{self.table}]', con)
            con.close()
            
            No_Columns = len(sample_data.columns)
            
            for Column in sample_data.columns:
                con = db_connecting(self.Server, self.db)
                nulls_df = pd.read_sql(f'SELECT count_big(*) FROM [{self.schema}].[{self.table}] WHERE [{Column}] is null', con)
                con.close()
                
                Nulls = nulls_df.values[0][0]
                Nulls_Percent = round((Nulls / self.Row) * 100, 2)
                
                con = db_connecting(self.Server, self.db)
                try:
                    distinct_df = pd.read_sql(f'SELECT count_big(DISTINCT [{Column}]) FROM [{self.schema}].[{self.table}] WHERE [{Column}] is not null', con)
                except:
                    try:
                        distinct_df = pd.read_sql(f'SELECT count_big(DISTINCT CAST(CAST([{Column}] as NVARCHAR) as NVARCHAR(max))) FROM [{self.schema}].[{self.table}] WHERE [{Column}] is not null', con)
                    except:
                        distinct_df = pd.read_sql(f'SELECT count_big(DISTINCT CONVERT(varbinary(max), [{Column}])) FROM [{self.schema}].[{self.table}] WHERE [{Column}] is not null', con)
                con.close()
                
                Distinct = distinct_df.values[0][0]
                row_data = pd.DataFrame(data=[[self.SourceID, self.Server, self.db, self.schema, self.table, Column, No_Columns, self.Size, self.Row, Nulls, Nulls_Percent, Distinct, pd.Timestamp.now()]],
                                       columns=['SourceID', 'Server', 'db', 'Schema', 'Table', 'Column', 'Total_Columns_in_Table', 'Table_Size (GB)', 'Row', 'Nulls', 'Nulls_Percent', 'Distinct', 'Insert_time'])
                CONCAT.append(row_data)
                
            export(CONCAT, self.table if len(CONCAT) >= 1 else 0)
            
        except Exception as E:
            print(f'! {self.table}, {E}')

def run(counter, SourceID, Server, db, schema, table, Row, Size):
    Run_class = MetaData(counter, SourceID, Server, db, schema, table, Row, Size)
    Run_class.My_ThreadPool()

if __name__ == '__main__':
    Start = time.time()

    ERD() 
    
    with ThreadPoolExecutor(max_workers=20) as executer:
        to_do = []
        for counter, i in enumerate(df.index, 1):
            x = executer.submit(run, counter, df.loc[i, 'SourceID'], df.loc[i, 'Server'], df.loc[i, 'db'], 
                                df.loc[i, 'Schema'], df.loc[i, 'Table'], df.loc[i, 'Row'], df.loc[i, 'Size'])
            to_do.append(x)
        
        for future in to_do:
            res = future.result()
            
    timer(Start)
