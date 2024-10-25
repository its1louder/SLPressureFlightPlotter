import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.style as style
import datetime as dt
import base64
import os

URL = "https://asp-interface.arc.nasa.gov/API/binary_packet_data/N809NA/PRESSURE?Start=0"
style.use('bmh')
SEPCHAR = "\\x0c"

def scrape_data(url):
    r = requests.get(url)
    html = str(r.content)
    msglst = [l for l in html.split(SEPCHAR) if len(l)>1]
    return msglst

def clean_data(msglst):
    plst = [ [f"{p.split(';')[1]} {p.split(';')[2]}", p.split(';')[0][1:-3],] for p in msglst if p[0]=="P"]
    tlst = [ [f"{t.split(';')[1]} {t.split(';')[2]}", t.split(';')[0][1:-1],] for t in msglst if t[0]=="T"]
    
    pdatf = pd.DataFrame(plst,columns=['time','podpressure'])
    pdatf['time'] = pd.to_datetime(pdatf['time'])
    pdatf['podpressure'] = pd.to_numeric(pdatf['podpressure'])

    tdatf = pd.DataFrame(tlst,columns=['time','podtemp'])
    tdatf['time'] = pd.to_datetime(tdatf['time'])
    tdatf['podtemp'] = pd.to_numeric(tdatf['podtemp'])
    
    pdatf['podPSI'] = pdatf['podpressure']*0.014503773773
    
    return pdatf, tdatf

def plot_data(pdatf, tdatf, datestmp):
    plt.ioff()
    pplot = pdatf.plot(x='time', y='podPSI',legend=False,grid=True, title=f"{datestmp} Pod Pressure, PSI")
    st.pyplot(pplot.figure)

    tplot = tdatf.plot(x='time', y='podtemp',legend=False,grid=True, title=f"{datestmp} Pod Temp, C")
    st.pyplot(tplot.figure)

def save_data(pdatf, tdatf, datestmp):
    pressure_file = f'/srv/podlog.d/{datestmp}_podpressure.h5'
    with pd.HDFStore(pressure_file) as pressurestore:
        pressurestore['pdatf'] = pdatf
    temp_file = f'/srv/podlog.d/{datestmp}_podtemp.h5'
    with pd.HDFStore(temp_file) as tempstore:
        tempstore['tdatf'] = tdatf
    return pressure_file, temp_file

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">{file_label}</a>'
    return href

def main(url=URL):
    st.title("Pod Temperature and Pressure Plotter")
    url = st.text_input('Enter the URL to scrape data from',url)
    year = st.number_input('Enter the year to filter data', 2000, 2100, 2044)
    if st.button('Scrape and Plot Data'):
        msglst = scrape_data(url)
        pdatf, tdatf = clean_data(msglst)

        pdatf=pdatf[pdatf['time'] < dt.datetime(year, 1, 1)]
        tdatf=tdatf[tdatf['time'] < dt.datetime(year, 1, 1)]
        try:
            datestmp = pdatf.iloc[0,0].strftime("%Y-%m-%d") 
            plot_data(pdatf, tdatf, datestmp)

            # this line to save the data will only work on local deployment, not on streamlit cloud
            #pressure_file, temp_file = save_data(pdatf, tdatf, datestmp)
            #st.markdown(get_binary_file_downloader_html(pressure_file, 'Download Pressure Data'), unsafe_allow_html=True)
            #st.write (pdatf.tail(10))
            st.write (pdatf)
            #st.markdown(get_binary_file_downloader_html(temp_file, 'Download Temperature Data'), unsafe_allow_html=True)
            #st.write (tdatf.tail(10))
            st.write (tdatf)
        except: 
            # print error capture to streamlit, not print
            errmsg = 'failed to load data from %s. Are you sure there is data there?' %url
            st.write(errmsg+msglst)
            print(errmsg+msglst)
            raise (errmsg)




if __name__ == "__main__":
    try:
        main(URL) 
    except Exception as error:
        st.exception(error)
