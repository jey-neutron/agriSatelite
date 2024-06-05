import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import sys
from pathlib import Path
import datetime
import numpy as np

try:
    # MAIN VIEW ============================
    # header html
    st.set_page_config(page_title="Agrimap Bali", layout="wide", page_icon="🗺️")
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        <style>
            html {
                scroll-behavior: smooth;
            }
            a:link.tautan, a:visited.tautan {
                background-color: rgb(76,155,130);
                color: white;
                padding: 0px 4px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                border-radius: 5px;
            }
            h1:hover, h3:hover{
                color: orange;
            }
            a:hover.tautan, a:active.tautan, .roundedFixedBtn:hover {
                background-color: rgb(236,112,20);
            }
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
                background-color: rgb(76,155,130);
                color: white;
                text-align: center;
                cursor: pointer;
            }
            .small-font {
                font-size:12px;
                font-style: italic;
                color: #b1a7a6;
            }
        </style>
        """, 
        unsafe_allow_html=True
    )

    #st.write(px.colors.sequential.swatches()) #colorpalette
    coolor = px.colors.sequential.Emrld
    coolor_nonsawah = px.colors.sequential.Greys #abu grey
    coolor_vegetatif = px.colors.sequential.Emrld #ijo emrld
    coolor_generatif = px.colors.sequential.YlOrBr #kuning ylorbr
    coolor_discret = ['rgb(115,115,115)','rgb(151,225,150)','rgb(76,155,130)','rgb(16,89,101)','rgb(236,112,20)'] 
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
        csv_luas_path = str(this_path) + r"/data/hasil_ML_satelit"
        csv_list = [[],[]]
        for (dirpath, dirnames, filenames) in walk(csv_luas_path, topdown=False):
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

    # TITLE ============================
    st.title("Dashboard Agrimap Bali 🗺️")
    st.write("Dashboard ini bertujuan untuk memetakan luas tanam atau panen padi berdasarkan hasil machine learning dan citra satelit.")
    classtautan = 'a' if selectbox_kab!='-' else 'span'
    st.markdown(f"""Peta heatmap di bawah akan menampilkan persentase luas jenis fase tanaman padi yang terpilih. Terdapat juga data pendukung atau rekomendasi <{classtautan} class="tautan" href="#grafik-perbandingan-wilayah">di bawah</{classtautan}> untuk melihat lebih detail potensi wilayah tersebut.""", unsafe_allow_html=True)

    # DATA FOR MAPPING ============================
    titiktengah = False
    # filter from date. read data luas padi satelit for mapping 
    des_df = pd.read_csv(csv_luas_path+f"/{selectbox_bln}_{selectbox_thn}.csv", dtype={'iddesa': object})
    
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
    #pilihan coolor
    displaymapchoosen = kec_gdf.columns[opt_displaymap.index(choose_displaymap)+5] if selectbox_kab=='-' else kec_gdf.columns[opt_displaymap.index(choose_displaymap)+8]
    if displaymapchoosen=='Fase_Generatif':
        coolor_choosen = coolor_generatif
    elif displaymapchoosen=='Luas_Nonsawah':
        coolor_choosen = coolor_nonsawah
    else:
        coolor_choosen = coolor_vegetatif
    #st.write(opt_displaymap.index(choose_displaymap))
    figmap = px.choropleth_mapbox(
                        kec_gdf,
                        geojson=kec_gdf.geometry,
                        locations=kec_gdf.index,
                        color=displaymapchoosen,
                        color_continuous_scale=coolor_choosen,
                        hover_name=kec_gdf.nmkab,
                        hover_data= hover_data
                    )
    # set layout map
    figmap.update_layout(
        mapbox_zoom=8,
        mapbox_center= {"lat": -8.409518, "lon": 115.188919}, 
        margin={"r":0,"t":0,"l":0,"b":0},
        #mapbox_style='carto-positron',
        mapbox_style='open-street-map',
        #legend=dict(yanchor="top", xanchor='left',orientation="h",)
        coloraxis_colorbar = dict(
            orientation='h',
            yanchor='bottom',
            y=-0.175,
            tickfont_weight='bold',
            title_font_weight = 'bold',
            #tickformat = ".2%"
        )
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

    # SEE DF DETAILS IF FILTER KAB GA KOSONG ============================
    if selectbox_kab !="-":
        # gtw gapenting
        st.markdown(
            """
            <hr>
            <a class="fixedButton" href="#grafik-perbandingan-wilayah" title="Scroll down">
                <div class="roundedFixedBtn"><i class="fa fa-arrow-circle-down"></i></div>
            </a>
            <script>
                function bottomFunction() {
                    document.getElementById('bottom').scrollIntoView({behavior: "smooth"});
                }
                document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                    anchor.addEventListener('click', function (e) {
                        e.preventDefault();

                        document.querySelector(this.getAttribute('href')).scrollIntoView({
                            behavior: 'smooth'
                        });
                    });
                });
            </script>
            """, unsafe_allow_html=True
        )        

        # VIEW GRAFIK STACK BAR ============================
        #st.write("df des col:", kec_gdf.columns)
        st.subheader("Grafik Perbandingan Wilayah")
        captionsect2 = f"Kecamatan di KAB. {str(get_nmkab(selectbox_kab))}" if selectbox_kec == '-' else f"Desa di KEC. {selectbox_kec}, KAB. {get_nmkab(selectbox_kab)}"
        caption2sect2 = "agregat rata-rata " if selectbox_kec == '-' else ""
        subjudulsect2 = f"Kecamatan di Kabupaten {str(get_nmkab(selectbox_kab).title())}" if selectbox_kec == '-' else f"Desa di Kecamatan {selectbox_kec.title()}, Kabupaten {get_nmkab(selectbox_kab).title()}"
        st.caption(captionsect2)
        st.write(f"Grafik di bawah menampilkan {caption2sect2}persentase luas wilayah berdasarkan jenis fase tanaman padi per ", subjudulsect2)

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
            color_discrete_sequence=coolor_discret
            #px.colors.qualitative.Plotly_r,
        )
        figbar.update_layout(legend=dict(
                orientation="h",
            )                
        )
        st.plotly_chart(figbar)

        # VIEW DATA PENDUKUNG
        st.markdown("<hr>", unsafe_allow_html=True,)
        st.subheader("Rekomendasi / Data pendukung")
        st.caption(captionsect2)
        
        # VIEW IF FILTER KAB ============================
        if selectbox_kec == "-":
            #dfpendukung = pd.read_csv(csv_path+f"/{selectbox_bln}_{selectbox_thn}.csv", dtype={'kd_wilayah': object})
            # read data ssn
            dfpendukung = pd.read_csv(str(this_path) + r"/data/pendukung"+f"/kecamatan_susenas.csv", dtype={'idkec': object})
            # drop col pertama
            # dfpendukung = dfpendukung.drop(dfpendukung.columns[0], axis=1)  # tidak terpakai, dataframe sudah diupdate
            # buat kolom pembantu buat filter
            dfpendukung['kdkab'] = dfpendukung.idkec.str[2:4]
            # filter pake kolom baru
            dfpendukung = dfpendukung[dfpendukung.kdkab == selectbox_kab].reset_index().drop(dfpendukung.columns[-1], axis=1)
            # select subset column
            dfpendukung = dfpendukung[['kec','rasio_kur','rasio_jasa_keuangan','rasio_rekening',]]
            dfpendukung = dfpendukung.rename(columns={
                'kec':'Kecamatan',
                'rasio_kur':'Rasio pengguna KUR',
                'rasio_jasa_keuangan':'Rasio Pengguna jasa keuangan',
                'rasio_rekening': 'Rasio pemilik nomor rekening'
            })

            # BAR
            multiselect_bar = st.multiselect(
                "Pilih variabel yang ingin dimunculkan:",
                ['Rasio pemilik nomor rekening', 'Rasio Pengguna jasa keuangan', 'Rasio pengguna KUR'],
                ['Rasio pemilik nomor rekening', 'Rasio Pengguna jasa keuangan', 'Rasio pengguna KUR']
            )
            figbar = px.bar(dfpendukung, x=multiselect_bar, y='Kecamatan', orientation='h', color_discrete_sequence=coolor_discret)
            figbar.update_layout(
                barmode='group', 
                legend=dict(orientation="h",)    
            )

            st.plotly_chart(figbar)
            st.write(' ')
            #st.markdown("<br> ", unsafe_allow_html=True)
            st.dataframe(dfpendukung[['Kecamatan']+multiselect_bar].set_index('Kecamatan'), use_container_width=True)
            #st.write(px.colors.qualitative.Plotly_r)

            # paragraf 
            st.markdown(
                f'<p class="small-font">Sumber Data: Susenas Maret {selectbox_thn}</p>',
                unsafe_allow_html=True,
            )
            # st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed felis arcu, mollis sit amet orci nec, tincidunt eleifend tortor. In vehicula est eget enim eleifend, ac aliquam sem gravida. Suspendisse arcu lectus, ornare viverra mi eu, egestas placerat lectus.")
            st.write("Tabel di atas menampilkan informasi tentang Wilayah, Rasio Anggota Rumah Tangga (ART) yang berusia 5 tahun ke-atas yang memiliki rekening, Rasio ART yang berusia 5 tahun ke atas yang menggunakan produk/layanan jasa keuangan, dan Rasio ART yang menerima Kredit Usaha Rakyat (KUR).")

        # VIEW IF FILTER KEC ============================
        else:
            st.write("Tampilan data hasil clustering")
            # read data ssn
            dfpendukung = pd.read_csv(str(this_path) + r"/data/pendukung"+f"/cluster_podes.csv", dtype={'kd_wilayah': object})
            # drop col pertama
            dfpendukung = dfpendukung.drop(dfpendukung.columns[0:1], axis=1)
            # buat kolom pembantu buat filter
            dfpendukung['nmkec'] = dfpendukung.r103.str[5:]
            dfpendukung['kdkab'] = dfpendukung.kd_wilayah.str[2:4]
            # filter pake kolom baru
            dfpendukung = dfpendukung[(dfpendukung.kdkab == selectbox_kab) & 
                (dfpendukung.nmkec.str.strip() == str(selectbox_kec))]#.drop(dfpendukung.columns[-2:], axis=1)
            # select subset columns
            dfpendukung = dfpendukung[['kd_wilayah','r104','r105','rasio_tani','sektor_utama','jumlah_bank','jumlah_koperasi','keberadaan_toko_sarana_pertanian','keberadaan_fasilitas_kredit','cluster']].rename(columns={
                'kd_wilayah':'iddesa',
                'r104':'Nama Desa',
                'r105':'Status Desa',
                'rasio_tani':'Rasio petani',
                'sektor_utama':'Sektor utama',
                'jumlah_bank':'Jumlah bank',
                'jumlah_koperasi':'Jumlah koperasi',
                'keberadaan_toko_sarana_pertanian':'Keberadaan toko sarana pertanian',
                'keberadaan_fasilitas_kredit':'Keberadaan fasilitas kredit'
            }).sort_values('Nama Desa').reset_index().drop('index', axis=1)
            dfpend = dfpendukung.copy()
            
            # PLOT CLUSTERING
            # merge
            #dfpend = dfpend.merge(kec_gdf[['iddesa','Desa','Luas_Nonsawah', 'Fase_Persiapan_lahan', 'Fase_Vegetatif1', 'Fase_Vegetatif2', 'Fase_Generatif']], how='inner', on='iddesa')
            #dfpend['cluster'] = dfpend['cluster'].astype("string")
            # list selectbox
            #numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
            #listnum = dfpend.select_dtypes(include=numerics)
            # selectbox
            #cols = st.columns(3)
            #with cols[0]:
            #    selectbox_dotx = st.selectbox("Pilih Variable X", listnum.columns, index=7)
            #    #st.write(kec_gdf.columns)   
            #with cols[1]:
            #    selectbox_doty = st.selectbox("Pilih Variable Y", listnum.columns, index=0)
            #    #st.write(dfpend.columns)
            #with cols[2]:
            #    selectbox_dotz = st.selectbox("Pilih Variable Size", listnum.columns, index=2)
            # plot            
            #figplot = px.scatter(
            #    dfpend, x=selectbox_dotx, y=selectbox_doty, size=selectbox_dotz, hover_data=[dfpend.Desa],
            #    color='cluster', color_discrete_sequence=coolor_discret
            #)
            #figplot.add_scatter
            #st.plotly_chart(figplot)

            
            # apply style coloring row df n SHOW
            def highlight_color(row):
                if row['cluster'] == 2:
                    return [f'background-color: {coolor_discret[3]}; color:white;'] * len(row)
                else:
                    return [''] * len(row)
            try:
                st.dataframe(dfpendukung.drop('iddesa', axis=1).style.apply(highlight_color, axis=1))
            except Exception as e:
                st.dataframe(dfpendukung.drop('iddesa', axis=1))
                #st.write("Terjadi error: ", str(e))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                #print(exc_type, exc_tb.tb_lineno)
                st.error(
                    f"""
                    **Terjadi kesalahan.**
                    Error: {e}. Type error: {exc_type}, on line no {exc_tb.tb_lineno}
                """
                )

            
            # paragraf 
            st.markdown(
                f'<p class="small-font">Sumber Data: Podes {selectbox_thn}</p>',
                unsafe_allow_html=True,
            )
            #st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed felis arcu, mollis sit amet orci nec, tincidunt eleifend tortor. In vehicula est eget enim eleifend, ac aliquam sem gravida. Suspendisse arcu lectus, ornare viverra mi eu, egestas placerat lectus.")
            st.write("""
            Data tabel di atas dihasilkan dari analisis clustering, menggunakan Elbow Method dengan variable rasio keluarga tani, sektor utama pekerjaan di desa, jumlah bank, jumlah koperasi, dan ada tidaknya fasilitas kredit dihasilkan 2 klaster.

            Klaster 1 : memiliki ciri-ciri rasio keluarga tani yang kecil, sector utama pekerjaan di desa bukan petani tanaman pangan, serta jumlah bank dan jumlah koperasi yang banyak
            Klaster 2 : memiliki ciri-ciri rasio keluarga tani yang tinggi, sector utama pekerjaan di desa adalah petani tanaman pangan, serta jumlah bank dan jumlah koperasi yang sedikit
            
            ...
            
            rekomendasi ...
            """)

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
