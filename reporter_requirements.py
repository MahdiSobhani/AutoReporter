from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from reportlab.lib.utils import ImageReader
from bidi.algorithm import get_display
from utils import *

Start = time.time()

NC_Source,total_NC,total_valid_NC_not_in_source = (set(nationalcode_source()['NationalCode']),set(),set())
ZP_Source,total_ZP,total_valid_ZP_not_in_source = (set(zipcode_source()['ZipCode']),set(),set())
Shnase_meli_source,total_NCid,total_valid_NCid_not_in_source = (set(shenase_meli_source()['CompanyNationalCode']),set(),set())
NC_Date_Source = nationalcode_date_source()
All_lat_long,City_by_lat_long = list(),list()


def combine_NC_Date(flt):
    nc_ = flt[flt['NationalCode'] >= 30][['Schema','Table','Column']].rename(columns={'Column':'NC'})
    date_ = flt[flt['Date'] >= 80][['Schema','Table','Column']].rename(columns={'Column':'Date'})
    NC_Date = pd.merge(nc_,date_,how='inner',on=['Schema','Table'])
    NC_Date = NC_Date[NC_Date['NC'] != NC_Date['Date']].reset_index(drop=True)
    return NC_Date


def combine_latitude_longitude(flt):
    lt = flt[flt['Latitude'] >= 90][['Schema','Table','Column']].rename(columns={'Column':'Latitude'})
    lg = flt[flt['Longitude'] >= 90][['Schema','Table','Column']].rename(columns={'Column':'Longitude'})
    lt_lg = pd.merge(lt,lg,how='inner',on=['Schema','Table'])
    return lt_lg


def valid_calculating(alg,Column,schema,table,Server,db):
    con_ = db_connection(Server,db)
    try:
        df = pd.read_sql(f"""SELECT DISTINCT [{Column}] FROM [{str(schema)}].[{str(table)}] WHERE [{Column}] IS NOT NULL """,con=con_)
    except:
        df = pd.read_sql(f"""SELECT DISTINCT CAST(CAST([{Column}] AS nvarchar) AS nvarchar(150)) AS [{Column}] FROM [{str(schema)}].[{str(table)}] WHERE [{Column}] IS NOT NULL """,con=con_)
    con_.close()

    if alg == 'NationalCode':
        function = national_code
        df[Column] = df[Column].apply(to_int_zfl)
        total_NC.update(set(df[Column].astype('str')))
        return valid_not_in_source(df,NC_Source,Column,function)

    elif alg == 'ZipCode':
        function = zip_code
        df[Column] = df[Column].apply(extract_zipcode_number)
        return valid_not_in_source(df,ZP_Source,Column,function)

    elif alg == 'NationalID':
        function = shenase_meli
        total_NCid.update(set(df[Column].astype('str')))
        return valid_not_in_source(df,Shnase_meli_source,Column,function)


def valid_not_in_source(df,Source,Column,function):
    T = set(df[Column].astype('str')) - Source
    Not_in_Source = pd.DataFrame(T,columns=[Column])

    if function == zip_code:
        DF = df[(df[Column] != False) & (df[Column].notnull())]
        T = set(DF[Column].astype('str')) - Source
        T = set(T)

        total_ZP.update(set(DF[(DF[Column] != False) & (DF[Column].notnull())][Column].astype('str')))

        Not_in_Source = pd.DataFrame(T,columns=[Column])
        Not_in_Source[f'{Column}_bool'] = True
        return len(df),Not_in_Source

    Not_in_Source[f'{Column}_bool'] = Not_in_Source[Column].apply(function)
    return len(df),Not_in_Source


def to_final1(SourceID,Column,Not_in_Source,Server,db,schema,table,alg,Row,len_dis):
    CHECK = Not_in_Source[f'{Column}_bool'].unique()

    if True in CHECK:
        No_valid = len(Not_in_Source[Not_in_Source[f'{Column}_bool'] == True])
        All_Valid = Not_in_Source[Not_in_Source[f'{Column}_bool'] == True]

        if alg == 'NationalCode':
            total_valid_NC_not_in_source.update(set(All_Valid[Column].astype('str')))

        if alg == 'ZipCode':
            total_valid_ZP_not_in_source.update(set(All_Valid[Column].astype('str')))
            All_Valid.rename(columns={Column:'ZipCode'},inplace=True)
            All_Valid['id'] = SourceID
            con_ = insert_to_autoreporter()
            All_Valid[['id','ZipCode']].to_sql('Valid_ZipCode',con=con_,if_exists='append',index=False,dtype=zip_dtypes)
            con_.close()

        if alg == 'NationalID':
            total_valid_NCid_not_in_source.update(set(All_Valid[Column].astype('str')))

        Percent = Not_in_Source[f'{Column}_bool'].value_counts(normalize=True).reset_index()
        Percent['Percent'] = Percent['proportion'] * 100
        PR = Percent[Percent[f'{Column}_bool'] == True]['Percent'].values[0].round(2)

        DATA = [(SourceID,Server,db,schema,table,Column,alg,Row,len_dis,len(Not_in_Source),No_valid,PR,insert_time())]

        total = pd.DataFrame(DATA,columns=['SourceID','Server','db','Schema','Table','Column','Algorithm','Row','Distinct','Not_in_Source','Valid Number','Percent','InsertTime'])

        con_ = insert_to_autoreporter()
        total.to_sql('Reporter_Final',con=con_,if_exists='append',index=False,dtype=Reporte_Finall)
        con_.close()

        print('Inserted to SQL...',Column)


def calculate_nc_on_date(Schema,Table,NC,Date):
    con_ = db_connection(server_search ,db_search)
    sample = pd.read_sql(f"""select DISTINCT top(10000) [{str(NC)}],[{str(Date)}] from [{str(Schema)}].[{str(Table)}] WHERE (len([{str(Date)}]) >= 8) AND ([{str(NC)}] IS NOT NULL) """,con=con_)
    con_.close()

    sample[Date] = sample[Date].apply(miladi_to_shamsi)
    sample = sample[sample[Date].notnull()]
    sample['NC_Date'] = sample[NC].astype('str').str.zfill(10) + sample[Date].astype('str').apply(lambda x:x[:2])

    avrde = len(set(sample['NC_Date']) & NC_Date_Source)
    try:
        sm1 = '%.2f' % ((avrde / len(sample)) * 100)
    except:
        sm1 = 0

    if float(sm1) >= 50:
        print(sm1,f"% {Table} : [{NC} == {Date}]")
        con_ = db_connection(server_search ,db_search)

        total = pd.read_sql(f"""select DISTINCT [{str(NC)}],[{str(Date)}] from [{str(Schema)}].[{str(Table)}] where [{str(Date)}] IS NOT NULL """,con=con_)
        con_.close()

        total[NC] = total[NC].astype('str').str.zfill(10)
        avrde = set(total[NC]) - NC_Source
        Not_in_Source = pd.DataFrame(avrde,columns=[NC])
        Not_in_Source[f'{NC}_'] = Not_in_Source[NC].apply(national_code)
        valid = Not_in_Source[Not_in_Source[f'{NC}_'] == True][NC]

        join = pd.merge(valid,total,how='inner',on=NC).rename(columns={NC:'NationalCode',Date:'BirthDate'})
        join['id'] = sourceID
        join['BirthDate'] = join['BirthDate'].apply(miladi_to_shamsi)

        con_ = insert_to_autoreporter()
        join.to_sql('NationalCode_on_Date',con=con_,if_exists='append',index=False,dtype=NC_on_Date_types)
        con_.close()

    else:
        print(f'----------------/SKIPED\\----------------{Table} : {NC} |= {Date}')


def detection_city_from_NC(total_NC,Cod3_Raghami,sourceID):
    print('City_NationalCode_Calculating...')

    total_NC = pd.DataFrame(total_NC,columns=['NationalCode'])
    total_NC['NationalCode'] = total_NC['NationalCode'].astype('str').str.zfill(10)

    ''' 
    print(f'Len All NC For Apply national_code: {len(total_NC)}')               # city_nc on only valid NC
    total_NC['0'] = total_NC['NationalCode'].apply(national_code)
    total_NC = total_NC[total_NC['0'] == True] 
    '''

    total_NC['NationalCode'] = total_NC['NationalCode'].apply(lambda x:x[:3])
    join = pd.merge(total_NC,Cod3_Raghami,how='inner',left_on='NationalCode',right_on='Code')
    prcnt = (join['City'].value_counts(normalize=True) * 100).round(2).reset_index().head(20)
    no_ = join['City'].value_counts().reset_index().head(20)

    final1 = pd.concat([prcnt,no_['count']],axis=1)
    final1.rename(columns={'proportion':'Percent','count':'Count'},inplace=True)
    final1['id'] = sourceID
    final1 = final1[['id','City','Count','Percent']]

    con_ = insert_to_autoreporter()
    final1.to_sql('City_NationalCode',con=con_,if_exists='append',index=False,dtype=City_NationalCode)
    con_.close()


def detection_city_from_ZP(total_ZP,ZipCode_City,sourceID):
    print('City_ZipCode_Calculating...')
    total_ZP = pd.DataFrame(total_ZP,columns=['3ZipCode'])
    total_ZP['3ZipCode'] = total_ZP['3ZipCode'].apply(extract_3index_zipCode)

    join = pd.merge(ZipCode_City,total_ZP,how='inner',left_on='Code',right_on='3ZipCode')

    prcnt = (join['City'].value_counts(normalize=True) * 100).round(2).reset_index().head(20)
    no_ = join['City'].value_counts().reset_index().head(20)

    final1 = pd.concat([prcnt,no_['count']],axis=1)
    final1.rename(columns={'proportion':'Percent','count':'Count'},inplace=True)
    final1['id'] = sourceID
    final1 = final1[['id','City','Count','Percent']]

    con_ = insert_to_autoreporter()
    final1.to_sql('City_ZipCode',con=con_,if_exists='append',index=False,dtype=City_ZipCode)
    con_.close()


def extract_3index_zipCode(x):
    x = str(x).lower()
    if x in none:
        return np.nan

    x = (x[:x.find(',')]if ',' in x else x)
    x = re.findall(r'\d{10}',str(x))

    if len(x) >= 1:
        # if more than 1 zipcode in a sentence
        for i in range(0,len(x)):
            if re.findall(r'\b(?!(\d)\1{3})[13-9][4][1346-9][13-9]{5}\b',x[i]):
                # return True
                return x[0][:3]
        return False

    return False


def extract_zipcode_number(x):
    x = str(x).lower()
    if x in none:
        return np.nan

    # x = x[:x.find(',')] if ',' in x else x
    x = re.findall(r'\b\d{10}\b',str(x))

    if (len(x) == 1 and re.findall(r'\b(?!(\d)\1{3})[13-9][4][1346-9][13-9]{5}\b',str(x))):
        return x[0]

    if len(x) > 1:
        # if more than 1 zipcode in a sentence
        for i in range(0,len(x)):
            if re.findall(r'\b(?!(\d)\1{3})[13-9][4][1346-9][13-9]{5}\b',x[i]):
                return x[i]
        return False
    return False


def cities_distribution():
    detection_city_from_ZP(total_ZP,ZipCode_City,sourceID)
    detection_city_from_NC(total_NC,Cod3_Raghami,sourceID)
    calculate_lat_long()
    print("cities applied...")
    print(f"NationalCode : Total_valid_NC_not_in_source {len(total_valid_NC_not_in_source)}")
    print(f"ZipCode : Total_valid_ZP_not_in_source {len(total_valid_ZP_not_in_source)}")
    print(f"NCid : Total_valid_NCid_not_in_source {len(total_valid_NCid_not_in_source)}")


def extract_lat_on_long(Schema,Table,lat,long):
    con_ = db_connection(server_search ,db_search)
    sample = pd.read_sql(f""" SELECT DISTINCT [{str(lat)}] AS LAT, [{str(long)}] AS LONG FROM [{str(Schema)}].[{str(Table)}] WHERE [{str(lat)}] IS NOT NULL AND [{str(long)}] IS NOT NULL """,con=con_)
    con_.close()
    All_lat_long.append(sample)


def calculate_lat_long():
    if len(All_lat_long) > 1:
        sample = pd.concat(All_lat_long).drop_duplicates()
        sample['city'] = sample.apply(detect_lat_long,axis=1)
        city_prcnt = (sample['city'].value_counts(normalize=True) * 100).round(2).reset_index().head(20)
        city_prcnt['id'] = sourceID
        city_prcnt.rename(columns={'proportion':'Percent'},inplace=True)
        con_ = insert_to_autoreporter()
        city_prcnt.to_sql('City_latitude_longitude',con=con_,if_exists='append',index=False,dtype=City_lat_long)
        con_.close()


columns_location = ['geonameid','name','asciiname','alternatenames','latitude','longitude','feature_class','feature_code','country_code','cc2','admin1_code','admin2_code','admin3_code','admin4_code','population','elevation','dem','timezone','modification_date']
df = pd.read_csv(r'E:\AutoReporter\AutoReport\Requirement\IR.txt',sep='\t',names=columns_location,low_memory=False)


def mapping_city_lat_long(x):
    if x == 15:return 'گلستان'
    if x == 35:return 'مازندران'
    if x == 7:return 'قزوین'
    if x == 28:return 'اصفهان'
    if x in [42,30]:return 'چهارمحال بختیاری'
    if x == 13:return 'آذربایجان شرقی'
    if x == 20:return 'کردستان'
    if x == 33:return 'آذربایجان غربی'
    if x == 26:return 'گیلان'
    if x == 4:return 'خراسان رضوی'
    if x == 1:return 'آذربایجان غربی'
    if x == 8:return 'قم'
    if x == 9:return 'یزد'
    if x == 23:return 'کرمان'
    if x == 37:return 'البرز'
    if x == 43:return 'خراسان شمالی'
    if x == 34:return 'مرکزی'
    if x == 11:return 'خراسان جنوبی'
    if x == 40:return 'یزد'
    if x == 25:return 'سمنان'
    if x == 32:return 'اردبیل'
    if x == 10:return 'ایلام'
    if x == 16:return 'کردستان'
    if x == 41:return 'خراسان جنوبی'
    if x == 5:return 'کهگیلویه و بویر احمد'
    if x == 22:return 'بوشهر'
    if x == 3:return 'چهارمحال و بختیاری'
    if x == 36:return 'زنجان'
    if x == 38:return 'قزوین'
    if x == 44:return 'البرز'
    if x == 39:return 'قم'
    if x == 0.17:return 'قشم'


def editing_lat_long(x):
    asciiname = x['asciiname']
    code = x['admin1_code']

    if asciiname in ['Gonbade - Kabus','Shahrestan-e Mashhad','Kalat']:
        return 42.0
    if asciiname == 'Faramand-eye Shahrestan-e Qeshm':
        return 0.17

    return code


def find_nearest_city_lat_long(lat,lon):
    coords = city_lat_long_edited[['latitude','longitude']].values
    tree = cKDTree(coords)
    dist,idx = tree.query([lat,lon],k=1)
    nearest_city = city_lat_long_edited.iloc[idx]['City']
    return nearest_city


def cities_lat_long_preprocessing():
    cities = df[df['feature_class'].isin(['A'])]
    cities['admin1_code'] = cities.apply(editing_lat_long,axis=1)
    cities['City'] = cities['admin1_code'].apply(mapping_city_lat_long)
    cities = cities[cities['City'].notnull()]
    return cities


city_lat_long_edited = cities_lat_long_preprocessing()


def detect_lat_long(x):
    lat = str(x['LAT'])
    long = str(x['LONG'])
    try:
        point = Point(long,lat)
        if iran_border.contains(point).values[0]:
            city = find_nearest_city_lat_long(float(lat),float(long))
            return city
        else:
            pass
    except:
        pass


# PDF maker
No_of_tables = {idx:tb for idx,tb in enumerate(show_tables(server_search ,db_search),1)}


def PDF_Insert_time():
    date = datetime.date.today()
    date = str(date).split()[0]
    INSERT_time = date
    return INSERT_time.replace('-','/')


def db_size_(Server,db):
    engine = sql.create_engine(f"mssql+pyodbc://@{Server}/{db}" f"?driver=ODBC Driver 17 for SQL Server" f"&trusted_connection=yes" f"&TrustServerCertificate=yes")
    connection = engine.connect()
    db_size = connection.execute("EXEC sp_spaceused")
    db_size = next(iter(db_size))[0][:-3]
    connection.close()
    db_size = float(db_size) / 1024
    return f"{db_size:.2f}"


img = ImageReader(r'AutoReport\Requirement\Logo.jpg')

cols_dict = {
    'NationalCode':'کد ملی','NationalID':'شناسه ملی','ZipCode':'کد پستی','Atba':'اتباع',
    'Mobile':'شماره موبایل','HomeTel':'تلفن ثابت','Sheba':'شماره شبا','IdCard':'کارت ملی',
    'Plaque':'پلاک','Job':'شغل','First/Last_Name':'نام و نام خانوادگی','Relational':'رابطه فامیلی',
    'Car':'خودرو','Color':'رنگ','Date':'تاریخ','Latitude':'عرض جغرافیایی','Longitude':'طول جغرافیایی'}


def PDF_detail(total_valid_NC_not_in_source,total_valid_ZP_not_in_source,total_valid_NCid_not_in_source):
    no_nc = int(len(total_valid_NC_not_in_source))
    no_zp = int(len(total_valid_ZP_not_in_source))
    no_ncid = int(len(total_valid_NCid_not_in_source))
    return (no_nc,no_zp,no_ncid)


No_of_tables = int(max(No_of_tables))
db_size = db_size_(server_search ,db_search)


def data_dict():
    data_dict = [
        f'تعداد کلیدهای ناموجود در مارت : {PDF_detail(total_valid_NC_not_in_source,total_valid_ZP_not_in_source,total_valid_NCid_not_in_source)[0]}',
        f'تعداد کلیدهای ناموجود در مارت : {PDF_detail(total_valid_NC_not_in_source,total_valid_ZP_not_in_source,total_valid_NCid_not_in_source)[1]}',
        f'تعداد شناسه‌ملی‌های ناموجود در مارت : {PDF_detail(total_valid_NC_not_in_source,total_valid_ZP_not_in_source,total_valid_NCid_not_in_source)[2]}']
    return data_dict


sazman,hoze,security = "....","....","...."


def create_pdf_with_data(flt,Connection_name):
    # c = canvas.Canvas(f"گزارش اتصال {Connection_name}.pdf",pagesize=A4)

    c = canvas.Canvas(r"AutoReporter\%s.pdf" % format(Connection_name),pagesize=A4)

    width,height = A4
    margin,radius = 10,12

    c.setLineWidth(2)
    c.setStrokeColor(colors.black)

    c.roundRect(margin,margin,width - 2 * margin,height - 2 * margin,radius,stroke=1,fill=0)
    c.drawImage(img,55,45,80,80)

    pdfmetrics.registerFont(TTFont('B Nazanin',r'E:\AutoReporter\AutoReport\Requirement\B_NAZANIN\B NAZANIN.ttf'))

    c.setFont("B Nazanin",28)
    reshaper = arabic_reshaper.reshape(f"گزارش اتصال {Connection_name}")
    txt = get_display(reshaper)
    text_width = c.stringWidth(txt,"B Nazanin",28)
    c.drawString((width - text_width) / 2,height - 35,txt,mode=2)

    c.setFont("B Nazanin",12)
    c.drawString(17,height - 35,f'{PDF_insert_time()}')

    c.setFont("B Nazanin",12)
    reshaper = arabic_reshaper.reshape(f"تاریخ گزارش:")
    txt = get_display(reshaper)
    text_width = c.stringWidth(txt,"B Nazanin",18)
    c.drawString((width - text_width) - 453,height - 35,txt)

    # c.setFont("B Nazanin",10)
    # c.drawString(120,height - 30,"-" * 100,mode=2)

    c.setFont("B Nazanin",18)
    reshaper = arabic_reshaper.reshape(f"* سازمان ارائه دهنده: {sazman}")
    txt = get_display(reshaper)
    text_width = c.stringWidth(txt,"B Nazanin",18)
    c.drawString((width - text_width) - 20,height - 70,txt)

    c.setFont("B Nazanin",18)
    reshaper = arabic_reshaper.reshape(f"* حوزه کسب و کار: {hoze}")
    txt = get_display(reshaper)
    text_width = c.stringWidth(txt,"B Nazanin",18)
    c.drawString((width - text_width) - 20,height - 90,txt)

    c.setFont("B Nazanin",18)
    reshaper = arabic_reshaper.reshape(f"* سطح محرمانگی: {security}")
    txt = get_display(reshaper)
    text_width = c.stringWidth(txt,"B Nazanin",18)
    c.drawString((width - text_width) - 20,height - 110,txt)

    c.setFont("B Nazanin",10)
    c.drawString(10,height - 125,"-" * 154)

    c.setFont("B Nazanin",18)
    reshaper = arabic_reshaper.reshape(f"* نوع پایگاه داده:")
    txt = get_display(reshaper)
    text_width = c.stringWidth(txt,"B Nazanin",18)
    c.drawString((width - text_width) - 20,height - 140,txt)

    c.setFont("Helvetica",13)
    if 'SQL' in sql_orcl.upper():
        _width = 415
    else:
        _width = 435

    c.drawString(_width,height - 140,f'{sql_orcl.title()}')
    c.setFont("B Nazanin",18)

    if float(db_size) > 1000:
        reshape = arabic_reshaper.reshape(f"* حجم پایگاه داده: {'%.2f' % (db_size / 1024)} ترابایت ")
        txt = get_display(reshape)
        text_width = c.stringWidth(txt,"B Nazanin",18)
        c.drawString((width - text_width) - 20,height - 160,txt)
    else:
        reshape = arabic_reshaper.reshape(f"* گیگابایت حجم پایگاه داده: {'%.2f' % (db_size)} گیگابایت ")
        txt = get_display(reshape)
        text_width = c.stringWidth(txt,"B Nazanin",18)
        c.drawString((width - text_width) - 20,height - 160,txt)

    reshape = arabic_reshaper.reshape(f"* تعداد جداول: {No_of_tables}")
    txt = get_display(reshape)
    text_width = c.stringWidth(txt,"B Nazanin",18)
    c.drawString((width - text_width) - 20,height - 180,txt)

    c.setFont("B Nazanin",10)
    c.drawString(10,height - 195,"-" * 154)

    c.setFont("B Nazanin",18)
    reshaper = arabic_reshaper.reshape(f"* داده هایی که در پارامترهای اطلاعاتی وجود ندارد: ")
    txt = get_display(reshaper)
    text_width = c.stringWidth(txt,"B Nazanin",18)
    c.drawString((width - text_width) - 20,height - 210,txt)

    y_position = height - 235

    for i in data_dict():
        c.setFont("B Nazanin",18)
        reshape = get_display(arabic_reshaper.reshape(i))
        c.drawRightString(500,y_position,f"{reshape}")
        y_position -= 25

    c.setFont("B Nazanin",10)
    c.drawString(10,height - 300,"-" * 154)

    c.setFont("B Nazanin",18)
    reshape = get_display(arabic_reshaper.reshape("اطلاعات زیر در این اتصال وجود دارد:"))
    c.drawString(340,height - 320,reshape)

    counter = 0

    for En,Fa in cols_dict.items():
        if En not in ['Latitude','Longitude']:
            x = flt[flt[En] >= 30]
        elif En == 'Latitude':
            x = combine_latitude_longitude(flt)

        if len(x) >= 1:
            Width = 575

            if counter >= 6:
                Width = 385

            if counter in (6,12):
                y_position = height - 310

            if counter >= 12:
                Width = 190

            counter += 1
            c.setFont("B Nazanin",15)
            reshape = get_display(arabic_reshaper.reshape(Fa))
            c.drawRightString(Width,y_position - 35,f"{reshape} ({counter}")
            y_position -= 25

    # c.setFont("B Nazanin",15)
    # reshape = arabic_reshaper.reshape(f"data Management")
    # txt = get_display(reshape)
    # text_width = c.stringWidth(txt,"B Nazanin",18)
    # c.drawString((width - text_width) - 430,height - 800,txt)
    c.save()