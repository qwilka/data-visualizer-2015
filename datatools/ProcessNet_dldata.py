# http://xlsxwriter.readthedocs.org/en/latest/index.html
# it is necessary to convert the spreadsheet to values only
# http://www.ozgrid.com/forum/showthread.php?t=38064

from datetime import date, timedelta
import xlsxwriter

WB_name_base = "11-PT-92012_5sec_"
date_start = date(2014,10,1)   # "01/10/2014"
date_end   = date(2014,10,31)
indicator_name = "VAL_11-PT-92012:X.Value"
data_source = "PI-SVG"
interval = 5
interval_unit = "s"

# http://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python
#date_list = [(date_start + timedelta(days=x)).strftime("%d/%m/%Y") for x in range((date_end-date_start).days + 1)]
date_list = [date_start + timedelta(days=x) for x in range((date_end-date_start).days + 1)]

def add_sheet_data(wb, date_ , indicator, source_, interval, interval_unit, write_params=False):
    total_sec = 60*60*24
    cdat_fmt = wb.add_format({'num_format': 'dd-mm-yyyy hh:mm:ss'})
    num_data = int(total_sec/interval) + 2   # add extra item for header line
    if interval_unit != "s":
        raise ValueError("Only 's' has been implemented for argument interval_unit.")
    ws = wb.add_worksheet(date_.strftime("%Y-%m-%d"))

    if write_params:  
        ws.write('G1', indicator_name)
        ws.write('G2', source_)
        ws.write('G3', "INTERP")   # this has no function
        ws.write('G4', date_.strftime("%d/%m/%Y") + " 00:00:00")   # "08/10/2014 00:00:00"
        ws.write('G5', (date_ + timedelta(1)).strftime("%d/%m/%Y") + " 00:00:00")
        ws.write('G6', str(interval) + interval_unit)     # "2s"
        ws.write('G7', "Timestamp")
        ws.write('G8', "Value")
        ws.write('G9', "True")
        ws.write_array_formula('A1:B'+str(num_data), 
        '{=GetHistoricalValues($G$1,$G$2,"INTERP",$G$4,$G$5,$G$6,"Timestamp","Value",TRUE)}'
        )
    else:
        ws.write_array_formula('A1:B'+str(num_data), 
        #'{=GetHistoricalValues("' + indicator_name +'","'+ source_ +'","INTERP","'+ date_.strftime("%d/%m/%Y") + " 00:00:00" +'","'+ (date_ + timedelta(1)).strftime("%d/%m/%Y") + " 00:00:00" +'","'+ str(interval) + interval_unit +'","Timestamp","Value","TRUE")}'
        '{=GetHistoricalValues("' + 
        indicator_name +
        '","'+ 
        source_ +
        '","INTERP","'+ 
        date_.strftime("%d/%m/%Y") + " 00:00:00" +
        '","'+ 
        (date_ + timedelta(1)).strftime("%d/%m/%Y") + " 00:00:00" +
        '","'+ 
        str(interval) + interval_unit +
        '","Timestamp","Value","TRUE")}'
        )

    # need to set cell format for timestamps, can only do this for the entire column
    # http://stackoverflow.com/questions/22352907/apply-format-to-a-cell-after-being-written-in-xlsxwriter
    ws.set_column(0, 0, 18, cdat_fmt)
    ws.set_column(1, 1, 15)



workbook = xlsxwriter.Workbook(WB_name_base+'_'+date_start.strftime("%Y%m%d")+'_'+date_end.strftime("%Y%m%d")+'.xlsx')

for dd in date_list:
    add_sheet_data(workbook, dd, indicator_name, data_source, interval, interval_unit, write_params=False)

workbook.close()
