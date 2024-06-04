import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import sys
from pathlib import Path
import datetime

try:
    # MAIN VIEW ============================
    # header html
    st.set_page_config(page_title="Agrimap Bali", layout="wide", page_icon="🗺️")
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        """, 
        unsafe_allow_html=True
    )

    # title
    st.title("Dashboard Agrimap Bali")
    st.write("Dashboard ini bertujuan untuk memetakan luas tanam atau panen padi berdasarkan hasil machine learning dan citra satelit.")
    st.write("Peta heatmap di bawah akan menampilkan jenis fase tanaman padi yang terpilih. Terdapat juga data pendukung atau rekomendasi di bawah untuk melihat lebih detail potensi wilayah tersebut.")

    # load file path
    this_path = Path().resolve()
    kec_path = str(this_path) + r"/map_source/geo_kec.geojson"
    
    # load in geopandas using function to improv performance
    @st.cache_data
    def read_gpd(path):
        return gpd.read_file(path, driver='GeoJSON')
    
    #kec_gdf = gpd.read_file(kec_path, driver='GeoJSON')
    kec_gdf = read_gpd(kec_path)
    kec_gdf = kec_gdf.rename(columns={
            'nmkec':'Kecamatan',
            'nmdesa':'Desa',
        })
    #kec_gdf = kec_gdf.to_crs("WGS84")

    # kab and its centroid
    kdkab = {'-':'-',
            '01': ["JEMBRANA",-8.3606,114.6257], 
            '02': ["TABANAN",-8.5376,115.1247], 
            '03': ["BADUNG",-8.5819,115.1771],
            '04': ["GIANYAR",-8.5367,115.3314],
            '05': ["KLUNGKUNG",-8.5388,115.4024],
            '06': ["BANGLI",-8.4543,115.3549],
            '07': ["KARANGASEM",-8.4463,115.6127],
            '08': ["BULELENG",-8.2239,114.9517],
            '71': ["DENPASAR",-8.6705,115.2126]
        }
    def get_nmkab(kode): #from dict above
        return kdkab[kode][0]
    def get_latlonkab(kode): #return lat,lon
        return kdkab[kode][1], kdkab[kode][2]
    
    
    # SIDEBAR VIEW ============================
    with st.sidebar: #.form(key="my_form"):
        st.header("Filter Data")
        
        # PILIH kab
        selectbox_kab = st.selectbox("Pilih Kabupaten", options=list(kdkab.keys()), format_func=get_nmkab)
        # set pilihan kec based on pilihan kab
        kec_choices = list( set(
                kec_gdf.loc[kec_gdf['nmkab'] == get_nmkab(selectbox_kab)].Kecamatan
            ) )
        kec_choices.insert(0, "-")
        des_path = str(this_path) + f"/map_source/geo_desa_{selectbox_kab}.geojson"
        
        # PILIH kec
        judulkec = " di KAB. "+get_nmkab(selectbox_kab) if selectbox_kab != '-' else ""
        selectbox_kec = st.selectbox("Pilih Kecamatan"+judulkec, kec_choices)

        # PILIH display choropleth
        #st.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)
        #t.write('<style>div.st-bf{flex-direction:column;} div.st-ag{font-weight:bold;padding-left:2px;}</style>', unsafe_allow_html=True)
        opt_displaymap = ["Luas Non Sawah", "Fase Persiapan Lahan","Fase Vegetatif 1","Fase Vegetatif 2","Fase Generatif",]
        choose_displaymap=st.radio("Display map: ",opt_displaymap, index=4) #pilihan defaultnya Generatif

        # PILIH date file source
        from os import walk
        csv_path = str(this_path) + r"/data"
        csv_list = [[],[]]
        for (dirpath, dirnames, filenames) in walk(csv_path, topdown=False):
            for filename in filenames:
                csv_list[0].append(filename.split('_')[0])
                csv_list[1].append(filename.split('_')[1].split('.')[0])
            break
        
        kdbln = {
            #'01':'Januari',
            #'02':'Februari',
            #'03':'Maret',
            #'04':'April',
            #'05':'Mei',
            #'06':'Juni',
            #'07':'Juli',
            #'08':'Agustus',
            '09':'September',
            #'10':'Oktober',
            #'11':'November',
            #'12':'Desember'
        }
        def get_namabln(kode):
            return kdbln[kode]
        
        col1, col2 = st.columns(2)
        with col1:
            datenow = datetime.datetime.now()
            selectbox_bln = st.selectbox("Bulan:", options=list(kdbln.keys()), format_func=get_namabln, 
                                         #index=datenow.date().month-1) #dummy only
                                         index=0)
        with col2:
            selectbox_thn = st.selectbox("Tahun:", set(csv_list[1]), index=len(set(csv_list[1]))-1 )

    #    pressed_filter = st.form_submit_button("Filter Map")
    # if submit form filter
    #if pressed_filter:
    #    kec_gdf = kec_gdf[kec_gdf["nmkab"] == selectbox_kab]

    # DATA FOR MAPPING
    titiktengah = False
    # filter from date. read data luas padi satelit for mapping 
    des_df = pd.read_csv(csv_path+f"/{selectbox_bln}_{selectbox_thn}.csv", dtype={'iddesa': object})
    
    # jika ga dipilih kab, maka tampilin aggregate
    des_df['idkec'] = des_df['iddesa'].str[:7]
    des_agg_df = des_df[['idkec','nonsawah','persiapan','vegetatif1','vegetatif2','generatif']].groupby("idkec").agg('mean')
    if selectbox_kec == '-':
        kec_gdf = kec_gdf.merge(des_agg_df, how='inner', on='idkec')
    
    # filter geomap desa (biar cuman ngeload ketika kefilter kab aja n ga mberatin)
    if Path(des_path).exists() :
        # koordinat centroid zoom map kec
        if selectbox_kec != '-':
            titiktengah = kec_gdf[kec_gdf['Kecamatan'] == selectbox_kec ].geometry.centroid.iloc[0]
        
        # read desa di kec terpilih
        #des_gdf = gpd.read_file(des_path, driver='GeoJSON')
        des_gdf = read_gpd(des_path)
        if selectbox_kec != '-':
            des_gdf = des_gdf.loc[des_gdf['nmkec'] == selectbox_kec ]
        des_gdf['nmkab'] = get_nmkab(selectbox_kab)
        
        # merge data hasil satelit dengan data shp geopandas
        des_df = des_gdf.merge(des_df, how='inner', on='iddesa')
        des_df['total'] = des_df['vegetatif1'] + des_df['vegetatif2'] + des_df['generatif'] + des_df['persiapan'] + des_df['nonsawah']
        # rename column
        
        # data final for display map
        #kec_gdf = kec_gdf.drop('nmdesa', axis=1)
        #kec_gdf = kec_gdf.merge(des_gdf, how='outer')
        kec_gdf = des_df # desa df yang udah dimerge sama df dan geodf
    kec_gdf[['nonsawah','persiapan','vegetatif1','vegetatif2','generatif']] = kec_gdf[['nonsawah','persiapan','vegetatif1','vegetatif2','generatif']].apply(lambda row: (row*100).round(3),axis = 1,result_type ='expand')
    kec_gdf = kec_gdf.rename(columns={
        'nmkec':'Kecamatan',
        'nmdesa':'Desa',
        'vegetatif1': 'Fase_Vegetatif1', 
        'vegetatif2': 'Fase_Vegetatif2',
        'generatif': 'Fase_Generatif',
        'persiapan': 'Fase_Persiapan_lahan',
        'nonsawah': 'Luas_Nonsawah'
    })


    # MAIN VIEW MAPPING ============================
    hover_data = [kec_gdf.Kecamatan, kec_gdf.Desa, kec_gdf.Luas_Nonsawah, kec_gdf.Fase_Persiapan_lahan, kec_gdf.Fase_Generatif, kec_gdf.Fase_Vegetatif1, kec_gdf.Fase_Vegetatif2] if selectbox_kab != '-' else [kec_gdf.Kecamatan, kec_gdf.Luas_Nonsawah, kec_gdf.Fase_Persiapan_lahan, kec_gdf.Fase_Generatif, kec_gdf.Fase_Vegetatif1, kec_gdf.Fase_Vegetatif2]
    figmap = px.choropleth_mapbox(
                        kec_gdf,
                        geojson=kec_gdf.geometry,
                        locations=kec_gdf.index,
                        color=kec_gdf.columns[opt_displaymap.index(choose_displaymap)+5] if selectbox_kab=='-' else kec_gdf.columns[opt_displaymap.index(choose_displaymap)+8],
                        color_continuous_scale=px.colors.sequential.Sunsetdark,
                        hover_name=kec_gdf.nmkab,
                        hover_data= hover_data
                        #color_continuous_scale="Viridis",
                    )
    # set layout map
    figmap.update_layout(
        mapbox_zoom=8,
        mapbox_center= {"lat": -8.409518, "lon": 115.188919}, 
        margin={"r":0,"t":0,"l":0,"b":0},
        #mapbox_style='carto-positron',
        mapbox_style='open-street-map',
    )
    # layout map jika filter kab
    if selectbox_kab != "-":
        figmap.update_layout(
            mapbox_zoom=9,
            mapbox_center={"lat": get_latlonkab(selectbox_kab)[0], 
                           "lon":get_latlonkab(selectbox_kab)[1]}
        )
    # layout map jika filter kec
    if titiktengah:
        figmap.update_layout(
            mapbox_zoom=10,
            mapbox_center={"lat": titiktengah.y, "lon": titiktengah.x}
        )

    # show in web
    st.write(" ")
    st.plotly_chart(figmap)

    # SEE DF DETAILS
    if selectbox_kab !="-":
        # gtw gapenting
        st.markdown(
            """
            <style>
                .fixedButton{
                    position: fixed;
                    bottom: 0px;
                    right: 0px; 
                    padding: 20px;
                }
                .roundedFixedBtn{
                    height: 60px;
                    line-height: 60px;  
                    width: 60px;  
                    font-size: 2em;
                    font-weight: bold;
                    border-radius: 50%;
                    background-color: #0094de;
                    color: white;
                    text-align: center;
                    cursor: pointer;
                }
            </style>
            <hr>
            <div class="fixedButton" onclick="bottomFunction()" title="Scroll down">
                <div class="roundedFixedBtn"><i class="fa fa-arrow-circle-down"></i></div>
            </div>
            <script>
                function bottomFunction() {
                    document.getElementById('bottom').scrollIntoView({behavior: "smooth"});
                }
            </script>
            """, unsafe_allow_html=True
        )        

        col3, col4 = st.columns([3,1])
        with col3: 
            #st.write("df des col:", kec_gdf.columns)
            if selectbox_kec == '-':
                dfstack = kec_gdf.iloc[:,[2,8,9,10,11,12]].groupby("Kecamatan").agg('mean').stack().to_frame().reset_index()
                dfstack.columns = ['Nama Kecamatan','Kategori','Persentase']
            else:
                dfstack = kec_gdf.iloc[:,[3,8,9,10,11,12]].set_index("Desa").stack().to_frame().reset_index()
                dfstack.columns = ['Nama desa','Kategori','Persentase']
            figbar = px.bar(
                dfstack,
                y="Nama Kecamatan" if selectbox_kec=='-' else "Nama desa",
                x='Persentase',
                color='Kategori',
                color_discrete_sequence=px.colors.qualitative.Plotly_r,
            )
            figbar.update_layout(legend=dict(
                    orientation="h",
                )                
            )
            st.plotly_chart(figbar)
        
        with col4:
            st.subheader("Rekomendasi / Data pendukung")
            if selectbox_kec == '-':
                st.caption("KAB. "+str(get_nmkab(selectbox_kab)))
            else:
                st.caption("KEC. "+str(selectbox_kec))
            st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed felis arcu, mollis sit amet orci nec, tincidunt eleifend tortor. In vehicula est eget enim eleifend, ac aliquam sem gravida. Suspendisse arcu lectus, ornare viverra mi eu, egestas placerat lectus.")

    #getrowindex = st.number_input('Enter an index of row to show')
    #st.write(kec_gdf.iloc[int(getrowindex)])
    st.markdown("<div id='bottom'>  </div>", unsafe_allow_html=True)


except Exception as e:
    #st.write("Terjadi error: ", str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    print(exc_type, exc_tb.tb_lineno)
    st.error(
        f"""
        **Terjadi kesalahan.**
        Error: {e}. Type error: {exc_type}, on line no {exc_tb.tb_lineno}
    """
    )
