import requests
import os
from pathlib import Path
import pandas as pd
import json
import logging
import argparse
from datetime import datetime
import xlsxwriter
import typing

logging.basicConfig(level=logging.DEBUG, filename='log.txt')

def parse_arguments():
    """ Parse input arguments """
    parser = argparse.ArgumentParser()
    parser.add_argument('-k','--keys', type=str, nargs='*', 
                        help='Give list of keys space seperated')
    parser.add_argument('-c','--colored', action=argparse.BooleanOptionalAction, default=True, 
                        help= 'Default colored, give --no-colored for no color')
    return parser.parse_args()

def diff_month(d1, d2):
    """Check the date is older that 12, 3, less, or future"""
    return (d1.year - d2.year) * 12 + (d1.month - d2.month)

def writerow(worksheet, row, data, cell_format, label_id_info=None):
    """for writing an excel line""" 
    colx=0 
    for c in data:
        if label_id_info and label_id_info['has_color'] and colx == label_id_info['position']:
            worksheet.write(row, colx, (str(c) if c else ''), label_id_info['color'])
        else: 
            worksheet.write(row, colx, (str(c) if c else ''), cell_format)
        colx+=1
        
def load_excel(df, coloured=False, needed_columns:typing.Set=None):
    """ excel file writer with colour """
    #remove output file
    output_file = Path(f"vehicles_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
    if output_file.exists():
        output_file.unlink()
    #create workbook and worksheet
    writer = xlsxwriter.Workbook(output_file)
    worksheet = writer.add_worksheet('vehicles')
    # write titles
    needed_columns_lst = list(needed_columns)
    writerow(worksheet, 0, needed_columns_lst, writer.add_format())
    current = datetime.now().date()
    
    has_label = 'labelIds' in needed_columns_lst
    label_position = needed_columns_lst.index('labelIds') if has_label else -1
    #write data rows
    i=0
    for _, rw in df.iterrows():
        #logging.debug(f" --- {rw['colorCodes']} {type(rw['colorCodes'])}")
        # writing cell by cell with colour formatting
        row= i + 1
        i += 1
        datex = datetime.strptime(rw['hu'], '%Y-%m-%d').date()
        r = rw.get(list(needed_columns))
        #if rw['colorCodes']
        label_color = rw['colorCodes'][0] if rw['colorCodes'] else ''
        label_id_info = {'position':label_position, 'has_color': bool(label_color) , 'color': writer.add_format({'bg_color': label_color})}
        if not coloured:
            # write without colours
            writerow(worksheet, row, r, None, label_id_info) 
        elif diff_month(current, datex) <= 3: 
            cell_format = writer.add_format({'bg_color': '#007500'})
            writerow(worksheet, row, r, cell_format, label_id_info)
        elif diff_month(current, datex) <= 12:
            cell_format = writer.add_format({'bg_color': '#FFA500'})
            writerow(worksheet, row, r, cell_format, label_id_info)
        else:
            cell_format = writer.add_format({'bg_color': '#b30000'})
            writerow(worksheet, row, r , cell_format, label_id_info)    
    writer.close()
    
def main():
    """ send vehicles.csv to server and get the final excel"""
    url= 'http://127.0.0.1:8000/send/'
    args = parse_arguments()
    logging.debug(f'incoming args = {args}')
    # Send vehicles.csv to the api
    response = requests.post(url, files={'file': open(Path(os.getcwd()) / Path('vehicles.csv'), 'rb')})
    # extract json information from the response
    data = response.json() 
    # put the json data into a dataframe
    df = pd.DataFrame(data = json.loads(data) )
    # create the excel output
    needed_columns = {'rnr',}
    needed_columns = needed_columns.union(args.keys if args.keys else [])
    if needed_columns.difference(df.columns):
        raise Exception(f""" keys=[{needed_columns.difference(df.columns)}] 
                        are not in the data. 
                        Please remove from key list""")
    # sort usign gruppe
    df.sort_values(by=['gruppe'], inplace=True)
    # load to excel with only needed columns
    load_excel(df, args.colored, needed_columns)

if __name__ == '__main__':
    main()
