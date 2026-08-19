from metadata import *
from utils import (futures,foreign_source ,job_source ,fn_ln_source ,cars_name ,color_source ,comparing_atba ,comparing_job ,comparing_fn_ln ,comparing_car 
,comparing_color ,algorithm_apply ,insert_time ,Reporter_types ,sourceID,insert_to_autoreporter)

Start ,ALL = time.time() ,list()
My_Atba ,My_job ,My_fn_ln ,My_cars ,My_Color= foreign_source() ,job_source() ,fn_ln_source() ,cars_name() ,color_source()

class Reporter:
    def __init__(
        self ,counter ,SourceID ,Server, db, schema, table, column,Row):
        self.counter = counter
        self.SourceID = SourceID
        self.Server = Server
        self.db = db
        self.schema = schema
        self.table = table
        self.column = column
        self.Row = Row

    def My_ThreadPool(self):
        try:
            print(f'{self.counter}) Reading... {self.table:35} Column == {self.column:25} Shape:{self.Row}')
            con_ = db_connecting(self.Server, self.db)
            try:
                Sample_data = pd.read_sql(f""" SELECT DISTINCT TOP(20000) [{self.column}] FROM [{str(self.schema)}].[{str(self.table)}] WHERE [{self.column}] IS NOT NULL """ ,con_)
            except:
                try:
                    Sample_data = pd.read_sql(f"""SELECT DISTINCT TOP(20000)CAST(CAST([{self.column}] AS NVARCHAR)AS NVARCHAR(MAX)) AS [{self.column}] FROM [{str(self.schema)}].[{str(self.table)}] WHERE [{self.column}] IS NOT NULL """,con_)
                except:
                    Sample_data = pd.read_sql(f"""SELECT DISTINCT TOP(20000) [{self.column}] FROM [{str(self.schema)}].[{str(self.table)}] WHERE [{self.column}] IS NOT NULL """,con_)
                    Sample_data[self.column] = Sample_data[self.column].apply(lambda x: x.decode("1256"))
            con_.close()

            if len(Sample_data) == 0:
                return 0
            Sample_len ,My_percent = len(Sample_data) ,list()

            Algorithm = ["national_code","shenase_meli","zip_code","Atba","mobile","hometel","sheba","idCard","plaque","Job","Fn_Ln","relational","Car","Color","date_detection","latitude","longitude"]

            for alg in Algorithm:
                if alg == "Atba":
                    My_percent.append(comparing_atba(Sample_data,self.column,My_Atba))

                elif alg == "Job":
                    My_percent.append(comparing_job(Sample_data,self.column,My_job))

                elif alg == "Fn_Ln":
                    My_percent.append(comparing_fn_ln(Sample_data,self.column,My_fn_ln) if ((Sample_len / self.Row) * 100 > 4 or len(Sample_data) > 1000) else 0)
                    
                elif alg == "Car":
                    My_percent.append(comparing_car(Sample_data,self.column,My_cars))

                elif alg == "Color":
                    My_percent.append(comparing_color(Sample_data,self.column,My_Color))

                else:
                    My_percent.append(algorithm_apply(Sample_data,self.column,alg))

            # At least one column should be more than 1%
            for i in My_percent:
                if float(i) > 1.0:
                    DATA = pd.DataFrame(data=[(self.SourceID ,self.Server ,self.db ,self.schema ,self.table ,self.column ,self.Row ,Sample_len 
                               ,My_percent[0],My_percent[1],My_percent[2],My_percent[3],My_percent[4],My_percent[5],My_percent[6],My_percent[7],My_percent[8]
                               ,My_percent[9],My_percent[10],My_percent[11],My_percent[12], My_percent[13],My_percent[14],My_percent[15],My_percent[16],insert_time())], 
                                columns=["SourceID","Server","db","Schema","Table","Column","Row","Sample_len","NationalCode","NationalID","ZipCode","Atba","Mobile","HomeTel","Sheba","IdCard","Plaque","Job","First/Last_Name",
                                "Relational","Car","Color","Date","Latitude","Longitude","Insert_time"])

                    ALL.append(DATA)
                    print(f'Inserted... {self.table} {self.column}')
                    break

        except Exception as E:
            print("!" * 15,self.table,E)


if __name__ == "__main__":

    def run(counter,SourceID,Server,db,schema,table,column,Row):

        Run_class = Reporter(counter,SourceID,Server,db,schema,table,column,Row)
        Run_class.My_ThreadPool()

    with futures.ThreadPoolExecutor(max_workers=20) as executor:
        to_do = []
        print(len(all_optimized_cols))

        for counter, i in enumerate(all_optimized_cols.index,1):
            x = executor.submit(run,counter,sourceID,all_optimized_cols.loc[i, "Server"],all_optimized_cols.loc[i, "db"],all_optimized_cols.loc[i, "SchemaName"],all_optimized_cols.loc[i, "TableName"],all_optimized_cols.loc[i, "ColumnName"], all_optimized_cols.loc[i, "Row"])
            to_do.append(x)

        for future in futures.as_completed(to_do):
            res = future.result()
            print(res)

    # Insert final result into SQL Server
    con_ = insert_to_autoreporter()
    pd.concat(ALL).to_sql("Reporter",con=con_,if_exists="append",index=False,dtype=Reporter_types)
    print("**** Inserted to SQL ****")

    timer(Start)

    con_.close()