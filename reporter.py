from utils import db_search ,server_search ,insert_to_autoreporter ,sourceID ,futures ,timer ,time ,pd ,connection_name
from reporter_requirements import (valid_calculating ,to_final1 ,combine_latitude_longitude ,combine_NC_Date ,calculate_nc_on_date ,extract_lat_on_long
                                         ,cities_distribution ,create_pdf_with_data ,)

class Final:
    def __init__(self, counter, SourceID, Server, db, schema, table, Column, Row, NC, ZP, NCid, Date):
        self.counter = counter
        self.SourceID = SourceID
        self.Server = Server
        self.db = db
        self.schema = schema
        self.table = table
        self.Column = Column
        self.Row = Row
        self.NC = NC
        self.ZP = ZP
        self.NCid = NCid
        self.Date = Date

    def My_ThreadPool(self):
        if self.NC >= 30:
            print(f'NationalCode :: {self.table} {self.Column} {self.Row}')
            len_did, not_in_source = valid_calculating('NationalCode', self.Column, self.schema, self.table, self.Server, self.db)
            to_final1(self.SourceID, self.Column, not_in_source, self.Server, self.db, self.schema, self.table, 'NationalCode', self.Row, len_did)

        if self.ZP >= 30:
            print(f'ZipCode :: {self.table} {self.Column} {self.Row}')
            len_did, not_in_source = valid_calculating('ZipCode', self.Column, self.schema, self.table, self.Server, self.db)
            to_final1(self.SourceID, self.Column, not_in_source, self.Server, self.db, self.schema, self.table, 'ZipCode', self.Row, len_did)

        if self.NCid >= 30:
            print(f'NationalID :: {self.table} {self.Column} {self.Row}')
            len_did, not_in_source = valid_calculating('NationalID', self.Column, self.schema, self.table, self.Server, self.db)
            to_final1(self.SourceID, self.Column, not_in_source, self.Server, self.db, self.schema, self.table, 'NationalID', self.Row, len_did)


if __name__ == "__main__":
    Start = time.time()
    con_ = insert_to_autoreporter()

    flt = pd.read_sql(f"""Select * from dbo.Reporterwhere [db] = '{db_search}' and [Server] = '{server_search}' """, con=con_)
    con_.close()
    flt['SourceID'] = sourceID

    NC_Date = combine_NC_Date(flt)
    lat_long = combine_latitude_longitude(flt)

    def run(counter, SourceID, Server, db, schema, table, Column, Row, NC, ZP, NCid, Date):
        Run_class = Final(counter, SourceID, Server, db, schema, table, Column, Row, NC, ZP, NCid, Date)
        Run_class.My_ThreadPool()

    def NC_on_Date(Schema, Table, NC, Date):
        calculate_nc_on_date(Schema, Table, NC, Date)

    def latitude_longitude(Schema, Table, lat, long):
        extract_lat_on_long(Schema, Table, lat, long)

    with futures.ThreadPoolExecutor(max_workers=20) as executor:
        to_do = []

        for counter, i in enumerate(flt.index, 1):
            x = executor.submit(run,counter,flt.loc[i, 'SourceID'],flt.loc[i, 'Server'],flt.loc[i, 'db'],flt.loc[i, 'Schema'],flt.loc[i, 'Table'],flt.loc[i, 'Column'],
                flt.loc[i, 'Row'],flt.loc[i, 'NationalCode'],flt.loc[i, 'ZipCode'],flt.loc[i, 'NationalID'],flt.loc[i, 'Date'])
            to_do.append(x)

        for future in futures.as_completed(to_do):
            res = future.result()
            print(res)

        print('------------- NC on Date -------------')
        to_do = []

        for counter, i in enumerate(NC_Date.index, 20):
            x = executor.submit(NC_on_Date,NC_Date.loc[i, 'Schema'],NC_Date.loc[i, 'Table'],NC_Date.loc[i, 'NC'],NC_Date.loc[i, 'Date'])
            to_do.append(x)

        for future in futures.as_completed(to_do):
            res = future.result()

        print('-------------- latitude/longitude --------------')
        to_do = []

        for counter, i in enumerate(lat_long.index, 1):
            x = executor.submit(latitude_longitude,lat_long.loc[i, 'Schema'],lat_long.loc[i, 'Table'],lat_long.loc[i, 'Latitude'],lat_long.loc[i, 'Longitude'])
            to_do.append(x)

        for future in futures.as_completed(to_do):
            res = future.result()
            print(res)

    cities_distribution()
    create_pdf_with_data(flt, connection_name)
    timer(Start)