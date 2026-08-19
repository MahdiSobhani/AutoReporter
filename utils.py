import numpy as np 
import pandas as pd 
import sqlalchemy as sql
import urllib
import jdatetime
from datetime import datetime 
from datetime import NOWTIME
import time 
from concurrent import futures
import pyodbc 
import os 
from sqlalchemy.exc import *
import warnings
from subprocess import *
import re
import gc
import geopandas as gpd
from modified import ClearPlaque
from shapely.geometry import Point
from scipy.spatial import cKDTree
warnings.filterwarnings('ignore')

flag = open('Flag.txt','r+') if os.path.exists('Flag.txt') else open('Flag.txt','a')

Cod3_Raghami = pd.read_csv('cod.csv')
Cod3_Raghami['Code'] = Cod3_Raghami['Code'].astype('str').str.zfill(3)
Cod3_zfill_list = Cod3_Raghami['Code'].to_list()

zipcode_city = pd.read_excel('Zip.xlsx')
zipcode_city = zipcode_city['Code'].astype('str')

keys = pd.read_excel('Relational_keys.xlsx')

none = ['nan','none','na','null']

metadata_types = {'SourceID':sql.types.BIGINT(),'Server':sql.types.NVARCHAR(20),'db':sql.types.NVARCHAR(80),'Schema':sql.types.NVARCHAR(80),'Table':sql.types.NVARCHAR(200),'Column':sql.types.NVARCHAR(200),
                  'total_table_in_column':sql.types.SMALLINT(),'Table_Size (GB)':sql.types.Float(5),'Row':sql.types.BIGINT(),'Nulls':sql.types.BIGINT(),'Null_Percent':sql.types.Float(5),'Distinct':sql.types.BIGINT(),
                  'InsertTime':sql.types.DateTime()}

Reporter_types = {'SourceID':sql.types.BIGINT(),'Server':sql.types.NVARCHAR(20),'db':sql.types.NVARCHAR(80),'Schema':sql.types.NVARCHAR(80),'Table':sql.types.NVARCHAR(200),'Column':sql.types.NVARCHAR(200),'Row':sql.types.BIGINT(),
                  'Sample_len':sql.types.Float(5),'NationalCode':sql.types.Float(5),'NationalID':sql.types.Float(5),'ZipCode':sql.types.Float(5),'Atba':sql.types.Float(5),'Mobile':sql.types.Float(5)
                  ,'HomeTel':sql.types.Float(5),'Sheba':sql.types.Float(5),'IDCard':sql.types.Float(5),'Plaque':sql.types.Float(5),'Job':sql.types.Float(5),'First/LastName':sql.types.Float(5),
                  'Car':sql.types.Float(5),'Color':sql.types.Float(5),'Latitude':sql.types.Float(5),'Longitude':sql.types.Float(5),'Date':sql.types.Float(5),'Relational':sql.types.Float(5),'InsertTime':sql.types.DateTime()}

NC_on_Date_types = {'NationalCode':sql.types.BIGINT(),'BirthDate':sql.types.INT(),'id':sql.types.INT()}

zip_dtypes = {'id':sql.types.BIGINT(),'ZipCode':sql.types.BIGINT()}

city_NationalCode = {'id':sql.types.BIGINT(),'City':sql.types.NVARCHAR(20),'Count':sql.types.INT(),'Percent':sql.types.Float(5)}

city_NationalCode = {'id':sql.types.BIGINT(),'City':sql.types.NVARCHAR(20),'Count':sql.types.INT(),'Percent':sql.types.Float(5)}

city_lat_long = {'City':sql.types.NVARCHAR(50),'Percent':sql.types.Float(5),'id':sql.types.BIGINT()}

Reporte_Finall = {'SourceID':sql.types.BIGINT(),'Server':sql.types.NVARCHAR(20),'db':sql.types.NVARCHAR(80),'Schema':sql.types.NVARCHAR(80),'Table':sql.types.NVARCHAR(200),
                  'Column':sql.types.NVARCHAR(200),'Algorithm':sql.types.Float(5),'InsertTime':sql.types.DateTime()}

Iran_min_max = {'min_lat':25 ,'max_lat':30.75 ,'min_long':44 ,'max_long':63.23}
world = gpd.read_file('countries.geojson')
iran_border = world[world['name'] == 'iran']

server_search ,db_search ,sourceID ,connection_name ,sql_orcl = 'localhost','Anything',7777,'information','SQL'


def insert_time() -> str:
    date = jdatetime.date.today()
    date = str(date).split[0]
    Now = NOWTIME.datetime.now().strftime('%H:%M:%S:')
    insert_time = date +' '+Now
    return insert_time


def db_connection(Server:str ,UID:str ,Password:int ,db:str) -> str:
    connection_str = (r'DRIVER={SQL SERVER};' f"SERVER={Server}; UID={UID}; PWD={Password}; DATABASE={db};")
    conncetion_uri = f'mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_str)}'
    engine = sql.create_engine(conncetion_uri ,fast_executemany=True)
    return engine.connect()


def read_datamart() -> str:
    return db_connection('localhost','username','QWE@zxc@345','DataMart')


def insert_to_autoETL() -> str:
    return db_connection('localhost','username','QWE@zxc@345','AutoETL')


def insert_to_autoreporter() -> str:
    return db_connection('localhost','username','QWE@zxc@345','AReporter')


def zipcode_source() -> str:
    con = db_connection('localhost','username','QWE@zxc@345','AReporter')
    zipcode = pd.read_sql('Select Distinct ZipCode From Realestate',con=con)
    con.close()
    zipcode['ZipCode'] = zipcode['ZipCode'].astype('str')
    return zipcode


def mobile_source() -> str:
    con = db_connection('localhost','username','QWE@zxc@345','contact')
    mobile = pd.read_sql('Select Distinct FullNumberINT From PhoneNumbs',con=con)
    con.close()
    mobile['FullNumberINT'] = mobile['FullNumberINT'].astype('int64')
    return mobile


def nationalcode_source() -> str:
    con = db_connection('localhost','username','QWE@zxc@345','mypesrons')
    ncode = pd.read_sql('Select Distinct nationalcode From NCcode',con=con)
    con.close()
    ncode['NationalCode'] = ncode['NationalCode'].astype('str').str.zfill(10)
    return ncode


def nationalcode_date_source() -> str:
    con = db_connection('localhost','username','QWE@zxc@345','mypesrons')
    ncode = pd.read_sql('Select Distinct nationalcode,birthdate From NCcode where validation = True and len(birthdate) = 10',con=con)
    con.close()
    ncode['NationalCode'] = ncode['NationalCode'].astype('str').str.zfill(10)
    return ncode


def shenase_meli_source() -> str:
    con = db_connection('localhost','username','QWE@zxc@345','calId')
    ncode = pd.read_sql('Select Distinct nationalcode,birthdate From NCcode where validation = True and len(birthdate) = 10',con=con)
    con.close()
    ncode['NationalCode'] = ncode['NationalCode'].astype('str')
    return ncode


def foreign_source() -> str:
    con = db_connection('localhost','username','QWE@zxc@345','mypesrons')
    ncode = pd.read_sql('Select Distinct Code From Fperson',con=con)
    con.close()
    return set(ncode['Code'])


def fn_ln_source() -> str:
    con = db_connection('localhost','username','QWE@zxc@345','mypesrons')
    all_ = pd.read_sql('Select * From fn_ln',con=con)
    con.close()
    all_['Name'] = all_['Name'].apply(edit_font_Fn_Ln)
    return set(all_['Name'])


def comparing_atba(sample_data:pd.DataFrame ,column:str ,atba_source_:set) -> float:
    sample_data[f'{column}_'] = sample_data[column].astype('str')
    set_col = set(sample_data[f'{column}_'])
    avarde = len(set_col & atba_source_)
    del sample_data[f'{column}_']
    try:
        sml = round((avarde / len(set_col)) * 100, 2)
    except ZeroDivisionError:
        sml = 0
    return sml


def comparing_NationalCode(sample_data:pd.DataFrame ,column:str, source:set) -> float:
    sample_data[f'{column}_'] = sample_data[column].astype('str').str.zfill(10)
    set_col = set(sample_data[f'{column}_'])
    avarde = len(set_col & source)
    del sample_data[f'{column}_']
    try:
        sml = round((avarde / len(set_col)) * 100, 2)
    except ZeroDivisionError:
        sml = 0
    return sml


def comparing_job(Sample_data:pd.DataFrame ,column:str ,source:set) -> float:
    Sample_data[f'{column}_'] = Sample_data[column].astype('str')
    Sample_data[f'{column}_'] = Sample_data[f'{column}_'].apply(edit_font)
    Sample_data[f'{column}_'] = Sample_data[f'{column}_'].str.replace(r'[0-9]','',regex=True)
    Sample_data[f'{column}_'] = Sample_data[f'{column}_'].str.replace(r'[A-Za-z]','',regex=True)
    Sample_data[f'{column}_'] = Sample_data[f'{column}_'].apply(zip_)
    set_col = set(Sample_data[f'{column}_'])
    avarde = len(set_col & source)
    del Sample_data[f'{column}_']
    try:
        sml = round((avarde / len(set_col)) * 100, 2)
    except ZeroDivisionError:
        sml = 0
    return sml


def comparing_fn_ln(Sample_data:pd.DataFrame ,column:str, source:set) -> float:
    Sample_data[f'{column}_'] = Sample_data[column].apply(edit_font_Fn_Ln)
    set_col = set(Sample_data[f'{column}_'])
    avarde = len(set_col & source)
    del Sample_data[f'{column}_']
    try:
        sml = round((avarde / len(set_col)) * 100, 2)
    except ZeroDivisionError:
        sml = 0
    return sml


def cars_name() -> set:
    cars_name = pd.read_csv(r'Cars_name.csv')
    cars_name['VehicleSystem'] = cars_name['VehicleSystem'].apply(edit_font)
    cars_name['VehicleSystem'] = cars_name['VehicleSystem'].apply(zip_)
    cars_name = cars[(cars['VehicleSystem'] != 'DAF') & (cars['VehicleSystem'] != 'TNK')]
    return set(cars_name['VehicleSystem'])


def comparing_car(Sample_data:pd.DataFrame ,column:str, source:set) -> float:
    Sample_data[f'{column}_'] = Sample_data[column].apply(edit_font)
    Sample_data[f'{column}_'] = Sample_data[f'{column}_'].apply(zip_)
    set_col = set(Sample_data[f'{column}_'])
    avarde = len(set_col & source)
    del Sample_data[f'{column}_']
    try:
        sml = round((avarde / len(set_col)) * 100, 2)
    except ZeroDivisionError:
        sml = 0
    return sml


def color_source() -> str:
    x = pd.read_csv('colors.txt')
    x['colors'] = x['colors'].apply(edit_font_Fn_Ln)
    return set(x['Colors'])


def comparing_color(sample_data:pd.DataFrame ,column:str, color:set) -> float:
    sample_data[f'{column}_'] = sample_data[column].astype(edit_font_Fn_Ln)
    set_col = set(sample_data[f'{column}_'])
    avarde = len(set_col & color)
    del sample_data[f'{column}_']
    try:
        sml = round((avarde / len(set_col)) * 100, 2)
    except ZeroDivisionError:
        sml = 0
    return sml


def show_tables(server:str ,db:str) -> pd.DataFrame:
    con = db_connection(server ,db)
    All_tables = con.execute('Select TABLE_SCHEMA, TABLE_NAME from Information_Schema.Tables Where Table_Type="Base Table";')
    tables = [row for row in All_tables]
    con.close()
    return tables


def show_optimize_columns(server:str ,db:str) -> pd.DataFrame:
    con = db_connection(server ,db)
    All_columns = con.execute(''' SELECT 
    SCHEMA_NAME(t.schema_id) AS SchemaName,
    t.name AS TableName,
    c.column_id AS ColumnOrder,
    c.name AS ColumnName,
    st.name AS DataType,
    
    CASE 
        WHEN c.max_length = -1 THEN 'MAX' 
        ELSE CAST(c.max_length AS VARCHAR) 
    END AS MaxLength,
    
    c.precision AS Precision,
    c.scale AS Scale,
    
    c.is_nullable AS IsNullable,
    c.is_identity AS IsIdentity,
    
    OBJECT_DEFINITION(c.default_object_id) AS DefaultValue
    FROM 
        sys.tables t
    INNER JOIN 
        sys.columns c ON t.object_id = c.object_id
    INNER JOIN 
        sys.types st ON c.user_type_id = st.user_type_id AND c.system_type_id = st.system_type_id
    WHERE 
        t.is_ms_shipped = 0 
    ORDER BY 
        SchemaName, TableName, ColumnOrder; ''')
    tables = [row for row in All_columns]
    con.close()
    return pd.DataFrame(tables)


def space_used(schema:str ,table:str ,server:str ,db:str) -> tuple:
    INFO = f'sp_spaceused"[{str(schema)}].[{str(table)}]" '
    INFO = pd.read_sql(INFO ,db_connection(server ,db))
    INFO = INFO.values[0]
    row = int(INFO[1])
    size = '%.3f'%(int(INFO[2].split(' ')[0]) / 1024 /1024)
    return schema ,table ,server ,db ,row ,size


def export(concat_:pd.DataFrame ,total_tables:int ,table:str) -> None:
    export = pd.concat(concat_)
    export['total_tables_in_db'] = total_tables
    export['nulls_percent'].fillna(0 ,inplace=True)
    export = export[['sourceID','server','db','schema','table','column','row','nulls','nulls_percent','Distinct','total_columns_in_table','total_tables_in_db','table_size (GB)','insert_time']]
    export.to_sql(f'metadata',con=insert_to_autoreporter() ,if_exist='append',index=False ,dtype=metadata_types)
    print(f'Inserted...{table}')    


def percent_calculate(sample_data:pd.DataFrame ,column:str) -> float:
    per = sample_data[column].value_counts(normalize=True).reset_index()
    percent = 0
    if True in per[column].unique():
        percent = '%.2f'%(per[per[column] == True]['proportion'].values[0] * 100)  
        if percent[-2:] == '00':
            percent = percent[:-3]
    return percent


def algorithm_apply(sample_data:pd.DataFrame ,column:str ,alg:str) -> float:
    if alg == relational and 100 in list(map(lambda x:100 if x in edit_font(column.replace(' ','').replace('-','')).lower() else 0,Keys)):
        return 100
    sample_data[f'{column}_'] = sample_data[column].apply(alg)
    prcnt = percent_calculate(sample_data ,f'{column}_')
    del sample_data[f'{column}_']
    return prcnt


def relational(x:str) -> bool:
    x = str(x).lower()
    if x in none:
        return np.nan
    elif edit_font(x.replace(' ','').replace('','')) in Keys:
        return True
    return False


def relational_source_ETL() -> list:
    global Keys
    Keys['key'] = Keys['key'].apply(edit_font)
    Keys['key'] = Keys['key'].apply(del_space)
    Keys = Keys['key'].to_list()


def atba_preprocessing(x:str) -> str:
    x= str(x).lower()
    if '.' in x and len(x) >= 9:
        return x[:x.find('.')] 
    elif x.isnumeric() and len(x) >= 7:
        return x
    else:
        return np.nan 


def edit_font(x:str) -> str:
    return str(x).replace('هً','').replace('آ','ا').replace('یٍ','ی')


def edit__Fn_Ln(x:str) -> str:
    return str(x).replace(' ','').replace('_','').replace('-','').replace('/','').replace('\\','').replace(',','')


def zip_(x:str) -> str:
    x = str(x).strip()
    return x.replace('!','').replace('?','').replace('@','').replace('$','')


def edit_font_Fn_Ln(x:str) -> str:
    translation = str.maketrans({'ي': 'ی','ى': 'ی','ك': 'ک','ة': 'ه','ۀ': 'ه','ؤ': 'و','إ': 'ا','أ': 'ا','ٱ': 'ا','ئ': 'ی',}) 
    return x.translate(translation)


def numbers_to_standard(x:str) -> str:
    return str(x).replace('۰','0').replace('۱','1').replace('۲','2').replace('۳','3').replace('۴','4').replace('۵','5').replace('۶','6').replace('۷','7').replace('۸','8').replace('۹','9')


def del_space(x:str) -> str:
    return x.replace(' ','')


def to_int_zfl(x:str) -> str:
    x = str(x).lower()
    if x in none:
        return np.nan
    elif '.' in x:
        x = x[:x.find('.')]
        return x.zfill(10)
    return x.zfill(10)


def len_(x:str) -> int:
    return len(str(x))


def job_source() -> set:
    job = pd.read_csv(r'job_source.csv')
    job['Jobdesc'] = job['Jobdesc'].apply(edit_font)
    job = set(job['jobdesc'])
    job.discard('')
    job.discard(' ')
    return job


def zip_code(x:int) -> bool:
    x = str(x).lower()
    if x in none:
        return np.nan
    x = re.findall('\b\d{10}\b',str(x))
    if len(x) == 1 and re.findall(r'\b(?!(\d)\1{3})[13-9]{4}[1346-9][13-9]{5}\b' ,str(x)):
        return True
    if len(x) >= 1:
        for i in range(0 ,len(x)):
            if re.findall(r'\b(?!(\d)\1{3})[13-9]{4}[1346-9][13-9]{5}\b' ,x[i]):
                return True
        return False
    return False    


def national_code(code:int) -> bool:
    code = str(code).lower()
    if code in none:
        return np.nan
    code = code[ :code.find('.')] if '.' in code else code
    if 8 <= len(code) <= 10:
        code = code.zfill(10)
        if not code.isnumeric() or code[:3] not in Cod3_Raghami['Code'].astype('str').str.zfill(3).tolist():
            return False
        total = 0
        control_digit = int(code[-1])
        for digit ,index in zip(code ,range(10 ,1 ,-1)):
            total += int(digit) * index
        reminder = total %11
        if reminder < 2:
            if (reminder == control_digit) and (code[:3] in Cod3_Raghami['Code'].astype('str').str.zfill(3).tolist()):
                return True
        else:
            if (11 - reminder == control_digit) and (code[:3] in Cod3_Raghami['Code'].astype('str').str.zfill(3).tolist()):
                return 
        return False
    else:
        return False


def shenase_meli(x:int) -> str:
    x = str(x).lower()
    if (len(x) == 11) and (x.isnumeric()):
        counter, s = 0, 0
        total = 0
        Control = int(x[-1:])
        Dahgan = int(x[-2:-1]) + 2
        Zarib = [29, 27, 23, 19, 17]

        for I in x:
            if counter == 10:
                break
            counter += 1
            Plus_dahgan = (int(I) + Dahgan)
            total += Plus_dahgan * Zarib[s]
            s += 1
            if s == 5:
                s = 0

        if total % 11 == 10:
            total = 0
            if total == Control:
                return True
            else:
                return False

        elif total % 11 == Control:
            return True
        else:
            return False
    elif x in None:
        return np.nan
    return False


def mobile(x:str) -> bool:
    x = str(x).lower()
    if x in none:
        return np.nan
    x = x[:x.find('.')] if '.' in x else x
    x = ''.join(re.findall(r'(\d+)', str(x)))

    if (re.fullmatch(r"((0?9)|(\+?989)|(\+?00989))((14)|(13)|(12)|(19)|(18)|(17)|(15)|(16)|(11)|(10)|(90)|(91)|(92)|(93)|(94)|(95)|(96))\d{7}", x) or
        re.fullmatch(r"((0?9)|(\+?989)|(\+?00989))((32)|(30)|(33)|(35)|(36)|(37)|(38)|(39)|(00)|(01)|(02)|(03)|(04)|(05)|(41))\d{7}", x) or 
        re.fullmatch(r"((0?9)|(\+?989)|(\+?00989))((20)|(21)|(22)|(23))\d{7}", x) or          # Rightel
        re.fullmatch(r"((0?9)|(\+?989)|(\+?00989))((9999)|(999))\w?\d{3}\W?\d{4}", x) or      # samatel
        re.fullmatch(r"((0?9)|(\+?989)|(\+?00989))(32)\d{7}", x)   or                         # talia
        re.fullmatch(r"((0?9)|(\+?00989)|(\+?989))(34)\d{7}", x)):                            # kish
        return True
    return False

 
def hometel(hm:str) -> bool:
    hm = str(hm).lower()
    if hm in none:
        return np.nan
    hm = hm[:hm.find('.')] if '.' in hm else hm
    hm = '@@@'.join(re.findall(r'(\d+)', str(hm)))
    hm = hm.split('@@@')

    for x in hm:
        x = x.zfill(11)
        if len(x) >= 12 and x[:2] == "98":
            x = '0' + x[2:]
            if (x[:3] in Area_Cod) and (x.isnumeric()):
                return True

        elif len(x) >= 10:
            if x[:2] == "98":
                x = '0' + x[2:]
                if (x[:3] in Area_Cod) and (len(x) == 11) and (x.isnumeric()):
                    return True

            elif x[:4] == "0098":
                x = '0' + x[4:]
                if (x[:3] in Area_Cod) and (len(x) == 11) and (x.isnumeric()):
                    return True

            elif (x[0] == '0') and (x[:3] in Area_Cod) and (len(x) == 11) and (x.isnumeric()):
                return True

            elif (x[:2] in Area_Cod) and (x[2] == x[3]) and (len(x) == 10) and (x.isnumeric()):
                return True
    return False


def sheba(x:int) -> bool:
    x = str(x).lower()
    if x in none:
        return np.nan

    x = x[:x.find('.')] if '.' in x else x
    x = ''.join(re.findall(r'(\d+)', str(x)))

    if len(x) == 24:
        x += '1827'
        x += x[:2]
        I = int(x[2:])

        if I % 97 == 1:
            return True
        return False
    else:
        return False


def idCard(x:str) -> bool:
    x = str(x).lower()
    if x in none:
        return np.nan

    x = x[:x.find('.')] if '.' in x else x
    if re.findall(r"^\d[a-z]\d{8}$", x):
        return True
    return False

def plaque(x:str) -> bool:
    x = str(x).lower()

    if x in none:
        return np.nan

    return ClearPlaque(x).check_form()


def latitude(x:float) -> bool:
    x = str(x).lower()
    if x in none:
        return np.nan
    try:
        after_dot = x[x.find('.') + 1:] if '.' in x else x
        if len(x) >= 5 and (x[2] == '.') and (re.findall(r"[1-9]", after_dot)) and (Iran_min_max["min_lat"] <= float(x[:2]) <= Iran_min_max["max_lat"]):
            return True
        return False
    except:
        return False

 
def longitude(xLfloat) -> bool:
    x = str(x).lower()
    if x in none:
        return np.nan
    try:
        after_dot = x[x.find('.') + 1:] if '.' in x else x
        if len(x) >= 5 and (x[2] == '.') and (re.findall(r"[1-9]", after_dot)) and (Iran_min_max["min_long"] <= float(x[:2]) <= Iran_min_max["max_long"]):
            return True
        return False
    except:
        return False


def miladi_to_shamsi(x:int) -> int:
    x = str(x).lower()
    if x in none:
        return np.nan

    x = ''.join(re.findall(r'(\d+)', str(x)))
    try:
        if int(x[:4]) >= 1850:
            return jdatetime.date.fromgregorian(year=int(x[:4]) ,month=int(x[4:6]), day=int(x[6:8])).strftime('%Y%m%d')
        return x
    except:
        return None


def timer(Start):
    TIME = time.time() - Start
    TIME = f'{int(TIME // 60)}:{int(TIME % 60)}'
    print('Time', TIME)
    print('\n', 20 * '*', 20 * '*', 'Finished ThreadPool', 20 * '*')


Area_Cod = ['41', '041','44', '044','45', '045','31', '031','84', '084','77', '077','21', '021','38', '038','54','054', 
            '51', '051','56', '056','58', '058','61', '061','24', '024','23', '023','71', '071','26', '026','25', '025','81','081''28','028',
            '87','087','34', '034','83', '083','74', '074','17', '017','13', '013','66', '066','11', '011','35','035','86', '086','76', '076']

relational_source_ETL()