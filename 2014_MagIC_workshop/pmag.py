import  numpy,string,sys
from numpy import random
import numpy.linalg
import exceptions
import os
import check_updates
import scipy
from scipy import array,sqrt,mean

def get_version():
    version=check_updates.get_version()
    return version
def sort_diclist(undecorated,sort_on):
    decorated=[(dict_[sort_on],dict_) for dict_ in undecorated]
    decorated.sort()
    return[dict_ for (key, dict_) in decorated]

def get_dictitem(In,k,v,flag):  
    # returns a list of dictionaries from list In with key,k  = value, v . CASE INSENSITIVE # allowed keywords:
    try:
        if flag=="T":return [dict for dict in In if dict[k].lower()==v.lower()] # return that which is
        if flag=="F":
            return [dict for dict in In if dict[k].lower()!=v.lower()] # return that which is not
        if flag=="has":return [dict for dict in In if v.lower() in dict[k].lower()] # return that which is contained
        if flag=="not":return [dict for dict in In if v.lower() not in dict[k].lower()] # return that which is not contained
        if flag=="eval":
            A=[dict for dict in In if dict[k]!=''] # find records with no blank values for key
            return [dict for dict in A if float(dict[k])==float(v)] # return that which is
        if flag=="min":
            A=[dict for dict in In if dict[k]!=''] # find records with no blank values for key
            return [dict for dict in A if float(dict[k])>=float(v)] # return that which is greater than
        if flag=="max":
            A=[dict for dict in In if dict[k]!=''] # find records with no blank values for key
            return [dict for dict in A if float(dict[k])<=float(v)] # return that which is less than
    except Exception, err:
        return []

def get_dictkey(In,k,dtype): 
    # returns list of given key from input list of dictionaries
    Out=[]
    for d in In: 
        if dtype=='': Out.append(d[k]) 
        if dtype=='f':
            if d[k]=="":
                Out.append(0)
            else:
                Out.append(float(d[k]))
        if dtype=='int':
            if d[k]=="":
                Out.append(0)
            else:
                Out.append(int(d[k]))
    return Out 
        

def find(f,seq):
    for item in seq:
       if f in item: return item
    return ""

def get_orient(samp_data,er_sample_name):
    # set orientation priorities
    EX=["SO-ASC","SO-POM"]
    orient={'er_sample_name':er_sample_name,'sample_azimuth':"",'sample_dip':"",'sample_description':""}
    orients=get_dictitem(samp_data,'er_sample_name',er_sample_name,'T') # get all the orientation data for this sample
    if 'sample_orientation_flag' in orients[0].keys(): orients=get_dictitem(orients,'sample_orientation_flag','b','F') # exclude all samples with bad orientation flag
    if len(orients)>0:orient=orients[0] # re-initialize to first one
    methods=get_dictitem(orients,'magic_method_codes','SO-','has')
    methods=get_dictkey(methods,'magic_method_codes','') # get a list of all orientation methods for this sample
    SO_methods=[]
    for methcode in methods:
        meths=methcode.split(":")
        for meth in meths:
           if meth.strip() not in EX:SO_methods.append(meth)
   # find top priority orientation method
    if len(SO_methods)==0:
        print "no orientation data for ",er_sample_name
        az_type="SO-NO"
    else:
        SO_priorities=set_priorities(SO_methods,0)
        az_type=SO_methods[SO_methods.index(SO_priorities[0])]
        orient=get_dictitem(orients,'magic_method_codes',az_type,'has')[0] # re-initialize to best one
    return orient,az_type
    

def cooling_rate(SpecRec,SampRecs,crfrac,crtype):
    CrSpecRec,frac,crmcd={},0,'DA-CR'
    for key in SpecRec.keys():CrSpecRec[key]=SpecRec[key]
    if len(SampRecs)>0:
        frac=.01*float(SampRecs[0]['cooling_rate_corr'])
        if 'DA-CR' in SampRecs[0]['cooling_rate_mcd']:
            crmcd=SampRecs[0]['cooling_rate_mcd']
        else:
            crmcd='DA-CR'
    elif crfrac!=0:
        frac=crfrac
        crmcd=crtype
    if frac!=0:
        inten=frac*float(CrSpecRec['specimen_int'])
        CrSpecRec["specimen_int"]='%9.4e '%(inten) # adjust specimen intensity by cooling rate correction
        CrSpecRec['magic_method_codes'] = CrSpecRec['magic_method_codes']+':crmcd'
        CrSpecRec["specimen_correction"]='c'
        return CrSpecRec
    else:
        return []


def convert_lat(Recs):
    """
    uses lat, for age<5Ma, model_lat if present, else tries to use average_inc to estimate plat.
    """
    New=[]
    for rec in Recs:
        if 'model_lat' in rec.keys() and rec['model_lat']!="":
             New.append(rec)
        elif 'average_age'  in rec.keys() and rec['average_age']!="" and  float(rec['average_age'])<=5.: 
            if 'site_lat' in rec.keys() and rec['site_lat']!="":
                 rec['model_lat']=rec['site_lat']
                 New.append(rec)
        elif 'average_inc' in rec.keys() and rec['average_inc']!="":
            rec['model_lat']='%7.1f'%(plat(float(rec['average_inc']))) 
            New.append(rec)
    return New

def convert_ages(Recs):
    """
    converts ages to Ma
    """
    New=[]
    for rec in Recs:
        age=''
        agekey=find('age',rec.keys())
        if agekey!="":
            keybase=agekey.split('_')[0]+'_'
            if rec[keybase+'age']!="": 
                age=float(rec[keybase+"age"])
            elif rec[keybase+'age_low']!="" and rec[keybase+'age_high']!='':
                age=float(rec[keybase+'age_low'])  +(float(rec[keybase+'age_high'])-float(rec[keybase+'age_low']))/2.
            if age!='':
                rec[keybase+'age_unit']
                if rec[keybase+'age_unit']=='Ma':
                    rec[keybase+'age']='%10.4e'%(age)
                elif rec[keybase+'age_unit']=='ka' or rec[keybase+'age_unit']=='Ka':
                    rec[keybase+'age']='%10.4e'%(age*.001)
                elif rec[keybase+'age_unit']=='Years AD (+/-)':
                    rec[keybase+'age']='%10.4e'%((2011-age)*1e-6)
                elif rec[keybase+'age_unit']=='Years BP':
                    rec[keybase+'age']='%10.4e'%((age)*1e-6)
                rec[keybase+'age_unit']='Ma'
                New.append(rec)
            else:
                if 'er_site_names' in rec.keys():
                    print 'problem in convert_ages:', rec['er_site_names']
                elif 'er_site_name' in rec.keys():
                    print 'problem in convert_ages:', rec['er_site_name']
                else:
                    print 'problem in convert_ages:', rec
        else:
            print 'no age key:', rec
    return New

def getsampVGP(SampRec,SiteNFO):
    site=get_dictitem(SiteNFO,'er_site_name',SampRec['er_site_name'],'T')
    try:
        lat=float(site['site_lat'])    
        lon=float(site['site_lon'])
        dec = float(SampRec['sample_dec'])
        inc = float(SampRec['sample_inc'])
        if SampRec['sample_alpha95']!="":
            a95=float(SampRec['sample_alpha95'])
        else:
            a95=0
        plong,plat,dp,dm=dia_vgp(dec,inc,a95,lat,lon)         
        ResRec={}
        ResRec['pmag_result_name']='VGP Sample: '+SampRec['er_sample_name']
        ResRec['er_location_names']=SampRec['er_location_name']
        ResRec['er_citation_names']="This study"
        ResRec['er_site_name']=SampRec['er_site_name']
        ResRec['average_dec']=SampRec['sample_dec']
        ResRec['average_inc']=SampRec['sample_inc']
        ResRec['average_alpha95']=SampRec['sample_alpha95']
        ResRec['tilt_correction']=SampRec['sample_tilt_correction']
        ResRec['pole_comp_name']=SampleRec['sample_comp_name']
        ResRec['vgp_lat']='%7.1f'%(plat)
        ResRec['vgp_lon']='%7.1f'%(plon)
        ResRec['vgp_dp']='%7.1f'%(dp)
        ResRec['vgp_dm']='%7.1f'%(dm)
        ResRec['magic_method_codes']=SampRec['magic_method_codes']+":DE-DI"
        return ResRec
    except:
        return ""

def getsampVDM(SampRec,SampNFO):
    samps=get_dictitem(SampNFO,'er_sample_name',SampRec['er_sample_name'],'T')
    if len(samps)>0:
        samp=samps[0]
        lat=float(samp['sample_lat'])    
        int = float(SampRec['sample_int'])
        vdm=b_vdm(int,lat)     
        if 'sample_int_sigma' in SampRec.keys() and  SampRec['sample_int_sigma']!="":
            sig=b_vdm(float(SampRec['sample_int_sigma']),lat)
            sig='%8.3e'%(sig)
        else:
            sig=""
    else:
        print 'could not find sample info for: ', SampRec['er_sample_name']
        return {} 
    ResRec={}
    ResRec['pmag_result_name']='V[A]DM Sample: '+SampRec['er_sample_name']
    ResRec['er_location_names']=SampRec['er_location_name']
    ResRec['er_citation_names']="This study"
    ResRec['er_site_names']=SampRec['er_site_name']
    ResRec['er_sample_names']=SampRec['er_sample_name']
    if 'sample_dec' in SampRec.keys():
        ResRec['average_dec']=SampRec['sample_dec']
    else:
        ResRec['average_dec']=""
    if 'sample_inc' in SampRec.keys():
        ResRec['average_inc']=SampRec['sample_inc']
    else:
        ResRec['average_inc']=""
    ResRec['average_int']=SampRec['sample_int']
    ResRec['vadm']='%8.3e'%(vdm)
    ResRec['vadm_sigma']=sig
    ResRec['magic_method_codes']=SampRec['magic_method_codes']
    ResRec['model_lat']=samp['sample_lat']
    return ResRec

def getfield(irmunits,coil,treat):
# calibration of ASC Impulse magnetizer
    if coil=="3": m,b=0.0071,-0.004 # B=mh+b where B is in T, treat is in Volts
    if coil=="2": m,b=0.00329,-0.002455 # B=mh+b where B is in T, treat is in Volts
    if coil=="1": m,b=0.0002,-0.0002 # B=mh+b where B is in T, treat is in Volts
    return float(treat)*m+b 
     

def sortbykeys(input,sort_list):
    Output = []
    List=[] # get a list of what to be sorted by second key
    for rec in input:
        if rec[sort_list[0]] not in List:List.append(rec[sort_list[0]])
    for current in List: # step through input finding all records of current
        Currents=[]
        for rec in input:
            if rec[sort_list[0]]==current:Currents.append(rec)
        Current_sorted=sort_diclist(Currents,sort_list[1])
        for rec in Current_sorted:
            Output.append(rec)
    return Output

def get_list(data,key): # return a colon delimited list of unique key values
    keylist=[]
    for rec in data:
        keys=rec[key].split(':')
        for k in keys: 
            if k not in keylist:keylist.append(k)
    keystring=""
    if len(keylist)==0:return keystring
    for k in keylist:keystring=keystring+':'+k
    return keystring[1:]

def ParseSiteFile(site_file):
    Sites,file_type=magic_read(site_file)
    LocNames,Locations=[],[]
    for site in Sites:
        if site['er_location_name'] not in LocNames: # new location name
            LocNames.append(site['er_location_name'])
            sites_locs=get_dictitem(Sites,'er_location_name',site['er_location_name'],'T') # get all sites for this loc
            lats=get_dictkey(sites_locs,'site_lat','f') # get all the latitudes as floats
            lons=get_dictkey(sites_locs,'site_lon','f') # get all the longitudes as floats
            LocRec={'er_citation_names':'This study','er_location_name':site['er_location_name'],'location_type':''}
            LocRec['location_begin_lat']=str(min(lats))
            LocRec['location_end_lat']=str(max(lats))
            LocRec['location_begin_lon']=str(min(lons))
            LocRec['location_end_lon']=str(max(lons))
            Locations.append(LocRec)
    return Locations

def ParseMeasFile(measfile,sitefile,instout,specout): # fix up some stuff for uploading
    #
    # read in magic_measurements file to get specimen, and instrument names
    #
    master_instlist=[]
    InstRecs=[]
    meas_data,file_type=magic_read(measfile)
    if file_type != 'magic_measurements':
        print file_type,"This is not a valid magic_measurements file "
        sys.exit()
    # read in site data
    if sitefile!="":
        SiteNFO,file_type=magic_read(sitefile)
        if file_type=="bad_file":
            print "Bad  or no er_sites file - lithology, etc will not be imported"
    else:
        SiteNFO=[]
    # define the Er_specimen records to create a new er_specimens.txt file
    #
    suniq,ErSpecs=[],[]
    for rec in meas_data:
# fill in some potentially missing fields
        if "magic_instrument_codes" in rec.keys():
            list=(rec["magic_instrument_codes"])
            list.strip()
            tmplist=list.split(":")
            for inst in tmplist:
                if inst not in master_instlist:
                    master_instlist.append(inst)
                    InstRec={}
                    InstRec["magic_instrument_code"]=inst
                    InstRecs.append(InstRec)
        if "measurement_standard" not in rec.keys():rec['measurement_standard']='u' # make this an unknown if not specified
        if rec["er_specimen_name"] not in suniq and rec["measurement_standard"]!='s': # exclude standards
            suniq.append(rec["er_specimen_name"])
            ErSpecRec={}
            ErSpecRec["er_citation_names"]="This study"
            ErSpecRec["er_specimen_name"]=rec["er_specimen_name"]
            ErSpecRec["er_sample_name"]=rec["er_sample_name"]
            ErSpecRec["er_site_name"]=rec["er_site_name"]
            ErSpecRec["er_location_name"]=rec["er_location_name"]
    #
    # attach site litho, etc. to specimen if not already there
            sites=get_dictitem(SiteNFO,'er_site_name',rec['er_site_name'],'T')
            if len(sites)==0:
                site={}
                print 'site record in er_sites table not found for: ',rec['er_site_name']
            else:
                site=sites[0]
            if 'site_class' not in site.keys() or 'site_lithology' not in site.keys() or 'site_type' not in site.keys():
                site['site_class']='Not Specified'
                site['site_lithology']='Not Specified'
                site['site_type']='Not Specified'
            if 'specimen_class' not in ErSpecRec.keys():ErSpecRec["specimen_class"]=site['site_class'] 
            if 'specimen_lithology' not in ErSpecRec.keys():ErSpecRec["specimen_lithology"]=site['site_lithology'] 
            if 'specimen_type' not in ErSpecRec.keys():ErSpecRec["specimen_type"]=site['site_type'] 
            if 'specimen_volume' not in ErSpecRec.keys():ErSpecRec["specimen_volume"]=""
            if 'specimen_weight' not in ErSpecRec.keys():ErSpecRec["specimen_weight"]=""
            ErSpecs.append(ErSpecRec)
    #
    #
    # save the data
    #
    magic_write(specout,ErSpecs,"er_specimens")
    print " Er_Specimen data (with updated info from site if necessary)  saved in ",specout
    #
    # write out the instrument list
    if len(InstRecs) >0:
        magic_write(instout,InstRecs,"magic_instruments")
        print " Instruments data saved in ",instout
    else: 
        print "No instruments found"

def ReorderSamples(specfile,sampfile,outfile): # take care of re-ordering sample table, putting used orientations first
    UsedSamps,RestSamps=[],[]
    Specs,filetype=magic_read(specfile) # read in specimen file
    Samps,filetype=magic_read(sampfile) # read in sample file
    for rec in Specs: # hunt through specimen by specimen
        meths=rec['magic_method_codes'].strip().strip('\n').split(':')
        for meth in meths:
            methtype=meth.strip().strip('\n').split('-')
            if 'SO' in methtype:
                SO_meth=meth # find the orientation method code
        samprecs=get_dictitem(Samps,'er_sample_name',rec['er_sample_name'],'T')
        used=get_dictitem(samprecs,'magic_method_codes',SO_meth,'has') 
        if len(used)>0:
            UsedSamps.append(used[0])
        else:
            print 'orientation not found for: ',rec['er_specimen_name']
        rest=get_dictitem(samprecs,'magic_method_codes',SO_meth,'not') 
        for rec in rest:
            RestSamps.append(rec)
    for rec in RestSamps:
        UsedSamps.append(rec) # append the unused ones to the end of the file
    magic_write(outfile,UsedSamps,'er_samples')

def orient(mag_azimuth,field_dip,or_con):
    """
    uses specified orientation convention to convert user supplied orientations
    to laboratory azimuth and plunge
    """
    or_con = str(or_con)
    if mag_azimuth==-999:return "",""
    if or_con=="1": # lab_mag_az=mag_az;  sample_dip = -dip
        return mag_azimuth, -field_dip
    if or_con=="2":
        return mag_azimuth-90.,-field_dip
    if or_con=="3": # lab_mag_az=mag_az;  sample_dip = 90.-dip
        return mag_azimuth, 90.-field_dip
    if or_con=="4": # lab_mag_az=mag_az;  sample_dip = dip
        return mag_azimuth, field_dip
    if or_con=="5": # lab_mag_az=mag_az;  sample_dip = dip-90.
        return mag_azimuth, field_dip-90.
    if or_con=="6": # lab_mag_az=mag_az-90.;  sample_dip = 90.-dip
        return mag_azimuth-90., 90.-field_dip
    if or_con=="7": # lab_mag_az=mag_az;  sample_dip = 90.-dip
        return mag_azimuth-90., 90.-field_dip
    print "Error in orientation convention"


def get_Sb(data):
    """
    returns vgp scatter for data set
    """
    Sb,N=0.,0.
    for  rec in data:
                delta=90.-abs(float(rec['vgp_lat']))
                if rec['average_k']!="0":
                    k=float(rec['average_k'])
                    L=float(rec['average_lat'])*numpy.pi/180. # latitude in radians
                    Nsi=float(rec['average_nn'])
                    K=k/(2.*(1.+3.*numpy.sin(L)**2)/(5.-3.*numpy.sin(L)**2))
                    Sw=81./numpy.sqrt(K)
                else:
                    Sw,Nsi=0,1.
                Sb+=delta**2.-(Sw**2)/Nsi
                N+=1.
    return numpy.sqrt( Sb/float(N-1.) )
def default_criteria(nocrit):
    Crits={}
    critkeys=['magic_experiment_names', 'measurement_step_min', 'measurement_step_max', 'measurement_step_unit', 'specimen_polarity', 'specimen_nrm', 'specimen_direction_type', 'specimen_comp_nmb', 'specimen_mad', 'specimen_alpha95', 'specimen_n', 'specimen_int_sigma', 'specimen_int_sigma_perc', 'specimen_int_rel_sigma', 'specimen_int_rel_sigma_perc', 'specimen_int_mad', 'specimen_int_n', 'specimen_w', 'specimen_q', 'specimen_f', 'specimen_fvds', 'specimen_b_sigma', 'specimen_b_beta', 'specimen_g', 'specimen_dang', 'specimen_md', 'specimen_ptrm', 'specimen_drat', 'specimen_drats', 'specimen_rsc', 'specimen_viscosity_index', 'specimen_magn_moment', 'specimen_magn_volume', 'specimen_magn_mass', 'specimen_int_dang','specimen_int_ptrm_n', 'specimen_delta', 'specimen_theta', 'specimen_gamma', 'specimen_frac','specimen_gmax','specimen_scat','sample_polarity', 'sample_nrm', 'sample_direction_type', 'sample_comp_nmb', 'sample_sigma', 'sample_alpha95', 'sample_n', 'sample_n_lines', 'sample_n_planes', 'sample_k', 'sample_r', 'sample_tilt_correction', 'sample_int_sigma', 'sample_int_sigma_perc', 'sample_int_rel_sigma', 'sample_int_rel_sigma_perc', 'sample_int_n', 'sample_magn_moment', 'sample_magn_volume', 'sample_magn_mass', 'site_polarity', 'site_nrm', 'site_direction_type', 'site_comp_nmb', 'site_sigma', 'site_alpha95', 'site_n', 'site_n_lines', 'site_n_planes', 'site_k', 'site_r', 'site_tilt_correction', 'site_int_sigma', 'site_int_sigma_perc', 'site_int_rel_sigma', 'site_int_rel_sigma_perc', 'site_int_n', 'site_magn_moment', 'site_magn_volume', 'site_magn_mass', 'average_age_min', 'average_age_max', 'average_age_sigma', 'average_age_unit', 'average_sigma', 'average_alpha95', 'average_n', 'average_nn', 'average_k', 'average_r', 'average_int_sigma', 'average_int_rel_sigma', 'average_int_rel_sigma_perc', 'average_int_n', 'average_int_nn', 'vgp_dp', 'vgp_dm', 'vgp_sigma', 'vgp_alpha95', 'vgp_n', 'vdm_sigma', 'vdm_n', 'vadm_sigma', 'vadm_n', 'criteria_description', 'er_citation_names']
    for key in critkeys:Crits[key]='' # set up dictionary with all possible
    Crits['pmag_criteria_code']='ACCEPT'
    Crits['criteria_definition']='acceptance criteria for study'
    Crits['er_citation_names']='This study'
    if nocrit==0: # use default criteria
# 
# set some sort of quasi-reasonable default criteria
#   
        Crits['specimen_mad']='5'
        Crits['specimen_dang']='10'
        Crits['specimen_int_n']='4'
        Crits['specimen_int_ptrm_n']='2'
        Crits['specimen_drats']='20'
        Crits['specimen_b_beta']='0.1'
        Crits['specimen_md']='15'
        Crits['specimen_fvds']='0.7'
        Crits['specimen_q']='1.0'
        Crits['specimen_int_dang']='10'
        Crits['specimen_int_mad']='10'
        Crits['sample_alpha95']='5'
        Crits['site_int_n']='2'
        Crits['site_int_sigma']='5e-6' 
        Crits['site_int_sigma_perc']='15'
        Crits['site_n']='5'
        Crits['site_n_lines']='4'
        Crits['site_k']='50'
    return [Crits]

def grade(PmagRec,ACCEPT,type): 
    """
    Finds the 'grade' (pass/fail; A/F) of a record (specimen,sample,site) given the acceptance criteria
    """
    GREATERTHAN=['specimen_q','site_k','site_n','site_n_lines','site_int_n','measurement_step_min','specimen_int_ptrm_n','specimen_fvds','specimen_frac','specimen_f','specimen_n','specimen_int_n','sample_int_n','average_age_min','average_k','average_r','specimen_magn_moment','specimen_magn_volumn','specimen_rsc','sample_n','sample_n_lines','sample_n_planes','sample_k','sample_r','site_magn_moment','site_magn_volumn','site_magn_mass','site_r'] # these statistics must be exceede to pass, all others must be less than (except specimen_scat, which must be true)
    ISTRUE=['specimen_scat']
    kill=[] # criteria that kill the record
    sigma_types=['sample_int_sigma','sample_int_sigma_perc','site_int_sigma','site_int_sigma_perc','average_int_sigma','average_int_sigma_perc']
    sigmas=[]
    accept={}
    if type=='specimen_int': 
        USEKEYS=['specimen_q','measurement_step_min','measurement_step_max','specimen_int_ptrm_n','specimen_fvds','specimen_frac','specimen_f','specimen_int_n','specimen_magn_moment','specimen_magn_volumn','specimen_rsc','specimen_scat','specimen_drats','specimen_int_mad','specimen_int_dang','specimen_md','specimen_b_beta','specimen_w','specimen_gmax'] 
    elif type=='specimen_dir':
        USEKEYS=['measurement_step_min','measurement_step_max','specimen_mad','specimen_n','specimen_magn_moment','specimen_magn_volumn']
    elif type=='sample_int':
        USEKEYS=['sample_int_n','sample_int_sigma','sample_int_sigma_perc']
    elif type=='sample_dir':
        USEKEYS=['sample_alpha95','sample_n','sample_n_lines','sample_n_planes','sample_k','sample_r']
    elif type=='site_int':
        USEKEYS=['site_int_sigma','site_int_sigma_perc','site_int_n']
    elif type=='site_dir':
        USEKEYS=['site_alpha95','site_k','site_n','site_n_lines','site_n_planes','site_r']
 
    for key in ACCEPT.keys():
        if ACCEPT[key]!="" and key in USEKEYS:
            if key in ISTRUE and ACCEPT[key]=='TRUE' or ACCEPT[key]=='True':
                ACCEPT[key]='1' # this is because Excel always capitalizes True to TRUE and python doesn't recognize that as a boolean.  never mind
            elif ACCEPT[key]=='FALSE' or ACCEPT[key]=='False':
                ACCEPT[key]='0'
            elif eval(ACCEPT[key])==0: 
                ACCEPT[key]=""
            accept[key]=ACCEPT[key]
    for key in sigma_types:
        if key in USEKEYS and key in accept.keys() and key in PmagRec.keys(): sigmas.append(key)
    if len(sigmas)>1:
        if PmagRec[sigmas[0]]=="" or PmagRec[sigmas[1]]=="":
           kill.append(sigmas[0]) 
           kill.append(sigmas[1]) 
        elif eval(PmagRec[sigmas[0]])>eval(accept[sigmas[0]]) and eval(PmagRec[sigmas[1]])>eval(accept[sigmas[1]]):
           kill.append(sigmas[0]) 
           kill.append(sigmas[1]) 
    elif len(sigmas)==1 and sigmas[0] in accept.keys():
        if PmagRec[sigmas[0]]>accept[sigmas[0]]:
           kill.append(sigmas[0]) 
    for key in accept.keys():
     if accept[key]!="": 
        if key not in PmagRec.keys() or PmagRec[key]=='': 
            kill.append(key)
        elif key not in sigma_types:
            if key in ISTRUE: # boolean must be true
                if PmagRec[key]!='1':
                    kill.append(key)
            if key in GREATERTHAN:
                if eval(PmagRec[key])<eval(accept[key]):
                    kill.append(key)
            else:
                if eval(PmagRec[key])>eval(accept[key]):
                    kill.append(key)
    return kill
    
#
def flip(D):
    """
     flip reverse mode
    """
    ppars=doprinc(D) # get principle direction
    D1,D2=[],[]
    for rec in D:
        ang=angle([rec[0],rec[1]],[ppars['dec'],ppars['inc']])
        if ang>90.:
            d,i=(rec[0]-180.)%360.,-rec[1]
            D2.append([d,i,1.])
        else:
            D1.append([rec[0],rec[1],1.])
    return D1,D2
#
def dia_vgp(*args): # new function interface by J.Holmes, SIO, 6/1/2011
    """
    converts declination, inclination, alpha95 to VGP, dp, dm
    """
    # test whether arguments are one 2-D list or 5 floats 
    if len(args) == 1: # args comes in as a tuple of multi-dim lists.
        largs=list(args).pop() # scrap the tuple.
        (decs, dips, a95s, slats, slongs) = zip(*largs) # reorganize the lists so that we get columns of data in each var.       
    else:
        # When args > 1, we are receiving five floats. This usually happens when the invoking script is 
        # executed in interactive mode.
        (decs, dips, a95s, slats, slongs) = (args)
       
    # We send all incoming data to numpy in an array form. Even if it means a 1x1 matrix. That's OKAY. Really.
    (dec, dip, a95, slat, slong) = (numpy.array(decs), numpy.array(dips), numpy.array(a95s), \
                                    numpy.array(slats), numpy.array(slongs)) # package columns into arrays
    rad=numpy.pi/180. # convert to radians
    dec,dip,a95,slat,slong=dec*rad,dip*rad,a95*rad,slat*rad,slong*rad
    p=numpy.arctan2(2.0,numpy.tan(dip))
    plat=numpy.arcsin(numpy.sin(slat)*numpy.cos(p)+numpy.cos(slat)*numpy.sin(p)*numpy.cos(dec))
    beta=(numpy.sin(p)*numpy.sin(dec))/numpy.cos(plat)
    
    #------------------------------------------------------------------------------------------------------------
    # The deal with "boolmask":
    # We needed a quick way to assign matrix values based on a logic decision, in this case setting boundaries
    # on out-of-bounds conditions. Creating a matrix of boolean values the size of the original matrix and using 
    # it to "mask" the assignment solves this problem nicely. The downside to this is that Numpy complains if you 
    # attempt to mask a non-matrix, so we have to check for array type and do a normal assignment if the type is 
    # scalar. These checks are made before calculating for the rest of the function.
    #------------------------------------------------------------------------------------------------------------

    boolmask = beta > 1. # create a mask of boolean values
    if isinstance(beta,numpy.ndarray):
        beta[boolmask] = 1. # assigns 1 only to elements that mask TRUE.
    else: # Numpy gets upset if you try our masking trick with a scalar or a 0-D matrix.
        if boolmask:
            beta = 1.
    boolmask = beta < -1.
    if isinstance(beta,numpy.ndarray):
        beta[boolmask] = -1. # assigns -1 only to elements that mask TRUE.
    else:
        if boolmask:
            beta = -1.

    beta=numpy.arcsin(beta)
    plong = slong+numpy.pi-beta
    if (numpy.cos(p) > numpy.sin(slat)*numpy.sin(plat)).any():
        boolmask = (numpy.cos(p) > (numpy.sin(slat)*numpy.sin(plat)))
        if isinstance(plong,numpy.ndarray):
            plong[boolmask] = (slong+beta)[boolmask]
        else:
            if boolmask:
                plong = slong+beta
        
    boolmask = (plong < 0)
    if isinstance(plong,numpy.ndarray):
        plong[boolmask] = plong[boolmask]+2*numpy.pi
    else:
        if boolmask:
            plong = plong+2*numpy.pi

    boolmask = (plong > 2*numpy.pi)
    if isinstance(plong,numpy.ndarray):
        plong[boolmask] = plong[boolmask]-2*numpy.pi
    else:
        if boolmask:
            plong = plong-2*numpy.pi

    dm=a95* (numpy.cos(slat)/numpy.cos(dip))/rad
    dp=a95*(1+3*(numpy.sin(slat)**2))/(2*rad)
    plat,plong=plat/rad,plong/rad
    return plong.tolist(),plat.tolist(),dp.tolist(),dm.tolist()

def int_pars(x,y,vds):
    """
     calculates York regression and Coe parameters (with Tauxe Fvds)
    """
# first do linear regression a la York
    xx,yer,xer,xyer,yy,xsum,ysum,xy=0.,0.,0.,0.,0.,0.,0.,0.
    xprime,yprime=[],[]
    pars={}
    pars["specimen_int_n"]=len(x)
    n=float(len(x))
    if n<=2:
        print "shouldn't be here at all!"
        return pars,1
    for i in range(len(x)):
        xx+=x[i]**2.
        yy+=y[i]**2.
        xy+=x[i]*y[i]
        xsum+=x[i]
        ysum+=y[i]
    xsig=numpy.sqrt((xx-(xsum**2./n))/(n-1.))
    ysig=numpy.sqrt((yy-(ysum**2./n))/(n-1.))
    sum=0
    for i in range(int(n)):
        yer+= (y[i]-ysum/n)**2.
        xer+= (x[i]-xsum/n)**2.
        xyer+= (y[i]-ysum/n)*(x[i]-xsum/n)
    slop=-numpy.sqrt(yer/xer)
    pars["specimen_b"]=slop
    s1=2.*yer-2.*slop*xyer
    s2=(n-2.)*xer
    sigma=numpy.sqrt(s1/s2)
    pars["specimen_b_sigma"]=sigma
    s=(xy-(xsum*ysum/n))/(xx-(xsum**2.)/n)
    r=(s*xsig)/ysig
    pars["specimen_rsc"]=r**2.
    ytot=abs(ysum/n-slop*xsum/n)
    for i in range(int(n)):
        xprime.append((slop*x[i]+y[i]-ytot)/(2.*slop))
        yprime.append(((slop*x[i]+y[i]-ytot)/2.)+ytot)
    sumdy,dy=0,[]
    dyt = abs(yprime[0]-yprime[int(n)-1])
    for i in range((int(n)-1)):
        dy.append(abs(yprime[i+1]-yprime[i]))
        sumdy+= dy[i]**2.
    f=dyt/ytot
    pars["specimen_f"]=f
    pars["specimen_ytot"]=ytot
    ff=dyt/vds
    pars["specimen_fvds"]=ff
    ddy=(1./dyt)*sumdy
    g=1.-ddy/dyt
    pars["specimen_g"]=g
    q=abs(slop)*f*g/sigma
    pars["specimen_q"]=q
    pars["specimen_b_beta"]=-sigma/slop
    return pars,0

def dovds(data):
    """
     calculates vector difference sum for demagnetization data
    """
    vds,X=0,[]
    for rec in data:
        X.append(dir2cart(rec))
    for k  in range(len(X)-1):
        xdif=X[k+1][0]-X[k][0]
        ydif=X[k+1][1]-X[k][1]
        zdif=X[k+1][2]-X[k][2]
        vds+=numpy.sqrt(xdif**2+ydif**2+zdif**2)
    vds+=numpy.sqrt(X[-1][0]**2+X[-1][1]**2+X[-1][2]**2)
    return vds
def vspec_magic(data):
    """
   takes average vector of replicate measurements
    """
    vdata,Dirdata,step_meth=[],[],""
    if len(data)==0:return vdata
    treat_init=["treatment_temp", "treatment_temp_decay_rate", "treatment_temp_dc_on", "treatment_temp_dc_off", "treatment_ac_field", "treatment_ac_field_decay_rate", "treatment_ac_field_dc_on", "treatment_ac_field_dc_off", "treatment_dc_field", "treatment_dc_field_decay_rate", "treatment_dc_field_ac_on", "treatment_dc_field_ac_off", "treatment_dc_field_phi", "treatment_dc_field_theta"]
    treats=[]
#
# find keys that are used
#
    for key in treat_init:
        if key in data[0].keys():treats.append(key)  # get a list of keys
    stop={}
    stop["er_specimen_name"]="stop"
    for key in treats:
        stop[key]="" # tells program when to quit and go home
    data.append(stop)
#
# set initial states
#
    DataState0,newstate={},0
    for key in treats:
        DataState0[key]=data[0][key] # set beginning treatment
    k,R=1,0
    for i in range(k,len(data)):
        Dirdata,DataStateCurr,newstate=[],{},0
        for key in treats:  # check if anything changed
	    DataStateCurr[key]=data[i][key] 
            if DataStateCurr[key].strip() !=  DataState0[key].strip(): newstate=1 # something changed
        if newstate==1:
            if i==k: # sample is unique 
                vdata.append(data[i-1])
            else: # measurement is not unique
                print "averaging: records " ,k,i
                for l in range(k-1,i):
                    Dirdata.append([float(data[l]['measurement_dec']),float(data[l]['measurement_inc']),float(data[l]['measurement_magn_moment'])])
                dir,R=vector_mean(Dirdata)
                Fpars=fisher_mean(Dirdata)
                vrec=data[i-1]
                vrec['measurement_dec']='%7.1f'%(dir[0])
                vrec['measurement_inc']='%7.1f'%(dir[1])
                vrec['measurement_magn_moment']='%8.3e'%(R/(i-k+1))
                vrec['measurement_csd']='%7.1f'%(Fpars['csd'])
                vrec['measurement_positions']='%7.1f'%(Fpars['n'])
                vrec['measurement_description']='average of multiple measurements'
                if "magic_method_codes" in vrec.keys():
                    meths=vrec["magic_method_codes"].strip().split(":")
                    if "DE-VM" not in meths:meths.append("DE-VM")
                    methods=""
                    for meth in meths:
                        methods=methods+meth+":"
                    vrec["magic_method_codes"]=methods[:-1]
                else: vrec["magic_method_codes"]="DE-VM"
                vdata.append(vrec)
# reset state to new one
            for key in treats:
                DataState0[key]=data[i][key] # set beginning treatment
            k=i+1
            if data[i]["er_specimen_name"] =="stop":
                del data[-1]  # get rid of dummy stop sign
                return vdata,treats # bye-bye

#
def get_specs(data):
    """
     takes a magic format file and returns a list of unique specimen names
    """
# sort the specimen names
#
    speclist=[]
    for rec in data:
      spec=rec["er_specimen_name"]
      if spec not in speclist:speclist.append(spec)
    speclist.sort()
    return speclist


def vector_mean(data):
    """
    calculates the vector mean of a given set of vectors
    """
    R,Xbar,X=0,[0,0,0],[]
    for rec in data:
        X.append(dir2cart(rec))
    for i in range(len(X)):
        for c in range(3):
           Xbar[c]+=X[i][c]
    for c in range(3):
        R+=Xbar[c]**2
    R=numpy.sqrt(R)
    for c in range(3):
        Xbar[c]=Xbar[c]/R    
    dir=cart2dir(Xbar)
    return dir, R 
def mark_dmag_rec(s,ind,data):
    """
    edits demagnetization data to mark "bad" points with measurement_flag
    """
    datablock=[]
    for rec in  data:
        if rec['er_specimen_name']==s:
            meths=rec['magic_method_codes'].split(':')
            if 'LT-NO' in meths or 'LT-AF-Z' in meths or 'LT-T-Z' in meths:
                datablock.append(rec)
    dmagrec=datablock[ind]
    for k in  range(len(data)):
        meths=data[k]['magic_method_codes'].split(':')
        if 'LT-NO' in meths or 'LT-AF-Z' in meths or 'LT-T-Z' in meths:
            if data[k]['er_specimen_name']==s:
                if data[k]['treatment_temp']==dmagrec['treatment_temp'] and data[k]['treatment_ac_field']==dmagrec['treatment_ac_field']:
                    if data[k]['measurement_dec']==dmagrec['measurement_dec'] and data[k]['measurement_inc']==dmagrec['measurement_inc'] and data[k]['measurement_magn_moment']==dmagrec['measurement_magn_moment']:
                        if data[k]['measurement_flag']=='g':
                            flag='b'
                        else:
                            flag='g'
                        data[k]['measurement_flag']=flag
                        break
    return data


def mark_samp(Samps,data,crd):




    return Samps

def find_dmag_rec(s,data):
    """
    returns demagnetization data for specimen s from the data - excludes other kinds of experiments and "bad" measurements
    """
    EX=["LP-AN-ARM","LP-AN-TRM","LP-ARM-AFD","LP-ARM2-AFD","LP-TRM-AFD","LP-TRM","LP-TRM-TD","LP-X"] # list of excluded lab protocols
    INC=["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z", "LP-PI-TRM-IZ", "LP-PI-M-IZ"]
    datablock,tr=[],""
    therm_flag,af_flag,mw_flag=0,0,0
    units=[]
    spec_meas=get_dictitem(data,'er_specimen_name',s,'T')
    for rec in spec_meas:
           if 'measurement_flag' not in rec.keys():rec['measurement_flag']='g'
           skip=1
           tr=""
           methods=rec["magic_method_codes"].split(":")
           for meth in methods:
               if meth.strip() in INC:
                   skip=0
           for meth in EX:
               if meth in methods:skip=1
           if skip==0:
               if "LT-NO" in methods: 
                   tr = float(rec["treatment_temp"])
               if "LT-AF-Z" in methods: 
                   af_flag=1
                   tr = float(rec["treatment_ac_field"])
                   if "T" not in units:units.append("T")
               if "LT-T-Z" in methods: 
                   therm_flag=1
                   tr = float(rec["treatment_temp"])
                   if "K" not in units:units.append("K")
               if "LT-M-Z" in methods: 
                   mw_flag=1
                   tr = float(rec["treatment_mw_power"])*float(rec["treatment_mw_time"])
                   if "J" not in units:units.append("J")
               if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:  # looking for in-field first thellier or microwave data - otherwise, just ignore this
                   ZI=0
               else:
                   ZI=1
               Mkeys=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
               if tr !="":
                   dec,inc,int = "","",""
                   if "measurement_dec" in rec.keys() and rec["measurement_dec"] != "":
                       dec=float(rec["measurement_dec"])
                   if "measurement_inc" in rec.keys() and rec["measurement_inc"] != "":
                       inc=float(rec["measurement_inc"])
                   for key in Mkeys:
                       if key in rec.keys() and rec[key]!="":int=float(rec[key])
                   if 'magic_instrument_codes' not in rec.keys():rec['magic_instrument_codes']=''
                   datablock.append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
    if therm_flag==1:
        for k in range(len(datablock)):
            if datablock[k][0]==0.: datablock[k][0]=273.
    if af_flag==1:
        for k in range(len(datablock)):
            if datablock[k][0]>=273 and datablock[k][0]<=323: datablock[k][0]=0.
    meas_units=""
    if len(units)>0:
        for u in units:meas_units=meas_units+u+":"
        meas_units=meas_units[:-1]
    return datablock,meas_units
 

def magic_read(infile):
    """ 
    reads  a Magic template file, puts data in a list of dictionaries
    """
    hold,magic_data,magic_record,magic_keys=[],[],{},[]
    try:
        f=open(infile,"rU")
    except:
        return [],'bad_file'
    d = f.readline()[:-1].strip('\n')
    if d[0]=="s" or d[1]=="s":
        delim='space'
    elif d[0]=="t" or d[1]=="t":
        delim='tab'
    else: 
        print 'error reading ', infile
        sys.exit()
    if delim=='space':file_type=d.split()[1]
    if delim=='tab':file_type=d.split('\t')[1]
    if file_type=='delimited':
        if delim=='space':file_type=d.split()[2]
        if delim=='tab':file_type=d.split('\t')[2]
    if delim=='space':line =f.readline()[:-1].split()
    if delim=='tab':line =f.readline()[:-1].split('\t')
    for key in line:
        magic_keys.append(key)
    lines=f.readlines()
    if len(lines)<1:
       return [],'empty_file' 
    for line in lines[:-1]:
        line.replace('\n','')
        if delim=='space':rec=line[:-1].split()
        if delim=='tab':rec=line[:-1].split('\t')
        hold.append(rec)
    line = lines[-1].replace('\n','')
    if delim=='space':rec=line[:-1].split()
    if delim=='tab':rec=line.split('\t')
    hold.append(rec)
    for rec in hold:
        magic_record={}
        if len(magic_keys) != len(rec):
            
            print "Warning: Uneven record lengths detected: "
            print magic_keys
            print rec
        # modified by Ron Shaar:
        # add a health check:
        # if len(magic_keys) > len(rec): take rec
        # if len(magic_keys) < len(rec): take magic_keys
        # original code: for k in range(len(rec)):
        # channged to: for k in range(min(len(magic_keys),len(rec))):
        for k in range(min(len(magic_keys),len(rec))):
           magic_record[magic_keys[k]]=rec[k].strip('\n')
        magic_data.append(magic_record)
    magictype=file_type.lower().split("_")
    Types=['er','magic','pmag','rmag']
    if magictype in Types:file_type=file_type.lower()
    return magic_data,file_type
#
def upload_read(infile,table):
    """
    reads  a table from a MagIC upload (or downloaded) txt file, 
     puts data in a list of dictionaries
    """
    delim='tab'
    hold,magic_data,magic_record,magic_keys=[],[],{},[]
    f=open(infile,"rU")
#
# look for right table
#
    line =f.readline()[:-1]
    file_type=line.split('\t')[1]
    if file_type=='delimited': file_type=line.split('\t')[2]
    if delim=='tab':
        line =f.readline()[:-1].split('\t')
    else:
        print "only tab delimitted files are supported now"
        sys.exit()
    while file_type!=table:
        while line[0][0:5] in f.readlines() !=">>>>>":
            pass
        line =f.readline()[:-1]
        file_type=line.split('\t')[1]
        if file_type=='delimited': file_type=line.split('\t')[2]
        ine =f.readline()[:-1].split('\t')
    while line[0][0:5] in f.readlines() !=">>>>>":
        for key in line:
            magic_keys.append(key)
        for line in f.readlines():
            rec=line[:-1].split('\t')
            hold.append(rec)
        for rec in hold:
            magic_record={}
            if len(magic_keys) != len(rec):
                print "Uneven record lengths detected: ",rec
                raw_input("Return to continue.... ")
            for k in range(len(magic_keys)):
                magic_record[magic_keys[k]]=rec[k]
            magic_data.append(magic_record)
    return magic_data
#
#
def putout(ofile,keylist,Rec):
    """
    writes out a magic format record to ofile
    """
    pmag_out=open(ofile,'a')
    outstring=""
    for key in keylist:
        try:
           outstring=outstring+'\t'+Rec[key].strip()
        except:
           print key,Rec[key]
           raw_input()
    outstring=outstring+'\n'
    pmag_out.write(outstring[1:])
    pmag_out.close()

def first_rec(ofile,Rec,file_type): 
    """
    opens the file ofile as a magic template file with headers as the keys to Rec
    """
    keylist=[]
    pmag_out=open(ofile,'w')
    outstring="tab \t"+file_type+"\n"
    pmag_out.write(outstring)
    keystring=""
    for key in Rec.keys():
        keystring=keystring+'\t'+key.strip()
        keylist.append(key)
    keystring=keystring + '\n'
    pmag_out.write(keystring[1:])
    pmag_out.close()
    return keylist

def magic_write(ofile,Recs,file_type):
    """
    writes out a magic format list of dictionaries to ofile
    """
    
    if len(Recs)<1:
        return False
    pmag_out=open(ofile,'w')
    outstring="tab \t"+file_type+"\n"
    pmag_out.write(outstring)
    keystring=""
    keylist=[]
    for key in Recs[0].keys():
        keylist.append(key)
    keylist.sort()
    for key in keylist:
        keystring=keystring+'\t'+key.strip()
    keystring=keystring + '\n'
    pmag_out.write(keystring[1:])
    for Rec in Recs:
        outstring=""
        for key in keylist:
           try:
              outstring=outstring+'\t'+str(Rec[key].strip())
           except:
              if 'er_specimen_name' in Rec.keys():
                  print Rec['er_specimen_name'] 
              elif 'er_specimen_names' in Rec.keys():
                  print Rec['er_specimen_names'] 
              print key,Rec[key]
              raw_input()
        outstring=outstring+'\n'
        pmag_out.write(outstring[1:])
    pmag_out.close()
    return True


def dotilt(dec,inc,bed_az,bed_dip):
    """
    does a tilt correction on dec,inc using bedding dip direction bed_az and dip bed_dip
    """
    rad=numpy.pi/180. # converts from degrees to radians
    X=dir2cart([dec,inc,1.]) # get cartesian coordinates of dec,inc
# get some sines and cosines of new coordinate system
    sa,ca= -numpy.sin(bed_az*rad),numpy.cos(bed_az*rad) 
    cdp,sdp= numpy.cos(bed_dip*rad),numpy.sin(bed_dip*rad) 
# do the rotation
    xc=X[0]*(sa*sa+ca*ca*cdp)+X[1]*(ca*sa*(1.-cdp))+X[2]*sdp*ca
    yc=X[0]*ca*sa*(1.-cdp)+X[1]*(ca*ca+sa*sa*cdp)-X[2]*sa*sdp
    zc=X[0]*ca*sdp-X[1]*sdp*sa-X[2]*cdp
# convert back to direction:
    Dir=cart2dir([xc,yc,-zc])
    return Dir[0],Dir[1] # return declination, inclination of rotated direction


def dotilt_V(input):
    """
    does a tilt correction on dec,inc using bedding dip direction bed_az and dip bed_dip
    """
    input=input.transpose() 
    dec, inc, bed_az, bed_dip =input[0],input[1],input[2],input[3]  # unpack input array into separate arrays
    rad=numpy.pi/180. # convert to radians
    Dir=numpy.array([dec,inc]).transpose()
    X=dir2cart(Dir).transpose() # get cartesian coordinates
    N=numpy.size(dec)

# get some sines and cosines of new coordinate system
    sa,ca= -numpy.sin(bed_az*rad),numpy.cos(bed_az*rad) 
    cdp,sdp= numpy.cos(bed_dip*rad),numpy.sin(bed_dip*rad) 
# do the rotation
    xc=X[0]*(sa*sa+ca*ca*cdp)+X[1]*(ca*sa*(1.-cdp))+X[2]*sdp*ca
    yc=X[0]*ca*sa*(1.-cdp)+X[1]*(ca*ca+sa*sa*cdp)-X[2]*sa*sdp
    zc=X[0]*ca*sdp-X[1]*sdp*sa-X[2]*cdp
# convert back to direction:
    cart=numpy.array([xc,yc,-zc]).transpose()
    Dir=cart2dir(cart).transpose()
    return Dir[0],Dir[1] # return declination, inclination arrays of rotated direction


def dogeo(dec,inc,az,pl):
    """
    rotates dec,in into geographic coordinates using az,pl as azimuth and plunge of X direction
    """
    A1,A2,A3=[],[],[] # set up lists for rotation vector
    Dir=[dec,inc,1.] # put dec inc in direction list and set  length to unity
    X=dir2cart(Dir) # get cartesian coordinates
#
#   set up rotation matrix
#
    A1=dir2cart([az,pl,1.])
    A2=dir2cart([az+90.,0,1.])
    A3=dir2cart([az-180.,90.-pl,1.])
#
# do rotation
#
    xp=A1[0]*X[0]+A2[0]*X[1]+A3[0]*X[2]
    yp=A1[1]*X[0]+A2[1]*X[1]+A3[1]*X[2]
    zp=A1[2]*X[0]+A2[2]*X[1]+A3[2]*X[2]
#
# transform back to dec,inc
#
    Dir_geo=cart2dir([xp,yp,zp])
    return Dir_geo[0],Dir_geo[1]    # send back declination and inclination
def dogeo_V(input):
    """
    rotates dec,in into geographic coordinates using az,pl as azimuth and plunge of X direction
    handles  array for  input 
    """
    input=input.transpose() 
    dec, inc, az, pl =input[0],input[1],input[2],input[3]  # unpack input array into separate arrays
    Dir=numpy.array([dec,inc]).transpose()
    X=dir2cart(Dir).transpose() # get cartesian coordinates
    N=numpy.size(dec)
    A1=dir2cart(numpy.array([az,pl,numpy.ones(N)]).transpose()).transpose()
    A2=dir2cart(numpy.array([az+90.,numpy.zeros(N),numpy.ones(N)]).transpose()).transpose()
    A3=dir2cart(numpy.array([az-180.,90.-pl,numpy.ones(N)]).transpose()).transpose()

# do rotation
#
    xp=A1[0]*X[0]+A2[0]*X[1]+A3[0]*X[2]
    yp=A1[1]*X[0]+A2[1]*X[1]+A3[1]*X[2]
    zp=A1[2]*X[0]+A2[2]*X[1]+A3[2]*X[2]
    cart=numpy.array([xp,yp,zp]).transpose()
#
# transform back to dec,inc
#
    Dir_geo=cart2dir(cart).transpose()
    return Dir_geo[0],Dir_geo[1]    # send back declination and inclination arrays

def dodirot(D,I,Dbar,Ibar):
    d,irot=dogeo(D,I,Dbar,90.-Ibar)
    drot=d-180.
#    drot,irot=dogeo(D,I,Dbar,Ibar)
    if drot<360.:drot=drot+360.
    if drot>360.:drot=drot-360.
    return drot,irot

def find_samp_rec(s,data,az_type):
    """
    find the orientation info for samp s
    """
    datablock,or_error,bed_error=[],0,0
    orient={}
    orient["sample_dip"]=""
    orient["sample_azimuth"]=""
    orient['sample_description']=""
    for rec in data:
        if rec["er_sample_name"].lower()==s.lower():
           if 'sample_orientation_flag' in  rec.keys() and rec['sample_orientation_flag']=='b': 
               orient['sample_orientation_flag']='b'
               return orient
           if "magic_method_codes" in rec.keys() and az_type != "0":
               methods=rec["magic_method_codes"].replace(" ","").split(":")
               if az_type in methods and "sample_azimuth" in rec.keys() and rec["sample_azimuth"]!="": orient["sample_azimuth"]= float(rec["sample_azimuth"])
               if "sample_dip" in rec.keys() and rec["sample_dip"]!="": orient["sample_dip"]=float(rec["sample_dip"])
               if "sample_bed_dip_direction" in rec.keys() and rec["sample_bed_dip_direction"]!="":orient["sample_bed_dip_direction"]=float(rec["sample_bed_dip_direction"])
               if "sample_bed_dip" in rec.keys() and rec["sample_bed_dip"]!="":orient["sample_bed_dip"]=float(rec["sample_bed_dip"])
           else: 
               if "sample_azimuth" in rec.keys():orient["sample_azimuth"]=float(rec["sample_azimuth"])
               if "sample_dip" in rec.keys(): orient["sample_dip"]=float(rec["sample_dip"])
               if "sample_bed_dip_direction" in rec.keys(): orient["sample_bed_dip_direction"]=float(rec["sample_bed_dip_direction"])
               if "sample_bed_dip" in rec.keys(): orient["sample_bed_dip"]=float(rec["sample_bed_dip"])
               if 'sample_description' in rec.keys(): orient['sample_description']=rec['sample_description']
        if orient["sample_azimuth"]!="": break
    return orient

def vspec(data):
    """
    takes the vector mean of replicate measurements at a give step
    """
    vdata,Dirdata,step_meth=[],[],[]
    tr0=data[0][0] # set beginning treatment
    data.append("Stop")
    k,R=1,0
    for i in range(k,len(data)):
        Dirdata=[]
        if data[i][0] != tr0: 
            if i==k: # sample is unique
                vdata.append(data[i-1])
                step_meth.append(" ")
            else: # sample is not unique
                for l in range(k-1,i):
                    Dirdata.append([data[l][1],data[l][2],data[l][3]])
                dir,R=vector_mean(Dirdata)
                vdata.append([data[i-1][0],dir[0],dir[1],R/(i-k+1),'1','g'])
                step_meth.append("DE-VM")
            tr0=data[i][0]
            k=i+1
            if tr0=="stop":break
    del data[-1]
    return step_meth,vdata

def Vdiff(D1,D2):
    """
    finds the vector difference between two directions D1,D2
    """
    A=dir2cart([D1[0],D1[1],1.])
    B=dir2cart([D2[0],D2[1],1.])
    C=[]
    for i in range(3):
        C.append(A[i]-B[i])
    return cart2dir(C)

def angle(D1,D2):
    """
    finds the angle between lists of two directions D1,D2
    """
    D1=numpy.array(D1)
    if len(D1.shape)>1:
        D1=D1[:,0:2] # strip off intensity
    else: D1=D1[:2]
    D2=numpy.array(D2)
    if len(D2.shape)>1:
        D2=D2[:,0:2] # strip off intensity
    else: D2=D2[:2]
    X1=dir2cart(D1) # convert to cartesian from polar
    X2=dir2cart(D2)
    angles=[] # set up a list for angles
    for k in range(X1.shape[0]): # single vector
        angle= numpy.arccos(numpy.dot(X1[k],X2[k]))*180./numpy.pi # take the dot product
        angle=angle%360.
        angles.append(angle)
    return numpy.array(angles)

def cart2dir(cart):
    """
    converts a direction to cartesian coordinates
    """
    cart=numpy.array(cart)
    rad=numpy.pi/180. # constant to convert degrees to radians
    if len(cart.shape)>1:
        Xs,Ys,Zs=cart[:,0],cart[:,1],cart[:,2]
    else: #single vector
        Xs,Ys,Zs=cart[0],cart[1],cart[2]
    Rs=numpy.sqrt(Xs**2+Ys**2+Zs**2) # calculate resultant vector length
    Decs=(numpy.arctan2(Ys,Xs)/rad)%360. # calculate declination taking care of correct quadrants (arctan2) and making modulo 360.
    try:
        Incs=numpy.arcsin(Zs/Rs)/rad # calculate inclination (converting to degrees) # 
    except:
        print 'trouble in cart2dir' # most likely division by zero somewhere
        return numpy.zeros(3)
        
    return numpy.array([Decs,Incs,Rs]).transpose() # return the directions list

#def cart2dir(cart): # OLD ONE
#    """
#    converts a direction to cartesian coordinates
#    """
#    Dir=[] # establish a list to put directions in
#    rad=numpy.pi/180. # constant to convert degrees to radians
#    R=numpy.sqrt(cart[0]**2+cart[1]**2+cart[2]**2) # calculate resultant vector length
#    if R==0:
#       print 'trouble in cart2dir'
#       print cart
#       return [0.0,0.0,0.0]
#    D=numpy.arctan2(cart[1],cart[0])/rad  # calculate declination taking care of correct quadrants (arctan2)
#    if D<0:D=D+360. # put declination between 0 and 360.
#    if D>360.:D=D-360.
#    Dir.append(D)  # append declination to Dir list
#    I=numpy.arcsin(cart[2]/R)/rad # calculate inclination (converting to degrees)
#    Dir.append(I) # append inclination to Dir list
#    Dir.append(R) # append vector length to Dir list
#    return Dir # return the directions list
#
def tauV(T):
    """
    gets the eigenvalues (tau) and eigenvectors (V) from matrix T
    """
    t,V,tr=[],[],0.
    ind1,ind2,ind3=0,1,2
    evalues,evectmps=numpy.linalg.eig(T)
    evectors=numpy.transpose(evectmps)  # to make compatible with Numeric convention
    for tau in evalues:
        tr+=tau
    if tr!=0:
        for i in range(3):
            evalues[i]=evalues[i]/tr
    else:
        return t,V
# sort evalues,evectors
    t1,t2,t3=0.,0.,1.
    for k in range(3):
        if evalues[k] > t1: 
            t1,ind1=evalues[k],k 
        if evalues[k] < t3: 
            t3,ind3=evalues[k],k 
    for k in range(3):
        if evalues[k] != t1 and evalues[k] != t3: 
            t2,ind2=evalues[k],k
    V.append(evectors[ind1])
    V.append(evectors[ind2])
    V.append(evectors[ind3])
    t.append(t1)
    t.append(t2)
    t.append(t3)
    return t,V

def Tmatrix(X):
    """
    gets the orientation matrix (T) from data in X
    """
    T=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    for row in X:
        for k in range(3):
            for l in range(3):
                T[k][l] += row[k]*row[l]
    return T


def dir2cart(d):
   # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
    ints=numpy.ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
    d=numpy.array(d)
    rad=numpy.pi/180.
    if len(d.shape)>1: # array of vectors
        decs,incs=d[:,0]*rad,d[:,1]*rad
        if d.shape[1]==3: ints=d[:,2] # take the given lengths
    else: # single vector
        decs,incs=numpy.array(d[0])*rad,numpy.array(d[1])*rad
        if len(d)==3: 
            ints=numpy.array(d[2])
        else:
            ints=numpy.array([1.])
    cart= numpy.array([ints*numpy.cos(decs)*numpy.cos(incs),ints*numpy.sin(decs)*numpy.cos(incs),ints*numpy.sin(incs)]).transpose()
    return cart


def dms2dd(d):
   # converts list or array of degree, minute, second locations to array of decimal degrees 
    d=numpy.array(d)
    if len(d.shape)>1: # array of angles
        degs,mins,secs=d[:,0],d[:,1],d[:,2]
        print degs,mins,secs
    else: # single vector
        degs,mins,secs=numpy.array(d[0]),numpy.array(d[1]),numpy.array(d[2])
        print degs,mins,secs
    dd= numpy.array(degs+mins/60.+secs/3600.).transpose()
    return dd

def findrec(s,data):
    """
    finds all the records belonging to s in data
    """
    datablock=[]
    for rec in data:
       if s==rec[0]:
           datablock.append([rec[1],rec[2],rec[3],rec[4]])
    return datablock

def domean(indata,start,end,calculation_type):
    """
     gets average direction using fisher or pca (line or plane) methods
    """
    mpars={}
    datablock=[]
    ind=0
    start0,end0=start,end
    for rec in indata:
        if len(rec)<6:rec.append('g')
        if rec[5]=='b' and ind==start: 
            mpars["specimen_direction_type"]="Error"
            print "Can't select 'bad' point as start for PCA"
            return mpars 
        if rec[5]=='b' and ind<start: 
            start-=1
            end-=1
        if rec[5]=='b' and ind>start and ind<end: 
            end-=1
        if rec[5]=='b' and ind>start and ind==end: 
            end-=1
        if rec[5]=='g':
            datablock.append(rec) # use only good data
 #       else:
 #           end-=1
        ind+=1
    mpars["calculation_type"]=calculation_type
    rad=numpy.pi/180.
    if end>len(datablock)-1 or end<start : end=len(datablock)-1
    control,data,X,Nrec=[],[],[],float(end-start+1)
    cm=[0.,0.,0.]
#
#  get cartesian coordinates
#
    fdata=[]
    for k in range(start,end+1):
        if calculation_type == 'DE-BFL' or calculation_type=='DE-BFL-A' or calculation_type=='DE-BFL-O' :  # best-fit line
            data=[datablock[k][1],datablock[k][2],datablock[k][3]]
        else: 
            data=[datablock[k][1],datablock[k][2],1.0] # unit weight
        fdata.append(data)
        cart= dir2cart(data)
        X.append(cart)
    if calculation_type=='DE-BFL-O': # include origin as point
        X.append([0.,0.,0.])
        #pass
    if calculation_type=='DE-FM': # for fisher means
        fpars=fisher_mean(fdata)    
        mpars["specimen_direction_type"]='l'
        mpars["specimen_dec"]=fpars["dec"]
        mpars["specimen_inc"]=fpars["inc"]
        mpars["specimen_alpha95"]=fpars["alpha95"]
        mpars["specimen_n"]=fpars["n"]
        mpars["specimen_r"]=fpars["r"]
        mpars["measurement_step_min"]=indata[start0][0]
        mpars["measurement_step_max"]=indata[end0][0]
        mpars["center_of_mass"]=cm
        mpars["specimen_dang"]=-1
        return mpars
#
#	get center of mass for principal components (DE-BFL or DE-BFP)
#
    for cart in X:
        for l in range(3):
            cm[l]+=cart[l]/Nrec
    mpars["center_of_mass"]=cm

#
#   transform to center of mass (if best-fit line)
#
    if calculation_type!='DE-BFP': mpars["specimen_direction_type"]='l'
    if calculation_type=='DE-BFL' or calculation_type=='DE-BFL-O': # not for planes or anchored lines
        for k in range(len(X)):
            for l in range(3):
               X[k][l]=X[k][l]-cm[l]
    else:
        mpars["specimen_direction_type"]='p'
#
#   put in T matrix
#
    T=numpy.array(Tmatrix(X))
#
#   get sorted evals/evects
#
    t,V=tauV(T)
    if t[2]<0:t[2]=0 # make positive
    if t==[]:
        mpars["specimen_direction_type"]="Error"
        print "Error in calculation"
        return mpars 
    v1,v3=V[0],V[2]
    if calculation_type=='DE-BFL-A':
        Dir,R=vector_mean(fdata) 
        mpars["specimen_direction_type"]='l'
        mpars["specimen_dec"]=Dir[0]
        mpars["specimen_inc"]=Dir[1]
        mpars["specimen_n"]=len(fdata)
        mpars["measurement_step_min"]=indata[start0][0]
        mpars["measurement_step_max"]=indata[end0][0]
        mpars["center_of_mass"]=cm
        s1=numpy.sqrt(t[0])
        MAD=numpy.arctan(numpy.sqrt(t[1]+t[2])/s1)/rad
        mpars["specimen_mad"]=MAD # I think this is how it is done - i never anchor the "PCA" - check
        return mpars
    if calculation_type!='DE-BFP':
#
#   get control vector for principal component direction
#
        rec=[datablock[start][1],datablock[start][2],datablock[start][3]]
        P1=dir2cart(rec)
        rec=[datablock[end][1],datablock[end][2],datablock[end][3]]
        P2=dir2cart(rec)
#
#   get right direction along principal component
##
        for k in range(3):
            control.append(P1[k]-P2[k])
        # changed by rshaar
        # control is taken as the center of mass
        #control=cm

        
        dot = 0
        for k in range(3):
            dot += v1[k]*control[k]
        if dot<-1:dot=-1
        if dot>1:dot=1
        if numpy.arccos(dot) > numpy.pi/2.:
            for k in range(3):
                v1[k]=-v1[k]
#   get right direction along principal component
#
        s1=numpy.sqrt(t[0])
        Dir=cart2dir(v1)
        MAD=numpy.arctan(numpy.sqrt(t[1]+t[2])/s1)/rad
    if calculation_type=="DE-BFP":
        Dir=cart2dir(v3)
        MAD=numpy.arctan(numpy.sqrt(t[2]/t[1]+t[2]/t[0]))/rad
#
#  	get angle with  center of mass
#
    CMdir=cart2dir(cm)
    Dirp=[Dir[0],Dir[1],1.]
    dang=angle(CMdir,Dirp)
    mpars["specimen_dec"]=Dir[0]
    mpars["specimen_inc"]=Dir[1]
    mpars["specimen_mad"]=MAD
    #mpars["specimen_n"]=int(Nrec)
    mpars["specimen_n"]=len(X)
    mpars["specimen_dang"]=dang[0]
    mpars["measurement_step_min"]=indata[start0][0]
    mpars["measurement_step_max"]=indata[end0][0]
    return mpars

def circ(dec,dip,alpha):
    """
    function to calculate points on an circle about dec,dip with angle alpha
    """
    rad=numpy.pi/180.
    D_out,I_out=[],[]
    dec,dip,alpha=dec*rad ,dip*rad,alpha*rad
    dec1=dec+numpy.pi/2.
    isign=1
    if dip!=0: isign=(abs(dip)/dip)
    dip1=(dip-isign*(numpy.pi/2.))
    t=[[0,0,0],[0,0,0],[0,0,0]]
    v=[0,0,0]
    t[0][2]=numpy.cos(dec)*numpy.cos(dip)
    t[1][2]=numpy.sin(dec)*numpy.cos(dip)
    t[2][2]=numpy.sin(dip)
    t[0][1]=numpy.cos(dec)*numpy.cos(dip1)
    t[1][1]=numpy.sin(dec)*numpy.cos(dip1)
    t[2][1]=numpy.sin(dip1)
    t[0][0]=numpy.cos(dec1)
    t[1][0]=numpy.sin(dec1)
    t[2][0]=0   
    for i in range(101): 
        psi=float(i)*numpy.pi/50. 
        v[0]=numpy.sin(alpha)*numpy.cos(psi) 
        v[1]=numpy.sin(alpha)*numpy.sin(psi) 
        v[2]=numpy.sqrt(abs(1.-v[0]**2 - v[1]**2))
        elli=[0,0,0]
        for j in range(3):
            for k in range(3):
                elli[j]=elli[j] + t[j][k]*v[k] 
        Dir=cart2dir(elli)
        D_out.append(Dir[0])
        I_out.append(Dir[1])
    return D_out,I_out


def PintPars(datablock,araiblock,zijdblock,start,end,accept):
    """
     calculate the paleointensity magic parameters  make some definitions
    """
    methcode,ThetaChecks,DeltaChecks,GammaChecks="","","",""
    zptrm_check=[]
    first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks=araiblock[0],araiblock[1],araiblock[2],araiblock[3],araiblock[4],araiblock[5]  
    if len(araiblock)>6: 
        ThetaChecks=araiblock[6] # used only for perpendicular method of paleointensity
        DeltaChecks=araiblock[7] # used only for perpendicular  method of paleointensity
    xi,yi,diffcum=[],[],0
    xiz,xzi,yiz,yzi=[],[],[],[]
    Nptrm,dmax=0,-1e-22
# check if even zero and infield steps
    if len(first_Z)>len(first_I): 
        maxe=len(first_I)-1
    else: maxe=len(first_Z)-1
    if end==0 or end > maxe:
        end=maxe
# get the MAD, DANG, etc. for directional data
    bstep=araiblock[0][start][0]
    estep=araiblock[0][end][0]
    zstart,zend=0,len(zijdblock)
    for k in range(len(zijdblock)): 
        zrec=zijdblock[k]
        if zrec[0]==bstep:zstart=k
        if zrec[0]==estep:zend=k
    PCA=domean(zijdblock,zstart,zend,'DE-BFL')  
    D,Diz,Dzi,Du=[],[],[],[]  # list of NRM vectors, and separated by zi and iz
    for rec in zijdblock:
        D.append((rec[1],rec[2],rec[3])) 
        Du.append((rec[1],rec[2])) 
        if rec[4]==1:
            Dzi.append((rec[1],rec[2]))  # if this is ZI step
        else:
            Diz.append((rec[1],rec[2]))  # if this is IZ step
# calculate the vector difference sum
    vds=dovds(D)
    b_zi,b_iz=[],[]
# collect data included in ZigZag calculation
    if end+1>=len(first_Z):
        stop=end-1
    else:
        stop=end
    for k in range(start,end+1):
       for l in range(len(first_I)):
           irec=first_I[l]
           if irec[0]==first_Z[k][0]: 
               xi.append(irec[3])
               yi.append(first_Z[k][3])
    pars,errcode=int_pars(xi,yi,vds) 
    if errcode==1:return pars,errcode
#    for k in range(start,end+1):
    for k in range(len(first_Z)-1):
        for l in range(k):
            if first_Z[k][3]/vds>0.1:   # only go down to 10% of NRM.....
               irec=first_I[l]
               if irec[4]==1 and first_I[l+1][4]==0: # a ZI step
                   xzi=irec[3]
                   yzi=first_Z[k][3]
                   xiz=first_I[l+1][3]
                   yiz=first_Z[k+1][3]
                   slope=numpy.arctan2((yzi-yiz),(xiz-xzi))
                   r=numpy.sqrt( (yzi-yiz)**2+(xiz-xzi)**2)
                   if r>.1*vds:b_zi.append(slope) # suppress noise
               elif irec[4]==0 and first_I[l+1][4]==1: # an IZ step
                   xiz=irec[3]
                   yiz=first_Z[k][3]
                   xzi=first_I[l+1][3]
                   yzi=first_Z[k+1][3]
                   slope=numpy.arctan2((yiz-yzi),(xzi-xiz))
                   r=numpy.sqrt( (yiz-yzi)**2+(xzi-xiz)**2)
                   if r>.1*vds:b_iz.append(slope) # suppress noise
#
    ZigZag,Frat,Trat=-1,0,0
    if len(Diz)>2 and len(Dzi)>2:
        ZigZag=0
        dizp=fisher_mean(Diz) # get Fisher stats on IZ steps
        dzip=fisher_mean(Dzi) # get Fisher stats on ZI steps
        dup=fisher_mean(Du) # get Fisher stats on all steps
#
# if directions are TOO well grouped, can get false positive for ftest, so
# angles must be > 3 degrees apart.
#
        if angle([dizp['dec'],dizp['inc']],[dzip['dec'],dzip['inc']])>3.: 
            F=(dup['n']-2.)* (dzip['r']+dizp['r']-dup['r'])/(dup['n']-dzip['r']-dizp['r']) # Watson test for common mean
            nf=2.*(dup['n']-2.) # number of degees of freedom
            ftest=fcalc(2,nf)
            Frat=F/ftest
            if Frat>1.:
                ZigZag=Frat # fails zigzag on directions
                methcode="SM-FTEST"
# now do slopes 
    if len(b_zi)>2 and len(b_iz)>2:
        bzi_m,bzi_sig=gausspars(b_zi)  # mean, std dev
        biz_m,biz_sig=gausspars(b_iz) 
        n_zi=float(len(b_zi))
        n_iz=float(len(b_iz))
        b_diff=abs(bzi_m-biz_m) # difference in means
#
# avoid false positives - set 3 degree slope difference here too
        if b_diff>3*numpy.pi/180.:
            nf=n_zi+n_iz-2.  # degrees of freedom
            svar= ((n_zi-1.)*bzi_sig**2 + (n_iz-1.)*biz_sig**2)/nf
            T=(b_diff)/numpy.sqrt(svar*(1.0/n_zi + 1.0/n_iz)) # student's t
            ttest=tcalc(nf,.05) # t-test at 95% conf.
            Trat=T/ttest
            if Trat>1  and Trat>Frat:
                ZigZag=Trat # fails zigzag on directions
                methcode="SM-TTEST"
    pars["specimen_Z"]=ZigZag 
    pars["method_codes"]=methcode
# do drats
    if len(ptrm_check) != 0:
        diffcum,drat_max=0,0
        for prec in ptrm_check:
            step=prec[0]
            endbak=end
            zend=end
            while zend>len(zijdblock)-1:
               zend=zend-2  # don't count alteration that happens after this step
            if step <zijdblock[zend][0]:
                Nptrm+=1
                for irec in first_I:
                    if irec[0]==step:break
                diffcum+=prec[3]-irec[3]
                if abs(prec[3]-irec[3])>drat_max:drat_max=abs(prec[3]-irec[3])
        pars["specimen_drats"]=(100*abs(diffcum)/first_I[zend][3])
        pars["specimen_drat"]=(100*abs(drat_max)/first_I[zend][3])
    elif len(zptrm_check) != 0:
        diffcum=0
        for prec in zptrm_check:
            step=prec[0]
            endbak=end
            zend=end
            while zend>len(zijdblock)-1:
               zend=zend-1
            if step <zijdblock[zend][0]:
                Nptrm+=1
                for irec in first_I:
                    if irec[0]==step:break
                diffcum+=prec[3]-irec[3]
        pars["specimen_drats"]=(100*abs(diffcum)/first_I[zend][3])
    else: 
        pars["specimen_drats"]=-1
        pars["specimen_drat"]=-1
# and the pTRM tails
    if len(ptrm_tail) != 0:
        for trec in ptrm_tail:
            step=trec[0]
            for irec in first_I:
                if irec[0]==step:break
            if abs(trec[3]) >dmax:dmax=abs(trec[3])
        pars["specimen_md"]=(100*dmax/vds)
    else: pars["specimen_md"]=-1
    pars["measurement_step_min"]=bstep
    pars["measurement_step_max"]=estep
    pars["specimen_dec"]=PCA["specimen_dec"]
    pars["specimen_inc"]=PCA["specimen_inc"]
    pars["specimen_int_mad"]=PCA["specimen_mad"]
    pars["specimen_int_dang"]=PCA["specimen_dang"]
    #pars["specimen_int_ptrm_n"]=len(ptrm_check) # this is WRONG!
    pars["specimen_int_ptrm_n"]=Nptrm
# and the ThetaChecks
    if ThetaChecks!="":
        t=0
        for theta in ThetaChecks:
            if theta[0]>=bstep and theta[0]<=estep and theta[1]>t:t=theta[1]
        pars['specimen_theta']=t
    else:
        pars['specimen_theta']=-1
# and the DeltaChecks
    if DeltaChecks!="":
        d=0
        for delta in DeltaChecks:
            if delta[0]>=bstep and delta[0]<=estep and delta[1]>d:d=delta[1]
        pars['specimen_delta']=d
    else:
        pars['specimen_delta']=-1
    pars['specimen_gamma']=-1
    if GammaChecks!="":
        for gamma in GammaChecks:
            if gamma[0]<=estep: pars['specimen_gamma']=gamma[1]


    #--------------------------------------------------------------
    # From here added By Ron Shaar 11-Dec 2012
    # New parameters defined in Shaar and Tauxe (2012):
    # FRAC (specimen_frac) - ranges from 0. to 1.
    # SCAT (specimen_scat) - takes 1/0
    # gap_max (specimen_gmax) - ranges from 0. to 1.
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # FRAC is similar to Fvds, but the numerator is the vds fraction:
    # FRAC= [ vds (start,end)] / total vds ]
    # gap_max= max [ (vector difference) /  vds (start,end)]
    #--------------------------------------------------------------

    # collect all zijderveld data to arrays and calculate VDS
    
    z_temperatures=[row[0] for row in zijdblock]
    zdata=[]                # array of zero-fields measurements in Cartezian coordinates
    vector_diffs=[]         # array of vector differences (for vds calculation)
    NRM=zijdblock[0][3]     # NRM

    for k in range(len(zijdblock)):
        DIR=[zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
        cart=dir2cart(DIR)
        zdata.append(array([cart[0],cart[1],cart[2]]))
        if k>0:
            vector_diffs.append(sqrt(sum((array(zdata[-2])-array(zdata[-1]))**2)))
    vector_diffs.append(sqrt(sum(array(zdata[-1])**2))) # last vector differnce: from the last point to the origin.
    vds=sum(vector_diffs)  # vds calculation       
    zdata=array(zdata)
    vector_diffs=array(vector_diffs)

    # calculate the vds within the chosen segment 
    vector_diffs_segment=vector_diffs[zstart:zend]
    # FRAC calculation
    FRAC=sum(vector_diffs_segment)/vds
    pars['specimen_frac']=FRAC

    # gap_max calculation
    max_FRAC_gap=max(vector_diffs_segment/sum(vector_diffs_segment))
    pars['specimen_gmax']=max_FRAC_gap
    

    #---------------------------------------------------------------------                     
    # Calculate the "scat box"
    # all data-points, pTRM checks, and tail-checks, should be inside a "scat box"
    #---------------------------------------------------------------------                     

    # intialization
    pars["fail_arai_beta_box_scatter"]=False # fail scat due to arai plot data points
    pars["fail_ptrm_beta_box_scatter"]=False # fail scat due to pTRM checks
    pars["fail_tail_beta_box_scatter"]=False # fail scat due to tail checks
    pars["specimen_scat"]="1" # Pass by default

    #--------------------------------------------------------------
    # collect all Arai plot data points in arrays 

    x_Arai,y_Arai,t_Arai,steps_Arai=[],[],[],[]           
    NRMs=araiblock[0]
    PTRMs=araiblock[1]
    ptrm_checks = araiblock[2]
    ptrm_tail = araiblock[3]
    
    PTRMs_temperatures=[row[0] for row in PTRMs]
    NRMs_temperatures=[row[0] for row in NRMs]
    NRM=NRMs[0][3]    

    for k in range(len(NRMs)):                  
      index_pTRMs=PTRMs_temperatures.index(NRMs[k][0])
      x_Arai.append(PTRMs[index_pTRMs][3]/NRM)
      y_Arai.append(NRMs[k][3]/NRM)
      t_Arai.append(NRMs[k][0])
      if NRMs[k][4]==1:
        steps_Arai.append('ZI')
      else:
        steps_Arai.append('IZ')        
    x_Arai=array(x_Arai)
    y_Arai=array(y_Arai)

    #--------------------------------------------------------------
    # collect all pTRM check to arrays 

    x_ptrm_check,y_ptrm_check,ptrm_checks_temperatures,=[],[],[]
    x_ptrm_check_starting_point,y_ptrm_check_starting_point,ptrm_checks_starting_temperatures=[],[],[]
    
    for k in range(len(ptrm_checks)):
      if ptrm_checks[k][0] in NRMs_temperatures:
        # find the starting point of the pTRM check:
        for i in range(len(datablock)):
            rec=datablock[i]                
            if "LT-PTRM-I" in rec['magic_method_codes'] and float(rec['treatment_temp'])==ptrm_checks[k][0]:
                starting_temperature=(float(datablock[i-1]['treatment_temp']))
                try:
                    index=t_Arai.index(starting_temperature)
                    x_ptrm_check_starting_point.append(x_Arai[index])
                    y_ptrm_check_starting_point.append(y_Arai[index])
                    ptrm_checks_starting_temperatures.append(starting_temperature)

                    index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
                    x_ptrm_check.append(ptrm_checks[k][3]/NRM)
                    y_ptrm_check.append(zerofields[index_zerofield][3]/NRM)
                    ptrm_checks_temperatures.append(ptrm_checks[k][0])

                    break
                except:
                    pass

    x_ptrm_check_starting_point=array(x_ptrm_check_starting_point)
    y_ptrm_check_starting_point=array(y_ptrm_check_starting_point)
    ptrm_checks_starting_temperatures=array(ptrm_checks_starting_temperatures)
    x_ptrm_check=array(x_ptrm_check)
    y_ptrm_check=array(y_ptrm_check)
    ptrm_checks_temperatures=array(ptrm_checks_temperatures)
    
    #--------------------------------------------------------------
    # collect tail checks to arrays

    x_tail_check,y_tail_check,tail_check_temperatures=[],[],[]
    x_tail_check_starting_point,y_tail_check_starting_point,tail_checks_starting_temperatures=[],[],[]

    for k in range(len(ptrm_tail)):
      if ptrm_tail[k][0] in NRMs_temperatures:

        # find the starting point of the pTRM check:
        for i in range(len(datablock)):
            rec=datablock[i]                
            if "LT-PTRM-MD" in rec['magic_method_codes'] and float(rec['treatment_temp'])==ptrm_tail[k][0]:
                starting_temperature=(float(datablock[i-1]['treatment_temp']))
                try:

                    index=t_Arai.index(starting_temperature)
                    x_tail_check_starting_point.append(x_Arai[index])
                    y_tail_check_starting_point.append(y_Arai[index])
                    tail_checks_starting_temperatures.append(starting_temperature)

                    index_infield=infield_temperatures.index(ptrm_tail[k][0])
                    x_tail_check.append(infields[index_infield][3]/NRM)
                    y_tail_check.append(ptrm_tail[k][3]/NRM + zerofields[index_infield][3]/NRM)
                    tail_check_temperatures.append(ptrm_tail[k][0])

                    break
                except:
                    pass

    x_tail_check=array(x_tail_check)  
    y_tail_check=array(y_tail_check)
    tail_check_temperatures=array(tail_check_temperatures)
    x_tail_check_starting_point=array(x_tail_check_starting_point)
    y_tail_check_starting_point=array(y_tail_check_starting_point)
    tail_checks_starting_temperatures=array(tail_checks_starting_temperatures)

            
    #--------------------------------------------------------------
    # collect the chosen segment in the Arai plot to arraya

    x_Arai_segment= x_Arai[start:end+1] # chosen segent in the Arai plot
    y_Arai_segment= y_Arai[start:end+1] # chosen segent in the Arai plot

    #--------------------------------------------------------------
    # collect pTRM checks in segment to arrays
    # notice, this is different than the conventional DRATS.
    # for scat calculation we take only the pTRM checks which were carried out
    # before reaching the highest temperature in the chosen segment  

    x_ptrm_check_for_SCAT,y_ptrm_check_for_SCAT=[],[]
    for k in range(len(ptrm_checks_temperatures)):
      if ptrm_checks_temperatures[k] >= pars["measurement_step_min"] and ptrm_checks_starting_temperatures <= pars["measurement_step_max"] :
            x_ptrm_check_for_SCAT.append(x_ptrm_check[k])
            y_ptrm_check_for_SCAT.append(y_ptrm_check[k])

    x_ptrm_check_for_SCAT=array(x_ptrm_check_for_SCAT)
    y_ptrm_check_for_SCAT=array(y_ptrm_check_for_SCAT)
    
    #--------------------------------------------------------------
    # collect Tail checks in segment to arrays
    # for scat calculation we take only the tail checks which were carried out
    # before reaching the highest temperature in the chosen segment  

    x_tail_check_for_SCAT,y_tail_check_for_SCAT=[],[]

    for k in range(len(tail_check_temperatures)):
      if tail_check_temperatures[k] >= pars["measurement_step_min"] and tail_checks_starting_temperatures[k] <= pars["measurement_step_max"] :
            x_tail_check_for_SCAT.append(x_tail_check[k])
            y_tail_check_for_SCAT.append(y_tail_check[k])

            
    x_tail_check_for_SCAT=array(x_tail_check_for_SCAT)
    y_tail_check_for_SCAT=array(y_tail_check_for_SCAT)
    
    #--------------------------------------------------------------
    # calculate the lines that define the scat box:            

    # if threshold value for beta is not defined, then scat cannot be calculated (pass)
    # in this case, scat pass
    if 'specimen_b_beta' in accept.keys() and accept['specimen_b_beta']!="": 
        b_beta_threshold=float(accept['specimen_b_beta'])
        b=pars['specimen_b']             # best fit line
        cm_x=mean(array(x_Arai_segment)) # x center of mass
        cm_y=mean(array(y_Arai_segment)) # y center of mass
        a=cm_y-b*cm_x                   

        # lines with slope = slope +/- 2*(specimen_b_beta)

        two_sigma_beta_threshold=2*b_beta_threshold
        two_sigma_slope_threshold=abs(two_sigma_beta_threshold*b)
             
        # a line with a  shallower  slope  (b + 2*beta*b) passing through the center of mass
        # y=a1+b1x
        b1=b+two_sigma_slope_threshold
        a1=cm_y-b1*cm_x

        # bounding line with steeper  slope (b - 2*beta*b) passing through the center of mass
        # y=a2+b2x
        b2=b-two_sigma_slope_threshold
        a2=cm_y-b2*cm_x

        # lower bounding line of the 'beta box'
        # y=intercept1+slop1x
        slop1=a1/((a2/b2))
        intercept1=a1

        # higher bounding line of the 'beta box'
        # y=intercept2+slop2x

        slop2=a2/((a1/b1))
        intercept2=a2       

        pars['specimen_scat_bounding_line_high']=[intercept2,slop2]
        pars['specimen_scat_bounding_line_low']=[intercept1,slop1]

        #--------------------------------------------------------------
        # check if the Arai data points are in the 'box'

        # the two bounding lines
        ymin=intercept1+x_Arai_segment*slop1
        ymax=intercept2+x_Arai_segment*slop2

        # arrays of "True" or "False"
        check_1=y_Arai_segment>ymax
        check_2=y_Arai_segment<ymin

        # check if at least one "True" 
        if (sum(check_1)+sum(check_2))>0:
         pars["fail_arai_beta_box_scatter"]=True

        #--------------------------------------------------------------
        # check if the pTRM checks data points are in the 'box'

        if len(x_ptrm_check_for_SCAT) > 0:

          # the two bounding lines
          ymin=intercept1+x_ptrm_check_for_SCAT*slop1
          ymax=intercept2+x_ptrm_check_for_SCAT*slop2

          # arrays of "True" or "False"
          check_1=y_ptrm_check_for_SCAT>ymax
          check_2=y_ptrm_check_for_SCAT<ymin


          # check if at least one "True" 
          if (sum(check_1)+sum(check_2))>0:
            pars["fail_ptrm_beta_box_scatter"]=True
            
        #--------------------------------------------------------------    
        # check if the tail checks data points are in the 'box'


        if len(x_tail_check_for_SCAT) > 0:

          # the two bounding lines
          ymin=intercept1+x_tail_check_for_SCAT*slop1
          ymax=intercept2+x_tail_check_for_SCAT*slop2

          # arrays of "True" or "False"
          check_1=y_tail_check_for_SCAT>ymax
          check_2=y_tail_check_for_SCAT<ymin


          # check if at least one "True" 
          if (sum(check_1)+sum(check_2))>0:
            pars["fail_tail_beta_box_scatter"]=True

        #--------------------------------------------------------------    
        # check if specimen_scat is PASS or FAIL:   

        if pars["fail_tail_beta_box_scatter"] or pars["fail_ptrm_beta_box_scatter"] or pars["fail_arai_beta_box_scatter"]:
              pars["specimen_scat"]='0'
        else:
              pars["specimen_scat"]='1'
                
    return pars,0

def getkeys(table):
    """
    customize by commenting out unwanted keys
    """
    keys=[]
    if table=="ER_expedition": 
        pass 
    if table=="ER_citations":
        keys.append("er_citation_name")
        keys.append("long_authors")
        keys.append("year")
        keys.append("title")
        keys.append("citation_type")
        keys.append("doi")
        keys.append("journal")
        keys.append("volume")
        keys.append("pages")
        keys.append("book_title")
        keys.append("book_editors")
        keys.append("publisher")
        keys.append("city")
    if table=="ER_locations":
        keys.append("er_location_name")
        keys.append("er_scientist_mail_names" )
#        keys.append("er_location_alternatives" )
        keys.append("location_type" )
        keys.append("location_begin_lat")
        keys.append("location_begin_lon" )
#        keys.append("location_begin_elevation" )
        keys.append("location_end_lat" )
        keys.append("location_end_lon" )
#        keys.append("location_end_elevation" )
        keys.append("continent_ocean" )
        keys.append("country" )
        keys.append("region" )
        keys.append("plate_block" )
        keys.append("terrane" )
        keys.append("tectonic_setting" )
#        keys.append("er_citation_names")
    if table=="ER_Formations":
        keys.append("er_formation_name")
        keys.append("formation_class")
        keys.append("formation_lithology")
        keys.append("formation_paleo_environment")
        keys.append("formation_thickness")
        keys.append("formation_description")
    if table=="ER_sections":
        keys.append("er_section_name")
        keys.append("er_section_alternatives")
        keys.append("er_expedition_name")
        keys.append("er_location_name")
        keys.append("er_formation_name")
        keys.append("er_member_name")
        keys.append("section_definition")
        keys.append("section_class")
        keys.append("section_lithology")
        keys.append("section_type")
        keys.append("section_n")
        keys.append("section_begin_lat")
        keys.append("section_begin_lon")
        keys.append("section_begin_elevation")
        keys.append("section_begin_height")
        keys.append("section_begin_drill_depth")
        keys.append("section_begin_composite_depth")
        keys.append("section_end_lat")
        keys.append("section_end_lon")
        keys.append("section_end_elevation")
        keys.append("section_end_height")
        keys.append("section_end_drill_depth")
        keys.append("section_end_composite_depth")
        keys.append("section_azimuth")
        keys.append("section_dip")
        keys.append("section_description")
        keys.append("er_scientist_mail_names")
        keys.append("er_citation_names")
    if table=="ER_sites":
        keys.append("er_location_name")
        keys.append("er_site_name")
#        keys.append("er_site_alternatives")
#        keys.append("er_formation_name")
#        keys.append("er_member_name")
#        keys.append("er_section_name")
        keys.append("er_scientist_mail_names")
        keys.append("site_class")
#        keys.append("site_type")
#        keys.append("site_lithology")
#        keys.append("site_height")
#        keys.append("site_drill_depth")
#        keys.append("site_composite_depth")
#        keys.append("site_lithology")
#        keys.append("site_description")
        keys.append("site_lat")
        keys.append("site_lon")
#        keys.append("site_location_precision")
#        keys.append("site_elevation")
    if table == "ER_samples" :
        keys.append("er_location_name")
        keys.append("er_site_name")
#       keys.append("er_sample_alternatives")
        keys.append("sample_azimuth")
        keys.append("sample_dip")
        keys.append("sample_bed_dip")
        keys.append("sample_bed_dip_direction")
#       keys.append("sample_cooling_rate")
#       keys.append("sample_type")
#       keys.append("sample_lat")
#       keys.append("sample_lon")
        keys.append("magic_method_codes")
    if table == "ER_ages" :
#       keys.append("er_location_name")
#       keys.append("er_site_name")
#       keys.append("er_section_name")
#       keys.append("er_formation_name")
#       keys.append("er_member_name")
#       keys.append("er_site_name")
#       keys.append("er_sample_name")
#       keys.append("er_specimen_name")
#       keys.append("er_fossil_name")
#       keys.append("er_mineral_name")
#       keys.append("tiepoint_name")
        keys.append("age")
        keys.append("age_sigma")
        keys.append("age_unit")
        keys.append("age_range_low")
        keys.append("age_range_hi")
        keys.append("timescale_eon")
        keys.append("timescale_era")
        keys.append("timescale_period")
        keys.append("timescale_epoch")
        keys.append("timescale_stage")
        keys.append("biostrat_zone")
        keys.append("conodont_zone")
        keys.append("magnetic_reversal_chron")
        keys.append("astronomical_stage")
#       keys.append("age_description")
#       keys.append("magic_method_codes")
#       keys.append("er_timescale_citation_names")
#       keys.append("er_citation_names")
    if table == "MAGIC_measurements" :
        keys.append("er_location_name")
        keys.append("er_site_name")
        keys.append("er_sample_name")
        keys.append("er_specimen_name")
        keys.append("measurement_positions")
        keys.append("treatment_temp")
        keys.append("treatment_ac_field")
        keys.append("treatment_dc_field")
        keys.append("treatment_dc_field_phi")
        keys.append("treatment_dc_field_theta")
        keys.append("magic_experiment_name")
        keys.append("magic_instrument_codes")
        keys.append("measurement_temp")
        keys.append("magic_method_codes")
        keys.append("measurement_inc")
        keys.append("measurement_dec")
        keys.append("measurement_magn_moment")
        keys.append("measurement_csd")
    return  keys


def getnames():
    """
    get mail names
    """
    namestring=""
    addmore=1
    while addmore:
        scientist=raw_input("Enter  name  - <Return> when done ")
        if scientist != "":
            namestring=namestring+":"+scientist
        else:
            namestring=namestring[1:]
            addmore=0
    return namestring

def magic_help(keyhelp):
    """
    returns a help message for a give magic key
    """
    helpme={}
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_location_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["location_type"]=	"Location type"
    helpme["location_begin_lat"]=	"Begin of section or core or outcrop -- latitude"
    helpme["location_begin_lon"]=	"Begin of section or core or outcrop -- longitude"
    helpme["location_begin_elevation"]=	"Begin of section or core or outcrop -- elevation relative to sealevel"
    helpme["location_end_lat"]=	"Ending of section or core -- latitude "
    helpme["location_end_lon"]=	"Ending of section or core -- longitude "
    helpme["location_end_elevation"]=	"Ending of section or core -- elevation relative to sealevel"
    helpme["location_geoid"]=	"Geoid used in determination of latitude and longitude:  WGS84, GEOID03, USGG2003, GEOID99, G99SSS , G99BM, DEFLEC99 "
    helpme["continent_ocean"]=	"Name for continent or ocean island region"
    helpme["ocean_sea"]=	"Name for location in an ocean or sea"
    helpme["country"]=	"Country name"
    helpme["region"]=	"Region name"
    helpme["plate_block"]=	"Plate or tectonic block name"
    helpme["terrane"]=	"Terrane name"
    helpme["tectonic_setting"]=	"Tectonic setting"
    helpme["location_description"]=	"Detailed description"
    helpme["location_url"]=	"Website URL for the location explicitly"
    helpme["er_scientist_mail_names"]=	"Colon-delimited list of names for scientists who described location"
    helpme["er_citation_names"]=	"Colon-delimited list of citations"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_formation_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["formation_class"]=	"General lithology class: igneous, metamorphic or sedimentary"
    helpme["formation_lithology"]=	"Lithology: e.g., basalt, sandstone, etc."
    helpme["formation_paleo_enviroment"]=	"Depositional environment"
    helpme["formation_thickness"]=	"Formation thickness"
    helpme["er_member_name"]=	"Name for member"
    helpme["er_member_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["member_class"]=	"General lithology type"
    helpme["member_lithology"]=	"Lithology"
    helpme["member_paleo_environment"]=	"Depositional environment"
    helpme["member_thickness"]=	"Member thickness"
    helpme["member_description"]=	"Detailed description"
    helpme["er_section_name"]=	"Name for section or core"
    helpme["er_section_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["section_definition"]=	"General definition of section"
    helpme["section_class"]=	"General lithology type"
    helpme["section_lithology"]=	"Section lithology or archeological classification"
    helpme["section_type"]=	"Section type"
    helpme["section_n"]=	"Number of subsections included composite (stacked) section"
    helpme["section_begin_lat"]=	"Begin of section or core -- latitude"
    helpme["section_begin_lon"]=	"Begin of section or core -- longitude"
    helpme["section_begin_elevation"]=	"Begin of section or core -- elevation relative to sealevel"
    helpme["section_begin_height"]=	"Begin of section or core -- stratigraphic height"
    helpme["section_begin_drill_depth"]=	"Begin of section or core -- depth in MBSF as used by ODP"
    helpme["section_begin_composite_depth"]=	"Begin of section or core -- composite depth in MBSF as used by ODP"
    helpme["section_end_lat"]=	"End of section or core -- latitude "
    helpme["section_end_lon"]=	"End of section or core -- longitude "
    helpme["section_end_elevation"]=	"End of section or core -- elevation relative to sealevel"
    helpme["section_end_height"]=	"End of section or core -- stratigraphic height"
    helpme["section_end_drill_depth"]=	"End of section or core -- depth in MBSF as used by ODP"
    helpme["section_end_composite_depth"]=	"End of section or core -- composite depth in MBSF as used by ODP"
    helpme["section_azimuth"]=	"Section azimuth as measured clockwise from the north"
    helpme["section_dip"]=	"Section dip as measured into the outcrop"
    helpme["section_description"]=	"Detailed description"
    helpme["er_site_name"]=	"Name for site"
    helpme["er_site_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_section_name"]=	"Name for section or core"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["site_definition"]=	"General definition of site"
    helpme["site_class"]=	"[A]rchaeologic,[E]xtrusive,[I]ntrusive,[M]etamorphic,[S]edimentary"
    helpme["site_lithology"]=	"Site lithology or archeological classification"
    helpme["site_type"]=	"Site type: slag, lava flow, sediment layer, etc."
    helpme["site_lat"]=	"Site location -- latitude"
    helpme["site_lon"]=	"Site location -- longitude"
    helpme["site_location_precision"]=	"Site location -- precision in latitude and longitude"
    helpme["site_elevation"]=	"Site location -- elevation relative to sealevel"
    helpme["site_height"]=	"Site location -- stratigraphic height"
    helpme["site_drill_depth"]=	"Site location -- depth in MBSF as used by ODP"
    helpme["site_composite_depth"]=	"Site location -- composite depth in MBSF as used by ODP"
    helpme["site_description"]=	"Detailed description"
    helpme["magic_method_codes"]=	"Colon-delimited list of method codes"
    helpme["er_sample_name"]=	"Name for sample"
    helpme["er_sample_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_section_name"]=	"Name for section or core"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["er_site_name"]=	"Name for site"
    helpme["sample_class"]=	"General lithology type"
    helpme["sample_lithology"]=	"Sample lithology or archeological classification"
    helpme["sample_type"]=	"Sample type"
    helpme["sample_texture"]=	"Sample texture"
    helpme["sample_alteration"]=	"Sample alteration grade"
    helpme["sample_alteration_type"]=	"Sample alteration type"
    helpme["sample_lat"]=	"Sample location -- latitude"
    helpme["sample_lon"]=	"Sample location -- longitude"
    helpme["sample_location_precision"]=	"Sample location -- precision in latitude and longitude"
    helpme["sample_elevation"]=	"Sample location -- elevation relative to sealevel"
    helpme["sample_height"]=	"Sample location -- stratigraphic height"
    helpme["sample_drill_depth"]=	"Sample location -- depth in MBSF as used by ODP"
    helpme["sample_composite_depth"]=	"Sample location -- composite depth in MBSF as used by ODP"
    helpme["sample_date"]=	"Sampling date"
    helpme["sample_time_zone"]=	"Sampling time zone"
    helpme["sample_azimuth"]=	"Sample azimuth as measured clockwise from the north"
    helpme["sample_dip"]=	"Sample dip as measured into the outcrop"
    helpme["sample_bed_dip_direction"]=	"Direction of the dip of a paleo-horizontal plane in the bedding"
    helpme["sample_bed_dip"]=	"Dip of the bedding as measured to the right of strike direction"
    helpme["sample_cooling_rate"]=	"Estimated ancient in-situ cooling rate per Ma"
    helpme["er_specimen_name"]=	"Name for specimen"
    helpme["er_specimen_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_section_name"]=	"Name for section or core"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["er_site_name"]=	"Name for site"
    helpme["er_sample_name"]=	"Name for sample"
    helpme["specimen_class"]=	"General lithology type"
    helpme["specimen_lithology"]=	"Specimen lithology or archeological classification"
    helpme["specimen_type"]=	"Specimen type"
    helpme["specimen_texture"]=	"Specimen texture"
    helpme["specimen_alteration"]=	"Specimen alteration grade"
    helpme["specimen_alteration_type"]=	"Specimen alteration type"
    helpme["specimen_elevation"]=	"Specimen location -- elevation relative to sealevel"
    helpme["specimen_height"]=	"Specimen location -- stratigraphic height"
    helpme["specimen_drill_depth"]=	"Specimen location -- depth in MBSF as used by ODP"
    helpme["specimen_composite_depth"]=	"Specimen location -- composite depth in MBSF as used by ODP"
    helpme["specimen_azimuth"]=	"Specimen azimuth as measured clockwise from the north"
    helpme["specimen_dip"]=	"Specimen dip as measured into the outcrop"
    helpme["specimen_volume"]=	"Specimen volume"
    helpme["specimen_weight"]=	"Specimen weight"
    helpme["specimen_density"]=	"Specimen density"
    helpme["specimen_size"]=	"Specimen grain size fraction"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["er_site_name"]=	"Name for site"
    helpme["er_sample_name"]=	"Name for sample"
    helpme["er_specimen_name"]=	"Name for specimen"
    helpme["er_fossil_name"]=	"Name for fossil"
    helpme["er_mineral_name"]=	"Name for mineral"
    helpme["GM-ALPHA"]=	"Age determination by using alpha counting"
    helpme["GM-ARAR"]=	"40Ar/39Ar age determination"
    helpme["GM-ARAR-AP"]=	"40Ar/39Ar age determination: Age plateau"
    helpme["GM-ARAR-II"]=	"40Ar/39Ar age determination: Inverse isochron"
    helpme["GM-ARAR-NI"]=	"40Ar/39Ar age determination: Normal isochron"
    helpme["GM-ARAR-TF"]=	"40Ar/39Ar age determination: Total fusion or recombined age"
    helpme["GM-C14"]=	"Radiocarbon age determination"
    helpme["GM-C14-AMS"]=	"Radiocarbon age determination: AMS"
    helpme["GM-C14-BETA"]=	"Radiocarbon age determination: Beta decay counting"
    helpme["GM-C14-CAL"]=	"Radiocarbon age determination: Calibrated"
    helpme["GM-CC"]=	"Correlation chronology"
    helpme["GM-CC-ARCH"]=	"Correlation chronology: Archeology"
    helpme["GM-CC-ARM"]=	"Correlation chronology: ARM"
    helpme["GM-CC-ASTRO"]=	"Correlation chronology: Astronomical"
    helpme["GM-CC-CACO3"]=	"Correlation chronology: Calcium carbonate"
    helpme["GM-CC-COLOR"]=	"Correlation chronology: Color or reflectance"
    helpme["GM-CC-GRAPE"]=	"Correlation chronology: Gamma Ray Polarimeter Experiment"
    helpme["GM-CC-IRM"]=	"Correlation chronology: IRM"
    helpme["GM-CC-ISO"]=	"Correlation chronology: Stable isotopes"
    helpme["GM-CC-REL"]=	"Correlation chronology: Relative chronology other than stratigraphic successions"
    helpme["GM-CC-STRAT"]=	"Correlation chronology: Stratigraphic succession"
    helpme["GM-CC-TECT"]=	"Correlation chronology: Tectites and microtectites"
    helpme["GM-CC-TEPH"]=	"Correlation chronology: Tephrochronology"
    helpme["GM-CC-X"]=	"Correlation chronology: Susceptibility"
    helpme["GM-CHEM"]=	"Chemical chronology"
    helpme["GM-CHEM-AAR"]=	"Chemical chronology: Amino acid racemization"
    helpme["GM-CHEM-OH"]=	"Chemical chronology: Obsidian hydration"
    helpme["GM-CHEM-SC"]=	"Chemical chronology: Stoan coatings CaCO3"
    helpme["GM-CHEM-TH"]=	"Chemical chronology: Tephra hydration"
    helpme["GM-COSMO"]=	"Cosmogenic age determination"
    helpme["GM-COSMO-AL26"]=	"Cosmogenic age determination: 26Al"
    helpme["GM-COSMO-AR39"]=	"Cosmogenic age determination: 39Ar"
    helpme["GM-COSMO-BE10"]=	"Cosmogenic age determination: 10Be"
    helpme["GM-COSMO-C14"]=	"Cosmogenic age determination: 14C"
    helpme["GM-COSMO-CL36"]=	"Cosmogenic age determination: 36Cl"
    helpme["GM-COSMO-HE3"]=	"Cosmogenic age determination: 3He"
    helpme["GM-COSMO-KR81"]=	"Cosmogenic age determination: 81Kr"
    helpme["GM-COSMO-NE21"]=	"Cosmogenic age determination: 21Ne"
    helpme["GM-COSMO-NI59"]=	"Cosmogenic age determination: 59Ni"
    helpme["GM-COSMO-SI32"]=	"Cosmogenic age determination: 32Si"
    helpme["GM-DENDRO"]=	"Dendrochronology"
    helpme["GM-ESR"]=	"Electron Spin Resonance"
    helpme["GM-FOSSIL"]=	"Age determined from fossil record"
    helpme["GM-FT"]=	"Fission track age determination"
    helpme["GM-HIST"]=	"Historically recorded geological event"
    helpme["GM-INT"]=	"Age determination through interpolation between at least two geological units of known age"
    helpme["GM-INT-L"]=	"Age determination through interpolation between at least two geological units of known age: Linear"
    helpme["GM-INT-S"]=	"Age determination through interpolation between at least two geological units of known age: Cubic spline"
    helpme["GM-ISO"]=	"Age determined by isotopic dating, but no further details available"
    helpme["GM-KAR"]=	"40K-40Ar age determination"
    helpme["GM-KAR-I"]=	"40K-40Ar age determination: Isochron"
    helpme["GM-KAR-MA"]=	"40K-40Ar age determination: Model age"
    helpme["GM-KCA"]=	"40K-40Ca age determination"
    helpme["GM-KCA-I"]=	"40K-40Ca age determination: Isochron"
    helpme["GM-KCA-MA"]=	"40K-40Ca age determination: Model age"
    helpme["GM-LABA"]=	"138La-138Ba age determination"
    helpme["GM-LABA-I"]=	"138La-138Ba age determination: Isochron"
    helpme["GM-LABA-MA"]=	"138La-138Ba age determination: Model age"
    helpme["GM-LACE"]=	"138La-138Ce age determination"
    helpme["GM-LACE-I"]=	"138La-138Ce age determination: Isochron"
    helpme["GM-LACE-MA"]=	"138La-138Ce age determination: Model age"
    helpme["GM-LICHE"]=	"Lichenometry"
    helpme["GM-LUHF"]=	"176Lu-176Hf age determination"
    helpme["GM-LUHF-I"]=	"176Lu-176Hf age determination: Isochron"
    helpme["GM-LUHF-MA"]=	"176Lu-176Hf age determination: Model age"
    helpme["GM-LUM"]=	"Luminescence"
    helpme["GM-LUM-IRS"]=	"Luminescence: Infrared stimulated luminescence"
    helpme["GM-LUM-OS"]=	"Luminescence: Optically stimulated luminescence"
    helpme["GM-LUM-TH"]=	"Luminescence: Thermoluminescence"
    helpme["GM-MOD"]=	"Model curve fit to available age dates"
    helpme["GM-MOD-L"]=	"Model curve fit to available age dates: Linear"
    helpme["GM-MOD-S"]=	"Model curve fit to available age dates: Cubic spline"
    helpme["GM-MORPH"]=	"Geomorphic chronology"
    helpme["GM-MORPH-DEF"]=	"Geomorphic chronology: Rate of deformation"
    helpme["GM-MORPH-DEP"]=	"Geomorphic chronology: Rate of deposition"
    helpme["GM-MORPH-POS"]=	"Geomorphic chronology: Geomorphology position"
    helpme["GM-MORPH-WEATH"]=	"Geomorphic chronology: Rock and mineral weathering"
    helpme["GM-NO"]=	"Unknown geochronology method"
    helpme["GM-O18"]=	"Oxygen isotope dating"
    helpme["GM-PBPB"]=	"207Pb-206Pb age determination"
    helpme["GM-PBPB-C"]=	"207Pb-206Pb age determination: Common Pb"
    helpme["GM-PBPB-I"]=	"207Pb-206Pb age determination: Isochron"
    helpme["GM-PLEO"]=	"Pleochroic haloes"
    helpme["GM-PMAG-ANOM"]=	"Paleomagnetic age determination: Magnetic anomaly identification"
    helpme["GM-PMAG-APWP"]=	"Paleomagnetic age determination: Comparing paleomagnetic data to APWP"
    helpme["GM-PMAG-ARCH"]=	"Paleomagnetic age determination: Archeomagnetism"
    helpme["GM-PMAG-DIR"]=	"Paleomagnetic age determination: Directions"
    helpme["GM-PMAG-POL"]=	"Paleomagnetic age determination: Polarities"
    helpme["GM-PMAG-REGSV"]=	"Paleomagnetic age determination: Correlation to a regional secular variation curve"
    helpme["GM-PMAG-RPI"]=	"Paleomagnetic age determination: Relative paleointensity"
    helpme["GM-PMAG-VEC"]=	"Paleomagnetic age determination: Full vector"
    helpme["GM-RATH"]=	"226Ra-230Th age determination"
    helpme["GM-RBSR"]=	"87Rb-87Sr age determination"
    helpme["GM-RBSR-I"]=	"87Rb-87Sr age determination: Isochron"
    helpme["GM-RBSR-MA"]=	"87Rb-87Sr age determination: Model age"
    helpme["GM-REOS"]=	"187Re-187Os age determination"
    helpme["GM-REOS-I"]=	"187Re-187Os age determination: Isochron"
    helpme["GM-REOS-MA"]=	"187Re-187Os age determination: Model age"
    helpme["GM-REOS-PT"]=	"187Re-187Os age determination: Pt normalization of 186Os"
    helpme["GM-SCLERO"]=	"Screlochronology"
    helpme["GM-SHRIMP"]=	"SHRIMP age dating"
    helpme["GM-SMND"]=	"147Sm-143Nd age determination"
    helpme["GM-SMND-I"]=	"147Sm-143Nd age determination: Isochron"
    helpme["GM-SMND-MA"]=	"147Sm-143Nd age determination: Model age"
    helpme["GM-THPB"]=	"232Th-208Pb age determination"
    helpme["GM-THPB-I"]=	"232Th-208Pb age determination: Isochron"
    helpme["GM-THPB-MA"]=	"232Th-208Pb age determination: Model age"
    helpme["GM-UPA"]=	"235U-231Pa age determination"
    helpme["GM-UPB"]=	"U-Pb age determination"
    helpme["GM-UPB-CC-T0"]=	"U-Pb age determination: Concordia diagram age, upper intersection"
    helpme["GM-UPB-CC-T1"]=	"U-Pb age determination: Concordia diagram age, lower intersection"
    helpme["GM-UPB-I-206"]=	"U-Pb age determination: 238U-206Pb isochron"
    helpme["GM-UPB-I-207"]=	"U-Pb age determination: 235U-207Pb isochron"
    helpme["GM-UPB-MA-206"]=	"U-Pb age determination: 238U-206Pb model age"
    helpme["GM-UPB-MA-207"]=	"U-Pb age determination: 235U-207Pb model age"
    helpme["GM-USD"]=	"Uranium series disequilibrium age determination"
    helpme["GM-USD-PA231-TH230"]=	"Uranium series disequilibrium age determination: 231Pa-230Th"
    helpme["GM-USD-PA231-U235"]=	"Uranium series disequilibrium age determination: 231Pa-235U"
    helpme["GM-USD-PB210"]=	"Uranium series disequilibrium age determination: 210Pb"
    helpme["GM-USD-RA226-TH230"]=	"Uranium series disequilibrium age determination: 226Ra-230Th"
    helpme["GM-USD-RA228-TH232"]=	"Uranium series disequilibrium age determination: 228Ra-232Th"
    helpme["GM-USD-TH228-TH232"]=	"Uranium series disequilibrium age determination: 228Th-232Th"
    helpme["GM-USD-TH230"]=	"Uranium series disequilibrium age determination: 230Th"
    helpme["GM-USD-TH230-TH232"]=	"Uranium series disequilibrium age determination: 230Th-232Th"
    helpme["GM-USD-TH230-U234"]=	"Uranium series disequilibrium age determination: 230Th-234U"
    helpme["GM-USD-TH230-U238"]=	"Uranium series disequilibrium age determination: 230Th-238U"
    helpme["GM-USD-U234-U238"]=	"Uranium series disequilibrium age determination: 234U-238U"
    helpme["GM-UTH"]=	"238U-230Th age determination"
    helpme["GM-UTHHE"]=	"U-Th-He age determination"
    helpme["GM-UTHPB"]=	"U-Th-Pb age determination"
    helpme["GM-UTHPB-CC-T0"]=	"U-Th-Pb age determination: Concordia diagram intersection age, upper intercept"
    helpme["GM-UTHPB-CC-T1"]=	"U-Th-Pb age determination: Concordia diagram intersection age, lower intercept"
    helpme["GM-VARVE"]=	"Age determined by varve counting"
    helpme["tiepoint_name"]=	"Name for tiepoint horizon"
    helpme["tiepoint_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["tiepoint_height"]=	"Tiepoint stratigraphic height relative to reference tiepoint"
    helpme["tiepoint_height_sigma"]=	"Tiepoint stratigraphic height uncertainty"
    helpme["tiepoint_elevation"]=	"Tiepoint elevation relative to sealevel"
    helpme["tiepoint_type"]=	"Tiepoint type"
    helpme["age"]=	"Age"
    helpme["age_sigma"]=	"Age -- uncertainty"
    helpme["age_range_low"]=	"Age -- low range"
    helpme["age_range_high"]=	"Age -- high range"
    helpme["age_unit"]=	"Age -- unit"
    helpme["timescale_eon"]=	"Timescale eon"
    helpme["timescale_era"]=	"Timescale era"
    helpme["timescale_period"]=	"Timescale period"
    helpme["timescale_epoch"]=	"Timescale epoch"
    helpme["timescale_stage"]=	"Timescale stage"
    helpme["biostrat_zone"]=	"Biostratigraphic zone"
    helpme["conodont_zone"]=	"Conodont zone"
    helpme["magnetic_reversal_chron"]=	"Magnetic reversal chron"
    helpme["astronomical_stage"]=	"Astronomical stage name"
    helpme["oxygen_stage"]=	"Oxygen stage name"
    helpme["age_culture_name"]=	"Age culture name"
    return helpme[keyhelp]

def dosundec(sundata):
    """
    returns the declination for a given set of suncompass data
    """
    rad=numpy.pi/180.
    iday=0
    timedate=sundata["date"]
    timedate=timedate.split(":") 
    year=int(timedate[0])
    mon=int(timedate[1])
    day=int(timedate[2])
    hours=float(timedate[3])
    min=float(timedate[4])
    du=int(sundata["delta_u"])
    hrs=hours-du
    if hrs > 24:
        day+=1
        hrs=hrs-24
    if hrs < 0:
        day=day-1
        hrs=hrs+24
    julian_day=julian(mon,day,year)
    utd=(hrs+min/60.)/24.
    greenwich_hour_angle,delta=gha(julian_day,utd)
    H=greenwich_hour_angle+float(sundata["lon"])
    if H > 360: H=H-360
    lat=float(sundata["lat"])
    if H > 90 and H < 270:lat=-lat
# now do spherical trig to get azimuth to sun
    lat=(lat)*rad
    delta=(delta)*rad
    H=H*rad
    ctheta=numpy.sin(lat)*numpy.sin(delta)+numpy.cos(lat)*numpy.cos(delta)*numpy.cos(H)
    theta=numpy.arccos(ctheta)
    beta=numpy.cos(delta)*numpy.sin(H)/numpy.sin(theta)
#
#       check which beta
#
    beta=numpy.arcsin(beta)/rad
    if delta < lat: beta=180-beta
    sunaz=180-beta
    suncor=(sunaz+float(sundata["shadow_angle"]))%360. #  mod 360
    return suncor

def gha(julian_day,f):
    """
    returns greenwich hour angle
    """
    rad=numpy.pi/180.
    d=julian_day-2451545.0+f
    L= 280.460 + 0.9856474*d
    g=  357.528 + 0.9856003*d
    L=L%360.
    g=g%360.
# ecliptic longitude
    lamb=L+1.915*numpy.sin(g*rad)+.02*numpy.sin(2*g*rad)
# obliquity of ecliptic
    epsilon= 23.439 - 0.0000004*d
# right ascension (in same quadrant as lambda)
    t=(numpy.tan((epsilon*rad)/2))**2
    r=1/rad
    rl=lamb*rad
    alpha=lamb-r*t*numpy.sin(2*rl)+(r/2)*t*t*numpy.sin(4*rl)
#       alpha=mod(alpha,360.0)
# declination
    delta=numpy.sin(epsilon*rad)*numpy.sin(lamb*rad)
    delta=numpy.arcsin(delta)/rad
# equation of time
    eqt=(L-alpha)
#
    utm=f*24*60
    H=utm/4+eqt+180
    H=H%360.0
    return H,delta


def julian(mon,day,year):
    """
    returns julian day
    """
    ig=15+31*(10+12*1582)
    if year == 0: 
        print "Julian no can do"
        return
    if year < 0: year=year+1
    if mon > 2:  
        julian_year=year
        julian_month=mon+1
    else:
        julian_year=year-1
        julian_month=mon+13
    j1=int(365.25*julian_year)
    j2=int(30.6001*julian_month)
    j3=day+1720995
    julian_day=j1+j2+j3
    if day+31*(mon+12*year) >= ig:
        jadj=int(0.01*julian_year)
        julian_day=julian_day+2-jadj+int(0.25*jadj)
    return julian_day

def fillkeys(Recs):
    """
    reconciles keys of dictionaries within Recs.
    """
    keylist,OutRecs=[],[]
    for rec in Recs:
        for key in rec.keys(): 
            if key not in keylist:keylist.append(key)
    for rec in  Recs:
        for key in keylist:
            if key not in rec.keys(): rec[key]=""
        OutRecs.append(rec)
    return OutRecs,keylist

def fisher_mean(data):
    """
    calculates fisher parameters for data
    """

    R,Xbar,X,fpars=0,[0,0,0],[],{}
    N=len(data)
    if N <2:
       return fpars
    X=dir2cart(data)
    #for rec in data:
    #    X.append(dir2cart([rec[0],rec[1],1.]))
    for i in range(len(X)):
        for c in range(3):
           Xbar[c]+=X[i][c]
    for c in range(3):
        R+=Xbar[c]**2
    R=numpy.sqrt(R)
    for c in range(3):
        Xbar[c]=Xbar[c]/R    
    dir=cart2dir(Xbar)
    fpars["dec"]=dir[0]
    fpars["inc"]=dir[1]
    fpars["n"]=N
    fpars["r"]=R
    if N!=R:
        k=(N-1.)/(N-R)
        fpars["k"]=k
        csd=81./numpy.sqrt(k)
    else:
        fpars['k']='inf'
        csd=0.
    b=20.**(1./(N-1.)) -1
    a=1-b*(N-R)/R
    if a<-1:a=-1
    a95=numpy.arccos(a)*180./numpy.pi
    fpars["alpha95"]=a95
    fpars["csd"]=csd
    if a<0: fpars["alpha95"] = 180.0
    return fpars
 
def gausspars(data):
    """
    calculates gaussian statistics for data
    """
    N,mean,d=len(data),0.,0.
    if N<1: return "",""
    if N==1: return data[0],0
    for j in range(N):
       mean+=data[j]/float(N)
    for j in range(N):
       d+=(data[j]-mean)**2 
    stdev=numpy.sqrt(d*(1./(float(N-1))))
    return mean,stdev

def weighted_mean(data):
    """
    calculates weighted mean of data
    """
    W,N,mean,d=0,len(data),0,0
    if N<1: return "",""
    if N==1: return data[0][0],0
    for x in data:
       W+=x[1] # sum of the weights
    for x in data:
       mean+=(float(x[1])*float(x[0]))/float(W)
    for x in data:
       d+=(float(x[1])/float(W))*(float(x[0])-mean)**2 
    stdev=numpy.sqrt(d*(1./(float(N-1))))
    return mean,stdev


def lnpbykey(data,key0,key1): # calculate a fisher mean of key1 data for a group of key0 
    PmagRec={}
    if len(data)>1:
        for rec in data:
            rec['dec']=float(rec[key1+'_dec'])
            rec['inc']=float(rec[key1+'_inc'])
        fpars=dolnp(data,key1+'_direction_type')
        PmagRec[key0+"_dec"]=fpars["dec"]
        PmagRec[key0+"_inc"]=fpars["inc"]
        PmagRec[key0+"_n"]=(fpars["n_total"])
        PmagRec[key0+"_n_lines"]=fpars["n_lines"]
        PmagRec[key0+"_n_planes"]=fpars["n_planes"]
        PmagRec[key0+"_r"]=fpars["R"]
        PmagRec[key0+"_k"]=fpars["K"]
        PmagRec[key0+"_alpha95"]=fpars["alpha95"]
        if int(PmagRec[key0+"_n_planes"])>0:
            PmagRec["magic_method_codes"]="DE-FM-LP"
        elif int(PmagRec[key0+"_n_lines"])>2:
            PmagRec["magic_method_codes"]="DE-FM"
    elif len(data)==1:
        PmagRec[key0+"_dec"]=data[0][key1+'_dec']
        PmagRec[key0+"_inc"]=data[0][key1+'_inc']
        PmagRec[key0+"_n"]='1'
        if data[0][key1+'_direction_type']=='l': 
            PmagRec[key0+"_n_lines"]='1'
            PmagRec[key0+"_n_planes"]='0'
        if data[0][key1+'_direction_type']=='p': 
            PmagRec[key0+"_n_planes"]='1'
            PmagRec[key0+"_n_lines"]='0'
        PmagRec[key0+"_alpha95"]=""
        PmagRec[key0+"_r"]=""
        PmagRec[key0+"_k"]=""
        PmagRec[key0+"_direction_type"]="l"
    return PmagRec

def fisher_by_pol(data):
    """
    input:    as in dolnp (list of dictionaries with 'dec' and 'inc')
    description: do fisher mean after splitting data into two polaroties domains.
    output: three dictionaries:
        'A'= polarity 'A'
        'B = polarity 'B'
        'ALL'= switching polarity of 'B' directions, and calculate fisher mean of all data     
    code modified from eqarea_ell.py b rshaar 1/23/2014
    """
    FisherByPoles={}
    DIblock,nameblock,locblock=[],[],[]
    for rec in data:
        if 'dec' in rec.keys() and 'inc' in rec.keys():
            DIblock.append([float(rec["dec"]),float(rec["inc"])]) # collect data for fisher calculation
        else:
            continue
        if 'name' in rec.keys():
            nameblock.append(rec['name'])
        else:
            nameblock.append("")    
        if 'loc' in rec.keys():
            locblock.append(rec['loc'])
        else:
            locblock.append("")
            
    ppars=doprinc(array(DIblock)) # get principal directions  
    reference_DI=[ppars['dec'],ppars['inc']] # choose the northerly declination principe component ("normal") 
    if reference_DI[0]>90 and reference_DI[0]<270: # make reference direction in northern hemisphere
        reference_DI[0]=(reference_DI[0]+180.)%360
        reference_DI[1]=reference_DI[1]*-1.
    nDIs,rDIs,all_DI,npars,rpars=[],[],[],[],[]
    nlist,rlist,alllist="","",""
    nloclist,rloclist,allloclist="","",""
    for k in range(len(DIblock)):            
        if angle([DIblock[k][0],DIblock[k][1]],reference_DI) > 90.:
            rDIs.append(DIblock[k])
            rlist=rlist+":"+nameblock[k]
            if locblock[k] not in rloclist:rloclist=rloclist+":"+locblock[k]
            all_DI.append( [(DIblock[k][0]+180.)%360.,-1.*DIblock[k][1]])
            alllist=alllist+":"+nameblock[k]
            if locblock[k] not in allloclist:allloclist=allloclist+":"+locblock[k]
        else:
            nDIs.append(DIblock[k])
            nlist=nlist+":"+nameblock[k]
            if locblock[k] not in nloclist:nloclist=nloclist+":"+locblock[k]
            all_DI.append(DIblock[k])
            alllist=alllist+":"+nameblock[k]
            if locblock[k] not in allloclist:allloclist=allloclist+":"+locblock[k]
            
    for mode in ['A','B','All']:
        if mode=='A' and len(nDIs)>2:
            fpars=fisher_mean(nDIs)
            fpars['sites']=nlist.strip(':')
            fpars['locs']=nloclist.strip(':')
            FisherByPoles[mode]=fpars
        elif mode=='B' and len(rDIs)>2:              
            fpars=fisher_mean(rDIs)
            fpars['sites']=rlist.strip(':')
            fpars['locs']=rloclist.strip(':')
            FisherByPoles[mode]=fpars
        elif mode=='All' and len(all_DI)>2:           
            fpars=fisher_mean(all_DI)
            fpars['sites']=alllist.strip(':')
            fpars['locs']=allloclist.strip(':')
            FisherByPoles[mode]=fpars
    return FisherByPoles       
    
     
def dolnp(data,direction_type_key):
    """
    returns fisher mean, a95 for data  using method of mcfadden and mcelhinny '88 for lines and planes
    """
    if "tilt_correction" in data[0].keys(): 
        tc=data[0]["tilt_correction"]
    else:
        tc='-1'
    n_lines,n_planes=0,0
    X,L,fdata,dirV=[],[],[],[0,0,0]
    E=[0,0,0]
    fpars={}
#
# sort data  into lines and planes and collect cartesian coordinates
    for rec in data:
        cart=dir2cart([rec["dec"],rec["inc"]])[0]
        if direction_type_key in rec.keys() and rec[direction_type_key]=='p': # this is a pole to a plane
            n_planes+=1
            L.append(cart) # this is the "EL, EM, EN" array of MM88
        else: # this is a line
            n_lines+=1
            fdata.append([rec["dec"],rec["inc"],1.]) # collect data for fisher calculation
            X.append(cart)
            E[0]+=cart[0] 
            E[1]+=cart[1] 
            E[2]+=cart[2] 
# set up initial points on the great circles
    V,XV=[],[]
    if n_planes !=0:
        if n_lines==0:
            V=dir2cart([180.,-45.,1.]) # set the initial direction arbitrarily
        else:
           R=numpy.sqrt(E[0]**2+E[1]**2+E[2]**2) 
           for c in E:
               V.append(c/R) # set initial direction as mean of lines
        U=E[:]   # make a copy of E
        for pole in L:
            XV.append(vclose(pole,V)) # get some points on the great circle
            for c in range(3):
               U[c]=U[c]+XV[-1][c]
# iterate to find best agreement
        angle_tol=1.
        while angle_tol > 0.1:
            angles=[]
            for k in range(n_planes): 
               for c in range(3): U[c]=U[c]-XV[k][c]
               R=numpy.sqrt(U[0]**2+U[1]**2+U[2]**2)
               for c in range(3):V[c]=U[c]/R
               XX=vclose(L[k],V)
               ang=XX[0]*XV[k][0]+XX[1]*XV[k][1]+XX[2]*XV[k][2]
               angles.append(numpy.arccos(ang)*180./numpy.pi)
               for c in range(3):
                   XV[k][c]=XX[c]
                   U[c]=U[c]+XX[c]
               amax =-1
               for ang in angles:
                   if ang > amax:amax=ang
               angle_tol=amax
# calculating overall mean direction and R
        U=E[:]
        for dir in XV:
            for c in range(3):U[c]=U[c]+dir[c]
        R=numpy.sqrt(U[0]**2+U[1]**2+U[2]**2)
        for c in range(3):U[c]=U[c]/R
# get dec and inc of solution points on gt circles
        dirV=cart2dir(U)
# calculate modified Fisher stats fo fit
        n_total=n_lines+n_planes
        NP=n_lines+0.5*n_planes
        if NP<1.1:NP=1.1
        if n_total-R !=0:
            K=(NP-1.)/(n_total-R)
            fac=(20.**(1./(NP-1.))-1.)
            fac=fac*(NP-1.)/K
            a=1.-fac/R
            a95=a
            if abs(a) > 1.0: a95=1.
            if a<0:a95=-a95
            a95=numpy.arccos(a95)*180./numpy.pi
        else: 
            a95=0.
            K='inf'
    else:
        dir=fisher_mean(fdata)
        n_total,R,K,a95=dir["n"],dir["r"],dir["k"],dir["alpha95"]
        dirV[0],dirV[1]=dir["dec"],dir["inc"]
    fpars["tilt_correction"]=tc
    fpars["n_total"]='%i '% (n_total)
    fpars["n_lines"]='%i '% (n_lines)
    fpars["n_planes"]='%i '% (n_planes)
    fpars["R"]='%5.4f '% (R)
    if K!='inf':
        fpars["K"]='%6.0f '% (K)
    else:
        fpars["K"]=K
    fpars["alpha95"]='%7.1f '% (a95)
    fpars["dec"]='%7.1f '% (dirV[0])
    fpars["inc"]='%7.1f '% (dirV[1])
    return fpars

def vclose(L,V):
    """
    gets the closest vector
    """
    lam,X=0,[]
    for k in range(3):
        lam=lam+V[k]*L[k] 
    beta=numpy.sqrt(1.-lam**2)
    for k in range(3):
        X.append( ((V[k]-lam*L[k])/beta))
    return X

   
def scoreit(pars,PmagSpecRec,accept,text,verbose):
    """
    gets a grade for a given set of data, spits out stuff
    """
    s=PmagSpecRec["er_specimen_name"]
    PmagSpecRec["measurement_step_min"]='%8.3e' % (pars["measurement_step_min"])
    PmagSpecRec["measurement_step_max"]='%8.3e' % (pars["measurement_step_max"])
    PmagSpecRec["measurement_step_unit"]=pars["measurement_step_unit"]
    PmagSpecRec["specimen_int_n"]='%i'%(pars["specimen_int_n"])
    PmagSpecRec["specimen_lab_field_dc"]='%8.3e'%(pars["specimen_lab_field_dc"])
    PmagSpecRec["specimen_int"]='%8.3e '%(pars["specimen_int"])
    PmagSpecRec["specimen_b"]='%5.3f '%(pars["specimen_b"])
    PmagSpecRec["specimen_q"]='%5.1f '%(pars["specimen_q"])
    PmagSpecRec["specimen_f"]='%5.3f '%(pars["specimen_f"])
    PmagSpecRec["specimen_fvds"]='%5.3f'%(pars["specimen_fvds"])
    PmagSpecRec["specimen_b_beta"]='%5.3f'%(pars["specimen_b_beta"])
    PmagSpecRec["specimen_int_mad"]='%7.1f'%(pars["specimen_int_mad"])
    PmagSpecRec["specimen_dec"]='%7.1f'%(pars["specimen_dec"])
    PmagSpecRec["specimen_inc"]='%7.1f'%(pars["specimen_inc"])
    PmagSpecRec["specimen_int_dang"]='%7.1f '%(pars["specimen_int_dang"])
    PmagSpecRec["specimen_drats"]='%7.1f '%(pars["specimen_drats"])
    PmagSpecRec["specimen_int_ptrm_n"]='%i '%(pars["specimen_int_ptrm_n"])
    PmagSpecRec["specimen_rsc"]='%6.4f '%(pars["specimen_rsc"])
    PmagSpecRec["specimen_md"]='%i '%(int(pars["specimen_md"]))
    PmagSpecRec["specimen_b_sigma"]='%5.3f '%(pars["specimen_b_sigma"])
    if 'specimen_scat' in pars.keys():PmagSpecRec['specimen_scat']=pars['specimen_scat']
    if 'specimen_gmax' in pars.keys():PmagSpecRec['specimen_gmax']='%5.3f'%(pars['specimen_gmax'])
    if 'specimen_frac' in pars.keys():PmagSpecRec['specimen_frac']='%5.3f'%(pars['specimen_frac'])
    #PmagSpecRec["specimen_Z"]='%7.1f'%(pars["specimen_Z"])
  # check score
   #
    kill=grade(PmagSpecRec,accept,'specimen_int')
    Grade=""
    if len(kill)==0:
        Grade='A'
    else:
        Grade='F'
    pars["specimen_grade"]=Grade
    if verbose==0:
        return pars,kill
    diffcum=0
    if pars['measurement_step_unit']=='K':
        outstr= "specimen     Tmin  Tmax  N  lab_field  B_anc  b  q  f(coe)  Fvds  beta  MAD  Dang  Drats  Nptrm  Grade  R  MD%  sigma  Gamma_max \n"
        pars_out= (s,(pars["measurement_step_min"]-273),(pars["measurement_step_max"]-273),(pars["specimen_int_n"]),1e6*(pars["specimen_lab_field_dc"]),1e6*(pars["specimen_int"]),pars["specimen_b"],pars["specimen_q"],pars["specimen_f"],pars["specimen_fvds"],pars["specimen_b_beta"],pars["specimen_int_mad"],pars["specimen_int_dang"],pars["specimen_drats"],pars["specimen_int_ptrm_n"],pars["specimen_grade"],numpy.sqrt(pars["specimen_rsc"]),int(pars["specimen_md"]), pars["specimen_b_sigma"],pars['specimen_gamma'])
        outstring= '%s %4.0f %4.0f %i %4.1f %4.1f %5.3f %5.1f %5.3f %5.3f %5.3f  %7.1f %7.1f %7.1f %s %s %6.3f %i %5.3f %7.1f' % pars_out +'\n'
    elif pars['measurement_step_unit']=='J':
        outstr= "specimen     Wmin  Wmax  N  lab_field  B_anc  b  q  f(coe)  Fvds  beta  MAD  Dang  Drats  Nptrm  Grade  R  MD%  sigma  ThetaMax DeltaMax GammaMax\n"
        pars_out= (s,(pars["measurement_step_min"]),(pars["measurement_step_max"]),(pars["specimen_int_n"]),1e6*(pars["specimen_lab_field_dc"]),1e6*(pars["specimen_int"]),pars["specimen_b"],pars["specimen_q"],pars["specimen_f"],pars["specimen_fvds"],pars["specimen_b_beta"],pars["specimen_int_mad"],pars["specimen_int_dang"],pars["specimen_drats"],pars["specimen_int_ptrm_n"],pars["specimen_grade"],numpy.sqrt(pars["specimen_rsc"]),int(pars["specimen_md"]), pars["specimen_b_sigma"],pars["specimen_theta"],pars["specimen_delta"],pars["specimen_gamma"])
        outstring= '%s %4.0f %4.0f %i %4.1f %4.1f %5.3f %5.1f %5.3f %5.3f %5.3f  %7.1f %7.1f %7.1f %s %s %6.3f %i %5.3f %7.1f %7.1f %7.1f' % pars_out +'\n'               
    if pars["specimen_grade"]!="A":
        print '\n killed by:'
        for k in kill:
            print k,':, criterion set to: ',accept[k],', specimen value: ',pars[k]
        print '\n'
    print outstr
    print outstring
    return pars,kill

def b_vdm(B,lat):
    """ 
    Converts field values in tesla to v(a)dm in Am^2
    """
    rad=numpy.pi/180.
    fact=((6.371e6)**3)*1e7 # changed radius of the earth from 3.367e6 3/12/2010
    colat=(90.-lat) * rad
    return fact*B/(numpy.sqrt(1+3*(numpy.cos(colat)**2)))

def vdm_b(vdm,lat):
    """ 
    Converts v(a)dm to  field values in tesla 
    """
    rad=numpy.pi/180.
    fact=((6.371e6)**3)*1e7 # changed radius of the earth from 3.367e6 3/12/2010
    colat=(90.-lat) * rad
    return vdm*(numpy.sqrt(1+3*(numpy.cos(colat)**2)))/fact

def binglookup(w1i,w2i):
    """
    Bingham statistics lookup table.
    """ 
    K={'0.06': {'0.02': ['-25.58', '-8.996'], '0.06': ['-9.043', '-9.043'], '0.04': ['-13.14', '-9.019']}, '0.22': {'0.08': ['-6.944', '-2.644'], '0.02': ['-25.63', '-2.712'], '0.20': ['-2.649', '-2.354'], '0.06': [ '-9.027', '-2.673'], '0.04': ['-13.17', '-2.695'], '0.14': ['-4.071', '-2.521'], '0.16': ['-3.518', '-2.470'], '0.10': ['-5.658', '-2.609'], '0.12': ['-4.757', '-2.568'], '0.18': ['-3.053', '-2.414'], '0.22': ['-2.289', '-2.289']}, '0.46': {'0.02': ['-25.12', '-0.250'], '0.08': ['-6.215', '0.000'], '0.06': ['-8.371', '-0.090'], '0.04': ['-12.58', '-0.173']}, '0.44': {'0.08': ['-6.305', '-0.186'], '0.02': ['-25.19', '-0.418'], '0.06': ['-8.454', '-0.270'], '0.04': ['-12.66', '-0.347'], '0.10': ['-4.955', '-0.097'], '0.12': ['-3.992', '0.000']}, '0.42': {'0.08': ['-6.388', '-0.374'], '0.02': ['-25.5', '-0.589'], '0.06': [ '-8.532', '-0.452'], '0.04': ['-12.73', '-0.523'], '0.14': ['-3.349', '-0.104'], '0.16': ['-2.741', '0.000'], '0.10': ['-5.045', '-0.290'], '0.12': ['-4.089', '-0.200']}, '0.40': {'0.08': ['-6.466', '-0.564'], '0.02': ['-25.31', '-0.762'], '0.20': ['-1.874', '-0.000'], '0.06': ['-8.604', '-0.636'], '0.04': ['-12.80', '-0.702'], '0.14': ['-3.446', '-0.312'], '0.16': ['-2.845', '-0.215'], '0.10': ['-5.126', '-0.486'] , '0.12': ['-4.179', '-0.402'], '0.18': ['-2.330', '-0.111']}, '0.08': {'0.02': ['-25.6', '-6.977'], '0.08': ['-7.035', '-7.035'], '0.06': ['-9.065', '-7.020'], '0.04': ['-13.16', '-6.999']}, '0.28': {'0.08': ['-6.827', '-1.828'], '0.28': ['-1.106', '-1.106'], '0.02': ['-25.57', '-1.939'], '0.20': ['-2.441', '-1.458'], '0.26': ['-1.406', '-1.203'], '0.24': ['-1.724', '-1.294'], '0.06': ['-8.928', '-1.871'], '0.04': ['-13.09', '-1.908'], '0.14': ['-3.906', '-1.665'], '0.16': ['-3.338', '-1.601'], '0.10': ['-5.523', '-1.779'], '0.12': ['-4.606', '-1.725'], '0.18': ['-2.859', '-1.532'], '0.22': ['-2.066', '-1.378']}, '0.02': {'0.02': ['-25.55','-25.55']}, '0.26': {'0.08': ['-6.870', '-2.078'], '0.02': ['-25.59', '-2.175'], '0.20': ['-2.515', '-1.735'], '0.26': ['-1.497', '-1.497'], '0.24': ['-1.809', '-1.582'], '0.06': ['-8.96 6', '-2.117'], '0.04': ['-13.12', '-2.149'], '0.14': ['-3.965', '-1.929'], '0.16': ['-3.403', '-1.869'], '0.10': ['-5.573', '-2.034'], '0.12': ['-4.661', '-1.984'], '0.18': ['-2.928', '-1.805'], '0.22': ['-2.1 46', '-1.661']}, '0.20': {'0.08': ['-6.974', '-2.973'], '0.02': ['-25.64', '-3.025'], '0.20': ['-2.709', '-2.709'], '0.06': ['-9.05', '-2.997'], '0.04': ['-13.18', '-3.014'], '0.14': ['-4.118', '-2.863'], '0.1 6': ['-3.570', '-2.816'], '0.10': ['-5.694', '-2.942'], '0.12': ['-4.799', '-2.905'], '0.18': ['-3.109', '-2.765']}, '0.04': {'0.02': ['-25.56', '-13.09'], '0.04': ['-13.11', '-13.11']}, '0.14': {'0.08': ['-7.  033', '-4.294'], '0.02': ['-25.64', '-4.295'], '0.06': ['-9.087', '-4.301'], '0.04': ['-13.20', '-4.301'], '0.14': ['-4.231', '-4.231'], '0.10': ['-5.773', '-4.279'], '0.12': ['-4.896', '-4.258']}, '0.16': {'0 .08': ['-7.019', '-3.777'], '0.02': ['-25.65', '-3.796'], '0.06': ['-9.081', '-3.790'], '0.04': ['-13.20', '-3.796'], '0.14': ['-4.198', '-3.697'], '0.16': ['-3.659', '-3.659'], '0.10': ['-5.752', '-3.756'], ' 0.12': ['-4.868', '-3.729']}, '0.10': {'0.02': ['-25.62', '-5.760'], '0.08': ['-7.042', '-5.798'], '0.06': ['-9.080', '-5.791'], '0.10': ['-5.797', '-5.797'], '0.04': ['-13.18', '-5.777']}, '0.12': {'0.08': [' -7.041', '-4.941'], '0.02': ['-25.63', '-4.923'], '0.06': ['-9.087', '-4.941'], '0.04': ['-13.19', '-4.934'], '0.10': ['-5.789', '-4.933'], '0.12': ['-4.917', '-4.917']}, '0.18': {'0.08': ['-6.999', '-3.345'], '0.02': ['-25.65', '-3.381'], '0.06': ['-9.068', '-3.363'], '0.04': ['-13.19', '-3.375'], '0.14': ['-4.160', '-3.249'], '0.16': ['-3.616', '-3.207'], '0.10': ['-5.726', '-3.319'], '0.12': ['-4.836', '-3.287'] , '0.18': ['-3.160', '-3.160']}, '0.38': {'0.08': ['-6.539', '-0.757'], '0.02': ['-25.37', '-0.940'], '0.20': ['-1.986', '-0.231'], '0.24': ['-1.202', '0.000'], '0.06': ['-8.670', '-0.824'], '0.04': ['-12.86', '-0.885'], '0.14': ['-3.536', '-0.522'], '0.16': ['-2.941', '-0.432'], '0.10': ['-5.207', '-0.684'], '0.12': ['-4.263', '-0.606'], '0.18': ['-2.434', '-0.335'], '0.22': ['-1.579', '-0.120']}, '0.36': {'0.08': ['-6.606', '-9.555'], '0.28': ['-0.642', '0.000'], '0.02': ['-25.42', '-1.123'], '0.20': ['-2.089', '-0.464'], '0.26': ['-0.974', '-0.129'], '0.24': ['-1.322', '-0.249'], '0.06': ['-8.731', '-1.017'], '0.04': ['-12.91', '-1.073'], '0.14': ['-3.620', '-0.736'], '0.16': ['-3.032', '-0.651'], '0.10': ['-5.280', '-0.887'], '0.12': ['-4.342', '-0.814'], '0.18': ['-2.531', '-0.561'], '0.22': ['-1.690', '-0.360']}, '0.34 ': {'0.08': ['-6.668', '-1.159'], '0.28': ['-0.771', '-0.269'], '0.02': ['-25.46', '-1.312'], '0.20': ['-2.186', '-0.701'], '0.26': ['-1.094', '-0.389'], '0.24': ['-1.433', '-0.500'], '0.06': ['-8.788', '-1.21 6'], '0.32': ['-0.152', '0.000'], '0.04': ['-12.96', '-1.267'], '0.30': ['-0.459', '-0.140'], '0.14': ['-3.699', '-0.955'], '0.16': ['-3.116', '-0.876'], '0.10': ['-5.348', '-1.096'], '0.12': ['-4.415', '-1.02 8'], '0.18': ['-2.621', '-0.791'], '0.22': ['-1.794', '-0.604']}, '0.32': {'0.08': ['-6.725', '-1.371'], '0.28': ['-0.891', '-0.541'], '0.02': ['-25.50', '-1.510'], '0.20': ['-2.277', '-0.944'], '0.26': ['-1.2 06', '-0.653'], '0.24': ['-1.537', '-0.756'], '0.06': ['-8.839', '-1.423'], '0.32': ['-0.292', '-0.292'], '0.04': ['-13.01', '-1.470'], '0.30': ['-0.588', '-0.421'], '0.14': ['-3.773', '-1.181'], '0.16': ['-3.  195', '-1.108'], '0.10': ['-5.411', '-1.313'], '0.12': ['-4.484', '-1.250'], '0.18': ['-2.706', '-1.028'], '0.22': ['-1.891', '-0.853']}, '0.30': {'0.08': ['-6.778', '-1.596'], '0.28': ['-1.002', '-0.819'], '0 .02': ['-25.54', '-1.718'], '0.20': ['-2.361', '-1.195'], '0.26': ['-1.309', '-0.923'], '0.24': ['-1.634', '-1.020'], '0.06': ['-8.886', '-1.641'], '0.04': ['-13.05', '-1.682'], '0.30': ['-0.708', '-0.708'], ' 0.14': ['-3.842', '-1.417'], '0.16': ['-3.269', '-1.348'], '0.10': ['-5.469', '-1.540'], '0.12': ['-4.547', '-1.481'], '0.18': ['-2.785', '-1.274'], '0.22': ['-1.981', '-1.110']}, '0.24': {'0.08': ['-6.910', ' -2.349'], '0.02': ['-25.61', '-2.431'], '0.20': ['-2.584', '-2.032'], '0.24': ['-1.888', '-1.888'], '0.06': ['-8.999', '-2.382'], '0.04': ['-23.14', '-2.410'], '0.14': ['-4.021', '-2.212'], '0.16': ['-3.463', '-2.157'], '0.10': ['-5.618', '-2.309'], '0.12': ['-4.711', '-2.263'], '0.18': ['-2.993', '-2.097'], '0.22': ['-2.220', '-1.963']}}
    w1,w2=0.,0.
    wstart,incr=0.01,0.02
    if w1i < wstart: w1='%4.2f'%(wstart+incr/2.)
    if w2i < wstart: w2='%4.2f'%(wstart+incr/2.)
    wnext=wstart+incr
    while wstart <0.5:
        if w1i >=wstart and w1i <wnext :  
            w1='%4.2f'%(wstart+incr/2.)
        if w2i >=wstart and w2i <wnext :  
            w2='%4.2f'%(wstart+incr/2.)
        wstart+=incr
        wnext+=incr
    k1,k2=float(K[w2][w1][0]),float(K[w2][w1][1])
    return  k1,k2

def cdfout(data,file):
    """
    spits out the cdf for data to file
    """
    f=open(file,"w")
    data.sort()
    for j in range(len(data)):
        y=float(j)/float(len(data))
        out=str(data[j])+' '+str(y)+ '\n'
        f.write(out)

def dobingham(data):
    """
    gets bingham parameters for data
    """
    control,X,bpars=[],[],{}
    N=len(data)
    if N <2:
       return bpars
#
#  get cartesian coordinates
#
    for rec in data:
        X.append(dir2cart([rec[0],rec[1],1.]))
#
#   put in T matrix
#
    T=numpy.array(Tmatrix(X))
    t,V=tauV(T)
    w1,w2,w3=t[2],t[1],t[0]
    k1,k2=binglookup(w1,w2)
    PDir=cart2dir(V[0])
    EDir=cart2dir(V[1])
    ZDir=cart2dir(V[2])
    if PDir[1] < 0: 
        PDir[0]+=180.
        PDir[1]=-PDir[1]
    PDir[0]=PDir[0]%360. 
    bpars["dec"]=PDir[0]
    bpars["inc"]=PDir[1]
    bpars["Edec"]=EDir[0]
    bpars["Einc"]=EDir[1]
    bpars["Zdec"]=ZDir[0]
    bpars["Zinc"]=ZDir[1]
    bpars["n"]=N
#
#  now for Bingham ellipses.
#
    fac1,fac2=-2*N*(k1)*(w3-w1),-2*N*(k2)*(w3-w2)
    sig31,sig32=numpy.sqrt(1./fac1), numpy.sqrt(1./fac2)
    bpars["Zeta"],bpars["Eta"]=2.45*sig31*180./numpy.pi,2.45*sig32*180./numpy.pi
    return  bpars


def doflip(dec,inc):
   """
   flips lower hemisphere data to upper hemisphere
   """
   if inc <0:
       inc=-inc
       dec=(dec+180.)%360.
   return dec,inc

def doincfish(inc):
    """
    gets fisher mean inc from inc only data
    """
    rad,SCOi,SSOi=numpy.pi/180.,0.,0. # some definitions
    abinc=[]
    for i in inc:abinc.append(abs(i))
    MI,std=gausspars(abinc) # get mean inc and standard deviation
    fpars={}
    N=len(inc)  # number of data
    fpars['n']=N
    fpars['ginc']=MI
    if MI<30:
        fpars['inc']=MI
        fpars['k']=0 
        fpars['alpha95']=0 
        fpars['csd']=0 
        fpars['r']=0 
        print 'WARNING: mean inc < 30, returning gaussian mean'
        return fpars
    for i in inc:  # sum over all incs (but take only positive inc)
        coinc=(90.-abs(i))*rad
        SCOi+= numpy.cos(coinc)
        SSOi+= numpy.sin(coinc)
    Oo=(90.0-MI)*rad # first guess at mean
    SCFlag = -1  # sign change flag
    epsilon = float(N)*numpy.cos(Oo) # RHS of zero equations
    epsilon+= (numpy.sin(Oo)**2-numpy.cos(Oo)**2)*SCOi
    epsilon-= 2.*numpy.sin(Oo)*numpy.cos(Oo)*SSOi
    while SCFlag < 0: # loop until cross zero
        if MI > 0 : Oo-=(.01*rad)  # get steeper
        if MI < 0 : Oo+=(.01*rad)  # get shallower
        prev=epsilon
        epsilon = float(N)*numpy.cos(Oo) # RHS of zero equations
        epsilon+= (numpy.sin(Oo)**2.-numpy.cos(Oo)**2.)*SCOi
        epsilon-= 2.*numpy.sin(Oo)*numpy.cos(Oo)*SSOi
        if abs(epsilon) > abs(prev): MI=-1*MI  # reverse direction
        if epsilon*prev < 0: SCFlag = 1 # changed sign
    S,C=0.,0.  # initialize for summation
    for i in inc:
        coinc=(90.-abs(i))*rad
        S+= numpy.sin(Oo-coinc)
        C+= numpy.cos(Oo-coinc)
    k=(N-1.)/(2.*(N-C))
    Imle=90.-(Oo/rad)
    fpars["inc"]=Imle
    fpars["r"],R=2.*C-N,2*C-N
    fpars["k"]=k
    f=fcalc(2,N-1)
    a95= 1. - (0.5)*(S/C)**2 - (f/(2.*C*k))
#    b=20.**(1./(N-1.)) -1.
#    a=1.-b*(N-R)/R
#    a95=numpy.arccos(a)*180./numpy.pi
    csd=81./numpy.sqrt(k)
    fpars["alpha95"]=a95
    fpars["csd"]=csd
    return fpars

def dokent(data,NN):
    """
    gets Kent  parameters for data
    """
    X,kpars=[],{}
    N=len(data)
    if N <2:
       return kpars
#
#  get fisher mean and convert to co-inclination (theta)/dec (phi) in radians
#
    fpars=fisher_mean(data)
    pbar=fpars["dec"]*numpy.pi/180.
    tbar=(90.-fpars["inc"])*numpy.pi/180.
#
#   initialize matrices
#
    H=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    w=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    b=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    gam=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    xg=[]
#
#  set up rotation matrix H
#
    H=[ [numpy.cos(tbar)*numpy.cos(pbar),-numpy.sin(pbar),numpy.sin(tbar)*numpy.cos(pbar)],[numpy.cos(tbar)*numpy.sin(pbar),numpy.cos(pbar),numpy.sin(pbar)*numpy.sin(tbar)],[-numpy.sin(tbar),0.,numpy.cos(tbar)]]
#
#  get cartesian coordinates of data
#
    for rec in data:
        X.append(dir2cart([rec[0],rec[1],1.]))
#
#   put in T matrix
#
    T=Tmatrix(X)
    for i in range(3):
        for j in range(3):
            T[i][j]=T[i][j]/float(N)
#
# compute B=H'TH
#
    for i in range(3):
        for j in range(3):
            for k in range(3):
                w[i][j]+=T[i][k]*H[k][j]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                b[i][j]+=H[k][i]*w[k][j]
#
# choose a rotation w about North pole to diagonalize upper part of B
#
    psi = 0.5*numpy.arctan(2.*b[0][1]/(b[0][0]-b[1][1]))
    w=[[numpy.cos(psi),-numpy.sin(psi),0],[numpy.sin(psi),numpy.cos(psi),0],[0.,0.,1.]]
    for i in range(3):
        for j in range(3):
            gamtmp=0.
            for k in range(3):
                gamtmp+=H[i][k]*w[k][j]      
            gam[i][j]=gamtmp
    for i in range(N):
        xg.append([0.,0.,0.])
        for k in range(3):  
            xgtmp=0.
            for j in range(3):
                xgtmp+=gam[j][k]*X[i][j]
            xg[i][k]=xgtmp
# compute asymptotic ellipse parameters
#
    xmu,sigma1,sigma2=0.,0.,0.
    for  i in range(N):
        xmu+= xg[i][2]
        sigma1=sigma1+xg[i][1]**2
        sigma2=sigma2+xg[i][0]**2
    xmu=xmu/float(N)
    sigma1=sigma1/float(N)
    sigma2=sigma2/float(N)
    g=-2.0*numpy.log(0.05)/(float(NN)*xmu**2)
    if numpy.sqrt(sigma1*g)<1:zeta=numpy.arcsin(numpy.sqrt(sigma1*g))
    if numpy.sqrt(sigma2*g)<1:eta=numpy.arcsin(numpy.sqrt(sigma2*g))
    if numpy.sqrt(sigma1*g)>=1.:zeta=numpy.pi/2.
    if numpy.sqrt(sigma2*g)>=1.:eta=numpy.pi/2.
#
#  convert Kent parameters to directions,angles
#
    kpars["dec"]=fpars["dec"]
    kpars["inc"]=fpars["inc"]
    kpars["n"]=NN
    ZDir=cart2dir([gam[0][1],gam[1][1],gam[2][1]])
    EDir=cart2dir([gam[0][0],gam[1][0],gam[2][0]])
    kpars["Zdec"]=ZDir[0]
    kpars["Zinc"]=ZDir[1]
    kpars["Edec"]=EDir[0]
    kpars["Einc"]=EDir[1]
    if kpars["Zinc"]<0:
        kpars["Zinc"]=-kpars["Zinc"]
        kpars["Zdec"]=(kpars["Zdec"]+180.)%360.
    if kpars["Einc"]<0:
        kpars["Einc"]=-kpars["Einc"]
        kpars["Edec"]=(kpars["Edec"]+180.)%360.
    kpars["Zeta"]=zeta*180./numpy.pi
    kpars["Eta"]=eta*180./numpy.pi
    return kpars


def doprinc(data):
    """
    gets principal components from data
    """
    ppars={}
    rad=numpy.pi/180.
    X=dir2cart(data)
    #for rec in data:
    #    dir=[]
    #    for c in rec: dir.append(c)
    #    cart= (dir2cart(dir))
    #    X.append(cart)
#   put in T matrix
#
    T=numpy.array(Tmatrix(X))
#
#   get sorted evals/evects
#
    t,V=tauV(T)
    Pdir=cart2dir(V[0])
    ppars['Edir']=cart2dir(V[1]) # elongation direction
    dec,inc=doflip(Pdir[0],Pdir[1])
    ppars['dec']=dec
    ppars['inc']=inc
    ppars['N']=len(data)
    ppars['tau1']=t[0]
    ppars['tau2']=t[1]
    ppars['tau3']=t[2]
    Pdir=cart2dir(V[1])
    dec,inc=doflip(Pdir[0],Pdir[1])
    ppars['V2dec']=dec
    ppars['V2inc']=inc
    Pdir=cart2dir(V[2])
    dec,inc=doflip(Pdir[0],Pdir[1])
    ppars['V3dec']=dec
    ppars['V3inc']=inc
    return ppars


def PTrot(EP,Lats,Lons):
    """ Does rotation of points on a globe  by finite rotations, using method of Cox and Hart 1986, box 7-3. """
# gets user input of Rotation pole lat,long, omega for plate and converts to radians
    E=dir2cart([EP[1],EP[0],1.])
    omega=EP[2]*numpy.pi/180.
    RLats,RLons=[],[]
    for k in range(len(Lats)):
      if Lats[k]<=90.: # peel off delimiters
# converts to rotation pole to cartesian coordinates
        A=dir2cart([Lons[k],Lats[k],1.])
# defines cartesian coordinates of the pole A
        R=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
        R[0][0]=E[0]*E[0]*(1-numpy.cos(omega)) + numpy.cos(omega)
        R[0][1]=E[0]*E[1]*(1-numpy.cos(omega)) - E[2]*numpy.sin(omega)
        R[0][2]=E[0]*E[2]*(1-numpy.cos(omega)) + E[1]*numpy.sin(omega)
        R[1][0]=E[1]*E[0]*(1-numpy.cos(omega)) + E[2]*numpy.sin(omega)
        R[1][1]=E[1]*E[1]*(1-numpy.cos(omega)) + numpy.cos(omega)
        R[1][2]=E[1]*E[2]*(1-numpy.cos(omega)) - E[0]*numpy.sin(omega)
        R[2][0]=E[2]*E[0]*(1-numpy.cos(omega)) - E[1]*numpy.sin(omega)
        R[2][1]=E[2]*E[1]*(1-numpy.cos(omega)) + E[0]*numpy.sin(omega)
        R[2][2]=E[2]*E[2]*(1-numpy.cos(omega)) + numpy.cos(omega)
# sets up rotation matrix
        Ap=[0,0,0]
        for i in range(3):
            for j in range(3):
                Ap[i]+=R[i][j]*A[j]
# does the rotation
        Prot=cart2dir(Ap)
        RLats.append(Prot[1])
        RLons.append(Prot[0])
      else:  # preserve delimiters
        RLats.append(Lats[k])
        RLons.append(Lons[k])
    return RLats,RLons

def dread(infile,cols):
    """
     reads in specimen, tr, dec, inc int into data[].  position of
     tr, dec, inc, int determined by cols[]
    """
    data=[]
    f=open(infile,"rU")
    for line in f.readlines():
        tmp=line.split()
        rec=(tmp[0],float(tmp[cols[0]]),float(tmp[cols[1]]),float(tmp[cols[2]]),
          float(tmp[cols[3]]) )
        data.append(rec)
    return data

def fshdev(k):
    """
    returns a direction from distribution with mean declination of 0, inclination of 90 and kappa of k
    """
    R1=random.random()
    R2=random.random()
    L=numpy.exp(-2*k)
    a=R1*(1-L)+L
    fac=numpy.sqrt((-numpy.log(a))/(2*k))
    inc=90.-2*numpy.arcsin(fac)*180./numpy.pi
    dec=2*numpy.pi*R2*180./numpy.pi
    return dec,inc

def lowes(data):
    """
    gets Lowe's power spectrum from infile - writes to ofile
    """  
    Ls=range(1,9)
    Rs=[]
    recno=0
    for l in Ls:
        pow=0
        for m in range(0,l+1):
            pow+=(l+1)*((1e-3*data[recno][2])**2+(1e-3*data[recno][3])**2)
            recno+=1
        Rs.append(pow)
    return Ls,Rs

def magnetic_lat(inc):
    """
    returns magnetic latitude from inclination
    """
    rad=numpy.pi/180.
    paleo_lat=numpy.arctan( 0.5*numpy.tan(inc*rad))/rad
    return paleo_lat

def check_F(AniSpec):
    s=numpy.zeros((6),'f')
    s[0]=float(AniSpec["anisotropy_s1"])
    s[1]=float(AniSpec["anisotropy_s2"])
    s[2]=float(AniSpec["anisotropy_s3"])
    s[3]=float(AniSpec["anisotropy_s4"])
    s[4]=float(AniSpec["anisotropy_s5"])
    s[5]=float(AniSpec["anisotropy_s6"])
    chibar=(s[0]+s[1]+s[2])/3.
    tau,Vdir=doseigs(s)
    t2sum=0
    for i in range(3): t2sum+=tau[i]**2
    if 'anisotropy_sigma' in AniSpec.keys() and 'anisotropy_n' in AniSpec.keys():
        if AniSpec['anisotropy_type']=='AMS':
            nf=int(AniSpec["anisotropy_n"])-6
        else:
            nf=3*int(AniSpec["anisotropy_n"])-6
        sigma=float(AniSpec["anisotropy_sigma"])
        F=0.4*(t2sum-3*chibar**2)/(sigma**2)
        Fcrit=fcalc(5,nf)
        if F>Fcrit: # anisotropic
            chi=numpy.array([[s[0],s[3],s[5]],[s[3],s[1],s[4]],[s[5],s[4],s[2]]])
            chi_inv=numpy.linalg.inv(chi)
            #trace=chi_inv[0][0]+chi_inv[1][1]+chi_inv[2][2] # don't normalize twice
            #chi_inv=3.*chi_inv/trace
        else: # isotropic
            chi_inv=numpy.array([[1.,0,0],[0,1.,0],[0,0,1.]]) # make anisotropy tensor identity tensor
            chi=chi_inv
    else: # no sigma key available - just do the correction
        print 'WARNING: NO FTEST ON ANISOTROPY PERFORMED BECAUSE OF MISSING SIGMA - DOING CORRECTION ANYWAY'
        chi=numpy.array([[s[0],s[3],s[5]],[s[3],s[1],s[4]],[s[5],s[4],s[2]]])
        chi_inv=numpy.linalg.inv(chi)
    return chi,chi_inv

def Dir_anis_corr(InDir,AniSpec):
    """
    takes the 6 element 's' vector and the Dec,Inc 'InDir' data,
    performs simple anisotropy correction. returns corrected Dec, Inc
    """
    Dir=numpy.zeros((3),'f')
    Dir[0]=InDir[0]
    Dir[1]=InDir[1]
    Dir[2]=1.
    chi,chi_inv=check_F(AniSpec)
    if chi[0][0]==1.:return Dir # isotropic
    X=dir2cart(Dir)
    M=numpy.array(X)
    H=numpy.dot(M,chi_inv)
    return cart2dir(H)

def doaniscorr(PmagSpecRec,AniSpec):
    """
    takes the 6 element 's' vector and the Dec,Inc, Int 'Dir' data,
    performs simple anisotropy correction. returns corrected Dec, Inc, Int
    """
    AniSpecRec={}
    for key in PmagSpecRec.keys():
        AniSpecRec[key]=PmagSpecRec[key]
    Dir=numpy.zeros((3),'f')
    Dir[0]=float(PmagSpecRec["specimen_dec"])
    Dir[1]=float(PmagSpecRec["specimen_inc"])
    Dir[2]=float(PmagSpecRec["specimen_int"])
# check if F test passes!  if anisotropy_sigma available
    chi,chi_inv=check_F(AniSpec)
    if chi[0][0]==1.: # isotropic
        cDir=[Dir[0],Dir[1]] # no change
        newint=Dir[2]
    else:
        X=dir2cart(Dir)
        M=numpy.array(X)
        H=numpy.dot(M,chi_inv)
        cDir= cart2dir(H)
        Hunit=[H[0]/cDir[2],H[1]/cDir[2],H[2]/cDir[2]] # unit vector parallel to Banc
        Zunit=[0,0,-1.] # unit vector parallel to lab field
        Hpar=numpy.dot(chi,Hunit) # unit vector applied along ancient field
        Zpar=numpy.dot(chi,Zunit) # unit vector applied along lab field
        HparInt=cart2dir(Hpar)[2] # intensity of resultant vector from ancient field
        ZparInt=cart2dir(Zpar)[2] # intensity of resultant vector from lab field
        newint=Dir[2]*ZparInt/HparInt
        if cDir[0]-Dir[0]>90:
            cDir[1]=-cDir[1]
            cDir[0]=(cDir[0]-180.)%360.
    AniSpecRec["specimen_dec"]='%7.1f'%(cDir[0])
    AniSpecRec["specimen_inc"]='%7.1f'%(cDir[1])
    AniSpecRec["specimen_int"]='%9.4e'%(newint)
    AniSpecRec["specimen_correction"]='c'
    if 'magic_method_codes' in AniSpecRec.keys():
        methcodes=AniSpecRec["magic_method_codes"]
    else:
        methcodes=""
    if methcodes=="": methcodes="DA-AC-"+AniSpec['anisotropy_type']
    if methcodes!="": methcodes=methcodes+":DA-AC-"+AniSpec['anisotropy_type']
    if chi[0][0]==1.: # isotropic 
        methcodes= methcodes+':DA-AC-ISO' # indicates anisotropy was checked and no change necessary
    AniSpecRec["magic_method_codes"]=methcodes.strip(":")
    return AniSpecRec

def vfunc(pars_1,pars_2):
    """
    returns 2*(Sw-Rw) for Watson's V
    """
    cart_1=dir2cart([pars_1["dec"],pars_1["inc"],pars_1["r"]])
    cart_2=dir2cart([pars_2['dec'],pars_2['inc'],pars_2["r"]])
    Sw=pars_1['k']*pars_1['r']+pars_2['k']*pars_2['r'] # k1*r1+k2*r2
    xhat_1=pars_1['k']*cart_1[0]+pars_2['k']*cart_2[0] # k1*x1+k2*x2
    xhat_2=pars_1['k']*cart_1[1]+pars_2['k']*cart_2[1] # k1*y1+k2*y2
    xhat_3=pars_1['k']*cart_1[2]+pars_2['k']*cart_2[2] # k1*z1+k2*z2
    Rw=numpy.sqrt(xhat_1**2+xhat_2**2+xhat_3**2)
    return 2*(Sw-Rw)

def vgp_di(plat,plong,slat,slong):
    """
    returns direction for a given observation site from a Virtual geomagnetic pole
    """
    rad,signdec=numpy.pi/180.,1.
    delphi=abs(plong-slong)
    if delphi!=0:signdec=(plong-slong)/delphi
    if slat==90.:slat=89.99
    thetaS=(90.-slat)*rad
    thetaP=(90.-plat)*rad
    delphi=delphi*rad
    cosp=numpy.cos(thetaS)*numpy.cos(thetaP)+numpy.sin(thetaS)*numpy.sin(thetaP)*numpy.cos(delphi)
    thetaM=numpy.arccos(cosp)
    cosd=(numpy.cos(thetaP)-numpy.cos(thetaM)*numpy.cos(thetaS))/(numpy.sin(thetaM)*numpy.sin(thetaS))
    C=abs(1.-cosd**2)
    if C!=0:
         dec=-numpy.arctan(cosd/numpy.sqrt(abs(C)))+numpy.pi/2.
    else:  
        dec=numpy.arccos(cosd)
    if -numpy.pi<signdec*delphi and signdec<0: dec=2.*numpy.pi-dec  # checking quadrant 
    if signdec*delphi> numpy.pi: dec=2.*numpy.pi-dec
    dec=(dec/rad)%360.
    inc=(numpy.arctan2(2.*numpy.cos(thetaM),numpy.sin(thetaM)))/rad
    return  dec,inc

def watsonsV(Dir1,Dir2):
    """
    calculates Watson's V statistic for two sets of directions
    """
    counter,NumSims=0,500
#
# first calculate the fisher means and cartesian coordinates of each set of Directions
#
    pars_1=fisher_mean(Dir1)
    pars_2=fisher_mean(Dir2)
#
# get V statistic for these
#
    V=vfunc(pars_1,pars_2)
#
# do monte carlo simulation of datasets with same kappas, but common mean
# 
    Vp=[] # set of Vs from simulations
    print "Doing ",NumSims," simulations"
    for k in range(NumSims):
        counter+=1
        if counter==50:
            print k+1
            counter=0
        Dirp=[]
# get a set of N1 fisher distributed vectors with k1, calculate fisher stats
        for i in range(pars_1["n"]):
            Dirp.append(fshdev(pars_1["k"]))
        pars_p1=fisher_mean(Dirp)
# get a set of N2 fisher distributed vectors with k2, calculate fisher stats
        Dirp=[]
        for i in range(pars_2["n"]):
            Dirp.append(fshdev(pars_2["k"]))
        pars_p2=fisher_mean(Dirp)
# get the V for these
        Vk=vfunc(pars_p1,pars_p2)
        Vp.append(Vk)
#
# sort the Vs, get Vcrit (95th one)
#
    Vp.sort()
    k=int(.95*NumSims)
    return V,Vp[k]


def dimap(D,I):
    """
    FUNCTION TO MAP DECLINATION, INCLINATIONS INTO EQUAL AREA PROJECTION, X,Y

    Usage:     dimap(D, I)
    Argin:     Declination (float) and Inclination (float)

    """
### DEFINE FUNCTION VARIABLES
    XY=[0.,0.]                                     # initialize equal area projection x,y

### GET CARTESIAN COMPONENTS OF INPUT DIRECTION
    X=dir2cart([D,I,1.])

### CHECK IF Z = 1 AND ABORT
    if X[2] ==1.0: return XY                       # return [0,0]

### TAKE THE ABSOLUTE VALUE OF Z
    if X[2]<0:X[2]=-X[2]                           # this only works on lower hemisphere projections

### CALCULATE THE X,Y COORDINATES FOR THE EQUAL AREA PROJECTION
    R=numpy.sqrt( 1.-X[2])/(numpy.sqrt(X[0]**2+X[1]**2)) # from Collinson 1983
    XY[1],XY[0]=X[0]*R,X[1]*R

### RETURN XY[X,Y]
    return XY

def dimap_V(D,I):
    """
    FUNCTION TO MAP DECLINATION, INCLINATIONS INTO EQUAL AREA PROJECTION, X,Y

    Usage:     dimap_V(D, I)
        D and I are both numpy arrays

    """
### GET CARTESIAN COMPONENTS OF INPUT DIRECTION
    DI=numpy.array([D,I]).transpose() # 
    X=dir2cart(DI).transpose()
### CALCULATE THE X,Y COORDINATES FOR THE EQUAL AREA PROJECTION
    R=numpy.sqrt( 1.-abs(X[2]))/(numpy.sqrt(X[0]**2+X[1]**2)) # from Collinson 1983
    XY=numpy.array([X[1]*R,X[0]*R]).transpose()

### RETURN XY[X,Y]
    return XY

def getmeths(method_type):
    """
    returns MagIC  method codes available for a given type
    """
    meths=[]
    if method_type=='GM':
        meths.append('GM-PMAG-APWP')
        meths.append('GM-ARAR')
        meths.append('GM-ARAR-AP')
        meths.append('GM-ARAR-II')
        meths.append('GM-ARAR-NI')
        meths.append('GM-ARAR-TF')
        meths.append('GM-CC-ARCH')
        meths.append('GM-CC-ARCHMAG')
        meths.append('GM-C14')
        meths.append('GM-FOSSIL')
        meths.append('GM-FT')
        meths.append('GM-INT-L')
        meths.append('GM-INT-S')
        meths.append('GM-ISO')
        meths.append('GM-KAR')
        meths.append('GM-PMAG-ANOM')
        meths.append('GM-PMAG-POL')
        meths.append('GM-PBPB')
        meths.append('GM-RATH')
        meths.append('GM-RBSR')
        meths.append('GM-RBSR-I')
        meths.append('GM-RBSR-MA')
        meths.append('GM-SMND')
        meths.append('GM-SMND-I')
        meths.append('GM-SMND-MA')
        meths.append('GM-CC-STRAT')
        meths.append('GM-LUM-TH')
        meths.append('GM-UPA')
        meths.append('GM-UPB')
        meths.append('GM-UTH')
        meths.append('GM-UTHHE')
    else: pass 
    return meths

def first_up(ofile,Rec,file_type): 
    """
    writes the header for a MagIC template file
    """
    keylist=[]
    pmag_out=open(ofile,'a')
    outstring="tab \t"+file_type+"\n"
    pmag_out.write(outstring)
    keystring=""
    for key in Rec.keys():
        keystring=keystring+'\t'+key
        keylist.append(key)
    keystring=keystring + '\n'
    pmag_out.write(keystring[1:])
    pmag_out.close()
    return keylist

def average_int(data,keybase,outkey): # returns dictionary with average intensities from list of arbitrary dictinaries.
    Ints,DataRec=[],{}
    for r in data:Ints.append(float(r[keybase+'_int']))
    if len(Ints)>1:
        b,sig=gausspars(Ints)
        sigperc=100.*sig/b
        DataRec[outkey+"_int_sigma"]='%8.3e '% (sig)
        DataRec[outkey+"_int_sigma_perc"]='%5.1f '%(sigperc)
    else: # if only one, just copy over specimen data
        b=Ints[0]
        DataRec[outkey+"_int_sigma"]=''
        DataRec[outkey+"_int_sigma_perc"]=''
    DataRec[outkey+"_int"]='%8.3e '%(b)
    DataRec[outkey+"_int_n"]='%i '% (len(data))
    return DataRec
 
def get_age(Rec,sitekey,keybase,Ages,DefaultAge):
    """
    finds the age record for a given site
    """
    site=Rec[sitekey]
    gotone=0
    if len(Ages)>0:
        for agerec in Ages:
            if agerec["er_site_name"]==site:
                if "age" in agerec.keys() and agerec["age"]!="":
                    Rec[keybase+"age"]=agerec["age"]
                    gotone=1
                if "age_unit" in agerec.keys(): Rec[keybase+"age_unit"]=agerec["age_unit"]
                if "age_sigma" in agerec.keys(): Rec[keybase+"age_sigma"]=agerec["age_sigma"]
    if gotone==0 and len(DefaultAge)>1:
        sigma=0.5*(float(DefaultAge[1])-float(DefaultAge[0]))
        age=float(DefaultAge[0])+sigma
        Rec[keybase+"age"]= '%10.4e'%(age)
        Rec[keybase+"age_sigma"]= '%10.4e'%(sigma)
        Rec[keybase+"age_unit"]=DefaultAge[2]
    return Rec
#
def adjust_ages(AgesIn):
    """
    Function to adjust ages to a common age_unit
    """
# get a list of age_units first
    age_units,AgesOut,factors,factor,maxunit,age_unit=[],[],[],1,1,"Ma"
    for agerec in AgesIn:
        if agerec[1] not in age_units:
            age_units.append(agerec[1])
            if agerec[1]=="Ga":
                factors.append(1e9)
                maxunit,age_unit,factor=1e9,"Ga",1e9
            if agerec[1]=="Ma":
                if maxunit==1:maxunit,age_unt,factor=1e6,"Ma",1e6
                factors.append(1e6)
            if agerec[1]=="Ka":
                factors.append(1e3)
                if maxunit==1:maxunit,age_unit,factor=1e3,"Ka",1e3
            if "Years" in agerec[1].split():factors.append(1)
    if len(age_units)==1: # all ages are of same type
        for agerec in AgesIn: 
            AgesOut.append(agerec[0])
    elif len(age_units)>1:
        for agerec in AgesIn:  # normalize all to largest age unit
            if agerec[1]=="Ga":AgesOut.append(agerec[0]*1e9/factor)
            if agerec[1]=="Ma":AgesOut.append(agerec[0]*1e6/factor)
            if agerec[1]=="Ka":AgesOut.append(agerec[0]*1e3/factor)
            if "Years" in agerec[1].split():
                if agerec[1]=="Years BP":AgesOut.append(agerec[0]/factor)
                if agerec[1]=="Years Cal BP":AgesOut.append(agerec[0]/factor)
                if agerec[1]=="Years AD (+/-)":AgesOut.append((1950-agerec[0])/factor) # convert to years BP first
                if agerec[1]=="Years Cal AD (+/-)":AgesOut.append((1950-agerec[0])/factor)
    return AgesOut,age_unit
#
def gaussdev(mean,sigma):
    """
    returns a number randomly drawn from a gaussian distribution with the given mean, sigma
    """
    return random.normal(mean,sigma) # return gaussian deviate
#
def get_unf(N):
#
# subroutine to retrieve N uniformly distributed directions
# using Fisher et al. (1987) way.
#
# get uniform directions  [dec,inc]
    z=random.uniform(-1.,1.,size=N)
    t=random.uniform(0.,360.,size=N) # decs
    i=numpy.arcsin(z)*180./numpy.pi # incs
    return numpy.array([t,i]).transpose()

#def get_unf(N): #Jeff's way
#    """
#     subroutine to retrieve N uniformly distributed directions
#    """
#    nmax,k=5550,66   # initialize stuff for uniform distribution
#    di,xn,yn,zn=[],[],[],[]
##
## get uniform direcctions (x,y,z)
#    for  i in range(1,k):
#        m = int(2*float(k)*numpy.sin(numpy.pi*float(i)/float(k)))
#        for j in range(m):
#            x=numpy.sin(numpy.pi*float(i)/float(k))*numpy.cos(2.*numpy.pi*float(j)/float(m))
#            y=numpy.sin(numpy.pi*float(i)/float(k))*numpy.sin(2.*numpy.pi*float(j)/float(m))
#            z=numpy.cos(numpy.pi*float(i)/float(k))
#            r=numpy.sqrt(x**2+y**2+z**2)
#            xn.append(x/r)      
#            yn.append(y/r)       
#            zn.append(z/r) 
##
## select N random phi/theta from unf dist.
#
#    while len(di)<N:
#        ind=random.randint(0,len(xn)-1)
#        dir=cart2dir((xn[ind],yn[ind],zn[ind]))
#        di.append([dir[0],dir[1]])
#    return di 
##
def s2a(s):
    """
     convert 6 element "s" list to 3,3 a matrix (see Tauxe 1998)
    """
    a=numpy.zeros((3,3,),'f') # make the a matrix
    for i in range(3):
        a[i][i]=s[i]
    a[0][1],a[1][0]=s[3],s[3]
    a[1][2],a[2][1]=s[4],s[4]
    a[0][2],a[2][0]=s[5],s[5]
    return a
#
def a2s(a):
    """
     convert 3,3 a matrix to 6 element "s" list  (see Tauxe 1998)
    """
    s=numpy.zeros((6,),'f') # make the a matrix
    for i in range(3):
        s[i]=a[i][i]
    s[3]=a[0][1]
    s[4]=a[1][2]
    s[5]=a[0][2]
    return s

def doseigs(s):
    """
    convert s format for eigenvalues and eigenvectors
    """
#
    A=s2a(s) # convert s to a (see Tauxe 1998)
    tau,V=tauV(A) # convert to eigenvalues (t), eigenvectors (V)
    Vdirs=[]
    for v in V: # convert from cartesian to direction
        Vdir= cart2dir(v)
        if Vdir[1]<0:
            Vdir[1]=-Vdir[1]
            Vdir[0]=(Vdir[0]+180.)%360.
        Vdirs.append([Vdir[0],Vdir[1]])
    return tau,Vdirs
#
#
def doeigs_s(tau,Vdirs):
    """
     get elements of s from eigenvaulues - note that this is very unstable
    """
#
    V=[]
    t=numpy.zeros((3,3,),'f') # initialize the tau diagonal matrix
    for j in range(3): t[j][j]=tau[j] # diagonalize tau
    for k in range(3):
        V.append(dir2cart([Vdirs[k][0],Vdirs[k][1],1.0]))
    V=numpy.transpose(V)
    tmp=numpy.dot(V,t)
    chi=numpy.dot(tmp,numpy.transpose(V))
    return a2s(chi)
#
#
def fcalc(col,row):
    """
  looks up f from ftables F(row,col), where row is number of degrees of freedom - this is 95% confidence (p=0.05)
    """
#
    if row>200:row=200
    if col>20:col=20
    ftest=numpy.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
[1, 161.469, 199.493, 215.737, 224.5, 230.066, 234.001, 236.772, 238.949, 240.496, 241.838, 242.968, 243.88, 244.798, 245.26, 245.956, 246.422, 246.89, 247.36, 247.596, 248.068],
[2, 18.5128, 18.9995, 19.1642, 19.2467, 19.2969, 19.3299, 19.3536, 19.371, 19.3852, 19.3963, 19.4043, 19.4122, 19.4186, 19.425, 19.4297, 19.4329, 19.4377, 19.4409, 19.4425, 19.4457],
[3, 10.1278, 9.5522, 9.2767, 9.1173, 9.0133, 8.9408, 8.8868, 8.8452, 8.8124, 8.7857, 8.7635, 8.7446, 8.7287, 8.715, 8.7028, 8.6923, 8.683, 8.6745, 8.667, 8.6602],
[4, 7.7087, 6.9444, 6.5915, 6.3882, 6.2561, 6.1631, 6.0943, 6.0411, 5.9988, 5.9644, 5.9359, 5.9117, 5.8912, 5.8733, 5.8578, 5.844, 5.8319, 5.8211, 5.8113, 5.8025],
[5, 6.608, 5.7861, 5.4095, 5.1922, 5.0503, 4.9503, 4.8759, 4.8184, 4.7725, 4.735, 4.7039, 4.6777, 4.6552, 4.6358, 4.6187, 4.6038, 4.5904, 4.5785, 4.5679, 4.5581],
[6, 5.9874, 5.1433, 4.757, 4.5337, 4.3874, 4.2838, 4.2067, 4.1468, 4.099, 4.06, 4.0275, 3.9999, 3.9764, 3.956, 3.9381, 3.9223, 3.9083, 3.8957, 3.8844, 3.8742],
[7, 5.5914, 4.7374, 4.3469, 4.1204, 3.9715, 3.866, 3.787, 3.7257, 3.6767, 3.6366, 3.603, 3.5747, 3.5504, 3.5292, 3.5107, 3.4944, 3.4799, 3.4669, 3.4552, 3.4445],
[8, 5.3177, 4.459, 4.0662, 3.8378, 3.6875, 3.5806, 3.5004, 3.4381, 3.3881, 3.3472, 3.313, 3.2839, 3.259, 3.2374, 3.2184, 3.2017, 3.1867, 3.1733, 3.1613, 3.1503],
[9, 5.1174, 4.2565, 3.8626, 3.6331, 3.4817, 3.3738, 3.2928, 3.2296, 3.1789, 3.1373, 3.1025, 3.0729, 3.0475, 3.0255, 3.0061, 2.989, 2.9737, 2.96, 2.9476, 2.9365],
[10, 4.9647, 4.1028, 3.7083, 3.4781, 3.3258, 3.2171, 3.1355, 3.0717, 3.0204, 2.9782, 2.9429, 2.913, 2.8872, 2.8648, 2.845, 2.8276, 2.812, 2.7981, 2.7855, 2.774],
[11, 4.8443, 3.9823, 3.5875, 3.3567, 3.2039, 3.0946, 3.0123, 2.948, 2.8962, 2.8536, 2.8179, 2.7876, 2.7614, 2.7386, 2.7186, 2.7009, 2.6851, 2.6709, 2.6581, 2.6464],
[12, 4.7472, 3.8853, 3.4903, 3.2592, 3.1059, 2.9961, 2.9134, 2.8486, 2.7964, 2.7534, 2.7173, 2.6866, 2.6602, 2.6371, 2.6169, 2.5989, 2.5828, 2.5684, 2.5554, 2.5436],
[13, 4.6672, 3.8055, 3.4106, 3.1791, 3.0255, 2.9153, 2.8321, 2.7669, 2.7144, 2.6711, 2.6347, 2.6037, 2.5769, 2.5536, 2.5331, 2.5149, 2.4987, 2.4841, 2.4709, 2.4589],
[14, 4.6001, 3.7389, 3.3439, 3.1122, 2.9582, 2.8477, 2.7642, 2.6987, 2.6458, 2.6021, 2.5655, 2.5343, 2.5073, 2.4837, 2.463, 2.4446, 2.4282, 2.4134, 2.4, 2.3879],
[15, 4.543, 3.6824, 3.2874, 3.0555, 2.9013, 2.7905, 2.7066, 2.6408, 2.5877, 2.5437, 2.5068, 2.4753, 2.4481, 2.4244, 2.4034, 2.3849, 2.3683, 2.3533, 2.3398, 2.3275],
[16, 4.494, 3.6337, 3.2389, 3.0069, 2.8524, 2.7413, 2.6572, 2.5911, 2.5377, 2.4935, 2.4564, 2.4247, 2.3973, 2.3733, 2.3522, 2.3335, 2.3167, 2.3016, 2.288, 2.2756],
[17, 4.4513, 3.5916, 3.1968, 2.9647, 2.81, 2.6987, 2.6143, 2.548, 2.4943, 2.4499, 2.4126, 2.3807, 2.3531, 2.329, 2.3077, 2.2888, 2.2719, 2.2567, 2.2429, 2.2303],
[18, 4.4139, 3.5546, 3.1599, 2.9278, 2.7729, 2.6613, 2.5767, 2.5102, 2.4563, 2.4117, 2.3742, 2.3421, 2.3143, 2.29, 2.2686, 2.2496, 2.2325, 2.2172, 2.2033, 2.1906],
[19, 4.3808, 3.5219, 3.1274, 2.8951, 2.7401, 2.6283, 2.5435, 2.4768, 2.4227, 2.378, 2.3402, 2.308, 2.28, 2.2556, 2.2341, 2.2149, 2.1977, 2.1823, 2.1683, 2.1555],
[20, 4.3512, 3.4928, 3.0984, 2.8661, 2.7109, 2.599, 2.514, 2.4471, 2.3928, 2.3479, 2.31, 2.2776, 2.2495, 2.2249, 2.2033, 2.184, 2.1667, 2.1511, 2.137, 2.1242],
[21, 4.3248, 3.4668, 3.0725, 2.8401, 2.6848, 2.5727, 2.4876, 2.4205, 2.3661, 2.3209, 2.2829, 2.2504, 2.2222, 2.1975, 2.1757, 2.1563, 2.1389, 2.1232, 2.109, 2.096],
[22, 4.3009, 3.4434, 3.0492, 2.8167, 2.6613, 2.5491, 2.4638, 2.3965, 2.3419, 2.2967, 2.2585, 2.2258, 2.1975, 2.1727, 2.1508, 2.1313, 2.1138, 2.098, 2.0837, 2.0707],
[23, 4.2794, 3.4221, 3.028, 2.7955, 2.64, 2.5276, 2.4422, 2.3748, 2.3201, 2.2747, 2.2364, 2.2036, 2.1752, 2.1503, 2.1282, 2.1086, 2.091, 2.0751, 2.0608, 2.0476],
[24, 4.2597, 3.4029, 3.0088, 2.7763, 2.6206, 2.5082, 2.4226, 2.3551, 2.3003, 2.2547, 2.2163, 2.1834, 2.1548, 2.1298, 2.1077, 2.088, 2.0703, 2.0543, 2.0399, 2.0267],
[25, 4.2417, 3.3852, 2.9913, 2.7587, 2.603, 2.4904, 2.4047, 2.3371, 2.2821, 2.2365, 2.1979, 2.1649, 2.1362, 2.1111, 2.0889, 2.0691, 2.0513, 2.0353, 2.0207, 2.0075],
[26, 4.2252, 3.369, 2.9752, 2.7426, 2.5868, 2.4741, 2.3883, 2.3205, 2.2655, 2.2197, 2.1811, 2.1479, 2.1192, 2.094, 2.0716, 2.0518, 2.0339, 2.0178, 2.0032, 1.9898],
[27, 4.21, 3.3542, 2.9603, 2.7277, 2.5719, 2.4591, 2.3732, 2.3053, 2.2501, 2.2043, 2.1656, 2.1323, 2.1035, 2.0782, 2.0558, 2.0358, 2.0179, 2.0017, 1.987, 1.9736],
[28, 4.196, 3.3404, 2.9467, 2.7141, 2.5581, 2.4453, 2.3592, 2.2913, 2.236, 2.1901, 2.1512, 2.1179, 2.0889, 2.0636, 2.0411, 2.021, 2.0031, 1.9868, 1.972, 1.9586],
[29, 4.1829, 3.3276, 2.9341, 2.7014, 2.5454, 2.4324, 2.3463, 2.2783, 2.2229, 2.1768, 2.1379, 2.1045, 2.0755, 2.05, 2.0275, 2.0074, 1.9893, 1.973, 1.9582, 1.9446],
[30, 4.1709, 3.3158, 2.9223, 2.6896, 2.5335, 2.4205, 2.3343, 2.2662, 2.2107, 2.1646, 2.1255, 2.0921, 2.0629, 2.0374, 2.0148, 1.9946, 1.9765, 1.9601, 1.9452, 1.9317],
[31, 4.1597, 3.3048, 2.9113, 2.6787, 2.5225, 2.4094, 2.3232, 2.2549, 2.1994, 2.1531, 2.1141, 2.0805, 2.0513, 2.0257, 2.003, 1.9828, 1.9646, 1.9481, 1.9332, 1.9196],
[32, 4.1491, 3.2945, 2.9011, 2.6684, 2.5123, 2.3991, 2.3127, 2.2444, 2.1888, 2.1425, 2.1033, 2.0697, 2.0404, 2.0147, 1.992, 1.9717, 1.9534, 1.9369, 1.9219, 1.9083],
[33, 4.1392, 3.2849, 2.8915, 2.6589, 2.5027, 2.3894, 2.303, 2.2346, 2.1789, 2.1325, 2.0933, 2.0596, 2.0302, 2.0045, 1.9817, 1.9613, 1.943, 1.9264, 1.9114, 1.8977],
[34, 4.13, 3.2759, 2.8826, 2.6499, 2.4936, 2.3803, 2.2938, 2.2253, 2.1696, 2.1231, 2.0838, 2.05, 2.0207, 1.9949, 1.972, 1.9516, 1.9332, 1.9166, 1.9015, 1.8877],
[35, 4.1214, 3.2674, 2.8742, 2.6415, 2.4851, 2.3718, 2.2852, 2.2167, 2.1608, 2.1143, 2.0749, 2.0411, 2.0117, 1.9858, 1.9629, 1.9424, 1.924, 1.9073, 1.8922, 1.8784],
[36, 4.1132, 3.2594, 2.8663, 2.6335, 2.4771, 2.3637, 2.2771, 2.2085, 2.1526, 2.1061, 2.0666, 2.0327, 2.0032, 1.9773, 1.9543, 1.9338, 1.9153, 1.8986, 1.8834, 1.8696],
[37, 4.1055, 3.2519, 2.8588, 2.6261, 2.4696, 2.3562, 2.2695, 2.2008, 2.1449, 2.0982, 2.0587, 2.0248, 1.9952, 1.9692, 1.9462, 1.9256, 1.9071, 1.8904, 1.8752, 1.8613],
[38, 4.0981, 3.2448, 2.8517, 2.619, 2.4625, 2.349, 2.2623, 2.1935, 2.1375, 2.0909, 2.0513, 2.0173, 1.9877, 1.9617, 1.9386, 1.9179, 1.8994, 1.8826, 1.8673, 1.8534],
[39, 4.0913, 3.2381, 2.8451, 2.6123, 2.4558, 2.3422, 2.2555, 2.1867, 2.1306, 2.0839, 2.0442, 2.0102, 1.9805, 1.9545, 1.9313, 1.9107, 1.8921, 1.8752, 1.8599, 1.8459],
[40, 4.0848, 3.2317, 2.8388, 2.606, 2.4495, 2.3359, 2.249, 2.1802, 2.124, 2.0773, 2.0376, 2.0035, 1.9738, 1.9476, 1.9245, 1.9038, 1.8851, 1.8682, 1.8529, 1.8389],
[41, 4.0786, 3.2257, 2.8328, 2.6, 2.4434, 2.3298, 2.2429, 2.174, 2.1178, 2.071, 2.0312, 1.9971, 1.9673, 1.9412, 1.9179, 1.8972, 1.8785, 1.8616, 1.8462, 1.8321],
[42, 4.0727, 3.2199, 2.8271, 2.5943, 2.4377, 2.324, 2.2371, 2.1681, 2.1119, 2.065, 2.0252, 1.991, 1.9612, 1.935, 1.9118, 1.8909, 1.8722, 1.8553, 1.8399, 1.8258],
[43, 4.067, 3.2145, 2.8216, 2.5888, 2.4322, 2.3185, 2.2315, 2.1625, 2.1062, 2.0593, 2.0195, 1.9852, 1.9554, 1.9292, 1.9059, 1.885, 1.8663, 1.8493, 1.8338, 1.8197],
[44, 4.0617, 3.2093, 2.8165, 2.5837, 2.4271, 2.3133, 2.2262, 2.1572, 2.1009, 2.0539, 2.014, 1.9797, 1.9499, 1.9236, 1.9002, 1.8794, 1.8606, 1.8436, 1.8281, 1.8139],
[45, 4.0566, 3.2043, 2.8115, 2.5787, 2.4221, 2.3083, 2.2212, 2.1521, 2.0958, 2.0487, 2.0088, 1.9745, 1.9446, 1.9182, 1.8949, 1.874, 1.8551, 1.8381, 1.8226, 1.8084],
[46, 4.0518, 3.1996, 2.8068, 2.574, 2.4174, 2.3035, 2.2164, 2.1473, 2.0909, 2.0438, 2.0039, 1.9695, 1.9395, 1.9132, 1.8898, 1.8688, 1.85, 1.8329, 1.8173, 1.8031],
[47, 4.0471, 3.1951, 2.8024, 2.5695, 2.4128, 2.299, 2.2118, 2.1427, 2.0862, 2.0391, 1.9991, 1.9647, 1.9347, 1.9083, 1.8849, 1.8639, 1.845, 1.8279, 1.8123, 1.798],
[48, 4.0426, 3.1907, 2.7981, 2.5653, 2.4085, 2.2946, 2.2074, 2.1382, 2.0817, 2.0346, 1.9946, 1.9601, 1.9301, 1.9037, 1.8802, 1.8592, 1.8402, 1.8231, 1.8075, 1.7932],
[49, 4.0384, 3.1866, 2.7939, 2.5611, 2.4044, 2.2904, 2.2032, 2.134, 2.0774, 2.0303, 1.9902, 1.9558, 1.9257, 1.8992, 1.8757, 1.8547, 1.8357, 1.8185, 1.8029, 1.7886],
[50, 4.0343, 3.1826, 2.79, 2.5572, 2.4004, 2.2864, 2.1992, 2.1299, 2.0734, 2.0261, 1.9861, 1.9515, 1.9214, 1.8949, 1.8714, 1.8503, 1.8313, 1.8141, 1.7985, 1.7841],
[51, 4.0303, 3.1788, 2.7862, 2.5534, 2.3966, 2.2826, 2.1953, 2.126, 2.0694, 2.0222, 1.982, 1.9475, 1.9174, 1.8908, 1.8673, 1.8462, 1.8272, 1.8099, 1.7942, 1.7798],
[52, 4.0266, 3.1752, 2.7826, 2.5498, 2.3929, 2.2789, 2.1916, 2.1223, 2.0656, 2.0184, 1.9782, 1.9436, 1.9134, 1.8869, 1.8633, 1.8422, 1.8231, 1.8059, 1.7901, 1.7758],
[53, 4.023, 3.1716, 2.7791, 2.5463, 2.3894, 2.2754, 2.1881, 2.1187, 2.062, 2.0147, 1.9745, 1.9399, 1.9097, 1.8831, 1.8595, 1.8383, 1.8193, 1.802, 1.7862, 1.7718],
[54, 4.0196, 3.1683, 2.7757, 2.5429, 2.3861, 2.272, 2.1846, 2.1152, 2.0585, 2.0112, 1.971, 1.9363, 1.9061, 1.8795, 1.8558, 1.8346, 1.8155, 1.7982, 1.7825, 1.768],
[55, 4.0162, 3.165, 2.7725, 2.5397, 2.3828, 2.2687, 2.1813, 2.1119, 2.0552, 2.0078, 1.9676, 1.9329, 1.9026, 1.876, 1.8523, 1.8311, 1.812, 1.7946, 1.7788, 1.7644],
[56, 4.0129, 3.1618, 2.7694, 2.5366, 2.3797, 2.2656, 2.1781, 2.1087, 2.0519, 2.0045, 1.9642, 1.9296, 1.8993, 1.8726, 1.8489, 1.8276, 1.8085, 1.7912, 1.7753, 1.7608],
[57, 4.0099, 3.1589, 2.7665, 2.5336, 2.3767, 2.2625, 2.1751, 2.1056, 2.0488, 2.0014, 1.9611, 1.9264, 1.896, 1.8693, 1.8456, 1.8244, 1.8052, 1.7878, 1.772, 1.7575],
[58, 4.0069, 3.1559, 2.7635, 2.5307, 2.3738, 2.2596, 2.1721, 2.1026, 2.0458, 1.9983, 1.958, 1.9233, 1.8929, 1.8662, 1.8424, 1.8212, 1.802, 1.7846, 1.7687, 1.7542],
[59, 4.0039, 3.1531, 2.7608, 2.5279, 2.371, 2.2568, 2.1693, 2.0997, 2.0429, 1.9954, 1.9551, 1.9203, 1.8899, 1.8632, 1.8394, 1.8181, 1.7989, 1.7815, 1.7656, 1.751],
[60, 4.0012, 3.1504, 2.7581, 2.5252, 2.3683, 2.254, 2.1665, 2.097, 2.0401, 1.9926, 1.9522, 1.9174, 1.887, 1.8603, 1.8364, 1.8151, 1.7959, 1.7784, 1.7625, 1.748],
[61, 3.9985, 3.1478, 2.7555, 2.5226, 2.3657, 2.2514, 2.1639, 2.0943, 2.0374, 1.9899, 1.9495, 1.9146, 1.8842, 1.8574, 1.8336, 1.8122, 1.793, 1.7755, 1.7596, 1.745],
[62, 3.9959, 3.1453, 2.753, 2.5201, 2.3631, 2.2489, 2.1613, 2.0917, 2.0348, 1.9872, 1.9468, 1.9119, 1.8815, 1.8547, 1.8308, 1.8095, 1.7902, 1.7727, 1.7568, 1.7422],
[63, 3.9934, 3.1428, 2.7506, 2.5176, 2.3607, 2.2464, 2.1588, 2.0892, 2.0322, 1.9847, 1.9442, 1.9093, 1.8789, 1.852, 1.8282, 1.8068, 1.7875, 1.77, 1.754, 1.7394],
[64, 3.9909, 3.1404, 2.7482, 2.5153, 2.3583, 2.244, 2.1564, 2.0868, 2.0298, 1.9822, 1.9417, 1.9068, 1.8763, 1.8495, 1.8256, 1.8042, 1.7849, 1.7673, 1.7514, 1.7368],
[65, 3.9885, 3.1381, 2.7459, 2.513, 2.356, 2.2417, 2.1541, 2.0844, 2.0274, 1.9798, 1.9393, 1.9044, 1.8739, 1.847, 1.8231, 1.8017, 1.7823, 1.7648, 1.7488, 1.7342],
[66, 3.9862, 3.1359, 2.7437, 2.5108, 2.3538, 2.2395, 2.1518, 2.0821, 2.0251, 1.9775, 1.937, 1.902, 1.8715, 1.8446, 1.8207, 1.7992, 1.7799, 1.7623, 1.7463, 1.7316],
[67, 3.9841, 3.1338, 2.7416, 2.5087, 2.3516, 2.2373, 2.1497, 2.0799, 2.0229, 1.9752, 1.9347, 1.8997, 1.8692, 1.8423, 1.8183, 1.7968, 1.7775, 1.7599, 1.7439, 1.7292],
[68, 3.9819, 3.1317, 2.7395, 2.5066, 2.3496, 2.2352, 2.1475, 2.0778, 2.0207, 1.973, 1.9325, 1.8975, 1.867, 1.84, 1.816, 1.7945, 1.7752, 1.7576, 1.7415, 1.7268],
[69, 3.9798, 3.1297, 2.7375, 2.5046, 2.3475, 2.2332, 2.1455, 2.0757, 2.0186, 1.9709, 1.9303, 1.8954, 1.8648, 1.8378, 1.8138, 1.7923, 1.7729, 1.7553, 1.7393, 1.7246],
[70, 3.9778, 3.1277, 2.7355, 2.5027, 2.3456, 2.2312, 2.1435, 2.0737, 2.0166, 1.9689, 1.9283, 1.8932, 1.8627, 1.8357, 1.8117, 1.7902, 1.7707, 1.7531, 1.7371, 1.7223],
[71, 3.9758, 3.1258, 2.7336, 2.5007, 2.3437, 2.2293, 2.1415, 2.0717, 2.0146, 1.9669, 1.9263, 1.8912, 1.8606, 1.8336, 1.8096, 1.7881, 1.7686, 1.751, 1.7349, 1.7202],
[72, 3.9739, 3.1239, 2.7318, 2.4989, 2.3418, 2.2274, 2.1397, 2.0698, 2.0127, 1.9649, 1.9243, 1.8892, 1.8586, 1.8316, 1.8076, 1.786, 1.7666, 1.7489, 1.7328, 1.7181],
[73, 3.9721, 3.1221, 2.73, 2.4971, 2.34, 2.2256, 2.1378, 2.068, 2.0108, 1.9631, 1.9224, 1.8873, 1.8567, 1.8297, 1.8056, 1.784, 1.7646, 1.7469, 1.7308, 1.716],
[74, 3.9703, 3.1204, 2.7283, 2.4954, 2.3383, 2.2238, 2.1361, 2.0662, 2.009, 1.9612, 1.9205, 1.8854, 1.8548, 1.8278, 1.8037, 1.7821, 1.7626, 1.7449, 1.7288, 1.714],
[75, 3.9685, 3.1186, 2.7266, 2.4937, 2.3366, 2.2221, 2.1343, 2.0645, 2.0073, 1.9595, 1.9188, 1.8836, 1.853, 1.8259, 1.8018, 1.7802, 1.7607, 1.7431, 1.7269, 1.7121],
[76, 3.9668, 3.117, 2.7249, 2.4921, 2.3349, 2.2204, 2.1326, 2.0627, 2.0055, 1.9577, 1.917, 1.8819, 1.8512, 1.8241, 1.8, 1.7784, 1.7589, 1.7412, 1.725, 1.7102],
[77, 3.9651, 3.1154, 2.7233, 2.4904, 2.3333, 2.2188, 2.131, 2.0611, 2.0039, 1.956, 1.9153, 1.8801, 1.8494, 1.8223, 1.7982, 1.7766, 1.7571, 1.7394, 1.7232, 1.7084],
[78, 3.9635, 3.1138, 2.7218, 2.4889, 2.3318, 2.2172, 2.1294, 2.0595, 2.0022, 1.9544, 1.9136, 1.8785, 1.8478, 1.8206, 1.7965, 1.7749, 1.7554, 1.7376, 1.7214, 1.7066],
[79, 3.9619, 3.1123, 2.7203, 2.4874, 2.3302, 2.2157, 2.1279, 2.0579, 2.0006, 1.9528, 1.912, 1.8769, 1.8461, 1.819, 1.7948, 1.7732, 1.7537, 1.7359, 1.7197, 1.7048],
[80, 3.9604, 3.1107, 2.7188, 2.4859, 2.3287, 2.2142, 2.1263, 2.0564, 1.9991, 1.9512, 1.9105, 1.8753, 1.8445, 1.8174, 1.7932, 1.7716, 1.752, 1.7342, 1.718, 1.7032],
[81, 3.9589, 3.1093, 2.7173, 2.4845, 2.3273, 2.2127, 2.1248, 2.0549, 1.9976, 1.9497, 1.9089, 1.8737, 1.8429, 1.8158, 1.7916, 1.77, 1.7504, 1.7326, 1.7164, 1.7015],
[82, 3.9574, 3.1079, 2.716, 2.483, 2.3258, 2.2113, 2.1234, 2.0534, 1.9962, 1.9482, 1.9074, 1.8722, 1.8414, 1.8143, 1.7901, 1.7684, 1.7488, 1.731, 1.7148, 1.6999],
[83, 3.956, 3.1065, 2.7146, 2.4817, 2.3245, 2.2099, 2.122, 2.052, 1.9947, 1.9468, 1.906, 1.8707, 1.8399, 1.8127, 1.7886, 1.7669, 1.7473, 1.7295, 1.7132, 1.6983],
[84, 3.9546, 3.1051, 2.7132, 2.4803, 2.3231, 2.2086, 2.1206, 2.0506, 1.9933, 1.9454, 1.9045, 1.8693, 1.8385, 1.8113, 1.7871, 1.7654, 1.7458, 1.728, 1.7117, 1.6968],
[85, 3.9532, 3.1039, 2.7119, 2.479, 2.3218, 2.2072, 2.1193, 2.0493, 1.9919, 1.944, 1.9031, 1.8679, 1.8371, 1.8099, 1.7856, 1.7639, 1.7443, 1.7265, 1.7102, 1.6953],
[86, 3.9519, 3.1026, 2.7106, 2.4777, 2.3205, 2.2059, 2.118, 2.048, 1.9906, 1.9426, 1.9018, 1.8665, 1.8357, 1.8085, 1.7842, 1.7625, 1.7429, 1.725, 1.7088, 1.6938],
[87, 3.9506, 3.1013, 2.7094, 2.4765, 2.3193, 2.2047, 2.1167, 2.0467, 1.9893, 1.9413, 1.9005, 1.8652, 1.8343, 1.8071, 1.7829, 1.7611, 1.7415, 1.7236, 1.7073, 1.6924],
[88, 3.9493, 3.1001, 2.7082, 2.4753, 2.318, 2.2034, 2.1155, 2.0454, 1.9881, 1.94, 1.8992, 1.8639, 1.833, 1.8058, 1.7815, 1.7598, 1.7401, 1.7223, 1.706, 1.691],
[89, 3.9481, 3.0988, 2.707, 2.4741, 2.3169, 2.2022, 2.1143, 2.0442, 1.9868, 1.9388, 1.8979, 1.8626, 1.8317, 1.8045, 1.7802, 1.7584, 1.7388, 1.7209, 1.7046, 1.6896],
[90, 3.9469, 3.0977, 2.7058, 2.4729, 2.3157, 2.2011, 2.1131, 2.043, 1.9856, 1.9376, 1.8967, 1.8613, 1.8305, 1.8032, 1.7789, 1.7571, 1.7375, 1.7196, 1.7033, 1.6883],
[91, 3.9457, 3.0965, 2.7047, 2.4718, 2.3146, 2.1999, 2.1119, 2.0418, 1.9844, 1.9364, 1.8955, 1.8601, 1.8292, 1.802, 1.7777, 1.7559, 1.7362, 1.7183, 1.702, 1.687],
[92, 3.9446, 3.0955, 2.7036, 2.4707, 2.3134, 2.1988, 2.1108, 2.0407, 1.9833, 1.9352, 1.8943, 1.8589, 1.828, 1.8008, 1.7764, 1.7546, 1.735, 1.717, 1.7007, 1.6857],
[93, 3.9435, 3.0944, 2.7025, 2.4696, 2.3123, 2.1977, 2.1097, 2.0395, 1.9821, 1.934, 1.8931, 1.8578, 1.8269, 1.7996, 1.7753, 1.7534, 1.7337, 1.7158, 1.6995, 1.6845],
[94, 3.9423, 3.0933, 2.7014, 2.4685, 2.3113, 2.1966, 2.1086, 2.0385, 1.981, 1.9329, 1.892, 1.8566, 1.8257, 1.7984, 1.7741, 1.7522, 1.7325, 1.7146, 1.6982, 1.6832],
[95, 3.9412, 3.0922, 2.7004, 2.4675, 2.3102, 2.1955, 2.1075, 2.0374, 1.9799, 1.9318, 1.8909, 1.8555, 1.8246, 1.7973, 1.7729, 1.7511, 1.7314, 1.7134, 1.6971, 1.682],
[96, 3.9402, 3.0912, 2.6994, 2.4665, 2.3092, 2.1945, 2.1065, 2.0363, 1.9789, 1.9308, 1.8898, 1.8544, 1.8235, 1.7961, 1.7718, 1.75, 1.7302, 1.7123, 1.6959, 1.6809],
[97, 3.9392, 3.0902, 2.6984, 2.4655, 2.3082, 2.1935, 2.1054, 2.0353, 1.9778, 1.9297, 1.8888, 1.8533, 1.8224, 1.7951, 1.7707, 1.7488, 1.7291, 1.7112, 1.6948, 1.6797],
[98, 3.9381, 3.0892, 2.6974, 2.4645, 2.3072, 2.1925, 2.1044, 2.0343, 1.9768, 1.9287, 1.8877, 1.8523, 1.8213, 1.794, 1.7696, 1.7478, 1.728, 1.71, 1.6936, 1.6786],
[99, 3.9371, 3.0882, 2.6965, 2.4636, 2.3062, 2.1916, 2.1035, 2.0333, 1.9758, 1.9277, 1.8867, 1.8513, 1.8203, 1.7929, 1.7686, 1.7467, 1.7269, 1.709, 1.6926, 1.6775],
[100, 3.9361, 3.0873, 2.6955, 2.4626, 2.3053, 2.1906, 2.1025, 2.0323, 1.9748, 1.9267, 1.8857, 1.8502, 1.8193, 1.7919, 1.7675, 1.7456, 1.7259, 1.7079, 1.6915, 1.6764],
[101, 3.9352, 3.0864, 2.6946, 2.4617, 2.3044, 2.1897, 2.1016, 2.0314, 1.9739, 1.9257, 1.8847, 1.8493, 1.8183, 1.7909, 1.7665, 1.7446, 1.7248, 1.7069, 1.6904, 1.6754],
[102, 3.9342, 3.0854, 2.6937, 2.4608, 2.3035, 2.1888, 2.1007, 2.0304, 1.9729, 1.9248, 1.8838, 1.8483, 1.8173, 1.7899, 1.7655, 1.7436, 1.7238, 1.7058, 1.6894, 1.6744],
[103, 3.9333, 3.0846, 2.6928, 2.4599, 2.3026, 2.1879, 2.0997, 2.0295, 1.972, 1.9238, 1.8828, 1.8474, 1.8163, 1.789, 1.7645, 1.7427, 1.7229, 1.7048, 1.6884, 1.6733],
[104, 3.9325, 3.0837, 2.692, 2.4591, 2.3017, 2.187, 2.0989, 2.0287, 1.9711, 1.9229, 1.8819, 1.8464, 1.8154, 1.788, 1.7636, 1.7417, 1.7219, 1.7039, 1.6874, 1.6723],
[105, 3.9316, 3.0828, 2.6912, 2.4582, 2.3009, 2.1861, 2.098, 2.0278, 1.9702, 1.922, 1.881, 1.8455, 1.8145, 1.7871, 1.7627, 1.7407, 1.7209, 1.7029, 1.6865, 1.6714],
[106, 3.9307, 3.082, 2.6903, 2.4574, 2.3, 2.1853, 2.0971, 2.0269, 1.9694, 1.9212, 1.8801, 1.8446, 1.8136, 1.7862, 1.7618, 1.7398, 1.72, 1.702, 1.6855, 1.6704],
[107, 3.9299, 3.0812, 2.6895, 2.4566, 2.2992, 2.1845, 2.0963, 2.0261, 1.9685, 1.9203, 1.8792, 1.8438, 1.8127, 1.7853, 1.7608, 1.7389, 1.7191, 1.7011, 1.6846, 1.6695],
[108, 3.929, 3.0804, 2.6887, 2.4558, 2.2984, 2.1837, 2.0955, 2.0252, 1.9677, 1.9195, 1.8784, 1.8429, 1.8118, 1.7844, 1.7599, 1.738, 1.7182, 1.7001, 1.6837, 1.6685],
[109, 3.9282, 3.0796, 2.6879, 2.455, 2.2976, 2.1828, 2.0947, 2.0244, 1.9669, 1.9186, 1.8776, 1.8421, 1.811, 1.7835, 1.7591, 1.7371, 1.7173, 1.6992, 1.6828, 1.6676],
[110, 3.9274, 3.0788, 2.6872, 2.4542, 2.2968, 2.1821, 2.0939, 2.0236, 1.9661, 1.9178, 1.8767, 1.8412, 1.8102, 1.7827, 1.7582, 1.7363, 1.7164, 1.6984, 1.6819, 1.6667],
[111, 3.9266, 3.0781, 2.6864, 2.4535, 2.2961, 2.1813, 2.0931, 2.0229, 1.9653, 1.917, 1.8759, 1.8404, 1.8093, 1.7819, 1.7574, 1.7354, 1.7156, 1.6975, 1.681, 1.6659],
[112, 3.9258, 3.0773, 2.6857, 2.4527, 2.2954, 2.1806, 2.0924, 2.0221, 1.9645, 1.9163, 1.8751, 1.8396, 1.8085, 1.7811, 1.7566, 1.7346, 1.7147, 1.6967, 1.6802, 1.665],
[113, 3.9251, 3.0766, 2.6849, 2.452, 2.2946, 2.1798, 2.0916, 2.0213, 1.9637, 1.9155, 1.8744, 1.8388, 1.8077, 1.7803, 1.7558, 1.7338, 1.7139, 1.6958, 1.6793, 1.6642],
[114, 3.9243, 3.0758, 2.6842, 2.4513, 2.2939, 2.1791, 2.0909, 2.0206, 1.963, 1.9147, 1.8736, 1.8381, 1.8069, 1.7795, 1.755, 1.733, 1.7131, 1.695, 1.6785, 1.6633],
[115, 3.9236, 3.0751, 2.6835, 2.4506, 2.2932, 2.1784, 2.0902, 2.0199, 1.9623, 1.914, 1.8729, 1.8373, 1.8062, 1.7787, 1.7542, 1.7322, 1.7123, 1.6942, 1.6777, 1.6625],
[116, 3.9228, 3.0744, 2.6828, 2.4499, 2.2925, 2.1777, 2.0895, 2.0192, 1.9615, 1.9132, 1.8721, 1.8365, 1.8054, 1.7779, 1.7534, 1.7314, 1.7115, 1.6934, 1.6769, 1.6617],
[117, 3.9222, 3.0738, 2.6821, 2.4492, 2.2918, 2.177, 2.0888, 2.0185, 1.9608, 1.9125, 1.8714, 1.8358, 1.8047, 1.7772, 1.7527, 1.7307, 1.7108, 1.6927, 1.6761, 1.6609],
[118, 3.9215, 3.0731, 2.6815, 2.4485, 2.2912, 2.1763, 2.0881, 2.0178, 1.9601, 1.9118, 1.8707, 1.8351, 1.804, 1.7765, 1.752, 1.7299, 1.71, 1.6919, 1.6754, 1.6602],
[119, 3.9208, 3.0724, 2.6808, 2.4479, 2.2905, 2.1757, 2.0874, 2.0171, 1.9594, 1.9111, 1.87, 1.8344, 1.8032, 1.7757, 1.7512, 1.7292, 1.7093, 1.6912, 1.6746, 1.6594],
[120, 3.9202, 3.0718, 2.6802, 2.4472, 2.2899, 2.175, 2.0868, 2.0164, 1.9588, 1.9105, 1.8693, 1.8337, 1.8026, 1.775, 1.7505, 1.7285, 1.7085, 1.6904, 1.6739, 1.6587],
[121, 3.9194, 3.0712, 2.6795, 2.4466, 2.2892, 2.1744, 2.0861, 2.0158, 1.9581, 1.9098, 1.8686, 1.833, 1.8019, 1.7743, 1.7498, 1.7278, 1.7078, 1.6897, 1.6732, 1.6579],
[122, 3.9188, 3.0705, 2.6789, 2.446, 2.2886, 2.1737, 2.0855, 2.0151, 1.9575, 1.9091, 1.868, 1.8324, 1.8012, 1.7736, 1.7491, 1.727, 1.7071, 1.689, 1.6724, 1.6572],
[123, 3.9181, 3.0699, 2.6783, 2.4454, 2.288, 2.1731, 2.0849, 2.0145, 1.9568, 1.9085, 1.8673, 1.8317, 1.8005, 1.773, 1.7484, 1.7264, 1.7064, 1.6883, 1.6717, 1.6565],
[124, 3.9176, 3.0693, 2.6777, 2.4448, 2.2874, 2.1725, 2.0842, 2.0139, 1.9562, 1.9078, 1.8667, 1.831, 1.7999, 1.7723, 1.7478, 1.7257, 1.7058, 1.6876, 1.6711, 1.6558],
[125, 3.9169, 3.0687, 2.6771, 2.4442, 2.2868, 2.1719, 2.0836, 2.0133, 1.9556, 1.9072, 1.866, 1.8304, 1.7992, 1.7717, 1.7471, 1.725, 1.7051, 1.6869, 1.6704, 1.6551],
[126, 3.9163, 3.0681, 2.6765, 2.4436, 2.2862, 2.1713, 2.083, 2.0126, 1.955, 1.9066, 1.8654, 1.8298, 1.7986, 1.771, 1.7464, 1.7244, 1.7044, 1.6863, 1.6697, 1.6544],
[127, 3.9157, 3.0675, 2.6759, 2.443, 2.2856, 2.1707, 2.0824, 2.0121, 1.9544, 1.906, 1.8648, 1.8291, 1.7979, 1.7704, 1.7458, 1.7237, 1.7038, 1.6856, 1.669, 1.6538],
[128, 3.9151, 3.0669, 2.6754, 2.4424, 2.285, 2.1701, 2.0819, 2.0115, 1.9538, 1.9054, 1.8642, 1.8285, 1.7974, 1.7698, 1.7452, 1.7231, 1.7031, 1.685, 1.6684, 1.6531],
[129, 3.9145, 3.0664, 2.6749, 2.4419, 2.2845, 2.1696, 2.0813, 2.0109, 1.9532, 1.9048, 1.8636, 1.828, 1.7967, 1.7692, 1.7446, 1.7225, 1.7025, 1.6843, 1.6677, 1.6525],
[130, 3.914, 3.0659, 2.6743, 2.4414, 2.2839, 2.169, 2.0807, 2.0103, 1.9526, 1.9042, 1.863, 1.8273, 1.7962, 1.7685, 1.744, 1.7219, 1.7019, 1.6837, 1.6671, 1.6519],
[131, 3.9134, 3.0653, 2.6737, 2.4408, 2.2834, 2.1685, 2.0802, 2.0098, 1.9521, 1.9037, 1.8624, 1.8268, 1.7956, 1.768, 1.7434, 1.7213, 1.7013, 1.6831, 1.6665, 1.6513],
[132, 3.9129, 3.0648, 2.6732, 2.4403, 2.2829, 2.168, 2.0796, 2.0092, 1.9515, 1.9031, 1.8619, 1.8262, 1.795, 1.7674, 1.7428, 1.7207, 1.7007, 1.6825, 1.6659, 1.6506],
[133, 3.9123, 3.0642, 2.6727, 2.4398, 2.2823, 2.1674, 2.0791, 2.0087, 1.951, 1.9026, 1.8613, 1.8256, 1.7944, 1.7668, 1.7422, 1.7201, 1.7001, 1.6819, 1.6653, 1.65],
[134, 3.9118, 3.0637, 2.6722, 2.4392, 2.2818, 2.1669, 2.0786, 2.0082, 1.9504, 1.902, 1.8608, 1.8251, 1.7939, 1.7662, 1.7416, 1.7195, 1.6995, 1.6813, 1.6647, 1.6494],
[135, 3.9112, 3.0632, 2.6717, 2.4387, 2.2813, 2.1664, 2.0781, 2.0076, 1.9499, 1.9015, 1.8602, 1.8245, 1.7933, 1.7657, 1.7411, 1.719, 1.6989, 1.6808, 1.6641, 1.6488],
[136, 3.9108, 3.0627, 2.6712, 2.4382, 2.2808, 2.1659, 2.0775, 2.0071, 1.9494, 1.901, 1.8597, 1.824, 1.7928, 1.7651, 1.7405, 1.7184, 1.6984, 1.6802, 1.6635, 1.6483],
[137, 3.9102, 3.0622, 2.6707, 2.4378, 2.2803, 2.1654, 2.077, 2.0066, 1.9488, 1.9004, 1.8592, 1.8235, 1.7922, 1.7646, 1.74, 1.7178, 1.6978, 1.6796, 1.663, 1.6477],
[138, 3.9098, 3.0617, 2.6702, 2.4373, 2.2798, 2.1649, 2.0766, 2.0061, 1.9483, 1.8999, 1.8586, 1.823, 1.7917, 1.7641, 1.7394, 1.7173, 1.6973, 1.6791, 1.6624, 1.6471],
[139, 3.9092, 3.0613, 2.6697, 2.4368, 2.2794, 2.1644, 2.0761, 2.0056, 1.9478, 1.8994, 1.8581, 1.8224, 1.7912, 1.7635, 1.7389, 1.7168, 1.6967, 1.6785, 1.6619, 1.6466],
[140, 3.9087, 3.0608, 2.6692, 2.4363, 2.2789, 2.1639, 2.0756, 2.0051, 1.9473, 1.8989, 1.8576, 1.8219, 1.7907, 1.763, 1.7384, 1.7162, 1.6962, 1.678, 1.6613, 1.646],
[141, 3.9083, 3.0603, 2.6688, 2.4359, 2.2784, 2.1634, 2.0751, 2.0046, 1.9469, 1.8984, 1.8571, 1.8214, 1.7901, 1.7625, 1.7379, 1.7157, 1.6957, 1.6775, 1.6608, 1.6455],
[142, 3.9078, 3.0598, 2.6683, 2.4354, 2.2779, 2.163, 2.0747, 2.0042, 1.9464, 1.8979, 1.8566, 1.8209, 1.7897, 1.762, 1.7374, 1.7152, 1.6952, 1.6769, 1.6603, 1.645],
[143, 3.9073, 3.0594, 2.6679, 2.435, 2.2775, 2.1625, 2.0742, 2.0037, 1.9459, 1.8975, 1.8562, 1.8204, 1.7892, 1.7615, 1.7368, 1.7147, 1.6946, 1.6764, 1.6598, 1.6444],
[144, 3.9068, 3.0589, 2.6675, 2.4345, 2.277, 2.1621, 2.0737, 2.0033, 1.9455, 1.897, 1.8557, 1.82, 1.7887, 1.761, 1.7364, 1.7142, 1.6941, 1.6759, 1.6592, 1.6439],
[145, 3.9064, 3.0585, 2.667, 2.4341, 2.2766, 2.1617, 2.0733, 2.0028, 1.945, 1.8965, 1.8552, 1.8195, 1.7882, 1.7605, 1.7359, 1.7137, 1.6936, 1.6754, 1.6587, 1.6434],
[146, 3.906, 3.0581, 2.6666, 2.4337, 2.2762, 2.1612, 2.0728, 2.0024, 1.9445, 1.8961, 1.8548, 1.819, 1.7877, 1.7601, 1.7354, 1.7132, 1.6932, 1.6749, 1.6582, 1.6429],
[147, 3.9055, 3.0576, 2.6662, 2.4332, 2.2758, 2.1608, 2.0724, 2.0019, 1.9441, 1.8956, 1.8543, 1.8186, 1.7873, 1.7596, 1.7349, 1.7127, 1.6927, 1.6744, 1.6578, 1.6424],
[148, 3.9051, 3.0572, 2.6657, 2.4328, 2.2753, 2.1604, 2.072, 2.0015, 1.9437, 1.8952, 1.8539, 1.8181, 1.7868, 1.7591, 1.7344, 1.7123, 1.6922, 1.6739, 1.6573, 1.6419],
[149, 3.9046, 3.0568, 2.6653, 2.4324, 2.2749, 2.1599, 2.0716, 2.0011, 1.9432, 1.8947, 1.8534, 1.8177, 1.7864, 1.7587, 1.734, 1.7118, 1.6917, 1.6735, 1.6568, 1.6414],
[150, 3.9042, 3.0564, 2.6649, 2.4319, 2.2745, 2.1595, 2.0711, 2.0006, 1.9428, 1.8943, 1.853, 1.8172, 1.7859, 1.7582, 1.7335, 1.7113, 1.6913, 1.673, 1.6563, 1.641],
[151, 3.9038, 3.056, 2.6645, 2.4315, 2.2741, 2.1591, 2.0707, 2.0002, 1.9424, 1.8939, 1.8526, 1.8168, 1.7855, 1.7578, 1.7331, 1.7109, 1.6908, 1.6726, 1.6558, 1.6405],
[152, 3.9033, 3.0555, 2.6641, 2.4312, 2.2737, 2.1587, 2.0703, 1.9998, 1.942, 1.8935, 1.8521, 1.8163, 1.785, 1.7573, 1.7326, 1.7104, 1.6904, 1.6721, 1.6554, 1.64],
[153, 3.903, 3.0552, 2.6637, 2.4308, 2.2733, 2.1583, 2.0699, 1.9994, 1.9416, 1.8931, 1.8517, 1.8159, 1.7846, 1.7569, 1.7322, 1.71, 1.6899, 1.6717, 1.6549, 1.6396],
[154, 3.9026, 3.0548, 2.6634, 2.4304, 2.2729, 2.1579, 2.0695, 1.999, 1.9412, 1.8926, 1.8513, 1.8155, 1.7842, 1.7565, 1.7318, 1.7096, 1.6895, 1.6712, 1.6545, 1.6391],
[155, 3.9021, 3.0544, 2.6629, 2.43, 2.2725, 2.1575, 2.0691, 1.9986, 1.9407, 1.8923, 1.8509, 1.8151, 1.7838, 1.7561, 1.7314, 1.7091, 1.6891, 1.6708, 1.654, 1.6387],
[156, 3.9018, 3.054, 2.6626, 2.4296, 2.2722, 2.1571, 2.0687, 1.9982, 1.9403, 1.8918, 1.8505, 1.8147, 1.7834, 1.7557, 1.7309, 1.7087, 1.6886, 1.6703, 1.6536, 1.6383],
[157, 3.9014, 3.0537, 2.6622, 2.4293, 2.2717, 2.1568, 2.0684, 1.9978, 1.94, 1.8915, 1.8501, 1.8143, 1.7829, 1.7552, 1.7305, 1.7083, 1.6882, 1.6699, 1.6532, 1.6378],
[158, 3.901, 3.0533, 2.6618, 2.4289, 2.2714, 2.1564, 2.068, 1.9974, 1.9396, 1.8911, 1.8497, 1.8139, 1.7826, 1.7548, 1.7301, 1.7079, 1.6878, 1.6695, 1.6528, 1.6374],
[159, 3.9006, 3.0529, 2.6615, 2.4285, 2.271, 2.156, 2.0676, 1.997, 1.9392, 1.8907, 1.8493, 1.8135, 1.7822, 1.7544, 1.7297, 1.7075, 1.6874, 1.6691, 1.6524, 1.637],
[160, 3.9002, 3.0525, 2.6611, 2.4282, 2.2706, 2.1556, 2.0672, 1.9967, 1.9388, 1.8903, 1.8489, 1.8131, 1.7818, 1.754, 1.7293, 1.7071, 1.687, 1.6687, 1.6519, 1.6366],
[161, 3.8998, 3.0522, 2.6607, 2.4278, 2.2703, 2.1553, 2.0669, 1.9963, 1.9385, 1.8899, 1.8485, 1.8127, 1.7814, 1.7537, 1.7289, 1.7067, 1.6866, 1.6683, 1.6515, 1.6361],
[162, 3.8995, 3.0518, 2.6604, 2.4275, 2.27, 2.155, 2.0665, 1.9959, 1.9381, 1.8895, 1.8482, 1.8124, 1.781, 1.7533, 1.7285, 1.7063, 1.6862, 1.6679, 1.6511, 1.6357],
[163, 3.8991, 3.0515, 2.6601, 2.4271, 2.2696, 2.1546, 2.0662, 1.9956, 1.9377, 1.8892, 1.8478, 1.812, 1.7806, 1.7529, 1.7282, 1.7059, 1.6858, 1.6675, 1.6507, 1.6353],
[164, 3.8987, 3.0512, 2.6597, 2.4268, 2.2693, 2.1542, 2.0658, 1.9953, 1.9374, 1.8888, 1.8474, 1.8116, 1.7803, 1.7525, 1.7278, 1.7055, 1.6854, 1.6671, 1.6503, 1.6349],
[165, 3.8985, 3.0508, 2.6594, 2.4264, 2.2689, 2.1539, 2.0655, 1.9949, 1.937, 1.8885, 1.8471, 1.8112, 1.7799, 1.7522, 1.7274, 1.7052, 1.685, 1.6667, 1.6499, 1.6345],
[166, 3.8981, 3.0505, 2.6591, 2.4261, 2.2686, 2.1536, 2.0651, 1.9945, 1.9367, 1.8881, 1.8467, 1.8109, 1.7795, 1.7518, 1.727, 1.7048, 1.6846, 1.6663, 1.6496, 1.6341],
[167, 3.8977, 3.0502, 2.6587, 2.4258, 2.2683, 2.1533, 2.0648, 1.9942, 1.9363, 1.8878, 1.8464, 1.8105, 1.7792, 1.7514, 1.7266, 1.7044, 1.6843, 1.6659, 1.6492, 1.6338],
[168, 3.8974, 3.0498, 2.6584, 2.4254, 2.268, 2.1529, 2.0645, 1.9939, 1.936, 1.8874, 1.846, 1.8102, 1.7788, 1.7511, 1.7263, 1.704, 1.6839, 1.6656, 1.6488, 1.6334],
[169, 3.8971, 3.0495, 2.6581, 2.4251, 2.2676, 2.1526, 2.0641, 1.9936, 1.9357, 1.8871, 1.8457, 1.8099, 1.7785, 1.7507, 1.7259, 1.7037, 1.6835, 1.6652, 1.6484, 1.633],
[170, 3.8967, 3.0492, 2.6578, 2.4248, 2.2673, 2.1523, 2.0638, 1.9932, 1.9353, 1.8868, 1.8454, 1.8095, 1.7781, 1.7504, 1.7256, 1.7033, 1.6832, 1.6648, 1.6481, 1.6326],
[171, 3.8965, 3.0488, 2.6575, 2.4245, 2.267, 2.152, 2.0635, 1.9929, 1.935, 1.8864, 1.845, 1.8092, 1.7778, 1.75, 1.7252, 1.703, 1.6828, 1.6645, 1.6477, 1.6323],
[172, 3.8961, 3.0485, 2.6571, 2.4242, 2.2667, 2.1516, 2.0632, 1.9926, 1.9347, 1.8861, 1.8447, 1.8088, 1.7774, 1.7497, 1.7249, 1.7026, 1.6825, 1.6641, 1.6473, 1.6319],
[173, 3.8958, 3.0482, 2.6568, 2.4239, 2.2664, 2.1513, 2.0628, 1.9923, 1.9343, 1.8858, 1.8443, 1.8085, 1.7771, 1.7493, 1.7246, 1.7023, 1.6821, 1.6638, 1.647, 1.6316],
[174, 3.8954, 3.0479, 2.6566, 2.4236, 2.266, 2.151, 2.0626, 1.9919, 1.934, 1.8855, 1.844, 1.8082, 1.7768, 1.749, 1.7242, 1.7019, 1.6818, 1.6634, 1.6466, 1.6312],
[175, 3.8952, 3.0476, 2.6563, 2.4233, 2.2658, 2.1507, 2.0622, 1.9916, 1.9337, 1.8852, 1.8437, 1.8078, 1.7764, 1.7487, 1.7239, 1.7016, 1.6814, 1.6631, 1.6463, 1.6309],
[176, 3.8948, 3.0473, 2.6559, 2.423, 2.2655, 2.1504, 2.0619, 1.9913, 1.9334, 1.8848, 1.8434, 1.8075, 1.7761, 1.7483, 1.7236, 1.7013, 1.6811, 1.6628, 1.646, 1.6305],
[177, 3.8945, 3.047, 2.6556, 2.4227, 2.2652, 2.1501, 2.0616, 1.991, 1.9331, 1.8845, 1.8431, 1.8072, 1.7758, 1.748, 1.7232, 1.7009, 1.6808, 1.6624, 1.6456, 1.6302],
[178, 3.8943, 3.0467, 2.6554, 2.4224, 2.2649, 2.1498, 2.0613, 1.9907, 1.9328, 1.8842, 1.8428, 1.8069, 1.7755, 1.7477, 1.7229, 1.7006, 1.6805, 1.6621, 1.6453, 1.6298],
[179, 3.8939, 3.0465, 2.6551, 2.4221, 2.2646, 2.1495, 2.0611, 1.9904, 1.9325, 1.8839, 1.8425, 1.8066, 1.7752, 1.7474, 1.7226, 1.7003, 1.6801, 1.6618, 1.645, 1.6295],
[180, 3.8936, 3.0462, 2.6548, 2.4218, 2.2643, 2.1492, 2.0608, 1.9901, 1.9322, 1.8836, 1.8422, 1.8063, 1.7749, 1.7471, 1.7223, 1.7, 1.6798, 1.6614, 1.6446, 1.6292],
[181, 3.8933, 3.0458, 2.6545, 2.4216, 2.264, 2.149, 2.0605, 1.9899, 1.9319, 1.8833, 1.8419, 1.806, 1.7746, 1.7468, 1.7219, 1.6997, 1.6795, 1.6611, 1.6443, 1.6289],
[182, 3.8931, 3.0456, 2.6543, 2.4213, 2.2638, 2.1487, 2.0602, 1.9896, 1.9316, 1.883, 1.8416, 1.8057, 1.7743, 1.7465, 1.7217, 1.6994, 1.6792, 1.6608, 1.644, 1.6286],
[183, 3.8928, 3.0453, 2.654, 2.421, 2.2635, 2.1484, 2.0599, 1.9893, 1.9313, 1.8827, 1.8413, 1.8054, 1.774, 1.7462, 1.7214, 1.6991, 1.6789, 1.6605, 1.6437, 1.6282],
[184, 3.8925, 3.045, 2.6537, 2.4207, 2.2632, 2.1481, 2.0596, 1.989, 1.9311, 1.8825, 1.841, 1.8051, 1.7737, 1.7459, 1.721, 1.6987, 1.6786, 1.6602, 1.6434, 1.6279],
[185, 3.8923, 3.0448, 2.6534, 2.4205, 2.263, 2.1479, 2.0594, 1.9887, 1.9308, 1.8822, 1.8407, 1.8048, 1.7734, 1.7456, 1.7208, 1.6984, 1.6783, 1.6599, 1.643, 1.6276],
[186, 3.892, 3.0445, 2.6531, 2.4202, 2.2627, 2.1476, 2.0591, 1.9885, 1.9305, 1.8819, 1.8404, 1.8045, 1.7731, 1.7453, 1.7205, 1.6981, 1.678, 1.6596, 1.6428, 1.6273],
[187, 3.8917, 3.0442, 2.6529, 2.4199, 2.2624, 2.1473, 2.0588, 1.9882, 1.9302, 1.8816, 1.8401, 1.8042, 1.7728, 1.745, 1.7202, 1.6979, 1.6777, 1.6593, 1.6424, 1.627],
[188, 3.8914, 3.044, 2.6526, 2.4197, 2.2621, 2.1471, 2.0586, 1.9879, 1.9299, 1.8814, 1.8399, 1.804, 1.7725, 1.7447, 1.7199, 1.6976, 1.6774, 1.659, 1.6421, 1.6267],
[189, 3.8912, 3.0437, 2.6524, 2.4195, 2.2619, 2.1468, 2.0583, 1.9877, 1.9297, 1.8811, 1.8396, 1.8037, 1.7722, 1.7444, 1.7196, 1.6973, 1.6771, 1.6587, 1.6418, 1.6264],
[190, 3.8909, 3.0435, 2.6521, 2.4192, 2.2617, 2.1466, 2.0581, 1.9874, 1.9294, 1.8808, 1.8393, 1.8034, 1.772, 1.7441, 1.7193, 1.697, 1.6768, 1.6584, 1.6416, 1.6261],
[191, 3.8906, 3.0432, 2.6519, 2.4189, 2.2614, 2.1463, 2.0578, 1.9871, 1.9292, 1.8805, 1.8391, 1.8032, 1.7717, 1.7439, 1.719, 1.6967, 1.6765, 1.6581, 1.6413, 1.6258],
[192, 3.8903, 3.043, 2.6516, 2.4187, 2.2611, 2.1461, 2.0575, 1.9869, 1.9289, 1.8803, 1.8388, 1.8029, 1.7714, 1.7436, 1.7188, 1.6964, 1.6762, 1.6578, 1.641, 1.6255],
[193, 3.8901, 3.0427, 2.6514, 2.4184, 2.2609, 2.1458, 2.0573, 1.9866, 1.9286, 1.88, 1.8385, 1.8026, 1.7712, 1.7433, 1.7185, 1.6961, 1.6759, 1.6575, 1.6407, 1.6252],
[194, 3.8899, 3.0425, 2.6512, 2.4182, 2.2606, 2.1456, 2.057, 1.9864, 1.9284, 1.8798, 1.8383, 1.8023, 1.7709, 1.7431, 1.7182, 1.6959, 1.6757, 1.6572, 1.6404, 1.6249],
[195, 3.8896, 3.0422, 2.6509, 2.418, 2.2604, 2.1453, 2.0568, 1.9861, 1.9281, 1.8795, 1.838, 1.8021, 1.7706, 1.7428, 1.7179, 1.6956, 1.6754, 1.657, 1.6401, 1.6247],
[196, 3.8893, 3.042, 2.6507, 2.4177, 2.2602, 2.1451, 2.0566, 1.9859, 1.9279, 1.8793, 1.8377, 1.8018, 1.7704, 1.7425, 1.7177, 1.6953, 1.6751, 1.6567, 1.6399, 1.6244],
[197, 3.8891, 3.0418, 2.6504, 2.4175, 2.26, 2.1448, 2.0563, 1.9856, 1.9277, 1.879, 1.8375, 1.8016, 1.7701, 1.7423, 1.7174, 1.6951, 1.6748, 1.6564, 1.6396, 1.6241],
[198, 3.8889, 3.0415, 2.6502, 2.4173, 2.2597, 2.1446, 2.0561, 1.9854, 1.9274, 1.8788, 1.8373, 1.8013, 1.7699, 1.742, 1.7172, 1.6948, 1.6746, 1.6562, 1.6393, 1.6238],
[199, 3.8886, 3.0413, 2.65, 2.417, 2.2595, 2.1444, 2.0558, 1.9852, 1.9272, 1.8785, 1.837, 1.8011, 1.7696, 1.7418, 1.7169, 1.6946, 1.6743, 1.6559, 1.6391, 1.6236],
[200, 3.8883, 3.041, 2.6497, 2.4168, 2.2592, 2.1441, 2.0556, 1.9849, 1.9269, 1.8783, 1.8368, 1.8008, 1.7694, 1.7415, 1.7166, 1.6943, 1.6741, 1.6557, 1.6388, 1.62]])
    return ftest[row][col]

def tcalc(nf,p):
    """
     t-table for nf degrees of freedom (95% confidence)
    """
#
    if p==.05:
        if nf> 2: t= 4.3027
        if nf> 3: t= 3.1824
        if nf> 4: t= 2.7765
        if nf> 5: t= 2.5706
        if nf> 6: t= 2.4469
        if nf> 7: t= 2.3646
        if nf> 8: t= 2.3060
        if nf> 9: t= 2.2622
        if nf> 10: t= 2.2281
        if nf> 11: t= 2.2010
        if nf> 12: t= 2.1788
        if nf> 13: t= 2.1604
        if nf> 14: t= 2.1448
        if nf> 15: t= 2.1315
        if nf> 16: t= 2.1199
        if nf> 17: t= 2.1098
        if nf> 18: t= 2.1009
        if nf> 19: t= 2.0930
        if nf> 20: t= 2.0860
        if nf> 21: t= 2.0796
        if nf> 22: t= 2.0739
        if nf> 23: t= 2.0687
        if nf> 24: t= 2.0639
        if nf> 25: t= 2.0595
        if nf> 26: t= 2.0555
        if nf> 27: t= 2.0518
        if nf> 28: t= 2.0484
        if nf> 29: t= 2.0452
        if nf> 30: t= 2.0423
        if nf> 31: t= 2.0395
        if nf> 32: t= 2.0369
        if nf> 33: t= 2.0345
        if nf> 34: t= 2.0322
        if nf> 35: t= 2.0301
        if nf> 36: t= 2.0281
        if nf> 37: t= 2.0262
        if nf> 38: t= 2.0244
        if nf> 39: t= 2.0227
        if nf> 40: t= 2.0211
        if nf> 41: t= 2.0195
        if nf> 42: t= 2.0181
        if nf> 43: t= 2.0167
        if nf> 44: t= 2.0154
        if nf> 45: t= 2.0141
        if nf> 46: t= 2.0129
        if nf> 47: t= 2.0117
        if nf> 48: t= 2.0106
        if nf> 49: t= 2.0096
        if nf> 50: t= 2.0086
        if nf> 51: t= 2.0076
        if nf> 52: t= 2.0066
        if nf> 53: t= 2.0057
        if nf> 54: t= 2.0049
        if nf> 55: t= 2.0040
        if nf> 56: t= 2.0032
        if nf> 57: t= 2.0025
        if nf> 58: t= 2.0017
        if nf> 59: t= 2.0010
        if nf> 60: t= 2.0003
        if nf> 61: t= 1.9996
        if nf> 62: t= 1.9990
        if nf> 63: t= 1.9983
        if nf> 64: t= 1.9977
        if nf> 65: t= 1.9971
        if nf> 66: t= 1.9966
        if nf> 67: t= 1.9960
        if nf> 68: t= 1.9955
        if nf> 69: t= 1.9949
        if nf> 70: t= 1.9944
        if nf> 71: t= 1.9939
        if nf> 72: t= 1.9935
        if nf> 73: t= 1.9930
        if nf> 74: t= 1.9925
        if nf> 75: t= 1.9921
        if nf> 76: t= 1.9917
        if nf> 77: t= 1.9913
        if nf> 78: t= 1.9908
        if nf> 79: t= 1.9905
        if nf> 80: t= 1.9901
        if nf> 81: t= 1.9897
        if nf> 82: t= 1.9893
        if nf> 83: t= 1.9890
        if nf> 84: t= 1.9886
        if nf> 85: t= 1.9883
        if nf> 86: t= 1.9879
        if nf> 87: t= 1.9876
        if nf> 88: t= 1.9873
        if nf> 89: t= 1.9870
        if nf> 90: t= 1.9867
        if nf> 91: t= 1.9864
        if nf> 92: t= 1.9861
        if nf> 93: t= 1.9858
        if nf> 94: t= 1.9855
        if nf> 95: t= 1.9852
        if nf> 96: t= 1.9850
        if nf> 97: t= 1.9847
        if nf> 98: t= 1.9845
        if nf> 99: t= 1.9842
        if nf> 100: t= 1.9840
        return t
#
    elif p==.01:
        if nf> 2: t= 9.9250
        if nf> 3: t= 5.8408
        if nf> 4: t= 4.6041
        if nf> 5: t= 4.0321
        if nf> 6: t= 3.7074
        if nf> 7: t= 3.4995
        if nf> 8: t= 3.3554
        if nf> 9: t= 3.2498
        if nf> 10: t= 3.1693
        if nf> 11: t= 3.1058
        if nf> 12: t= 3.0545
        if nf> 13: t= 3.0123
        if nf> 14: t= 2.9768
        if nf> 15: t= 2.9467
        if nf> 16: t= 2.9208
        if nf> 17: t= 2.8982
        if nf> 18: t= 2.8784
        if nf> 19: t= 2.8609
        if nf> 20: t= 2.8453
        if nf> 21: t= 2.8314
        if nf> 22: t= 2.8188
        if nf> 23: t= 2.8073
        if nf> 24: t= 2.7970
        if nf> 25: t= 2.7874
        if nf> 26: t= 2.7787
        if nf> 27: t= 2.7707
        if nf> 28: t= 2.7633
        if nf> 29: t= 2.7564
        if nf> 30: t= 2.7500
        if nf> 31: t= 2.7440
        if nf> 32: t= 2.7385
        if nf> 33: t= 2.7333
        if nf> 34: t= 2.7284
        if nf> 35: t= 2.7238
        if nf> 36: t= 2.7195
        if nf> 37: t= 2.7154
        if nf> 38: t= 2.7116
        if nf> 39: t= 2.7079
        if nf> 40: t= 2.7045
        if nf> 41: t= 2.7012
        if nf> 42: t= 2.6981
        if nf> 43: t= 2.6951
        if nf> 44: t= 2.6923
        if nf> 45: t= 2.6896
        if nf> 46: t= 2.6870
        if nf> 47: t= 2.6846
        if nf> 48: t= 2.6822
        if nf> 49: t= 2.6800
        if nf> 50: t= 2.6778
        if nf> 51: t= 2.6757
        if nf> 52: t= 2.6737
        if nf> 53: t= 2.6718
        if nf> 54: t= 2.6700
        if nf> 55: t= 2.6682
        if nf> 56: t= 2.6665
        if nf> 57: t= 2.6649
        if nf> 58: t= 2.6633
        if nf> 59: t= 2.6618
        if nf> 60: t= 2.6603
        if nf> 61: t= 2.6589
        if nf> 62: t= 2.6575
        if nf> 63: t= 2.6561
        if nf> 64: t= 2.6549
        if nf> 65: t= 2.6536
        if nf> 66: t= 2.6524
        if nf> 67: t= 2.6512
        if nf> 68: t= 2.6501
        if nf> 69: t= 2.6490
        if nf> 70: t= 2.6479
        if nf> 71: t= 2.6469
        if nf> 72: t= 2.6458
        if nf> 73: t= 2.6449
        if nf> 74: t= 2.6439
        if nf> 75: t= 2.6430
        if nf> 76: t= 2.6421
        if nf> 77: t= 2.6412
        if nf> 78: t= 2.6403
        if nf> 79: t= 2.6395
        if nf> 80: t= 2.6387
        if nf> 81: t= 2.6379
        if nf> 82: t= 2.6371
        if nf> 83: t= 2.6364
        if nf> 84: t= 2.6356
        if nf> 85: t= 2.6349
        if nf> 86: t= 2.6342
        if nf> 87: t= 2.6335
        if nf> 88: t= 2.6329
        if nf> 89: t= 2.6322
        if nf> 90: t= 2.6316
        if nf> 91: t= 2.6309
        if nf> 92: t= 2.6303
        if nf> 93: t= 2.6297
        if nf> 94: t= 2.6291
        if nf> 95: t= 2.6286
        if nf> 96: t= 2.6280
        if nf> 97: t= 2.6275
        if nf> 98: t= 2.6269
        if nf> 99: t= 2.6264
        if nf> 100: t= 2.6259
        return t   
        return t
    else:
        return 0
#
def sbar(Ss):
    """
    calculate average s,sigma from list of "s"s.
    """
    npts=len(Ss)
    Ss=numpy.array(Ss).transpose()
    avd,avs=[],[]
    #D=numpy.array([Ss[0],Ss[1],Ss[2],Ss[3]+0.5*(Ss[0]+Ss[1]),Ss[4]+0.5*(Ss[1]+Ss[2]),Ss[5]+0.5*(Ss[0]+Ss[2])]).transpose()
    D=numpy.array([Ss[0],Ss[1],Ss[2],Ss[3]+0.5*(Ss[0]+Ss[1]),Ss[4]+0.5*(Ss[1]+Ss[2]),Ss[5]+0.5*(Ss[0]+Ss[2])])
    for j in range(6):
        avd.append(numpy.average(D[j]))
        avs.append(numpy.average(Ss[j]))
    D=D.transpose()
    #for s in Ss:
    #    print 'from sbar: ',s
    #    D.append(s[:]) # append a copy of s
    #    D[-1][3]=D[-1][3]+0.5*(s[0]+s[1])
    #    D[-1][4]=D[-1][4]+0.5*(s[1]+s[2])
    #    D[-1][5]=D[-1][5]+0.5*(s[0]+s[2])
    #    for j in range(6):
    #        avd[j]+=(D[-1][j])/float(npts)
    #        avs[j]+=(s[j])/float(npts)
#   calculate sigma
    nf=(npts-1)*6 # number of degrees of freedom
    s0=0
    Dels=(D-avd)**2
    s0=numpy.sum(Dels)
    sigma=numpy.sqrt(s0/float(nf))
    return nf,sigma,avs

def dohext(nf,sigma,s):
    """
    calculates hext parameters for nf, sigma and s
    """
#
    if nf==-1:return hextpars 
    f=numpy.sqrt(2.*fcalc(2,nf))
    t2sum=0
    tau,Vdir=doseigs(s)
    for i in range(3): t2sum+=tau[i]**2
    chibar=(s[0]+s[1]+s[2])/3.
    hpars={}
    hpars['F_crit']='%s'%(fcalc(5,nf))
    hpars['F12_crit']='%s'%(fcalc(2,nf))
    hpars["F"]=0.4*(t2sum-3*chibar**2)/(sigma**2)
    hpars["F12"]=0.5*((tau[0]-tau[1])/sigma)**2
    hpars["F23"]=0.5*((tau[1]-tau[2])/sigma)**2
    hpars["v1_dec"]=Vdir[0][0]
    hpars["v1_inc"]=Vdir[0][1]
    hpars["v2_dec"]=Vdir[1][0]
    hpars["v2_inc"]=Vdir[1][1]
    hpars["v3_dec"]=Vdir[2][0]
    hpars["v3_inc"]=Vdir[2][1]
    hpars["t1"]=tau[0]
    hpars["t2"]=tau[1]
    hpars["t3"]=tau[2]
    hpars["e12"]=numpy.arctan((f*sigma)/(2*abs(tau[0]-tau[1])))*180./numpy.pi
    hpars["e23"]=numpy.arctan((f*sigma)/(2*abs(tau[1]-tau[2])))*180./numpy.pi
    hpars["e13"]=numpy.arctan((f*sigma)/(2*abs(tau[0]-tau[2])))*180./numpy.pi
    return hpars
#
#
def design(npos):
    """
     make a design matrix for an anisotropy experiment
    """
    if npos==15:
#
# rotatable design of Jelinek for kappabridge (see Tauxe, 1998)
#
        A=numpy.array([[.5,.5,0,-1.,0,0],[.5,.5,0,1.,0,0],[1,.0,0,0,0,0],[.5,.5,0,-1.,0,0],[.5,.5,0,1.,0,0],[0,.5,.5,0,-1.,0],[0,.5,.5,0,1.,0],[0,1.,0,0,0,0],[0,.5,.5,0,-1.,0],[0,.5,.5,0,1.,0],[.5,0,.5,0,0,-1.],[.5,0,.5,0,0,1.],[0,0,1.,0,0,0],[.5,0,.5,0,0,-1.],[.5,0,.5,0,0,1.]]) #  design matrix for 15 measurment positions
    elif npos==6:
        A=numpy.array([[1.,0,0,0,0,0],[0,1.,0,0,0,0],[0,0,1.,0,0,0],[.5,.5,0,1.,0,0],[0,.5,.5,0,1.,0],[.5,0,.5,0,0,1.]]) #  design matrix for 6 measurment positions

    else:
        print "measurement protocol not supported yet "
        sys.exit()
    B=numpy.dot(numpy.transpose(A),A)
    B=numpy.linalg.inv(B)
    B=numpy.dot(B,numpy.transpose(A))
    return A,B
#
#
def dok15_s(k15):
    """
    calculates least-squares matrix for 15 measurements from Jelinek [1976]
    """
#
    A,B=design(15) #  get design matrix for 15 measurements
    sbar=numpy.dot(B,k15) # get mean s
    t=(sbar[0]+sbar[1]+sbar[2]) # trace
    bulk=t/3. # bulk susceptibility
    Kbar=numpy.dot(A,sbar)  # get best fit values for K
    dels=k15-Kbar  # get deltas
    dels,sbar=dels/t,sbar/t# normalize by trace
    So= sum(dels**2) 
    sigma=numpy.sqrt(So/9.) # standard deviation
    return sbar,sigma,bulk
#
def cross(v, w):
    """
     cross product of two vectors
    """
    x = v[1]*w[2] - v[2]*w[1]
    y = v[2]*w[0] - v[0]*w[2]
    z = v[0]*w[1] - v[1]*w[0]
    return [x, y, z]
#
def dosgeo(s,az,pl):
    """
     rotates  matrix a to az,pl returns  s
    """
#
    a=s2a(s) # convert to 3,3 matrix
#  first get three orthogonal axes
    X1=dir2cart((az,pl,1.))
    X2=dir2cart((az+90,0.,1.))
    X3=cross(X1,X2)
    A=numpy.transpose([X1,X2,X3])
    b=numpy.zeros((3,3,),'f') # initiale the b matrix
    for i in range(3):
        for j in range(3): 
            dum=0
            for k in range(3): 
                for l in range(3): 
                    dum+=A[i][k]*A[j][l]*a[k][l]
            b[i][j]=dum 
    return a2s(b)
#
#
def dostilt(s,bed_az,bed_dip):
    """
     rotate "s" data to stratigraphic coordinates
    """
    tau,Vdirs=doseigs(s)
    Vrot=[] 
    for evec in Vdirs:
        d,i=dotilt(evec[0],evec[1],bed_az,bed_dip)
        Vrot.append([d,i])
    return doeigs_s(tau,Vrot)
#
#
def apseudo(Ss,ipar,sigma):
    """
     draw a bootstrap sample of Ss
    """
#
    Is=random.randint(0,len(Ss)-1,size=len(Ss)) # draw N random integers
    Ss=numpy.array(Ss)
    if ipar==0:
        BSs=Ss[Is]
    else: # need to recreate measurement - then do the parametric stuffr
        A,B=design(6) # get the design matrix for 6 measurements
        K,BSs=[],[]
        for k in range(len(Ss)):
            K.append(numpy.dot(A,Ss[k]))
        Pars=numpy.random.normal(K,sigma)
        for k in range(len(Ss)):
            BSs.append(numpy.dot(B,Pars[k]))
    return numpy.array(BSs)
#
def sbootpars(Taus,Vs):
    """
     get bootstrap parameters for s data
    """
#
    Tau1s,Tau2s,Tau3s=[],[],[]
    V1s,V2s,V3s=[],[],[]
    nb=len(Taus)
    bpars={}
    for k in range(nb):
        Tau1s.append(Taus[k][0])
        Tau2s.append(Taus[k][1])
        Tau3s.append(Taus[k][2])
        V1s.append(Vs[k][0])
        V2s.append(Vs[k][1])
        V3s.append(Vs[k][2])
    x,sig=gausspars(Tau1s) 
    bpars["t1_sigma"]=sig
    x,sig=gausspars(Tau2s) 
    bpars["t2_sigma"]=sig
    x,sig=gausspars(Tau3s) 
    bpars["t3_sigma"]=sig
    kpars=dokent(V1s,len(V1s))
    bpars["v1_dec"]=kpars["dec"]
    bpars["v1_inc"]=kpars["inc"]
    bpars["v1_zeta"]=kpars["Zeta"]*numpy.sqrt(nb)
    bpars["v1_eta"]=kpars["Eta"]*numpy.sqrt(nb)
    bpars["v1_zeta_dec"]=kpars["Zdec"]
    bpars["v1_zeta_inc"]=kpars["Zinc"]
    bpars["v1_eta_dec"]=kpars["Edec"]
    bpars["v1_eta_inc"]=kpars["Einc"]
    kpars=dokent(V2s,len(V2s))
    bpars["v2_dec"]=kpars["dec"]
    bpars["v2_inc"]=kpars["inc"]
    bpars["v2_zeta"]=kpars["Zeta"]*numpy.sqrt(nb)
    bpars["v2_eta"]=kpars["Eta"]*numpy.sqrt(nb)
    bpars["v2_zeta_dec"]=kpars["Zdec"]
    bpars["v2_zeta_inc"]=kpars["Zinc"]
    bpars["v2_eta_dec"]=kpars["Edec"]
    bpars["v2_eta_inc"]=kpars["Einc"]
    kpars=dokent(V3s,len(V3s))
    bpars["v3_dec"]=kpars["dec"]
    bpars["v3_inc"]=kpars["inc"]
    bpars["v3_zeta"]=kpars["Zeta"]*numpy.sqrt(nb)
    bpars["v3_eta"]=kpars["Eta"]*numpy.sqrt(nb)
    bpars["v3_zeta_dec"]=kpars["Zdec"]
    bpars["v3_zeta_inc"]=kpars["Zinc"]
    bpars["v3_eta_dec"]=kpars["Edec"]
    bpars["v3_eta_inc"]=kpars["Einc"]
    return bpars
#
#
def s_boot(Ss,ipar,nb):
    """
     returns bootstrap parameters for S data
    """
    npts=len(Ss)
# get average s for whole dataset
    nf,Sigma,avs=sbar(Ss)
    Tmean,Vmean=doseigs(avs) # get eigenvectors of mean tensor
#
# now do bootstrap to collect Vs and taus of bootstrap means
#
    Taus,Vs=[],[]  # number of bootstraps, list of bootstrap taus and eigenvectors
#

    for k in range(nb): # repeat nb times
#        if k%50==0:print k,' out of ',nb
        BSs=apseudo(Ss,ipar,Sigma) # get a pseudosample - if ipar=1, do a parametric bootstrap
        nf,sigma,avbs=sbar(BSs) # get bootstrap mean s
        tau,Vdirs=doseigs(avbs) # get bootstrap eigenparameters
        Taus.append(tau)
        Vs.append(Vdirs)
    return Tmean,Vmean,Taus,Vs

#
def designAARM(npos):
#
    """  
    calculates B matrix for AARM calculations.  
    """
    if npos!=9:
        print 'Sorry - only 9 positions available'
        sys.exit()
    Dec=[315.,225.,180.,135.,45.,90.,270.,270.,270.,90.,180.,180.,0.,0.,0.]
    Dip=[0.,0.,0.,0.,0.,-45.,-45.,0.,45.,45.,45.,-45.,-90.,-45.,45.]
    index9=[0,1, 2,5,6,7,10,11,12]
    H=[]
    for ind in range(15):
        Dir=[Dec[ind],Dip[ind],1.]
        H.append(dir2cart(Dir))  # 15 field directionss
#
# make design matrix A
#
    A=numpy.zeros((npos*3,6),'f')
    tmpH=numpy.zeros((npos,3),'f') # define tmpH
    if npos == 9:
        for i in range(9):
            k=index9[i]
            ind=i*3
            A[ind][0]=H[k][0]
            A[ind][3]=H[k][1]
            A[ind][5]=H[k][2]
            ind=i*3+1
            A[ind][3]=H[k][0]
            A[ind][1]=H[k][1]
            A[ind][4]=H[k][2]
            ind=i*3+2
            A[ind][5]=H[k][0]
            A[ind][4]=H[k][1]
            A[ind][2]=H[k][2]
            for j in range(3):
                tmpH[i][j]=H[k][j]
        At=numpy.transpose(A)
        ATA=numpy.dot(At,A)
        ATAI=numpy.linalg.inv(ATA)
        B=numpy.dot(ATAI,At)
    else:
        print "B matrix not yet supported"
        sys.exit()
    return B,H,tmpH
#
def designATRM(npos):
#
    """
    calculates B matrix for ATRM calculations.
    """
    #if npos!=6:
    #    print 'Sorry - only 6 positions available'
    #    sys.exit()
    Dec=[0,0,  0,90,180,270,0] # for shuhui only
    Dip=[90,-90,0,0,0,0,90]
    Dec=[0,90,0,180,270,0,0,90,0]
    Dip=[0,0,90,0,0,-90,0,0,90]
    H=[]
    for ind in range(6):
        Dir=[Dec[ind],Dip[ind],1.]
        H.append(dir2cart(Dir))  # 6 field directionss
#
# make design matrix A
#
    A=numpy.zeros((npos*3,6),'f')
    tmpH=numpy.zeros((npos,3),'f') # define tmpH
    #if npos == 6:
    #    for i in range(6):
    for i in range(6):
            ind=i*3
            A[ind][0]=H[i][0]
            A[ind][3]=H[i][1]
            A[ind][5]=H[i][2]
            ind=i*3+1
            A[ind][3]=H[i][0]
            A[ind][1]=H[i][1]
            A[ind][4]=H[i][2]
            ind=i*3+2
            A[ind][5]=H[i][0]
            A[ind][4]=H[i][1]
            A[ind][2]=H[i][2]
            for j in range(3):
                tmpH[i][j]=H[i][j]
    At=numpy.transpose(A)
    ATA=numpy.dot(At,A)
    ATAI=numpy.linalg.inv(ATA)
    B=numpy.dot(ATAI,At)
    #else:
    #    print "B matrix not yet supported"
    #    sys.exit()
    return B,H,tmpH

#
def domagicmag(file,Recs):
    """
    converts a magic record back into the SIO mag format
    """
    for rec in Recs:
        type=".0"
        meths=[]
        tmp=rec["magic_method_codes"].split(':') 
        for meth in tmp:
            meths.append(meth.strip())
        if 'LT-T-I' in meths: type=".1"
        if 'LT-PTRM-I' in meths: type=".2"
        if 'LT-PTRM-MD' in meths: type=".3"
        treatment=float(rec["treatment_temp"])-273
        tr='%i'%(treatment)+type
        inten='%8.7e '%(float(rec["measurement_magn_moment"])*1e3)
        outstring=rec["er_specimen_name"]+" "+tr+" "+rec["measurement_csd"]+" "+inten+" "+rec["measurement_dec"]+" "+rec["measurement_inc"]+"\n"
        file.write(outstring)
#
#
def cleanup(first_I,first_Z):
    """
     cleans up unbalanced steps
     failure can be from unbalanced final step, or from missing steps,
     this takes care of  missing steps
    """
    cont=0
    Nmin=len(first_I)
    if len(first_Z)<Nmin:Nmin=len(first_Z)
    for kk in range(Nmin):
        if first_I[kk][0]!=first_Z[kk][0]:
            print "\n WARNING: "
            if first_I[kk]<first_Z[kk]:
                del first_I[kk] 
            else:
                del first_Z[kk] 
            print "Unmatched step number: ",kk+1,'  ignored'
            cont=1
        if cont==1: return first_I,first_Z,cont
    return first_I,first_Z,cont
#
#
def sortarai(datablock,s,Zdiff):
    """
     sorts data block in to first_Z, first_I, etc.
    """
    first_Z,first_I,zptrm_check,ptrm_check,ptrm_tail=[],[],[],[],[]
    field,phi,theta="","",""
    starthere=0
    Treat_I,Treat_Z,Treat_PZ,Treat_PI,Treat_M=[],[],[],[],[]
    ISteps,ZSteps,PISteps,PZSteps,MSteps=[],[],[],[],[]
    GammaChecks=[] # comparison of pTRM direction acquired and lab field
    Mkeys=['measurement_magn_moment','measurement_magn_volume','measurement_magn_mass','measurement_magnitude']
    rec=datablock[0]
    for key in Mkeys:
        if key in rec.keys() and rec[key]!="":
            momkey=key
            break
# first find all the steps
    for k in range(len(datablock)):
	rec=datablock[k]
        temp=float(rec["treatment_temp"])
        methcodes=[]
        tmp=rec["magic_method_codes"].split(":")
        for meth in tmp:
            methcodes.append(meth.strip())
        if 'LT-T-I' in methcodes and 'LP-TRM' not in methcodes and 'LP-PI-TRM' in methcodes:
            Treat_I.append(temp)
            ISteps.append(k)
            if field=="":field=float(rec["treatment_dc_field"])
            if phi=="":
                phi=float(rec['treatment_dc_field_phi'])
                theta=float(rec['treatment_dc_field_theta'])
# stick  first zero field stuff into first_Z 
        if 'LT-NO' in methcodes:
            Treat_Z.append(temp)
            ZSteps.append(k)
        if 'LT-T-Z' in methcodes: 
            Treat_Z.append(temp)
            ZSteps.append(k)
        if 'LT-PTRM-Z' in methcodes:
            Treat_PZ.append(temp)
            PZSteps.append(k)
        if 'LT-PTRM-I' in methcodes:
            Treat_PI.append(temp)
            PISteps.append(k)
        if 'LT-PTRM-MD' in methcodes:
            Treat_M.append(temp)
            MSteps.append(k)
        if 'LT-NO' in methcodes:
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            str=float(rec[momkey])
            first_I.append([273,0.,0.,0.,1])
            first_Z.append([273,dec,inc,str,1])  # NRM step
    for temp in Treat_I: # look through infield steps and find matching Z step
        if temp in Treat_Z: # found a match
            istep=ISteps[Treat_I.index(temp)]
            irec=datablock[istep]
            methcodes=[]
            tmp=irec["magic_method_codes"].split(":")
            for meth in tmp: methcodes.append(meth.strip())
            brec=datablock[istep-1] # take last record as baseline to subtract  
            zstep=ZSteps[Treat_Z.index(temp)]
            zrec=datablock[zstep]
    # sort out first_Z records 
            if "LP-PI-TRM-IZ" in methcodes: 
                ZI=0    
            else:   
                ZI=1    
            dec=float(zrec["measurement_dec"])
            inc=float(zrec["measurement_inc"])
            str=float(zrec[momkey])
            first_Z.append([temp,dec,inc,str,ZI])
    # sort out first_I records 
            idec=float(irec["measurement_dec"])
            iinc=float(irec["measurement_inc"])
            istr=float(irec[momkey])
            X=dir2cart([idec,iinc,istr])
            BL=dir2cart([dec,inc,str])
            I=[]
            for c in range(3): I.append((X[c]-BL[c]))
            if I[2]!=0:
                iDir=cart2dir(I)
                if Zdiff==0:
                    first_I.append([temp,iDir[0],iDir[1],iDir[2],ZI])
                else:
                    first_I.append([temp,0.,0.,I[2],ZI])
                gamma=angle([iDir[0],iDir[1]],[phi,theta])
            else:
                first_I.append([temp,0.,0.,0.,ZI])
                gamma=0.0
# put in Gamma check (infield trm versus lab field)
            if 180.-gamma<gamma:  gamma=180.-gamma
            GammaChecks.append([temp-273.,gamma])
    for temp in Treat_PI: # look through infield steps and find matching Z step
        step=PISteps[Treat_PI.index(temp)]
        rec=datablock[step]
        dec=float(rec["measurement_dec"])
        inc=float(rec["measurement_inc"])
        str=float(rec[momkey])
        brec=datablock[step-1] # take last record as baseline to subtract
        pdec=float(brec["measurement_dec"])
        pinc=float(brec["measurement_inc"])
        pint=float(brec[momkey])
        X=dir2cart([dec,inc,str])
        prevX=dir2cart([pdec,pinc,pint])
        I=[]
        for c in range(3): I.append(X[c]-prevX[c])
        dir1=cart2dir(I)
        if Zdiff==0:
            ptrm_check.append([temp,dir1[0],dir1[1],dir1[2]])
        else:
            ptrm_check.append([temp,0.,0.,I[2]])
# in case there are zero-field pTRM checks (not the SIO way)
    for temp in Treat_PZ:
        step=PZSteps[Treat_PZ.index(temp)]
        rec=datablock[step]
        dec=float(rec["measurement_dec"])
        inc=float(rec["measurement_inc"])
        str=float(rec[momkey])
        brec=datablock[step-1]
        pdec=float(brec["measurement_dec"])
        pinc=float(brec["measurement_inc"])
        pint=float(brec[momkey])
        X=dir2cart([dec,inc,str])
        prevX=dir2cart([pdec,pinc,pint])
        I=[]
        for c in range(3): I.append(X[c]-prevX[c])
        dir2=cart2dir(I)
        zptrm_check.append([temp,dir2[0],dir2[1],dir2[2]])
    ## get pTRM tail checks together -
    for temp in Treat_M:
        step=MSteps[Treat_M.index(temp)] # tail check step - just do a difference in magnitude!
        rec=datablock[step]
#        dec=float(rec["measurement_dec"])
#        inc=float(rec["measurement_inc"])
        str=float(rec[momkey])
        if temp in Treat_Z:
            step=ZSteps[Treat_Z.index(temp)]
            brec=datablock[step]
#        pdec=float(brec["measurement_dec"])
#        pinc=float(brec["measurement_inc"])
            pint=float(brec[momkey])
#        X=dir2cart([dec,inc,str])
#        prevX=dir2cart([pdec,pinc,pint])
#        I=[]
#        for c in range(3):I.append(X[c]-prevX[c])
#        d=cart2dir(I)
#        ptrm_tail.append([temp,d[0],d[1],d[2]])
            ptrm_tail.append([temp,0,0,str-pint])  # difference - if negative, negative tail!
        else:
            print s, '  has a tail check with no first zero field step - check input file! for step',temp-273.
#
# final check
#
    if len(first_Z)!=len(first_I):
               print len(first_Z),len(first_I)
               print " Something wrong with this specimen! Better fix it or delete it "
               raw_input(" press return to acknowledge message")
    araiblock=(first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks)
    return araiblock,field

def sortmwarai(datablock,exp_type):
    """
     sorts microwave double heating data block in to first_Z, first_I, etc.
    """
    first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check=[],[],[],[],[]
    field,phi,theta="","",""
    POWT_I,POWT_Z,POWT_PZ,POWT_PI,POWT_M=[],[],[],[],[]
    ISteps,ZSteps,PZSteps,PISteps,MSteps=[],[],[],[],[]
    rad=numpy.pi/180.
    ThetaChecks=[] # 
    DeltaChecks=[]
    GammaChecks=[]
# first find all the steps
    for k in range(len(datablock)):
        rec=datablock[k]
        powt=int(float(rec["treatment_mw_energy"]))
        methcodes=[]
        tmp=rec["magic_method_codes"].split(":")
        for meth in tmp: methcodes.append(meth.strip())
        if 'LT-M-I' in methcodes and 'LP-MRM' not in methcodes:
            POWT_I.append(powt)
            ISteps.append(k)
            if field=="":field=float(rec['treatment_dc_field'])
            if phi=="":
                phi=float(rec['treatment_dc_field_phi'])
                theta=float(rec['treatment_dc_field_theta'])
        if 'LT-M-Z' in methcodes:
            POWT_Z.append(powt)
            ZSteps.append(k)
        if 'LT-PMRM-Z' in methcodes:
            POWT_PZ.append(powt)
            PZSteps.append(k)
        if 'LT-PMRM-I' in methcodes:
            POWT_PI.append(powt)
            PISteps.append(k)
        if 'LT-PMRM-MD' in methcodes:
            POWT_M.append(powt)
            MSteps.append(k)
        if 'LT-NO' in methcodes:
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            str=float(rec["measurement_magn_moment"])
            first_I.append([0,0.,0.,0.,1])
            first_Z.append([0,dec,inc,str,1])  # NRM step
    if exp_type=="LP-PI-M-D":
# now look trough infield steps and  find matching Z step
        for powt in POWT_I:
            if powt in POWT_Z: 
                istep=ISteps[POWT_I.index(powt)]
                irec=datablock[istep]
                methcodes=[]
                tmp=irec["magic_method_codes"].split(":")
                for meth in tmp: methcodes.append(meth.strip())
                brec=datablock[istep-1] # take last record as baseline to subtract  
                zstep=ZSteps[POWT_Z.index(powt)]
                zrec=datablock[zstep]
    # sort out first_Z records
                if "LP-PI-M-IZ" in methcodes: 
                    ZI=0
                else:
                    ZI=1
                dec=float(zrec["measurement_dec"])
                inc=float(zrec["measurement_inc"])
                str=float(zrec["measurement_magn_moment"])
                first_Z.append([powt,dec,inc,str,ZI])
    # sort out first_I records
                idec=float(irec["measurement_dec"])
                iinc=float(irec["measurement_inc"])
                istr=float(irec["measurement_magn_moment"])
                X=dir2cart([idec,iinc,istr])
                BL=dir2cart([dec,inc,str])
                I=[]
                for c in range(3): I.append((X[c]-BL[c]))
                iDir=cart2dir(I)
                first_I.append([powt,iDir[0],iDir[1],iDir[2],ZI])
# put in Gamma check (infield trm versus lab field)
                gamma=angle([iDir[0],iDir[1]],[phi,theta])
                GammaChecks.append([powt,gamma])
    elif exp_type=="LP-PI-M-S":
# find last zero field step before first infield step
        lzrec=datablock[ISteps[0]-1]
        irec=datablock[ISteps[0]]
        ndec=float(lzrec["measurement_dec"])
        ninc=float(lzrec["measurement_inc"])
        nstr=float(lzrec["measurement_magn_moment"])
        NRM=dir2cart([ndec,ninc,nstr])
        fdec=float(irec["treatment_dc_field_phi"])
        finc=float(irec["treatment_dc_field_theta"])
        Flab=dir2cart([fdec,finc,1.])
        for step in ISteps:
            irec=datablock[step]
            rdec=float(irec["measurement_dec"])
            rinc=float(irec["measurement_inc"])
            rstr=float(irec["measurement_magn_moment"])
            theta1=angle([ndec,ninc],[rdec,rinc])
            theta2=angle([rdec,rinc],[fdec,finc])
            powt=int(float(irec["treatment_mw_energy"]))
            ThetaChecks.append([powt,theta1+theta2])
            p=(180.-(theta1+theta2))
            nstr=rstr*(numpy.sin(theta2*rad)/numpy.sin(p*rad))
            tmstr=rstr*(numpy.sin(theta1*rad)/numpy.sin(p*rad))
            first_Z.append([powt,ndec,ninc,nstr,1])
            first_I.append([powt,dec,inc,tmstr,1])
# check if zero field steps are parallel to assumed NRM
        for step in ZSteps:
            zrec=datablock[step]
            powt=int(float(zrec["treatment_mw_energy"]))
            zdec=float(zrec["measurement_dec"])
            zinc=float(zrec["measurement_inc"])
            delta=angle([ndec,ninc],[zdec,zinc])
            DeltaChecks.append([powt,delta])
    # get pTRMs together - take previous record and subtract
    for powt in POWT_PI:
        step=PISteps[POWT_PI.index(powt)]
        rec=datablock[step]
        dec=float(rec["measurement_dec"])
        inc=float(rec["measurement_inc"])
        str=float(rec["measurement_magn_moment"])
        brec=datablock[step-1] # take last record as baseline to subtract  
        pdec=float(brec["measurement_dec"])
        pinc=float(brec["measurement_inc"])
        pint=float(brec["measurement_magn_moment"])
        X=dir2cart([dec,inc,str])
        prevX=dir2cart([pdec,pinc,pint])
        I=[]
        for c in range(3): I.append(X[c]-prevX[c])
        dir1=cart2dir(I)
        ptrm_check.append([powt,dir1[0],dir1[1],dir1[2]])
    ## get zero field pTRM  checks together 
    for powt in POWT_PZ:
        step=PZSteps[POWT_PZ.index(powt)]
        rec=datablock[step]
        dec=float(rec["measurement_dec"])
        inc=float(rec["measurement_inc"])
        str=float(rec["measurement_magn_moment"])
        brec=datablock[step-1]
        pdec=float(brec["measurement_dec"])
        pinc=float(brec["measurement_inc"])
        pint=float(brec["measurement_magn_moment"])
        X=dir2cart([dec,inc,str])
        prevX=dir2cart([pdec,pinc,pint])
        I=[]
        for c in range(3): I.append(X[c]-prevX[c])
        dir2=cart2dir(I)
        zptrm_check.append([powt,dir2[0],dir2[1],dir2[2]])
    ## get pTRM tail checks together - 
    for powt in POWT_M:
        step=MSteps[POWT_M.index(powt)] # tail check step
        rec=datablock[step]
#        dec=float(rec["measurement_dec"])
#        inc=float(rec["measurement_inc"])
        str=float(rec["measurement_magn_moment"])
        step=ZSteps[POWT_Z.index(powt)]
        brec=datablock[step]
#        pdec=float(brec["measurement_dec"])
#        pinc=float(brec["measurement_inc"])
        pint=float(brec["measurement_magn_moment"])
#        X=dir2cart([dec,inc,str])
#        prevX=dir2cart([pdec,pinc,pint])
#        I=[]
#        for c in range(3):I.append(X[c]-prevX[c])
#        d=cart2dir(I)
 #       ptrm_tail.append([powt,d[0],d[1],d[2]])
        ptrm_tail.append([powt,0,0,str-pint])  # just do absolute magnitude difference # not vector diff
    #  check
    #
        if len(first_Z)!=len(first_I):
                   print len(first_Z),len(first_I)
                   print " Something wrong with this specimen! Better fix it or delete it "
                   raw_input(" press return to acknowledge message")
                   print MaxRec
    araiblock=(first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks,ThetaChecks,DeltaChecks)
    return araiblock,field
    
    #
def doigrf(long,lat,alt,date,**kwargs):
    """
#       calculates the interpolated (<2010) or extrapolated (>2010) main field and
#       secular variation coefficients and passes these to the Malin and Barraclough
#       routine to calculate the IGRF field. dgrf coefficients for 1945 to 2005, igrf for pre 1945 and post 2010 
#       from http://www.ngdc.noaa.gov/IAGA/vmod/igrf.html 
#
#      for dates prior to between 1900 and 1600, this program uses coefficients from the GUFM1 model of Jackson et al. 2000
#      prior to that, it uses either arch3k or one of the cals models
#    
#
#       input:
#       date  = Required date in years and decimals of a year (A.D.)
#       alt   = height above mean sea level in km (itype = 1 assumed)
#       lat   = latitude in degrees (-90 to 90)
#       long  = east longitude in degrees (0 to 360 or -180 to 180)
# Output:
#       x     = north component of the magnetic force in nT
#       y     = east component of the magnetic force in nT
#       z     = downward component of the magnetic force in nT
#       f     = total magnetic force in nT
#
#       To check the results you can run the interactive program at the NGDC
#        http://www.ngdc.noaa.gov/geomagmodels/IGRFWMM.jsp
    """

#
#
    gh,sv=[],[]
    colat = 90.-lat                                         
#! convert to colatitude for MB routine
    if long>0: long=long+360.                       
# ensure all positive east longitudes
    itype = 1                                                       
    models,igrf11coeffs=get_igrf11()
    if 'mod' in kwargs.keys():
        if kwargs['mod']=='arch3k':
            psvmodels,psvcoeffs=get_arch3k() # use ARCH3k coefficients
        elif kwargs['mod']=='cals3k':
            psvmodels,psvcoeffs=get_cals3k() # default: use CALS3K_4b coefficients between -1000,1900
        else:
            psvmodels,psvcoeffs=get_cals10k() # use prior to -1000
# use geodetic coordinates
    if 'models' in kwargs:
        if 'mod' in kwargs.keys():
            return psvmodels,psvcoeffs
        else:
            return models,igrf11coeffs
    if date<-8000:
        print 'too old'
        sys.exit()
    if date<-1000:
        model=date-date%50
        gh=psvcoeffs[psvcoeffs.index(model)]
        sv=(psvcoeffs[psvmodels.index(model+50)]-gh)/50.
        x,y,z,f=magsyn(gh,sv,model,date,itype,alt,colat,long)
    elif date<1900:
        model=date-date%50
        gh=psvcoeffs[psvmodels.index(model)]
        if model+50<1900:
            sv=(psvcoeffs[psvmodels.index(model+50)]-gh)/50.
        else:
            field2=igrf11coeffs[models.index(1900)][0:120]
            sv=(field2-gh)/float(1900-model)
        x,y,z,f=magsyn(gh,sv,model,date,itype,alt,colat,long)
    else:
        model=date-date%5
        if date<2010:
            gh=igrf11coeffs[models.index(model)]
            sv=(igrf11coeffs[models.index(model+5)]-gh)/5.
            x,y,z,f=magsyn(gh,sv,model,date,itype,alt,colat,long)
        else:
            gh=igrf11coeffs[models.index(2010)]
            sv=igrf11coeffs[models.index(2010.15)]
            x,y,z,f=magsyn(gh,sv,model,date,itype,alt,colat,long)
    if 'coeffs' in kwargs.keys():
        return gh
    else:
        return x,y,z,f
#
def get_igrf11():
    models=[1900, 1905, 1910, 1915, 1920, 1925, 1930, 1935, 1940, 1945, 1950, 1955, 1960, 1965, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010,2010.15]
    coeffs= numpy.array([[-31543,-31464,-31354,-31212,-31060,-30926,-30805,-30715,-30654,-30594,-30554,-30500,-30421,-30334,-30220,-30100,-29992,-29873,-29775,-29692,-29619.4,-29554.63,-29496.5,11.4],
    [-2298,-2298,-2297,-2306,-2317,-2318,-2316,-2306,-2292,-2285,-2250,-2215,-2169,-2119,-2068,-2013,-1956,-1905,-1848,-1784,-1728.2,-1669.05,-1585.9,16.7],
    [5922,5909,5898,5875,5845,5817,5808,5812,5821,5810,5815,5820,5791,5776,5737,5675,5604,5500,5406,5306,5186.1,5077.99,4945.1,-28.8],
    [-677,-728,-769,-802,-839,-893,-951,-1018,-1106,-1244,-1341,-1440,-1555,-1662,-1781,-1902,-1997,-2072,-2131,-2200,-2267.7,-2337.24,-2396.6,-11.3],
    [2905,2928,2948,2956,2959,2969,2980,2984,2981,2990,2998,3003,3002,2997,3000,3010,3027,3044,3059,3070,3068.4,3047.69,3026.0,-3.9],
    [-1061,-1086,-1128,-1191,-1259,-1334,-1424,-1520,-1614,-1702,-1810,-1898,-1967,-2016,-2047,-2067,-2129,-2197,-2279,-2366,-2481.6,-2594.50,-2707.7,-23.0],
    [924,1041,1176,1309,1407,1471,1517,1550,1566,1578,1576,1581,1590,1594,1611,1632,1663,1687,1686,1681,1670.9,1657.76,1668.6,2.7],
    [1121,1065,1000,917,823,728,644,586,528,477,381,291,206,114,25,-68,-200,-306,-373,-413,-458.0,-515.43,-575.4,-12.9],
    [1022,1037,1058,1084,1111,1140,1172,1206,1240,1282,1297,1302,1302,1297,1287,1276,1281,1296,1314,1335,1339.6,1336.30,1339.7,1.3],
    [-1469,-1494,-1524,-1559,-1600,-1645,-1692,-1740,-1790,-1834,-1889,-1944,-1992,-2038,-2091,-2144,-2180,-2208,-2239,-2267,-2288.0,-2305.83,-2326.3,-3.9],
    [-330,-357,-389,-421,-445,-462,-480,-494,-499,-499,-476,-462,-414,-404,-366,-333,-336,-310,-284,-262,-227.6,-198.86,-160.5,8.6],
    [1256,1239,1223,1212,1205,1202,1205,1215,1232,1255,1274,1288,1289,1292,1278,1260,1251,1247,1248,1249,1252.1,1246.39,1231.7,-2.9],
    [3,34,62,84,103,119,133,146,163,186,206,216,224,240,251,262,271,284,293,302,293.4,269.72,251.7,-2.9],
    [572,635,705,778,839,881,907,918,916,913,896,882,878,856,838,830,833,829,802,759,714.5,672.51,634.2,-8.1],
    [523,480,425,360,293,229,166,101,43,-11,-46,-83,-130,-165,-196,-223,-252,-297,-352,-427,-491.1,-524.72,-536.8,-2.1],
    [876,880,884,887,889,891,896,903,914,944,954,958,957,957,952,946,938,936,939,940,932.3,920.55,912.6,-1.4],
    [628,643,660,678,695,711,727,744,762,776,792,796,800,804,800,791,782,780,780,780,786.8,797.96,809.0,2.0],
    [195,203,211,218,220,216,205,188,169,144,136,133,135,148,167,191,212,232,247,262,272.6,282.07,286.4,0.4],
    [660,653,644,631,616,601,584,565,550,544,528,510,504,479,461,438,398,361,325,290,250.0,210.65,166.6,-8.9],
    [-69,-77,-90,-109,-134,-163,-195,-226,-252,-276,-278,-274,-278,-269,-266,-265,-257,-249,-240,-236,-231.9,-225.23,-211.2,3.2],
    [-361,-380,-400,-416,-424,-426,-422,-415,-405,-421,-408,-397,-394,-390,-395,-405,-419,-424,-423,-418,-403.0,-379.86,-357.1,4.4],
    [-210,-201,-189,-173,-153,-130,-109,-90,-72,-55,-37,-23,3,13,26,39,53,69,84,97,119.8,145.15,164.4,3.6],
    [134,146,160,178,199,217,234,249,265,304,303,290,269,252,234,216,199,170,141,122,111.3,100.00,89.7,-2.3],
    [-75,-65,-55,-51,-57,-70,-90,-114,-141,-178,-210,-230,-255,-269,-279,-288,-297,-297,-299,-306,-303.8,-305.36,-309.2,-0.8],
    [-184,-192,-201,-211,-221,-230,-237,-241,-241,-253,-240,-229,-222,-219,-216,-218,-218,-214,-214,-214,-218.8,-227.00,-231.1,-0.5],
    [328,328,327,327,326,326,327,329,334,346,349,360,362,358,359,356,357,355,353,352,351.4,354.41,357.2,0.5],
    [-210,-193,-172,-148,-122,-96,-72,-51,-33,-12,3,15,16,19,26,31,46,47,46,46,43.8,42.72,44.7,0.5],
    [264,259,253,245,236,226,218,211,208,194,211,230,242,254,262,264,261,253,245,235,222.3,208.95,200.3,-1.5],
    [53,56,57,58,58,58,60,64,71,95,103,110,125,128,139,148,150,150,154,165,171.9,180.25,188.9,1.5],
    [5,-1,-9,-16,-23,-28,-32,-33,-33,-20,-20,-23,-26,-31,-42,-59,-74,-93,-109,-118,-130.4,-136.54,-141.2,-0.7],
    [-33,-32,-33,-34,-38,-44,-53,-64,-75,-67,-87,-98,-117,-126,-139,-152,-151,-154,-153,-143,-133.1,-123.45,-118.1,0.9],
    [-86,-93,-102,-111,-119,-125,-131,-136,-141,-142,-147,-152,-156,-157,-160,-159,-162,-164,-165,-166,-168.6,-168.05,-163.1,1.3],
    [-124,-125,-126,-126,-125,-122,-118,-115,-113,-119,-122,-121,-114,-97,-91,-83,-78,-75,-69,-55,-39.3,-19.57,0.1,3.7],
    [-16,-26,-38,-51,-62,-69,-74,-76,-76,-82,-76,-69,-63,-62,-56,-49,-48,-46,-36,-17,-12.9,-13.55,-7.7,1.4],
    [3,11,21,32,43,51,58,64,69,82,80,78,81,81,83,88,92,95,97,107,106.3,103.85,100.9,-0.6],
    [63,62,62,61,61,61,60,59,57,59,54,47,46,45,43,45,48,53,61,68,72.3,73.60,72.8,-0.3],
    [61,60,58,57,55,54,53,53,54,57,57,57,58,61,64,66,66,65,65,67,68.2,69.56,68.6,-0.3],
    [-9,-7,-5,-2,0,3,4,4,4,6,-1,-9,-10,-11,-12,-13,-15,-16,-16,-17,-17.4,-20.33,-20.8,-0.1],
    [-11,-11,-11,-10,-10,-9,-9,-8,-7,6,4,3,1,8,15,28,42,51,59,68,74.2,76.74,76.0,-0.3],
    [83,86,89,93,96,99,102,104,105,100,99,96,99,100,100,99,93,88,82,72,63.7,54.75,44.2,-2.1],
    [-217,-221,-224,-228,-233,-238,-242,-246,-249,-246,-247,-247,-237,-228,-212,-198,-192,-185,-178,-170,-160.9,-151.34,-141.4,1.9],
    [2,4,5,8,11,14,19,25,33,16,33,48,60,68,72,75,71,69,69,67,65.1,63.63,61.5,-0.4],
    [-58,-57,-54,-51,-46,-40,-32,-25,-18,-25,-16,-8,-1,4,2,1,4,4,3,-1,-5.9,-14.58,-22.9,-1.6],
    [-35,-32,-29,-26,-22,-18,-16,-15,-15,-9,-12,-16,-20,-32,-37,-41,-43,-48,-52,-58,-61.2,-63.53,-66.3,-0.5],
    [59,57,54,49,44,39,32,25,18,21,12,7,-2,1,3,6,14,16,18,19,16.9,14.58,13.1,-0.2],
    [36,32,28,23,18,13,8,4,0,-16,-12,-12,-11,-8,-6,-4,-2,-1,1,1,0.7,0.24,3.1,0.8],
    [-90,-92,-95,-98,-101,-103,-104,-106,-107,-104,-105,-107,-113,-111,-112,-111,-108,-102,-96,-93,-90.4,-86.36,-77.9,1.8],
    [-69,-67,-65,-62,-57,-52,-46,-40,-33,-39,-30,-24,-17,-7,1,11,17,21,24,36,43.8,50.94,54.9,0.5],
    [70,70,71,72,73,73,74,74,74,70,65,65,67,75,72,71,72,74,77,77,79.0,79.88,80.4,0.2],
    [-55,-54,-54,-54,-54,-54,-54,-53,-53,-40,-55,-56,-56,-57,-57,-56,-59,-62,-64,-72,-74.0,-74.46,-75.0,-0.1],
    [-45,-46,-47,-48,-49,-50,-51,-52,-52,-45,-35,-50,-55,-61,-70,-77,-82,-83,-80,-69,-64.6,-61.14,-57.8,0.6],
    [0,0,1,2,2,3,4,4,4,0,2,2,5,4,1,1,2,3,2,1,0.0,-1.65,-4.7,-0.6],
    [-13,-14,-14,-14,-14,-14,-15,-17,-18,-18,-17,-24,-28,-27,-27,-26,-27,-27,-26,-25,-24.2,-22.57,-21.2,0.3],
    [34,33,32,31,29,27,25,23,20,0,1,10,15,13,14,16,21,24,26,28,33.3,38.73,45.3,1.4],
    [-10,-11,-12,-12,-13,-14,-14,-14,-14,2,0,-4,-6,-2,-4,-5,-5,-2,0,4,6.2,6.82,6.6,-0.2],
    [-41,-41,-40,-38,-37,-35,-34,-33,-31,-29,-40,-32,-32,-26,-22,-14,-12,-6,-1,5,9.1,12.30,14.0,0.3],
    [-1,0,1,2,4,5,6,7,7,6,10,8,7,6,8,10,16,20,21,24,24.0,25.35,24.9,-0.1],
    [-21,-20,-19,-18,-16,-14,-12,-11,-9,-10,-7,-11,-7,-6,-2,0,1,4,5,4,6.9,9.37,10.4,0.1],
    [28,28,28,28,28,29,29,29,29,28,36,28,23,26,23,22,18,17,17,17,14.8,10.93,7.0,-0.8],
    [18,18,18,19,19,19,18,18,17,15,5,9,17,13,13,12,11,10,9,8,7.3,5.42,1.6,-0.8],
    [-12,-12,-13,-15,-16,-17,-18,-19,-20,-17,-18,-20,-18,-23,-23,-23,-23,-23,-23,-24,-25.4,-26.32,-27.7,-0.3],
    [6,6,6,6,6,6,6,6,5,29,19,18,8,1,-2,-5,-2,0,0,-2,-1.2,1.94,4.9,0.4],
    [-22,-22,-22,-22,-22,-21,-20,-19,-19,-22,-16,-18,-17,-12,-11,-12,-10,-7,-4,-6,-5.8,-4.64,-3.4,0.2],
    [11,11,11,11,11,11,11,11,11,13,22,11,15,13,14,14,18,21,23,25,24.4,24.80,24.3,-0.1],
    [8,8,8,8,7,7,7,7,7,7,15,9,6,5,6,6,6,6,5,6,6.6,7.62,8.2,0.1],
    [8,8,8,8,8,8,8,8,8,12,5,10,11,7,7,6,7,8,10,11,11.9,11.20,10.9,0.0],
    [-4,-4,-4,-4,-3,-3,-3,-3,-3,-8,-4,-6,-4,-4,-2,-1,0,0,-1,-6,-9.2,-11.73,-14.5,-0.5],
    [-14,-15,-15,-15,-15,-15,-15,-15,-14,-21,-22,-15,-14,-12,-15,-16,-18,-19,-19,-21,-21.5,-20.88,-20.0,0.2],
    [-9,-9,-9,-9,-9,-9,-9,-9,-10,-5,-1,-14,-11,-14,-13,-12,-11,-11,-10,-9,-7.9,-6.88,-5.7,0.3],
    [7,7,6,6,6,6,5,5,5,-12,0,5,7,9,6,4,4,5,6,8,8.5,9.83,11.9,0.5],
    [1,1,1,2,2,2,2,1,1,9,11,6,2,0,-3,-8,-7,-9,-12,-14,-16.6,-18.11,-19.3,-0.3],
    [-13,-13,-13,-13,-14,-14,-14,-15,-15,-7,-21,-23,-18,-16,-17,-19,-22,-23,-22,-23,-21.5,-19.71,-17.4,0.4],
    [2,2,2,3,4,4,5,6,6,7,15,10,10,8,5,4,4,4,3,9,9.1,10.17,11.6,0.3],
    [5,5,5,5,5,5,5,5,5,2,-8,3,4,4,6,6,9,11,12,15,15.5,16.22,16.7,0.1],
    [-9,-8,-8,-8,-7,-7,-6,-6,-5,-10,-13,-7,-5,-1,0,0,3,4,4,6,7.0,9.36,10.9,0.2],
    [16,16,16,16,17,17,18,18,19,18,17,23,23,24,21,18,16,14,12,11,8.9,7.61,7.1,-0.1],
    [5,5,5,6,6,7,8,8,9,7,5,6,10,11,11,10,6,4,2,-5,-7.9,-11.25,-14.1,-0.5],
    [-5,-5,-5,-5,-5,-5,-5,-5,-5,3,-4,-4,1,-3,-6,-10,-13,-15,-16,-16,-14.9,-12.76,-10.8,0.4],
    [8,8,8,8,8,8,8,7,7,2,-1,9,8,4,3,1,-1,-4,-6,-7,-7.0,-4.87,-3.7,0.2],
    [-18,-18,-18,-18,-19,-19,-19,-19,-19,-11,-17,-13,-20,-17,-16,-17,-15,-11,-10,-4,-2.1,-0.06,1.7,0.4],
    [8,8,8,8,8,8,8,8,8,5,3,4,4,8,8,7,5,5,4,4,5.0,5.58,5.4,0.0],
    [10,10,10,10,10,10,10,10,10,-21,-7,9,6,10,10,10,10,10,9,9,9.4,9.76,9.4,0.0],
    [-20,-20,-20,-20,-20,-20,-20,-20,-21,-27,-24,-11,-18,-22,-21,-21,-21,-21,-20,-20,-19.7,-20.11,-20.5,0.0],
    [1,1,1,1,1,1,1,1,1,1,-1,-4,0,2,2,2,1,1,1,3,3.0,3.58,3.4,0.0],
    [14,14,14,14,14,14,14,15,15,17,19,12,12,15,16,16,16,15,15,15,13.4,12.69,11.6,0.0],
    [-11,-11,-11,-11,-11,-11,-12,-12,-12,-11,-25,-5,-9,-13,-12,-12,-12,-12,-12,-10,-8.4,-6.94,-5.3,0.0],
    [5,5,5,5,5,5,5,5,5,29,12,7,2,7,6,7,9,9,11,12,12.5,12.67,12.8,0.0],
    [12,12,12,12,12,12,12,11,11,3,10,2,1,10,10,10,9,9,9,8,6.3,5.01,3.1,0.0],
    [-3,-3,-3,-3,-3,-3,-3,-3,-3,-9,2,6,0,-4,-4,-4,-5,-6,-7,-6,-6.2,-6.72,-7.2,0.0],
    [1,1,1,1,1,1,1,1,1,16,5,4,4,-1,-1,-1,-3,-3,-4,-8,-8.9,-10.76,-12.4,0.0],
    [-2,-2,-2,-2,-2,-2,-2,-3,-3,4,2,-2,-3,-5,-5,-5,-6,-6,-7,-8,-8.4,-8.16,-7.4,0.0],
    [-2,-2,-2,-2,-2,-2,-2,-2,-2,-3,-5,1,-1,-1,0,-1,-1,-1,-2,-1,-1.5,-1.25,-0.8,0.0],
    [8,8,8,8,9,9,9,9,9,9,8,10,9,10,10,10,9,9,9,8,8.4,8.10,8.0,0.0],
    [2,2,2,2,2,2,3,3,3,-4,-2,2,-2,5,3,4,7,7,7,10,9.3,8.76,8.4,0.0],
    [10,10,10,10,10,10,10,11,11,6,8,7,8,10,11,11,10,9,8,5,3.8,2.92,2.2,0.0],
    [-1,0,0,0,0,0,0,0,1,-3,3,2,3,1,1,1,2,1,1,-2,-4.3,-6.66,-8.4,0.0],
    [-2,-2,-2,-2,-2,-2,-2,-2,-2,1,-11,-6,0,-4,-2,-3,-6,-7,-7,-8,-8.2,-7.73,-6.1,0.0],
    [-1,-1,-1,-1,-1,-1,-2,-2,-2,-4,8,5,-1,-2,-1,-2,-5,-5,-6,-8,-8.2,-9.22,-10.1,0.0],
    [2,2,2,2,2,2,2,2,2,8,-7,5,5,1,1,1,2,2,2,3,4.8,6.01,7.0,0.0],
    [-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-8,-3,1,-2,-3,-3,-4,-4,-3,-3,-2.6,-2.17,-2.0,0.0],
    [-4,-4,-4,-4,-4,-4,-4,-4,-4,11,4,-5,-3,-3,-3,-3,-4,-4,-4,-6,-6.0,-6.12,-6.3,0.0],
    [2,2,2,2,2,2,2,2,2,5,13,-4,4,2,1,1,1,1,2,1,1.7,2.19,2.8,0.0],
    [2,2,2,2,2,2,2,2,2,1,-1,-1,4,2,2,2,2,3,2,2,1.7,1.42,0.9,0.0],
    [1,1,1,1,1,1,1,1,1,1,-2,0,1,1,1,1,0,0,1,0,0.0,0.10,-0.1,0.0],
    [-5,-5,-5,-5,-5,-5,-5,-5,-5,2,13,2,0,-5,-5,-5,-5,-5,-5,-4,-3.1,-2.35,-1.1,0.0],
    [2,2,2,2,2,2,2,2,2,-20,-10,-8,0,2,3,3,3,3,3,4,4.0,4.46,4.7,0.0],
    [-2,-2,-2,-2,-2,-2,-2,-2,-2,-5,-4,-3,-1,-2,-1,-2,-2,-2,-2,-1,-0.5,-0.15,-0.2,0.0],
    [6,6,6,6,6,6,6,6,6,-1,2,-2,2,6,4,4,6,6,6,5,4.9,4.76,4.4,0.0],
    [6,6,6,6,6,6,6,6,6,-1,4,7,4,4,6,5,5,5,4,4,3.7,3.06,2.5,0.0],
    [-4,-4,-4,-4,-4,-4,-4,-4,-4,-6,-3,-4,-5,-4,-4,-4,-4,-4,-4,-5,-5.9,-6.58,-7.2,0.0],
    [4,4,4,4,4,4,4,4,4,8,12,4,6,4,4,4,3,3,3,2,1.0,0.29,-0.3,0.0],
    [0,0,0,0,0,0,0,0,0,6,6,1,1,0,0,-1,0,0,0,-1,-1.2,-1.01,-1.0,0.0],
    [0,0,0,0,0,0,0,0,0,-1,3,-2,1,0,1,1,1,1,1,2,2.0,2.06,2.2,0.0],
    [-2,-2,-2,-2,-2,-2,-2,-1,-1,-4,-3,-3,-1,-2,-1,-1,-1,-1,-2,-2,-2.9,-3.47,-4.0,0.0],
    [2,2,2,1,1,1,1,2,2,-3,2,6,-1,2,0,0,2,2,3,5,4.2,3.77,3.1,0.0],
    [4,4,4,4,4,4,4,4,4,-2,6,7,6,3,3,3,4,4,3,1,0.2,-0.86,-2.0,0.0],
    [2,2,2,2,3,3,3,3,3,5,10,-2,2,2,3,3,3,3,3,1,0.3,-0.21,-1.0,0.0],
    [0,0,0,0,0,0,0,0,0,0,11,-1,0,0,1,1,0,0,-1,-2,-2.2,-2.31,-2.0,0.0],
    [0,0,0,0,0,0,0,0,0,-2,3,0,0,0,-1,-1,0,0,0,0,-1.1,-2.09,-2.8,0.0],
    [-6,-6,-6,-6,-6,-6,-6,-6,-6,-2,8,-3,-7,-6,-4,-5,-6,-6,-6,-7,-7.4,-7.93,-8.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2.7,2.95,3.0,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1.7,-1.60,-1.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.1,0.26,0.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1.9,-1.88,-2.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.3,1.44,1.7,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.5,1.44,1.6,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.9,-0.77,-0.6,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.1,-0.31,-0.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-2.6,-2.27,-1.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.1,0.29,0.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.9,0.90,0.9,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.7,-0.79,-0.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.7,-0.58,-0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.7,0.53,0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-2.8,-2.69,-2.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.7,1.80,1.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.9,-1.08,-1.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.1,0.16,0.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1.2,-1.58,-2.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.2,0.96,0.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1.9,-1.90,-1.9,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4.0,3.99,3.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.9,-1.39,-1.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-2.2,-2.15,-2.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.3,-0.29,-0.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.4,-0.55,-0.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.2,0.21,0.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.3,0.23,0.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.9,0.89,1.0,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2.5,2.38,2.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.2,-0.38,-0.7,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-2.6,-2.63,-2.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.9,0.96,0.9,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.7,0.61,0.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.5,-0.30,-0.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.3,0.40,0.6,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.3,0.46,0.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0,0.01,0.0,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.3,-0.35,-0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0,0.02,0.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.4,-0.36,-0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.3,0.28,0.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.1,0.08,0.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.9,-0.87,-0.9,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.2,-0.49,-0.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.4,-0.34,-0.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.4,-0.08,0.0,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.8,0.88,0.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.2,-0.16,-0.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.9,-0.88,-0.9,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.9,-0.76,-0.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.3,0.30,0.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.2,0.33,0.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.1,0.28,0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.8,1.72,1.7,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.4,-0.43,-0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.4,-0.54,-0.6,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.3,1.18,1.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1.0,-1.07,-1.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.4,-0.37,-0.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.1,-0.04,-0.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.7,0.75,0.8,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.7,0.63,0.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.4,-0.26,-0.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.3,0.21,0.1,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.3,0.35,0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.6,0.53,0.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.1,-0.05,0.0,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.3,0.38,0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.4,0.41,0.4,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.2,-0.22,-0.2,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0,-0.10,-0.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.5,-0.57,-0.5,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.1,-0.18,-0.3,0.0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.9,-0.82,-0.8,0.0]]).transpose()
    return models, coeffs

def get_cals3k():
    models=[-1000, -950, -900, -850, -800, -750, -700, -650, -600, -550, -500, -450, -400, -350, -300, -250, -200, -150, -100, -50, 0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600,650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 1850]
    coeffs= numpy.array([[-3.371973835505838360e+04,-2.637483127065906388e+02,-3.182517180476654175e+03,-1.429827060584611900e+03,-3.025541082597257628e+03,2.131552594373067677e+02,2.266511415135732477e+03,-3.602347472564175632e+02,-6.717056721155671539e+02,8.867320397791309006e+02,2.825503991406449700e+02,-6.723409896882714065e+02,-4.265622300090018371e+01,-2.479831630264299633e+02,4.222624705996046259e+02,-3.529897284659763841e+02,-3.315631343829834350e+02,2.771899687878023997e+02,-9.305109847217473771e+02,-2.830791114508747341e+02,-1.244583793840007786e+02,-2.519870986685857872e+01,2.433992192663830281e+02,-4.699600448877839085e+02,8.390467870246402526e+01,9.467156259212811165e+01,-6.285084553883064018e+01,1.444416077610565878e+02,1.090193639392103364e+02,1.233527076252275378e+02,-1.801389576646381840e+02,-1.667009914125297598e+02,-1.349525840636474783e+01,-2.092129264009508347e+02,2.684656033335692769e+02,-9.364339344224543282e+00,2.748591635633186314e+01,2.248975821980631906e+01,1.275300254126040755e+01,-1.531273119213398104e+01,-4.584684050682281509e+01,-7.534701296023555983e+01,-9.199021175931964933e+01,-3.906101287250196119e+00,-6.899939021671339390e+01,4.524824980007841191e+01,-2.893502410551764115e+01,-1.319153864112146834e+01,2.154436673082064324e+00,2.966708877807920253e+00,1.337087142226235148e+00,5.259845058418675556e+00,-6.451942991190254162e+00,-3.652504881857559393e+00,-1.851825208104409981e+01,-1.503572865268170577e+00,-2.968805216769892041e+01,-3.086776100541900547e+01,-2.225601786079300481e+00,-1.203041048590876549e+01,1.642933629810828222e+01,3.959353332002265358e+00,9.813072597464287838e+00,5.084968678880742443e-01,8.927548157058996514e-01,-5.049513185216417455e+00,2.992236082830670441e+00,1.189848987790705692e+00,5.161268102484536158e+00,-2.724249599049376691e+00,-2.931666509033242551e+00,-4.689519202103889839e+00,-8.616169746170944777e+00,6.111967670686221155e+00,-3.401470841349071961e+00,8.104633998494222169e+00,-3.396058788203837331e+00,-2.340165149151129498e+00,-3.436531738984788475e+00,-1.478847788248174977e+00,-1.807500623757149205e-01,-8.893179458723869946e-01,2.573152213919582820e-01,-2.186184020420782748e-01,-8.096304764199431514e-02,-5.411803880834294977e-01,-4.551331756737759249e-01,-6.400123406715370056e-01,-1.608054640469032348e+00,-8.099989287388975612e-01,-2.700992758624647383e-01,-9.511575741985645038e-01,5.867276594775461263e-01,-5.985262562608120174e-01,-3.556487208417905554e-01,-9.824989841152820258e-02,-1.040505818585571784e+00,2.816145042340302274e-01,-7.393805074021785328e-01,-7.533128704618248517e-02,9.015428000219517790e-03,-1.358381843196785344e-01,-5.792106675400368609e-02,-1.364836136796775401e-01,2.573405710368518659e-02,4.755450124953274071e-02,2.563841640878813388e-01,-1.525717422569146664e-01,-1.401223892038745700e-01,2.647979369684170387e-02,2.104131341828635315e-01,8.367963578879074049e-01,6.116263830137875779e-01,8.812765284248312569e-02,-9.407660012225718682e-02,-7.148446308934208737e-01,-4.685169037062388853e-01,-2.587916461654701794e-01,-9.685104403349376057e-02,1.803319184754505755e-01],
    [-3.388785471108437923e+04,-5.159619684154215520e+02,-3.082756929749083611e+03,-1.242124388385167777e+03,-2.858243897205784833e+03,2.303379295691564153e+02,2.178847494600404843e+03,-2.921897914035978943e+02,-8.464487736947573921e+02,7.578765847941325546e+02,2.196854449943864154e+02,-6.098193587261404218e+02,-6.535851027180695105e+00,-3.013375210265371607e+02,4.982688498598349724e+02,-3.262097045452721886e+02,-3.573361540672205479e+02,2.839766284186438838e+02,-9.176226959982445806e+02,-2.682343954043750500e+02,-9.531536936295157147e+01,-3.926523893446949387e+01,2.515928231573385858e+02,-5.253627782340622616e+02,6.872034223119504759e+01,9.555792772191671247e+01,-7.877256309675181001e+01,1.491339078194980061e+02,1.027398005705644266e+02,1.408239450609028722e+02,-1.991112957318834447e+02,-1.698409786720398529e+02,-3.636342724680849869e+01,-2.226722004692410337e+02,2.809271888827254884e+02,-6.022613945435073113e+00,2.588530689686472286e+01,2.883221117340103490e+01,9.057924941423795673e+00,-1.585361747857608172e+01,-4.488928511781912079e+01,-8.334027084759486570e+01,-9.690924055968916662e+01,-8.881500950250963200e+00,-7.409759187343340159e+01,4.705063217480939386e+01,-2.710536970080985952e+01,-1.476699517102891335e+01,1.922175321219813160e+00,3.790735685213181938e+00,2.228606511282469338e-01,5.101479307298988353e+00,-8.055149891479780777e+00,-2.576860370031397895e+00,-1.999815905173480246e+01,-1.309624388968724240e+00,-3.102264911731907659e+01,-3.227012794529935036e+01,-1.458098972823068218e+00,-1.225078545657092732e+01,1.687912104143452297e+01,3.727525118610946375e+00,9.641803270117724978e+00,6.355635665422332270e-01,1.081328049366331756e+00,-4.800851697432539922e+00,2.639658034620722127e+00,1.080017446393592317e+00,5.390525792771735603e+00,-2.945108339504182382e+00,-2.819952309311894556e+00,-5.296456552467837753e+00,-9.230845881510120421e+00,6.366162458044616557e+00,-3.487911960717728466e+00,8.420305763762305773e+00,-3.558384589937571896e+00,-2.659711085376050832e+00,-3.520456632573893518e+00,-1.509837718556766406e+00,-1.059748951764174635e-01,-8.624382658848483985e-01,2.959092947993856582e-01,-8.490295531999064726e-02,5.671480559287765677e-02,-5.863306153615366334e-01,-4.837657158164617166e-01,-6.230983571620147821e-01,-1.811456683393079636e+00,-8.932705760101601333e-01,-2.914177072843990302e-01,-1.024510892649701077e+00,5.973255491850261167e-01,-6.420846315935960780e-01,-5.226443958085973396e-01,-1.071050532006920797e-01,-1.033211617829658202e+00,2.946473100741104356e-01,-7.417742707988652651e-01,-1.098470380342991548e-01,1.406026750864134388e-02,-1.300905249316655909e-01,-3.636681291399249116e-02,-1.485114535634251276e-01,3.645619072281958140e-02,3.220560900581899422e-02,3.193613386072442495e-01,-1.929499661579320013e-01,-1.349027224414157955e-01,1.816211888929936688e-03,1.882296308128581230e-01,8.668225862217467936e-01,6.006090767571240496e-01,6.441897173512645125e-02,-1.297453688342141420e-01,-7.456268149198870265e-01,-4.888821889668303333e-01,-2.663544437491371930e-01,-9.949456785972667083e-02,1.959441383328379416e-01],
    [-3.397866169487794832e+04,-7.435696850452688977e+02,-2.871546540909014766e+03,-1.041550679547531672e+03,-2.635603182755573016e+03,2.208319843233664983e+02,2.078810631458664375e+03,-2.331528685472983966e+02,-9.796056248699644584e+02,5.872400102373319442e+02,2.072125231589710097e+02,-5.502980190797269415e+02,2.445369594542345837e+01,-3.607010538636476440e+02,5.951839883978371972e+02,-2.902121534288279463e+02,-3.809740221659121744e+02,2.865428930749429810e+02,-9.058806659193104451e+02,-2.436786307744203555e+02,-6.566583882249838666e+01,-4.880511807106398692e+01,2.623674907099268694e+02,-5.906666950482442644e+02,5.703471417775588748e+01,9.789347252210717443e+01,-1.010257119110051462e+02,1.585696988126501594e+02,9.934219822554459256e+01,1.635353372865430686e+02,-2.162706643971329186e+02,-1.733389197914927990e+02,-6.174823555839972755e+01,-2.409901302737250148e+02,2.975084563038955707e+02,-1.410096627392092072e+00,2.430861087573067891e+01,3.386238676379730350e+01,5.712111943873281028e+00,-1.518178844222109802e+01,-4.550042320633608028e+01,-9.091318157840115077e+01,-1.031012447497080871e+02,-1.469697952302543520e+01,-8.008889346881609583e+01,4.869317043865110861e+01,-2.511271343783998589e+01,-1.675307910921740984e+01,1.721786777158146542e+00,4.300352329735749990e+00,-1.239821344449930196e+00,4.891313313913787653e+00,-1.034455035401132150e+01,-1.749419425690390328e+00,-2.119834522032600077e+01,-1.098944943194409607e+00,-3.273518423192533078e+01,-3.372977206591664867e+01,-1.198888118575442308e+00,-1.224920648448843252e+01,1.747799239117777148e+01,3.704988770649985774e+00,9.655738929409773519e+00,8.416985893399758778e-01,1.242876837926121025e+00,-4.628518909646196278e+00,2.302363476892840932e+00,8.354760460382859577e-01,5.647928043279440757e+00,-3.028438017290494777e+00,-2.750268918989702271e+00,-5.918598108204736974e+00,-9.929339753726184270e+00,6.591982768826568417e+00,-3.512896367793294061e+00,8.787643616060972107e+00,-3.718605298066663067e+00,-3.016432353394419508e+00,-3.660404381300486953e+00,-1.612920625957561693e+00,-4.977977085951339545e-03,-8.451714698354871880e-01,3.656685993911104604e-01,5.192118286994538978e-02,1.658843825563403040e-01,-6.177702143618213348e-01,-4.889372907524117129e-01,-6.404207427360834037e-01,-2.022068234763637395e+00,-9.855430148070482010e-01,-3.729812004034835926e-01,-1.082552591704208700e+00,5.470058954398548945e-01,-6.771835923593813034e-01,-7.112676509846755923e-01,-1.005895989279852187e-01,-1.032798967690739200e+00,3.156325531104279269e-01,-7.668951631249776302e-01,-1.418113100201344179e-01,2.015190965476645196e-02,-1.108378705228881544e-01,-1.326823409273956110e-02,-1.720378940191007178e-01,5.807414350885716642e-02,1.095148631462374705e-02,4.000957570322306034e-01,-2.339251308732262502e-01,-1.230877666299034223e-01,-3.385088185720639548e-02,1.728105238567649027e-01,8.917777376212477902e-01,6.001978563463120642e-01,3.972291504625542757e-02,-1.644796027201465005e-01,-7.770928367586753538e-01,-5.180794085775540792e-01,-2.749828676541693495e-01,-1.084324817251655915e-01,2.167381287737740470e-01],
    [-3.404727757954374101e+04,-9.035453280734176360e+02,-2.640260312237453491e+03,-9.015448744366960909e+02,-2.397264766662137845e+03,1.904674472446247648e+02,1.931817042274123651e+03,-2.217913737764188795e+02,-1.067958865637790723e+03,3.816531632411195005e+02,2.316627230077590980e+02,-5.027420148229168149e+02,3.551289876899499376e+01,-4.104541026535293327e+02,6.698974049159213564e+02,-2.511772100788635669e+02,-3.868564186615647031e+02,2.791934062762791768e+02,-9.015573021852451348e+02,-2.143386591185588372e+02,-3.035675572464127825e+01,-5.898008484421329456e+01,2.706262940008512032e+02,-6.562634739575837557e+02,4.771884301271759199e+01,1.008792679769870233e+02,-1.242184216733662652e+02,1.686841758507536611e+02,9.713433546623180348e+01,1.887793231982114719e+02,-2.314413631335756918e+02,-1.737374728242145636e+02,-9.021838583869848094e+01,-2.597281957441553004e+02,3.147189395125850524e+02,3.167898166577747254e+00,2.376610947431977294e+01,3.777166010817245478e+01,3.008293511104614737e+00,-1.283427569823975922e+01,-4.701207273213342575e+01,-9.732368613161614235e+01,-1.083962753437630511e+02,-2.152599207419802241e+01,-8.554648080916479103e+01,4.927760109325798510e+01,-2.257655034808797367e+01,-1.843053816657900512e+01,1.377825996837726885e+00,4.511738351103745437e+00,-2.610598090360760182e+00,4.839469487576995910e+00,-1.276129495239380418e+01,-1.238511677346287643e+00,-2.186330713200094422e+01,-6.437405335134130935e-01,-3.488762666184098293e+01,-3.470454295607110851e+01,-1.540686907243182358e+00,-1.184585886403480615e+01,1.815271638763915973e+01,3.888767917155666609e+00,9.698995987712079270e+00,1.025950707889288438e+00,1.284330293801157152e+00,-4.438595095878839381e+00,2.049029303634621435e+00,5.902588304609042158e-01,5.792142792269372009e+00,-3.008789393092387687e+00,-2.657538300014727461e+00,-6.568227503159769221e+00,-1.049230551660493305e+01,6.627407291400814415e+00,-3.349246282733080893e+00,9.130740147987369326e+00,-3.807218606109034731e+00,-3.331990085088550657e+00,-3.824980067428791486e+00,-1.757790484241971818e+00,9.503042257589658370e-02,-8.551542598119783456e-01,4.506002462867534364e-01,1.944480594774006810e-01,2.477383888828953440e-01,-6.365114396270943331e-01,-4.433327162142740585e-01,-6.874996622842501903e-01,-2.214434933733730571e+00,-1.052378555322722731e+00,-5.168162748517022287e-01,-1.099683670479087327e+00,4.532587374072589159e-01,-6.812379271213959697e-01,-8.929213576410126585e-01,-8.136695161049813108e-02,-1.025447194049359689e+00,3.354622566782128334e-01,-8.025051050145932674e-01,-1.649088848760247028e-01,1.559551771397624589e-02,-8.431247010674554343e-02,5.345918888517100023e-03,-1.967564913233085244e-01,8.336820832283314830e-02,-9.979969414556704929e-03,4.830259340763984888e-01,-2.703350322500513991e-01,-1.043899221884063977e-01,-7.847142400444430399e-02,1.718628960476253353e-01,9.022385253120639437e-01,6.083626382769048435e-01,1.877360312833317030e-02,-1.943513599591525365e-01,-7.996322206639973063e-01,-5.461346287958664947e-01,-2.806262467780624159e-01,-1.211941782729273887e-01,2.374503391010835684e-01],
    [-3.411501079306476458e+04,-1.154478543851087352e+03,-2.457972280526495069e+03,-8.582515132349933538e+02,-2.175068789668820500e+03,1.944383222697710494e+02,1.749791425171787978e+03,-2.035235937783040470e+02,-1.115836860981405835e+03,1.646850113093242669e+02,2.737390179162239292e+02,-4.765686378495188364e+02,2.344212535775184847e+01,-4.425161410786047327e+02,7.035961155575954535e+02,-2.095103253307577233e+02,-3.730568815323106264e+02,2.577234496098830050e+02,-9.075750971693710198e+02,-1.850046048016913574e+02,1.451395159797215584e+01,-6.819182169803272586e+01,2.707555443143227194e+02,-7.148936721215923171e+02,4.005416663398983701e+01,1.012662177016902234e+02,-1.441117394603170965e+02,1.755753075917488104e+02,9.268411548811350542e+01,2.134551036514965290e+02,-2.427150769165685347e+02,-1.700819731747184278e+02,-1.194685590699971272e+02,-2.726308396599976618e+02,3.295676511367522608e+02,6.691518609876951018e+00,2.461746206235923751e+01,4.096875710725379349e+01,7.871836151121303082e-01,-9.453473623688244842e+00,-4.845796429783008819e+01,-1.017838986292136099e+02,-1.105568786746851515e+02,-2.889827003455081567e+01,-8.884481525838612015e+01,4.810867771247176705e+01,-1.996149295454260653e+01,-1.960022223733433222e+01,7.524050443444258995e-01,4.679846760654795546e+00,-3.455831087441773697e+00,4.961070270893436884e+00,-1.469912814250366040e+01,-8.746745990531703541e-01,-2.194570035769462280e+01,3.944493763403824627e-01,-3.735409771636132348e+01,-3.482074595932045469e+01,-2.381647434809712749e+00,-1.110421838922346005e+01,1.887550913848683365e+01,4.360004098405870110e+00,9.739385431796833359e+00,1.091464313405037911e+00,1.203195068480183094e+00,-4.104571611582162660e+00,1.912244348126050708e+00,5.043702657466617723e-01,5.767040350935330295e+00,-2.965162274017610233e+00,-2.437353385945209450e+00,-7.225466076430636875e+00,-1.074048376705872521e+01,6.425504355807369450e+00,-2.978680956551199799e+00,9.413030686042334949e+00,-3.780403283796479386e+00,-3.529663332709620072e+00,-3.988557752578438365e+00,-1.923066966939801947e+00,1.665640591023940797e-01,-8.917499575165035441e-01,5.343202184592160675e-01,3.483941841865479394e-01,3.199262697943635048e-01,-6.485294299405791607e-01,-3.380200381845538393e-01,-7.460341524316106421e-01,-2.358410515833584853e+00,-1.056894340244450836e+00,-7.020558439250339511e-01,-1.063609919587485741e+00,3.642829772195046445e-01,-6.400171901574446265e-01,-1.030997477135085161e+00,-4.333248133539498170e-02,-1.017047472290384391e+00,3.492791034558958563e-01,-8.319547194913687882e-01,-1.751989819670279613e-01,-6.607763786018552334e-03,-5.965319329171817064e-02,1.721995709616537876e-02,-2.155392393767870951e-01,1.028352269852661482e-01,-2.056696171114592159e-02,5.498004599797569059e-01,-2.960687668452333665e-01,-7.780897480769854990e-02,-1.252952146748683715e-01,1.903236047836608658e-01,9.026689317575550264e-01,6.235598459732614174e-01,8.152861125435686973e-03,-2.147282092403152987e-01,-8.101465634161687523e-01,-5.662748755825827152e-01,-2.763446114039495582e-01,-1.327921690564245194e-01,2.545896379693917133e-01],
    [-3.421181504245140241e+04,-1.442490754564336612e+03,-2.281113707657606483e+03,-8.962865759438773239e+02,-1.950495102189078352e+03,2.501010762509658889e+02,1.571995583116241050e+03,-1.060531640320042612e+02,-1.128652358948745359e+03,-2.243332328870833337e+00,3.233622314624157070e+02,-4.541958451121724920e+02,1.041002497492905121e+01,-4.520697087839746473e+02,7.017582766440157229e+02,-1.694055137568829537e+02,-3.470175573223257857e+02,2.241420781909276911e+02,-9.109164960811420997e+02,-1.648303641321181203e+02,6.404860277180992512e+01,-6.630370745532475496e+01,2.539525928888906208e+02,-7.509971379998629573e+02,3.413501218298788586e+01,9.731084658024484213e+01,-1.587542055206339739e+02,1.792394427930826737e+02,8.418335723801807546e+01,2.352217704278390897e+02,-2.441355805341627274e+02,-1.644362550887908299e+02,-1.408125224234020152e+02,-2.747573941268615840e+02,3.400281092603784145e+02,8.874185188018264725e+00,2.585173348038079411e+01,4.361739672475535201e+01,-4.891120964547559513e-01,-6.445268689406983498e+00,-4.855415996296329695e+01,-1.027366391692294485e+02,-1.090773150381236860e+02,-3.411283884680216261e+01,-8.904340960282556239e+01,4.618444935161061693e+01,-1.820236270672415912e+01,-2.007408234913621570e+01,-5.397550386348171081e-02,4.928688209659091157e+00,-3.445008179136878734e+00,5.181868014469192651e+00,-1.585011089064608925e+01,-3.870832880362214956e-01,-2.163715089490361265e+01,2.098417409613908990e+00,-3.926549151539632021e+01,-3.405394526566481517e+01,-3.078735714937183676e+00,-1.038780474524186914e+01,1.968784305662167355e+01,5.080251713470100405e+00,9.875364460785206688e+00,1.041126569701265048e+00,1.097569197734843405e+00,-3.560068571922436753e+00,1.910726792600867530e+00,5.933391139964068195e-01,5.667480578960435444e+00,-2.989486374714829697e+00,-2.059625740687126338e+00,-7.722352254990759945e+00,-1.067603065380334115e+01,6.204451153724273027e+00,-2.557985028254731397e+00,9.709088015768962521e+00,-3.643143276447045054e+00,-3.519488673986144178e+00,-4.135009074519614636e+00,-2.103236175939556141e+00,2.105024061286285275e-01,-9.249658847909614234e-01,6.180736831829594102e-01,5.032191494011934996e-01,3.941652322183773483e-01,-6.462644413620600714e-01,-2.336099701856061417e-01,-7.859255212479160368e-01,-2.436677937401358740e+00,-1.005613206966846640e+00,-8.481342355257626142e-01,-1.003351757268513111e+00,3.490199243638646420e-01,-5.820842988521697237e-01,-1.084097576330124824e+00,-3.539585792265769089e-03,-1.018861358651578453e+00,3.501935582081926457e-01,-8.358688512229466294e-01,-1.729848858005801349e-01,-3.887133546145497831e-02,-4.125701623580210753e-02,2.562162227911628926e-02,-2.238522419816134923e-01,1.148633664058036630e-01,-2.285103396306644233e-02,5.896267133432383512e-01,-3.157528781369015602e-01,-4.502647180924349013e-02,-1.610242801567719761e-01,2.172593185635804114e-01,9.091484247401020458e-01,6.312710565227187542e-01,1.715425822684161355e-02,-2.274982672053142974e-01,-8.071009498127497128e-01,-5.776683531614289491e-01,-2.575133976209295628e-01,-1.403617737204706506e-01,2.638982221489615254e-01],
    [-3.449385591428855696e+04,-1.720361932141135412e+03,-2.067670339442361637e+03,-1.018528177939050920e+03,-1.764026659857144296e+03,3.328264937397044605e+02,1.424448148641223952e+03,7.199615653679248339e+01,-1.111246225863172867e+03,-9.536064235163354397e+01,3.681822781313288715e+02,-4.348016083310472482e+02,2.424489890990074947e+00,-4.293077922446921093e+02,6.726793696661565036e+02,-1.349848161456141042e+02,-3.220004388812103571e+02,1.845080857476719132e+02,-8.956949356926711516e+02,-1.639031948598093038e+02,1.098211090122644862e+02,-5.543723158002221396e+01,2.094685036127509363e+02,-7.629933533612610290e+02,3.070050613949037910e+01,9.013553006246647215e+01,-1.672019830241744671e+02,1.820779842284944152e+02,7.097216043057474621e+01,2.506508382123867023e+02,-2.350566606992985044e+02,-1.618971285577690651e+02,-1.498971889623243783e+02,-2.640758928954336966e+02,3.450612817088566544e+02,9.922163534145663988e+00,2.663489748976089544e+01,4.560533630850240883e+01,4.701349837914486907e-02,-5.139744081258976749e+00,-4.657590822411266629e+01,-9.999049155174439818e+01,-1.052967632753700968e+02,-3.637524258299276170e+01,-8.613066126818020507e+01,4.407417523424992822e+01,-1.786729047304993401e+01,-2.006874965851650572e+01,-7.294048927313822039e-01,5.217871484676149585e+00,-2.459123245566573246e+00,5.495561182140343170e+00,-1.619092855321346747e+01,4.030515322820746316e-01,-2.123665121648444298e+01,4.114691124410276402e+00,-4.003620959234243060e+01,-3.262990429544615978e+01,-3.288506134582040996e+00,-9.851959801800536098e+00,2.040629529154199062e+01,5.963250072337857866e+00,1.021087872847904521e+01,9.468633026534860608e-01,1.042910990693230344e+00,-2.846861701130681155e+00,2.040138893856115576e+00,7.703185853294363117e-01,5.640149077506202424e+00,-3.103333856184387507e+00,-1.567501595840145701e+00,-7.935809008821385291e+00,-1.039184463931861124e+01,6.074343140377187034e+00,-2.237108458658722210e+00,1.001813000706522772e+01,-3.415456634880908116e+00,-3.268102048123347814e+00,-4.214342617526503076e+00,-2.298246507097635671e+00,2.399441604355696533e-01,-9.295112821168362016e-01,7.049117668838615902e-01,6.369954178636179076e-01,4.653478364612932960e-01,-6.099448836110477057e-01,-1.844257101771749063e-01,-7.818223076227865942e-01,-2.449622497574110991e+00,-9.287651372511711578e-01,-8.948309468316624216e-01,-9.377318952406304975e-01,4.426761877765215125e-01,-5.159086942560056066e-01,-1.043646832774103750e+00,3.452273639290018292e-02,-1.050747404971794419e+00,3.320243992202390748e-01,-8.038118398784582785e-01,-1.596975617751422716e-01,-6.845161145717321149e-02,-2.960454738691255250e-02,3.545830768263948801e-02,-2.199735311200215482e-01,1.227014447845271999e-01,-2.142237433893347948e-02,6.000027025960780191e-01,-3.321204531467871757e-01,-1.118593063282516051e-02,-1.750010312794459955e-01,2.409941965054665791e-01,9.304450042260641318e-01,6.231953307778492768e-01,4.250414830819624484e-02,-2.318661334155243114e-01,-7.957001913605940002e-01,-5.808148307653486775e-01,-2.232196093997191877e-01,-1.409181856305715685e-01,2.640576812682634000e-01],
    [-3.483938834034981846e+04,-1.880157932422677959e+03,-1.867341650913676858e+03,-1.220612960592570516e+03,-1.618779851023460651e+03,4.169526277163886903e+02,1.306130629370696397e+03,2.831738202345991340e+02,-1.052650345162213398e+03,-1.358008851930149206e+02,4.239035944570873653e+02,-4.161108550269732405e+02,-3.378368387549239316e+01,-3.652360632871574353e+02,6.176187159587360611e+02,-1.076314915667522314e+02,-3.016978440372773207e+02,1.405988645051260448e+02,-8.571088131467979565e+02,-1.838126478762401064e+02,1.425797895888457276e+02,-4.706569880989363241e+01,1.398493033403107120e+02,-7.613891839052367914e+02,2.984371156084274546e+01,8.125219954132489875e+01,-1.697930781966418294e+02,1.860515052860790490e+02,5.389369534612661283e+01,2.568725879564321986e+02,-2.206575866375135320e+02,-1.673497968169383228e+02,-1.495663085101550678e+02,-2.421186255289293854e+02,3.463365193543833129e+02,1.011500529924829195e+01,2.655962863640554872e+01,4.633242900204612624e+01,2.760272256088377674e+00,-5.429157155190814876e+00,-4.429821120484926666e+01,-9.512858833340982301e+01,-1.017157288617574835e+02,-3.689913503089784541e+01,-8.067411791035921453e+01,4.181413701519217341e+01,-1.886590879101812490e+01,-2.031312099119007186e+01,-1.148133446218290388e+00,5.304639922400225416e+00,-8.784360212961763725e-01,5.701254686690136353e+00,-1.611834666119218440e+01,1.307678775405320959e+00,-2.093613295420623288e+01,5.820265455401806953e+00,-3.982341316733118930e+01,-3.089684489114251775e+01,-3.312851182686163298e+00,-9.492636891207384409e+00,2.085436434633839298e+01,6.891037684230369109e+00,1.094425665503175793e+01,9.164858854187003523e-01,1.022748693137359277e+00,-2.122983805695573434e+00,2.231613881483619721e+00,9.369381114620543016e-01,5.708193430291075288e+00,-3.253079092898362390e+00,-1.113550148492779668e+00,-7.909743456038991205e+00,-1.004345363704140404e+01,6.005496049474325027e+00,-2.085477434377769335e+00,1.029328160972630890e+01,-3.161597640440505064e+00,-2.826194565493012956e+00,-4.224427059803053552e+00,-2.505424891505728890e+00,2.713834153985566489e-01,-9.019866938166541948e-01,7.923543543027228298e-01,7.274519375655302822e-01,5.058638870417981881e-01,-5.386565538903721473e-01,-2.032125061191893400e-01,-7.677171381634062541e-01,-2.413230817273231743e+00,-8.597375935670270586e-01,-8.636852636255445415e-01,-8.709272499054983019e-01,6.130805322033218152e-01,-4.476639672670856829e-01,-9.393318321178873997e-01,7.651022378229738186e-02,-1.123107808346082814e+00,2.982406523193825709e-01,-7.385340038321100975e-01,-1.363306598488346899e-01,-8.560635979856784372e-02,-1.882362920274839591e-02,4.890562458634912374e-02,-2.117310938813865007e-01,1.276521732588384583e-01,-2.082565333634423324e-02,5.842998198781094166e-01,-3.480012721511370755e-01,1.837444554544596584e-02,-1.706847733638645614e-01,2.573158321153092842e-01,9.627691616214016923e-01,6.036556495580618353e-01,7.257000136850060013e-02,-2.297772500435756593e-01,-7.873535506516351479e-01,-5.826424430147050249e-01,-1.782703262074847306e-01,-1.342989483277554075e-01,2.586485220685590392e-01],
    [-3.521154996931951609e+04,-1.889210806328207582e+03,-1.713122570190223996e+03,-1.460181547087731360e+03,-1.584107007416746001e+03,5.164528356610073843e+02,1.199345090020533917e+03,5.024585912260462806e+02,-9.554587332371379489e+02,-1.638145535232729060e+02,5.035499027653153234e+02,-3.925520031920570432e+02,-1.167366464575511458e+02,-2.607620325613308410e+02,5.434427091466761794e+02,-8.227488545094887229e+01,-2.843900411552253331e+02,9.295211621933806612e+01,-8.090275491492868696e+02,-2.194564988391903171e+02,1.557331547472011550e+02,-4.505297922669004151e+01,5.996670862164171467e+01,-7.531377982045970612e+02,3.212474710345697559e+01,7.218841394369042064e+01,-1.698499710265946305e+02,1.896983293217191715e+02,3.613006277598772442e+01,2.525487928245702278e+02,-2.062650116432590437e+02,-1.808442854357479064e+02,-1.459622731705824208e+02,-2.130590894005088956e+02,3.454007218003511639e+02,9.681432814036238454e+00,2.554259246742018163e+01,4.520250878881898871e+01,6.797542014607291350e+00,-6.751141987811910106e+00,-4.449635710754233031e+01,-8.980788411954326023e+01,-1.001947784796769270e+02,-3.750413919264398999e+01,-7.323854919230207372e+01,3.894303747330437204e+01,-2.077872242567999450e+01,-2.126036566130972361e+01,-1.370671532748365173e+00,5.037445487316182025e+00,5.548990268190291397e-01,5.612716423777511565e+00,-1.611318209717373406e+01,1.751279884766514083e+00,-2.066129500001238739e+01,6.769670080110061328e+00,-3.936802582318198773e+01,-2.904988949778313057e+01,-3.810076271456963148e+00,-9.276310438295750416e+00,2.104770627229125068e+01,7.703913054321658294e+00,1.219830272066494281e+01,9.810923342054769236e-01,9.713775835513260848e-01,-1.558615196314476314e+00,2.401363157913517288e+00,9.870183535903986893e-01,5.789423290874413652e+00,-3.360130579899425207e+00,-8.947896949727502935e-01,-7.795650141759409735e+00,-9.736487906773596990e+00,5.869078439973701045e+00,-2.032633056276822003e+00,1.052995079510181142e+01,-2.936907479066527493e+00,-2.250955744690634752e+00,-4.212669545502783386e+00,-2.716375952775836211e+00,3.120772745629418199e-01,-8.619100000319090960e-01,8.776738959880485691e-01,7.681389464489045693e-01,4.829379096314425635e-01,-4.606429015059259058e-01,-2.669636793310616318e-01,-8.069733879326823622e-01,-2.343874290828439566e+00,-8.134659414552152246e-01,-8.276931707069625777e-01,-7.881602775768956626e-01,7.989502049575636367e-01,-3.796672577044460928e-01,-7.905515093746500188e-01,1.209034168675124365e-01,-1.215018153438127246e+00,2.620201726144843479e-01,-6.556204793427460320e-01,-1.050479469364924562e-01,-8.923185855482433648e-02,-2.483596886752423034e-03,6.146611867676717716e-02,-2.135221772247740957e-01,1.315940287757863258e-01,-2.283168848635853260e-02,5.458520083278923796e-01,-3.572211482940632621e-01,3.815311709071819712e-02,-1.619594153381818391e-01,2.728951458680141662e-01,9.962939828855081892e-01,5.867979320487045625e-01,1.052106314662745595e-01,-2.240796498302857487e-01,-7.851927628356960565e-01,-5.893259392965783938e-01,-1.308795119962568865e-01,-1.234230814736384796e-01,2.504404287576255106e-01],
    [-3.542279770122680202e+04,-1.804856001003622623e+03,-1.531533285599736018e+03,-1.654572206561181247e+03,-1.602212150763185946e+03,6.629338181660776854e+02,1.072575493067468187e+03,6.606908710577675947e+02,-8.306636949683042985e+02,-1.825489629384815657e+02,6.138819718650515824e+02,-3.612822606732092936e+02,-2.223970687478266939e+02,-1.239608586783296715e+02,4.528752057849977746e+02,-6.151654606961322003e+01,-2.644485730877485707e+02,4.770564400876653366e+01,-7.647753166727732150e+02,-2.615673485996375689e+02,1.494745722952635845e+02,-5.499739603225370388e+01,-1.662543190279810545e+01,-7.383297116995212264e+02,3.598332764388936056e+01,6.487962859307650376e+01,-1.713003990026646193e+02,1.904762008636577661e+02,2.086677953020512533e+01,2.388331270001320661e+02,-1.936351660842104820e+02,-1.973984892213039757e+02,-1.433550004811770862e+02,-1.799932066042264296e+02,3.418266210655471582e+02,9.006296995237317304e+00,2.328527100486154566e+01,4.183143981126633548e+01,1.069865322240358907e+01,-8.147633513193564880e+00,-4.841068681149840813e+01,-8.474513974460569443e+01,-1.009028174817159851e+02,-3.972564153255017771e+01,-6.430877886415099454e+01,3.521286725995534539e+01,-2.294407976005990335e+01,-2.270560116285411567e+01,-1.514706354779956410e+00,4.239497134104400544e+00,1.271063733815843477e+00,5.187955489070114723e+00,-1.650637842592855264e+01,1.155975649524578763e+00,-2.028871150232180298e+01,6.880474037360458262e+00,-3.930501479328062686e+01,-2.690149956799819009e+01,-5.067933492520000804e+00,-8.975694436569668255e+00,2.102747571601718235e+01,8.244244169951944201e+00,1.386277011458334485e+01,1.115539843816507615e+00,8.442907855432435493e-01,-1.250921490184672358e+00,2.476986742802183006e+00,8.286741648524157400e-01,5.728132211380511762e+00,-3.356124269664605198e+00,-9.876984869380682763e-01,-7.726582742445913254e+00,-9.468674283629841426e+00,5.556259683574730879e+00,-1.922035506886905942e+00,1.076735018278403899e+01,-2.732261883493405819e+00,-1.529405371395436086e+00,-4.203333080785317755e+00,-2.906369880145846629e+00,3.662961825407138328e-01,-8.298672606437376142e-01,9.574772935524842321e-01,7.582456820453267188e-01,3.848902410174254163e-01,-4.110454389047332180e-01,-3.449197206261718218e-01,-9.438813008151486494e-01,-2.259044847126011835e+00,-7.892650897693800349e-01,-8.357529803210632657e-01,-6.483575312944437341e-01,9.736899910352254661e-01,-2.972437446925792481e-01,-5.937699299085117399e-01,1.539205468863825144e-01,-1.290801718161987077e+00,2.296954348874959140e-01,-5.691835597954872927e-01,-7.019544550597200949e-02,-8.380283019382273046e-02,2.401853966476714952e-02,6.719700302793835123e-02,-2.349437423384955759e-01,1.341584078385459344e-01,-2.928732655470118323e-02,4.853709138780897270e-01,-3.510840500883156690e-01,4.640935809546933161e-02,-1.598333080010403695e-01,2.998593478009420332e-01,1.024056609638910098e+00,5.847921919231547916e-01,1.507665296663976695e-01,-2.167918621274265989e-01,-7.763136623659911972e-01,-5.995963393047731849e-01,-8.651464157249905140e-02,-1.111687325076072125e-01,2.373661283574735326e-01],
    [-3.539530611063484685e+04,-1.737273794671114274e+03,-1.323923950136927488e+03,-1.756248630483482657e+03,-1.577518392815281913e+03,8.580856657185128142e+02,9.651888363545461971e+02,7.427847795323536957e+02,-7.170999835298878224e+02,-2.015362853163302361e+02,7.417318692922086711e+02,-3.322261757367957671e+02,-3.256394569719126366e+02,3.242034966622009406e+00,3.646913565797866568e+02,-5.577452894077494250e+01,-2.460735293117889739e+02,1.336645801967598501e+01,-7.339255466206233223e+02,-3.049963257307178992e+02,1.327958014033276015e+02,-7.753848313203525322e+01,-6.929779029815966851e+01,-7.142363783514706483e+02,3.883436656455867109e+01,6.052710481532352560e+01,-1.736189072126738040e+02,1.859264336860687763e+02,1.011950808197789264e+01,2.204714089950346647e+02,-1.802326595271991323e+02,-2.110879082501084270e+02,-1.391556383295234127e+02,-1.456565229019064702e+02,3.367514183331207960e+02,8.770395949831588212e+00,1.956600417018002958e+01,3.781962687300804049e+01,1.300538795201019937e+01,-8.900339562039235375e+00,-5.526999786376821078e+01,-7.994485579670184450e+01,-1.025724695710672734e+02,-4.305037288868305723e+01,-5.443847268882123558e+01,3.101386982912715951e+01,-2.469849145224468856e+01,-2.457661206491746952e+01,-1.574234396020854021e+00,2.975185829579689578e+00,1.299987268605788060e+00,4.425687580201919324e+00,-1.728159764579675439e+01,-6.455644245362370803e-01,-1.983753563361337768e+01,6.425896954550751161e+00,-3.950974926000952081e+01,-2.423271253528165659e+01,-6.695434612126288876e+00,-8.285160228672676652e+00,2.095602787791188248e+01,8.493848455904045025e+00,1.577983594492117980e+01,1.286502232261718115e+00,6.787823598590718710e-01,-1.200455045165611079e+00,2.429285224202066384e+00,4.593789093618115826e-01,5.390847617599770381e+00,-3.215110992744967255e+00,-1.353236115171958964e+00,-7.693063024400229821e+00,-9.207277396503613431e+00,5.171744555414043099e+00,-1.700551172482967832e+00,1.101940642497399558e+01,-2.562809955080144420e+00,-6.978839973602372071e-01,-4.213158381679380504e+00,-3.008839852148741834e+00,4.333038497108371856e-01,-8.105992766873492128e-01,1.011355795176468231e+00,7.125782545816484737e-01,2.422303538161401371e-01,-4.386915456503590049e-01,-4.262359334872847794e-01,-1.192411471428237224e+00,-2.177967414072941477e+00,-7.826817923540441146e-01,-8.758791109239456585e-01,-4.389147952349117254e-01,1.138444264088559255e+00,-1.936381251931298120e-01,-3.467326197769929896e-01,1.841940178541647821e-01,-1.313160464519699921e+00,2.157784900421249319e-01,-4.930414480554812795e-01,-4.194279336944747860e-02,-7.552360683015373055e-02,5.468501233713720516e-02,6.633445280562480506e-02,-2.768357618961599376e-01,1.314459553602839725e-01,-4.294320009511483349e-02,3.989576959838019299e-01,-3.321173103063602694e-01,4.321934130353914660e-02,-1.655712515245153504e-01,3.385599011172351069e-01,1.048855448713050365e+00,5.995796264193333780e-01,2.200105363869388764e-01,-2.072095441605590616e-01,-7.445774798389297455e-01,-6.098670045666824135e-01,-4.695968585025221687e-02,-1.019351978504277056e-01,2.210094323176766407e-01],
    [-3.538167162389180885e+04,-1.705199606483086882e+03,-1.051108987213458477e+03,-1.767237694296854670e+03,-1.499457416584633847e+03,1.071830031368184336e+03,9.530964959303910291e+02,8.033558932789754863e+02,-6.494802212987136727e+02,-2.153283288321310920e+02,8.738252853565111309e+02,-2.801877954092914251e+02,-4.234702392227409860e+02,6.824358553872787070e+01,2.943859793903710624e+02,-6.596585374197785256e+01,-2.232759918386193192e+02,-7.399585367039406947e+00,-7.101872871518088459e+02,-3.441813122996078960e+02,1.170547320537652922e+02,-9.980600882016972264e+01,-8.054786815702175318e+01,-6.809118906693701092e+02,3.941533661549245693e+01,5.980074707189724847e+01,-1.714815192973925093e+02,1.772278825544337622e+02,4.797833457400441759e+00,2.066791955381930563e+02,-1.632522711712472017e+02,-2.183442545214595327e+02,-1.303867726794711359e+02,-1.146607999557622151e+02,3.306721715990566395e+02,8.770004302024444698e+00,1.520451700784712301e+01,3.536973250156187731e+01,1.389444971541123941e+01,-9.101027684611874946e+00,-6.207159879821551840e+01,-7.469513099552050051e+01,-1.038378786229270929e+02,-4.513601366829762185e+01,-4.523136471054563401e+01,2.718624751442042964e+01,-2.544534380249091754e+01,-2.655026788738752686e+01,-1.587950082108589456e+00,1.567274559574228787e+00,1.002690467337122637e+00,3.236620511080573248e+00,-1.809985355407028962e+01,-3.075876274326307946e+00,-1.921486046465599884e+01,5.744666393425736040e+00,-3.923126098461312949e+01,-2.150875339014913123e+01,-7.946619316365073793e+00,-7.123621030507024443e+00,2.105473329717952780e+01,8.596141575600535489e+00,1.760673678542577392e+01,1.425091074520413947e+00,4.700022729328025006e-01,-1.330423067576864682e+00,2.231216706230176428e+00,-8.689971187217666176e-03,4.737279009663541984e+00,-2.959956864838380497e+00,-1.881936241890612038e+00,-7.513243126081217582e+00,-8.996949263161109656e+00,5.040260848909469793e+00,-1.425459270980719007e+00,1.128189291303845820e+01,-2.424704139605124986e+00,6.948552181773057224e-02,-4.229688722232457287e+00,-2.951858479448614236e+00,4.891527957508258195e-01,-8.021286303851853372e-01,1.006770379122390757e+00,6.368945919330436523e-01,9.934845961301683182e-02,-5.908500985634385083e-01,-5.011833419024945835e-01,-1.508612236362229631e+00,-2.070041996289388564e+00,-8.021077880118141490e-01,-8.636651315669363616e-01,-2.112558899360148512e-01,1.307803789523881210e+00,-7.532748462949301338e-02,-8.602827161864171068e-02,2.402576975448529328e-01,-1.265559814372715808e+00,2.384041794060071107e-01,-4.407853483101013548e-01,-2.674923845264669600e-02,-7.042354143237447572e-02,7.681574096722640355e-02,5.856023181500929348e-02,-3.267465510741154877e-01,1.115945222366972328e-01,-6.029429812841181208e-02,2.905219022393734640e-01,-3.073505467586692963e-01,2.893076127349221080e-02,-1.617560650944998013e-01,3.755484671492582693e-01,1.083823917319962415e+00,6.269504478514317247e-01,3.055962718273380618e-01,-1.900635637005073098e-01,-6.909067446485408492e-01,-6.140624126855879217e-01,-1.451141987297276635e-02,-1.003585676230525497e-01,2.075758964492247505e-01],
    [-3.551807777364442882e+04,-1.733791875141179389e+03,-8.276519200355922976e+02,-1.723719494227983432e+03,-1.408979171593658975e+03,1.228431616958245741e+03,1.000734189962942310e+03,8.066710668577138676e+02,-6.311682918466755154e+02,-1.863839543813007253e+02,9.687782396497389072e+02,-1.876403963749404511e+02,-5.416745467965954504e+02,2.213765878201506609e+01,2.247123065393971615e+02,-8.465573532090628817e+01,-1.790129285581037664e+02,-1.620304163310262879e+01,-6.853833300471916345e+02,-3.827591128063127144e+02,9.702071356886501974e+01,-1.194623490889000834e+02,-5.296071227195593423e+01,-6.454602064056149402e+02,3.870727590574628607e+01,6.418087252162584377e+01,-1.596744073134814812e+02,1.678968698532439134e+02,1.458768157808795873e+00,2.003017734825099012e+02,-1.459069818709245112e+02,-2.195042541355663843e+02,-1.202363887535095017e+02,-9.110223858743785286e+01,3.197668512124237736e+02,7.875252321832734381e+00,1.187187886442553086e+01,3.585296609393404310e+01,1.474628511443821566e+01,-9.844244878824566669e+00,-6.573330534261103253e+01,-6.949856432053218214e+01,-1.040093758182124759e+02,-4.528339936342125327e+01,-3.838584662191397001e+01,2.350781315155506945e+01,-2.463271028042977306e+01,-2.796182632838837279e+01,-1.719645322442751034e+00,3.189916998803721815e-01,9.299016679518018469e-01,1.933158585635053495e+00,-1.840556903393038013e+01,-5.315654220668749375e+00,-1.834577217527150239e+01,4.968271829923803118e+00,-3.811489457800593783e+01,-1.929057694185212313e+01,-8.590475967618472097e+00,-5.513850922415352684e+00,2.113486355439108877e+01,8.690132812724790767e+00,1.877413621069860028e+01,1.411965658863881812e+00,1.376343919203074362e-01,-1.530335543401913911e+00,1.913081499410452579e+00,-3.458199339357180824e-01,3.873444417744297041e+00,-2.612473691604807691e+00,-2.395863883920472226e+00,-7.052625491886995945e+00,-8.787842629405684391e+00,5.246801148981919738e+00,-1.095409040495940678e+00,1.138425740224801785e+01,-2.235113062806880713e+00,5.516333486782882822e-01,-4.193209252918689955e+00,-2.694390393211899770e+00,5.045197971692854111e-01,-8.320489095509366884e-01,9.254145286347498223e-01,5.224934442686524072e-01,7.311780358392878237e-03,-8.557059705054510523e-01,-5.281380742413839258e-01,-1.792200135653110316e+00,-1.882706518454319911e+00,-8.153188294540678616e-01,-7.458966586522930431e-01,2.983352322811136208e-03,1.449468767106733225e+00,6.237132744040929655e-02,1.217458580634982745e-01,3.350069911095795994e-01,-1.148572736907740977e+00,2.982106683433682348e-01,-4.142050230920955034e-01,-1.982616115305996241e-02,-7.589813095511668828e-02,7.524408588130539199e-02,3.598472119706051103e-02,-3.639977952728197796e-01,6.780732670479706903e-02,-6.748895502227941767e-02,1.767024378481373836e-01,-2.687827840871012119e-01,1.209889865187084752e-02,-1.334076915583743139e-01,4.052207603172412465e-01,1.120058119025072019e+00,6.634159345943241304e-01,3.820081349509482638e-01,-1.570490526700812628e-01,-6.236741646831944763e-01,-6.011746533353236055e-01,8.639002438186252700e-03,-1.079259541454175575e-01,2.000648569914459940e-01],
    [-3.582480618419480743e+04,-1.800029005435243107e+03,-5.146871634868723504e+02,-1.723170623695841641e+03,-1.359863404416864341e+03,1.308867282173573130e+03,1.071372966829816050e+03,7.438319629936605679e+02,-6.531652849049798988e+02,-1.062530671396849442e+02,1.002600404570626097e+03,-6.991342533787648961e+01,-6.806360994134061002e+02,-1.411954161615077510e+02,1.277989775807848645e+02,-9.797921132371918418e+01,-1.158316146676086476e+02,-1.847259569354423903e+01,-6.614364120728222360e+02,-4.254630168334644509e+02,5.733878694162476819e+01,-1.363346075794858336e+02,1.485645466934481629e+00,-6.055992777459113086e+02,4.232976062975046005e+01,7.220504930631724960e+01,-1.393200026418137440e+02,1.557592788307401861e+02,-5.289869261123580912e+00,1.958860869357549461e+02,-1.303116049470110340e+02,-2.153025620775322864e+02,-1.090500038014538973e+02,-7.449066285181535818e+01,2.997532276936782409e+02,6.541539850724805483e+00,1.083938615948472872e+01,3.899063487511882897e+01,1.562726347661498494e+01,-1.227716576022138817e+01,-6.590522048684701417e+01,-6.510644254499230499e+01,-1.032227908393557101e+02,-4.358424097903579764e+01,-3.411194804174545681e+01,1.971555780529807222e+01,-2.216213409161188608e+01,-2.772908110348628696e+01,-2.079259047339185429e+00,-2.043392499468030810e-01,1.520799624358226243e+00,9.523955103405857825e-01,-1.787458589189749247e+01,-7.108956149813751679e+00,-1.748823435114368152e+01,3.972628669632524812e+00,-3.617765205097131087e+01,-1.773114767784115031e+01,-8.601850210930624741e+00,-3.621510313218557986e+00,2.102895943133907508e+01,8.903977902209028628e+00,1.907413448701596437e+01,1.122620935781914575e+00,-1.971566678746445589e-01,-1.688924414622261727e+00,1.633542766151529824e+00,-3.699776699659829693e-01,2.951252993259863455e+00,-2.244206573033871166e+00,-2.797858611073289925e+00,-6.353600326332952797e+00,-8.503761884191153086e+00,5.668321498189841989e+00,-7.036538196031321135e-01,1.121595185895417579e+01,-1.880235158285884056e+00,7.156720030938088506e-01,-4.064065187098345078e+00,-2.234159621968557552e+00,4.483193353252470925e-01,-8.984490784275189768e-01,7.796385275232703416e-01,3.985503913612634674e-01,3.415703002054437751e-03,-1.151534799186142877e+00,-4.956725467376399408e-01,-1.973883572090153082e+00,-1.609525536524049061e+00,-7.912882066239010914e-01,-5.324625003370359044e-01,2.122063072230518932e-01,1.524249720565814759e+00,2.336684793310936648e-01,2.475263583384400001e-01,4.463467509717520265e-01,-9.657394368943537089e-01,3.773684391995305587e-01,-3.938263759841935663e-01,-1.925955900193677267e-02,-9.687181852759396694e-02,4.415220501020221400e-02,1.972445550044324945e-03,-3.753960636992046407e-01,1.472478089216513499e-02,-5.666128276269373487e-02,7.627033506559803555e-02,-2.088215937505474018e-01,2.662245379312133068e-03,-8.334493686966634729e-02,4.283118642802449250e-01,1.135435193652163388e+00,7.036772377426981917e-01,4.325263985063809713e-01,-1.061824293809828790e-01,-5.451288930038482583e-01,-5.644769304394523513e-01,2.501207548332343156e-02,-1.260362583087439592e-01,1.950476422635753493e-01],
    [-3.626398816264164634e+04,-1.619309616829860943e+03,-1.317352012386231479e+02,-1.858617611755545340e+03,-1.325638480326253102e+03,1.312305489011513600e+03,1.154678737703160323e+03,7.097916163713146034e+02,-7.226489753393591400e+02,-4.007442971043814417e+00,9.663168190346852953e+02,4.966850733868906786e+01,-7.877557621955817240e+02,-3.464248805522439625e+02,2.962201746895369681e+01,-9.772545707372681534e+01,-6.614522202062528322e+01,-2.289858702718273875e+01,-6.380097089959310779e+02,-4.626748841392384861e+02,5.939467862239115270e+00,-1.316452378163243679e+02,6.659778766642823200e+01,-5.596015124146834978e+02,5.586874723118225461e+01,7.557812401760045873e+01,-1.193008704811368830e+02,1.404246452663769276e+02,-1.744442270364588055e+01,1.925011004306633140e+02,-1.120703370611215206e+02,-2.063326171243261058e+02,-9.325053736816872174e+01,-6.190236220243595255e+01,2.720118765267189929e+02,6.714784839860065802e+00,1.150283153668445557e+01,4.287409390734319459e+01,1.523427980408034976e+01,-1.773768126369226295e+01,-6.311824088180225800e+01,-6.117222040093987800e+01,-1.015824733534874014e+02,-3.961756802915316911e+01,-3.213726708114640473e+01,1.624375127569479815e+01,-1.914653050647422816e+01,-2.593898294635618740e+01,-2.153738269817550233e+00,4.056997609660372150e-01,2.833777885354880954e+00,1.362466635530017178e-01,-1.699033790093129781e+01,-8.477792834336755234e+00,-1.702683791262135671e+01,2.951649862201192853e+00,-3.353921065609115004e+01,-1.709495711044935717e+01,-7.963895744927880216e+00,-1.965740524063393835e+00,2.064406565733312249e+01,9.351782170499204128e+00,1.886215718536469055e+01,6.421086244672324916e-01,-2.502646427112278915e-01,-1.732781196757456454e+00,1.422022160526241308e+00,-1.598733952192842867e-01,2.122102752963288097e+00,-2.056871584625425076e+00,-3.008991074812123578e+00,-5.519152033018160708e+00,-8.232763217656419386e+00,6.197528632400517878e+00,-4.090452513949102697e-01,1.086802159792959621e+01,-1.372944600185254993e+00,7.114086690161054438e-01,-3.832956343842066627e+00,-1.661852320487287704e+00,3.187743829593150391e-01,-9.275264079451076560e-01,6.204969047455367592e-01,2.919890799513626956e-01,7.676528124708548173e-02,-1.414764842324181870e+00,-4.591740283598692018e-01,-2.032356707837888798e+00,-1.301049920051425168e+00,-7.372151139929704611e-01,-2.617609630795268982e-01,3.823369772938277622e-01,1.549285763379362857e+00,4.276131937488034662e-01,3.086282584750751345e-01,5.574056362064803150e-01,-7.595120896017181211e-01,4.487375779238412243e-01,-3.653169766735938628e-01,-3.129012090341116298e-02,-1.170944975293809337e-01,-8.525945493285034399e-03,-2.725418601835578880e-02,-3.548771867501661070e-01,-3.415261391971666227e-02,-3.677308534104496707e-02,2.518689023166737796e-03,-1.363543337777614606e-01,6.580832393740899261e-03,-2.243062073629116873e-02,4.380494337701023033e-01,1.130932646058140367e+00,7.391834339142663302e-01,4.547574698622044442e-01,-4.217785852841610117e-02,-4.681394976466890512e-01,-5.112085797563050704e-01,3.746399579895082210e-02,-1.515108218820999941e-01,1.899158386389759867e-01],
    [-3.652601346035928873e+04,-1.370700852928095856e+03,1.163440969925556203e+02,-2.018847268148758303e+03,-1.258604875841661396e+03,1.305916111819132084e+03,1.186906444480260689e+03,6.591772429433337948e+02,-7.921554437099832739e+02,1.046896589511628406e+02,8.981288336403890753e+02,1.051707830098413297e+02,-8.585678638242957277e+02,-5.175582013385326263e+02,-5.373712409438706317e+01,-7.655700629306301153e+01,-5.258256115809373910e+01,-2.407020382087378962e+01,-6.191353941230959208e+02,-4.866742277432754236e+02,-4.222541145575567612e+01,-1.170544725485139708e+02,1.239786703415913394e+02,-5.245403619612964121e+02,7.748712373189374603e+01,7.187229968028712790e+01,-1.074020687137528682e+02,1.267707485346336398e+02,-3.175459646529217039e+01,1.909618778884041319e+02,-9.632514214104955386e+01,-1.947237087790050509e+02,-7.491041178315360582e+01,-4.835705643157962896e+01,2.442202426772275885e+02,8.335543713552194589e+00,1.296032280305892570e+01,4.554526163161983732e+01,1.323914387747403154e+01,-2.535781676060251044e+01,-5.917099495272952936e+01,-5.856843164869281537e+01,-9.897499887420438824e+01,-3.542318048326194457e+01,-3.035076224100613373e+01,1.368395466759977097e+01,-1.715827460965358853e+01,-2.423747993125681077e+01,-1.736872844536851979e+00,1.836571378027882284e+00,4.435688853005887111e+00,-7.724112487838075136e-01,-1.615677640760826606e+01,-9.617343506987770851e+00,-1.707721799714848032e+01,2.334500288757922259e+00,-3.096836524485575737e+01,-1.684632863830368876e+01,-6.836716519772239486e+00,-6.137053590238600309e-01,2.001215872167186660e+01,1.009237758369888915e+01,1.879927889364391547e+01,1.440565319969162039e-01,3.434668855090404829e-03,-1.705715063185395675e+00,1.204809090635609259e+00,1.095618927583750929e-01,1.501151145800905917e+00,-2.032853530752433358e+00,-3.030700220223724983e+00,-4.680705745070803836e+00,-7.910928043826386258e+00,6.785840689626613020e+00,-1.888990387747507271e-01,1.058573080753436102e+01,-8.536617761411781080e-01,7.966918781421155060e-01,-3.525720198773362846e+00,-1.120730744460845862e+00,1.617374990588326678e-01,-9.010119080138758729e-01,4.993928557227138576e-01,1.938997049456610278e-01,1.781927156750054420e-01,-1.630131121882489875e+00,-4.250461319253836523e-01,-2.011939915485483787e+00,-1.001245770611640440e+00,-6.470973777376151093e-01,1.600705762683121702e-02,5.391866526690745065e-01,1.592443531819011771e+00,6.245754125766300735e-01,3.810986280687885253e-01,6.742622504497739477e-01,-5.816599141799498884e-01,4.915689276816989639e-01,-3.396849122487826667e-01,-5.177818565936398443e-02,-1.225856806594786547e-01,-6.869861953452957581e-02,-4.545438250902612831e-02,-3.141974821875790358e-01,-7.649266764942082297e-02,-1.187784457005566438e-02,-4.908841309276194831e-02,-5.604642887400039519e-02,2.211549700228385845e-02,3.846354268987674935e-02,4.462078988670499791e-01,1.132707786404274497e+00,7.705271511263085404e-01,4.685665324609698534e-01,2.456817643479063465e-02,-3.996582066068628536e-01,-4.621099130966696000e-01,5.001175066225947707e-02,-1.757765608801206692e-01,1.862728601577767484e-01],
    [-3.639042350339962286e+04,-1.005592368856973053e+03,2.415595180242394804e+02,-2.082776079164283601e+03,-1.090766414622553839e+03,1.441742013144802286e+03,1.116101828731362275e+03,6.160674252192588938e+02,-8.422177827883465397e+02,2.069254521923722336e+02,8.515307176255496415e+02,6.729248641495821914e+01,-8.751305024539282158e+02,-6.471686268150624528e+02,-1.080808391988784365e+02,-3.911998978086143097e+01,-7.781839188450516076e+01,-1.306643199768166497e+01,-6.109146986628036302e+02,-4.866238170909031737e+02,-8.991819699168127045e+01,-1.100783411403908332e+02,1.545634875016774572e+02,-5.059053514829413416e+02,1.007695252961324144e+02,6.274303693093018808e+01,-1.067360335604689965e+02,1.202164519036349049e+02,-4.346768039616821255e+01,1.881881780650333269e+02,-9.027102705474597144e+01,-1.873321356720268227e+02,-5.632400152159524964e+01,-3.217472625877401526e+01,2.247298463976988501e+02,1.041230077658804376e+01,1.449015349916700401e+01,4.600803740111282281e+01,1.061298732121375821e+01,-3.378613605958776844e+01,-5.647411887066297709e+01,-5.888109683535846273e+01,-9.697247573561540435e+01,-3.237267402956996420e+01,-2.733696172007171299e+01,1.321029865214461374e+01,-1.707563930378983486e+01,-2.426743970309036769e+01,-8.927309290833940203e-01,3.480524075951155538e+00,5.657149566161174370e+00,-1.658860895469516317e+00,-1.578163251232212616e+01,-1.067793451369084501e+01,-1.760497704266943231e+01,1.958964186479756897e+00,-2.905258696714032851e+01,-1.638962605133438188e+01,-5.201819861734153783e+00,4.727592854901635500e-01,1.914742579926862476e+01,1.091765726071303000e+01,1.922212549139828042e+01,-2.091929338735130928e-01,3.744111482728082474e-01,-1.693811195557943794e+00,9.328576042654239675e-01,2.579586346872208003e-01,1.161728704137490187e+00,-2.079004969621319088e+00,-2.994998316523817206e+00,-3.913076687663493924e+00,-7.460457605987794061e+00,7.490624961650711455e+00,4.974449406353985415e-02,1.050263086424128467e+01,-4.989432354312005602e-01,1.086450130326411356e+00,-3.186996760261990858e+00,-7.169591170028295490e-01,3.744168769053884960e-02,-8.540263351741873565e-01,4.390088301501207657e-01,8.537568932014308332e-02,2.583464479803337377e-01,-1.788504326203751216e+00,-3.749531688961021403e-01,-1.972142611959051273e+00,-7.228188406179838488e-01,-5.129987083883312815e-01,2.849580475838421334e-01,7.188386840632862151e-01,1.693133627869185531e+00,7.796967259510875214e-01,5.084804016133211979e-01,8.005378354193313228e-01,-4.580429557795913098e-01,5.015022772366015680e-01,-3.373641862335400865e-01,-7.113179426254613580e-02,-1.105378035506002637e-01,-1.217944827226088572e-01,-6.191299162045423021e-02,-2.685411649260594502e-01,-1.101047222941060610e-01,1.496238318840297822e-02,-8.279352000501644104e-02,3.177711507946362479e-02,4.332587624815077698e-02,9.744593589965593050e-02,4.666713237176170481e-01,1.158478300700952923e+00,7.935109166404604730e-01,4.893998727117732095e-01,8.292296706079888002e-02,-3.411579741818703826e-01,-4.309155675164058619e-01,5.982666044249938808e-02,-1.925577631657635069e-01,1.853994816175463245e-01],
    [-3.615612404209076340e+04,-6.252389503999936551e+02,9.299317850957251608e+01,-2.036575643957625743e+03,-9.236194310577069473e+02,1.602675097807379188e+03,9.959800212839918458e+02,5.707556223693696893e+02,-8.744045582948001538e+02,2.648870602343474161e+02,8.244803635559943586e+02,-1.895061795077005229e+01,-8.455676143364116797e+02,-7.315136150215038242e+02,-1.209680781124414182e+02,1.271750295711757950e+01,-1.281063823242973001e+02,9.878219630869093493e+00,-6.145742810032783154e+02,-4.632961142036108413e+02,-1.329360341769391027e+02,-1.080237578359138695e+02,1.548378279056524320e+02,-4.884079517835581328e+02,1.228412470256466236e+02,5.295576373314448659e+01,-1.111640366247297749e+02,1.221139209034682551e+02,-5.017819590487879111e+01,1.864001247615505292e+02,-9.269197809205253691e+01,-1.861985050148020377e+02,-3.497613761189456483e+01,-1.741303504179951034e+01,2.183473487996109554e+02,1.314761040282315463e+01,1.666251355383221622e+01,4.628327236184645699e+01,8.982781947001900136e+00,-4.076457325310144597e+01,-5.580391107282185459e+01,-6.173104317343313596e+01,-9.635213739388721876e+01,-2.867151393005637416e+01,-2.446177212066311313e+01,1.581007989015276216e+01,-1.867762140760506284e+01,-2.640003983574677093e+01,3.997015688255731169e-02,5.153454925958475208e+00,6.286498499741231427e+00,-2.240532195619016509e+00,-1.569486558010202337e+01,-1.160174917337888978e+01,-1.837557346482938314e+01,1.786202275916231486e+00,-2.755408401370513971e+01,-1.586554579423707523e+01,-3.108932459230568490e+00,9.994041518604241947e-01,1.808414182009436644e+01,1.155999587383288230e+01,1.989628915721221958e+01,-4.254751159115168213e-01,6.825032282621124047e-01,-1.773469544462167091e+00,6.363745049562368195e-01,3.459502574962577404e-01,1.034622155975771562e+00,-2.089125506004253285e+00,-3.007244520694427159e+00,-3.218002879440195585e+00,-6.981173096652296906e+00,8.369650680973578005e+00,1.938825874786876680e-01,1.058988921466661459e+01,-3.947433622867277392e-01,1.465211028424885598e+00,-2.904887860947547473e+00,-4.964176903430944643e-01,-4.881903350293546190e-02,-8.353822881367778397e-01,3.916147574978243728e-01,-3.509380699622152017e-02,3.154251590982425912e-01,-1.907516305885057717e+00,-2.866063688121911479e-01,-1.971274497176297658e+00,-4.642961280595298001e-01,-3.549176808065292454e-01,5.501555216088684919e-01,8.694834928114651973e-01,1.823907578961877718e+00,8.487417187986193712e-01,6.603988955976015651e-01,9.191594289341258328e-01,-4.012197691926103205e-01,4.898920619612364691e-01,-3.636841572733621741e-01,-8.720240644560926790e-02,-9.508524127152494232e-02,-1.684384206455940280e-01,-8.771387995663085246e-02,-2.348345173211026649e-01,-1.372244172545832031e-01,4.702664418325589596e-02,-1.065535456147899129e-01,1.203133599885329585e-01,6.650986105733716625e-02,1.584423601734907538e-01,4.921570576402994335e-01,1.206055854046577114e+00,8.015232029495693578e-01,5.201097745210921941e-01,1.272952063054667293e-01,-3.011406342662834579e-01,-4.179799298859296908e-01,5.937045091953688930e-02,-1.994810606833995470e-01,1.880207295493025732e-01],
    [-3.605281510292765597e+04,-4.197378005563290344e+02,-3.174783431824299385e+01,-1.916357643086058943e+03,-8.304316052320650670e+02,1.726121871075203217e+03,9.559804295673889101e+02,5.096017367415537365e+02,-9.311015834605910868e+02,2.708960463534901351e+02,7.604284098203310123e+02,-7.353772911829216241e+01,-8.071468039860008048e+02,-7.539103214936303630e+02,-1.590870289462791902e+02,5.854572511684241221e+01,-1.791120810441687752e+02,2.429173895958167151e+01,-6.414658419163930603e+02,-4.286148413228926302e+02,-1.519717707089013174e+02,-1.070461446398762746e+02,1.309979061479088784e+02,-4.620573569288945919e+02,1.423238263954478384e+02,4.296996251939985711e+01,-1.125855342727282959e+02,1.287624928297146880e+02,-5.179273265965355222e+01,1.913469429512036868e+02,-9.353446838436580890e+01,-1.886867335645729611e+02,-1.279015617683968742e+01,-1.055072977465395567e+01,2.254296507754691561e+02,1.813880843093275175e+01,1.887672805106508633e+01,4.944625745068839962e+01,9.839577233028693470e+00,-4.370054202965435763e+01,-5.654377233671575453e+01,-6.434864447911661500e+01,-9.474224443051240030e+01,-2.249501917502712445e+01,-2.401493949372492409e+01,2.048071350521179568e+01,-1.931022364579427020e+01,-3.004447425878450417e+01,1.051106263444099520e+00,6.608756222077414755e+00,6.508966941567420506e+00,-2.100169526948626242e+00,-1.531731820124845633e+01,-1.218531411963774858e+01,-1.888113548627595861e+01,2.748123714152296504e+00,-2.620091196767012676e+01,-1.557330415975917148e+01,-1.474443240230332686e+00,1.139978781221211213e+00,1.700602226127003291e+01,1.210081723889691929e+01,2.012006778225097747e+01,-5.282687070342796387e-01,8.306514849672690382e-01,-1.987359073607184001e+00,3.342119266961652846e-01,6.113772056583677283e-01,9.821467311010052548e-01,-2.031955365987578865e+00,-2.948256547946063844e+00,-2.601437832228739921e+00,-6.573732348788255742e+00,9.236314124825113936e+00,1.877067822937025787e-01,1.072137763663087640e+01,-3.689640831151788092e-01,1.641073099876696251e+00,-2.889710014540356919e+00,-4.704940016324957175e-01,-1.210405949614948018e-01,-8.555279950417185031e-01,2.985699709105428257e-01,-1.951435987485842516e-01,3.705651546114557826e-01,-2.017464783752842106e+00,-1.565245989451283237e-01,-2.051669014945127323e+00,-2.195205439329929453e-01,-1.665478024321279116e-01,7.991684671513271665e-01,9.296652140006060883e-01,1.932543668675803739e+00,8.606888529895881934e-01,7.837697490000026246e-01,9.782697149258813285e-01,-4.136338217669943140e-01,4.803544826564267178e-01,-3.765290540872707203e-01,-1.060084615665809749e-01,-8.260370364095750984e-02,-2.112626292102990910e-01,-1.397154660253510650e-01,-2.300185312748607713e-01,-1.648721219136768390e-01,8.660740452982851334e-02,-1.338360650823886278e-01,2.026432092100132754e-01,9.678189606547944746e-02,2.358431195617964882e-01,5.114161063993502010e-01,1.268030908255771916e+00,8.075071403359735944e-01,5.699341546243713585e-01,1.557193402999377529e-01,-2.893022506317830533e-01,-4.157465857699038647e-01,5.289770683980767052e-02,-1.916470609490852905e-01,1.933808407790053585e-01],
    [-3.583491187112571788e+04,-3.877844492092829114e+02,4.154358429954422149e+01,-1.786163050080771654e+03,-7.241757509247875078e+02,1.842522436994116561e+03,9.666114080498176691e+02,4.506133416796486131e+02,-1.048991128243448884e+03,2.640242512407299387e+02,6.537914019429060772e+02,-5.631183159311234476e+01,-7.782511694997792802e+02,-7.347189198288629086e+02,-2.369451561747934534e+02,8.711955358248178527e+01,-2.172644150328912929e+02,1.973611676756238253e+01,-6.790761067295569546e+02,-3.931530707215516713e+02,-1.343879502653602458e+02,-1.007959337258117500e+02,9.896260455733649053e+01,-4.390649148680363965e+02,1.598624286599809068e+02,2.981829220927213697e+01,-1.076838724252570216e+02,1.391423708659460772e+02,-5.041141252871852885e+01,2.063123768247696717e+02,-8.758708698430859840e+01,-1.915529504241082748e+02,4.216086634630583418e+00,-1.578720140350726453e+01,2.376260737989579184e+02,2.619363540274527224e+01,1.970950031924947865e+01,5.629038501480034995e+01,1.270225067090794013e+01,-4.157445158337792179e+01,-5.698392029467517261e+01,-6.486355158105887142e+01,-9.051320927877499400e+01,-1.381313040518154445e+01,-2.766530451449788686e+01,2.368217707545131034e+01,-1.770950995608679079e+01,-3.508335103759132778e+01,2.071596153200780499e+00,7.546481177343887126e+00,6.601992564744097791e+00,-1.704212322476213348e+00,-1.401493785124633717e+01,-1.208964218566180904e+01,-1.858803396235329330e+01,5.393015463559773792e+00,-2.476517855786743638e+01,-1.569378318894894164e+01,-1.207613726687453370e+00,1.180495788062422502e+00,1.560854467425535219e+01,1.279034548333106613e+01,1.939157455174401434e+01,-5.391321623428286802e-01,7.851535316616449212e-01,-2.252606408381284897e+00,-1.055293385589845256e-01,1.252693568482695419e+00,8.864231119782911561e-01,-1.781707380907268767e+00,-2.604099107832726023e+00,-1.995112659954942691e+00,-6.199495085730387878e+00,9.894127209871545148e+00,1.434870805407891803e-01,1.059485545673268447e+01,-2.026719786784899613e-01,1.334882216311223724e+00,-3.148248136081810422e+00,-6.210306413444449669e-01,-1.741457984650611468e-01,-8.855599798326014849e-01,1.355679821124492201e-01,-4.155712430114503197e-01,4.422845965869340867e-01,-2.154795772517802188e+00,2.775176335019664819e-02,-2.169865266028141448e+00,4.159325937397077844e-02,7.558256096018042824e-02,1.025814299160074272e+00,9.186411763941511044e-01,1.946426210793362088e+00,8.922742348011067914e-01,7.804426388388545632e-01,9.932884785242336312e-01,-5.075215898727021280e-01,4.996227431462149093e-01,-3.679927133041976939e-01,-1.229432070676717698e-01,-6.252497165199287499e-02,-2.538991063325691799e-01,-2.184978214282771170e-01,-2.607101118035222709e-01,-2.072214736209767594e-01,1.262471733221965375e-01,-1.700960112835165627e-01,2.782347538923967134e-01,1.374662544779720330e-01,3.383129027522431276e-01,5.253833033403405572e-01,1.331393527371702579e+00,8.339872037920991188e-01,6.207500602507729504e-01,1.806945997457033992e-01,-3.141132621446927620e-01,-4.052299274154902431e-01,4.070572045192179245e-02,-1.692517398607446544e-01,2.000779980080717446e-01],
    [-3.558478388477100088e+04,-5.531196185624680766e+02,6.442171579636571721e+01,-1.699443117217788767e+03,-5.763930924622540033e+02,1.892764823311881855e+03,8.700791191030054961e+02,4.069101596724283354e+02,-1.208508991872293791e+03,2.625401297167917960e+02,5.338813298140161123e+02,-1.671573687667138941e+01,-7.562945126669700358e+02,-7.249569035081345874e+02,-2.894307466932655188e+02,1.085655438313276306e+02,-2.534623861716025885e+02,4.543131021755372423e+00,-7.075476825073707232e+02,-3.668236076363640450e+02,-8.684993052136425717e+01,-8.573592305189531260e+01,7.134416463163481126e+01,-4.476532629484597692e+02,1.765589951763677448e+02,1.325635231915004297e+01,-9.611519274577952388e+01,1.531187113703209661e+02,-5.003552480607405784e+01,2.293339858647523215e+02,-8.008626956031106658e+01,-1.937401891832419665e+02,9.862239100555942883e+00,-3.078441239347616687e+01,2.453702521826318161e+02,3.642567565327649959e+01,1.940186460327106843e+01,6.628968156381921517e+01,1.586286173118111620e+01,-3.551538233571169911e+01,-5.578944784490060016e+01,-6.428209765851491397e+01,-8.417521051666437870e+01,-4.819519278359025272e+00,-3.500506482443683609e+01,2.204735801286451746e+01,-1.549351822668542411e+01,-4.227739278139845425e+01,2.818510313414880120e+00,8.098171086315339551e+00,6.910230659197588388e+00,-1.832797971724701158e+00,-1.127932504015486970e+01,-1.105975008057736630e+01,-1.757174416646165582e+01,9.542063646359785878e+00,-2.344558656588966628e+01,-1.606349276479072330e+01,-2.729595540095612005e+00,1.135844274446557112e+00,1.318427205053736806e+01,1.371256195145023327e+01,1.783850682457741854e+01,-5.251133697088254948e-01,5.272189288954631792e-01,-2.441028602219647681e+00,-7.528787485235289845e-01,2.373022041451807507e+00,7.540663474909730102e-01,-1.161763273028587840e+00,-1.820221804819141642e+00,-1.390602134179153015e+00,-5.700067234043952880e+00,1.017002972066780586e+01,1.858134767118316266e-01,9.884356717003804249e+00,1.266843846162857001e-01,4.834675967517921280e-01,-3.441182139843239174e+00,-9.057779690768723579e-01,-1.841823922237301459e-01,-9.283068899826680820e-01,-9.768092243128280450e-02,-6.784784638365441989e-01,5.585613371397089022e-01,-2.338028133886941973e+00,3.076849671425148647e-01,-2.225364612365588801e+00,3.383797567627911951e-01,3.894984477202841910e-01,1.186693269813152929e+00,9.097341763650378388e-01,1.788775910651382528e+00,9.975208276303005883e-01,5.620971859977529350e-01,1.061525781039946326e+00,-7.044862528545304814e-01,5.580933829232643806e-01,-3.803618105408988481e-01,-1.228124483896469304e-01,-3.032116098364208770e-02,-3.037809064960863559e-01,-3.129897933565741752e-01,-3.207736185975266219e-01,-2.753644126784225987e-01,1.656266546241538240e-01,-2.104040224225293132e-01,3.532718803882828329e-01,1.887046405016199468e-01,4.511897801012185183e-01,5.481878521617653544e-01,1.374617725329005946e+00,8.995418030764250616e-01,6.318133848702948141e-01,2.287050797708925498e-01,-3.814456710218581126e-01,-3.697868098747166821e-01,1.613505615651023364e-02,-1.379255677820648285e-01,2.066899973076347652e-01],
    [-3.533795324703360529e+04,-6.333409217802318381e+02,-5.328184762962667520e+01,-1.639897824413455510e+03,-3.553780396135832689e+02,1.885891808930967272e+03,8.693250053423769259e+02,4.937985862672679218e+02,-1.353937981787329136e+03,2.812134304428561791e+02,4.402872204116367811e+02,4.405397421134044578e+01,-6.815967521138709344e+02,-7.858578438860355391e+02,-2.848914895783562997e+02,1.199313929138096739e+02,-3.196591800126985277e+02,-4.273313211050702165e+00,-7.279780671717713858e+02,-3.453239607777699689e+02,-3.170955113229869227e+01,-6.253257997744849206e+01,5.305646965813737381e+01,-5.156617977903607652e+02,1.900285148330976881e+02,-1.331730853321887409e+01,-7.635224075091284135e+01,1.634764856102229373e+02,-5.459735073764123570e+01,2.560992864842918380e+02,-7.555430978124282149e+01,-1.932167051238665749e+02,-1.400367613735774786e+00,-4.446811418021088258e+01,2.467719961670581199e+02,4.721942153780422302e+01,1.765124717380623665e+01,7.786825918578193750e+01,1.652207354210896639e+01,-2.910230486356012136e+01,-5.233102227325138500e+01,-6.370274020950714089e+01,-7.545122704399211955e+01,1.757441376686398549e+00,-4.201299323312819212e+01,1.535230182508804830e+01,-1.456638139950975130e+01,-5.123410174289209351e+01,3.651842432268296967e+00,8.613805223376163056e+00,7.397081336420007425e+00,-3.146166228068133286e+00,-7.338104918572270208e+00,-9.020115402683330785e+00,-1.654144712337906142e+01,1.510169062682664887e+01,-2.282882698208979733e+01,-1.582502141158449049e+01,-5.942095126408122319e+00,1.013076331394589413e+00,9.852531732559828725e+00,1.493064217025060714e+01,1.580175902119692033e+01,-3.958302853711083147e-01,2.195902474093477386e-01,-2.620440108978799199e+00,-1.544140417760528683e+00,3.958495982452121087e+00,6.687070424266817747e-01,-2.820547780779044666e-01,-5.980933492146784936e-01,-8.321847503365066290e-01,-4.836644451354411345e+00,9.991326506948670527e+00,3.921482423692091990e-01,8.647609622103718863e+00,5.424648939441973905e-01,-8.075543734020577125e-01,-3.585529944743684805e+00,-1.234360674486796761e+00,-1.270738083895064374e-01,-9.585257433981636543e-01,-3.715368592285943627e-01,-9.549032287637535532e-01,7.462440811248334249e-01,-2.589051342569476333e+00,6.814274106521207575e-01,-2.172450762975258520e+00,6.771844619118718711e-01,7.893838683918596999e-01,1.220984184196191702e+00,9.713888638079207771e-01,1.458802079296825926e+00,1.185425270731450542e+00,1.355443481585577037e-01,1.263862225053526300e+00,-9.934540727800399429e-01,6.442559055151884095e-01,-4.334183478140564150e-01,-9.637025561891382486e-02,2.290355180612489716e-02,-3.576433150513270709e-01,-4.083649193695951252e-01,-3.894901602484461822e-01,-3.790657542003009750e-01,2.201325672478222917e-01,-2.560429389878834949e-01,4.352767250870462346e-01,2.458101969943881360e-01,5.483109789754934127e-01,6.058414469723568674e-01,1.386143408356037554e+00,1.015892255549173839e+00,5.873301333276124137e-01,3.246010945940253634e-01,-4.844386602637087424e-01,-3.103605513216893264e-01,-1.410321663673328590e-02,-1.041743315904650885e-01,2.112860363825554977e-01],
    [-3.507227580934837897e+04,-6.726630600905932624e+02,-1.792347165033409624e+02,-1.684730979710234578e+03,-2.621547013528328876e+02,1.794843083239687076e+03,9.342600748346690125e+02,6.590335615677053056e+02,-1.456739491617092654e+03,2.949231413916190832e+02,3.611968327332602939e+02,1.001285550593955946e+02,-5.560931360643878634e+02,-8.912980352030174345e+02,-2.671881835416240847e+02,1.197406925410150791e+02,-4.157761085122796203e+02,-1.161685620524793805e+01,-7.530144383260294489e+02,-3.223985870916825434e+02,1.959734110781799998e+01,-3.681365835252630347e+01,4.391191845172323127e+01,-6.132275498223136765e+02,2.019099660924260320e+02,-4.802180535707969256e+01,-5.294767000494390174e+01,1.649408861956089254e+02,-5.995714916890916868e+01,2.843489819830007264e+02,-7.488329244197905155e+01,-1.872660110384140921e+02,-2.505435156463264335e+01,-4.972382648956041606e+01,2.402648007183838672e+02,5.769119199139637999e+01,1.446500539312852496e+01,8.896916284261416763e+01,1.422565837832330793e+01,-2.387109280742037143e+01,-4.741333909042763395e+01,-6.298836619974319717e+01,-6.484204269795644393e+01,4.913136893504544744e+00,-4.540665718256493477e+01,5.490674110422743226e+00,-1.572689433635670753e+01,-6.094428119479469075e+01,4.969427569085693719e+00,9.220148141147459953e+00,8.058724207730865174e+00,-5.437905181803381005e+00,-3.174176570156099331e+00,-6.697629454824690853e+00,-1.575518675447959360e+01,2.150179533428908130e+01,-2.326754951866031007e+01,-1.468213377872937286e+01,-1.027937871606854259e+01,5.771622852863821374e-01,6.006542885269192666e+00,1.619166445077011929e+01,1.400388765027790861e+01,-6.744882281643173327e-02,8.078441075108219738e-02,-2.822425115633909964e+00,-2.352986858453424368e+00,5.678449946034852758e+00,6.019947061986238301e-01,6.449305081232195036e-01,8.321226055883630401e-01,-4.631616697930291959e-01,-3.712658628268775907e+00,9.459521487345805113e+00,7.288302618085404916e-01,7.215437313224223992e+00,9.990329259459358457e-01,-2.125662888427814146e+00,-3.503307898921653951e+00,-1.571328695492931082e+00,-1.761863781227849743e-02,-9.373464910616966517e-01,-6.180281287505116072e-01,-1.213616091233036265e+00,9.651311870428960216e-01,-2.888778699091964164e+00,1.062479802301902199e+00,-2.039528295732458751e+00,9.988112649075613358e-01,1.231740130344628037e+00,1.133673024466066881e+00,1.104796125681283048e+00,1.034245915899319801e+00,1.409400808435514962e+00,-3.590003294530506039e-01,1.571164540566916124e+00,-1.309084819424698010e+00,7.407301630345675125e-01,-5.179666902161366160e-01,-5.641854155355009726e-02,1.007508066156828086e-01,-4.096551261201464289e-01,-4.849214682137785726e-01,-4.499371790386481051e-01,-4.997861184614003638e-01,2.858918773869414398e-01,-2.998730550268234873e-01,5.198283427348249219e-01,3.089305548023144055e-01,6.116558827874627458e-01,6.915126416852430680e-01,1.372953946124110924e+00,1.159724823841952857e+00,5.111248160131768303e-01,4.586760085168155587e-01,-5.998370552136349509e-01,-2.377779400297366230e-01,-4.830623999702634425e-02,-7.552875375446008177e-02,2.123851426918583474e-01],
    [-3.470022476223434933e+04,-5.753771181094987242e+02,-2.071456830849878372e+02,-1.900046786335702109e+03,-2.708962794933192981e+02,1.615801795933357880e+03,1.024314265106876746e+03,8.087346326748609044e+02,-1.531996186560405022e+03,2.965164059361505338e+02,2.871198768431938788e+02,1.426396400180303203e+02,-4.232032707579960515e+02,-9.934161388303608646e+02,-2.860864376172949619e+02,9.885492890014643308e+01,-5.082674722924781463e+02,-2.256537828097454934e+01,-7.683310989857442337e+02,-2.703743493408544509e+02,7.753472175526336230e+01,-8.277782510343492106e+00,4.511446450561186339e+01,-6.859905306117636883e+02,2.072384884471184989e+02,-8.509872644006726716e+01,-3.022975159690093250e+01,1.615404332873923465e+02,-5.306207769957172360e+01,3.151486198013287776e+02,-6.919339710444789660e+01,-1.755544837155259472e+02,-4.622701746770867004e+01,-4.449279121020686034e+01,2.282709887157883770e+02,6.664644735263561870e+01,8.188799326776621257e+00,9.733621543348874638e+01,1.027777199491512228e+01,-1.849513876634539855e+01,-4.187448209368107399e+01,-5.846445136409674603e+01,-5.339215472707637389e+01,7.383801815908904942e+00,-4.370595575033336644e+01,-3.960907737232704395e+00,-1.867715863555178046e+01,-7.074034329149175448e+01,7.175949189775780113e+00,9.218564679515502291e+00,8.460773978843167953e+00,-8.395492670818036629e+00,-3.542500954996214424e-01,-4.931731821424791384e+00,-1.445835119338210006e+01,2.734553212869983341e+01,-2.331623004423950718e+01,-1.322243111380107017e+01,-1.398541436625639278e+01,-3.633815959244813820e-01,2.276053514308808534e+00,1.705973768225736009e+01,1.307895852701304662e+01,6.637510298428869193e-01,2.232473422779882033e-01,-3.022587834651659477e+00,-3.255415021090039218e+00,6.865473991625866468e+00,3.517142707636781163e-01,1.314261409590205654e+00,2.043927031032130248e+00,-9.489435912720507738e-02,-2.857864072884899187e+00,9.054370550456564359e+00,9.249720471015845380e-01,5.991102620644285004e+00,1.361058706745482683e+00,-3.002506159051007373e+00,-3.209259110983841978e+00,-1.871728103260969167e+00,1.312841296067186470e-01,-7.843991888951122871e-01,-7.700393510042484735e-01,-1.443531756143266120e+00,1.122904573333717737e+00,-3.200795660619937255e+00,1.261710020345564676e+00,-1.892746347925271078e+00,1.240564496345843759e+00,1.557023992787367028e+00,1.058960723990206354e+00,1.164088427670569637e+00,6.647546524149061664e-01,1.561267700980743856e+00,-7.356026584919800326e-01,1.894082038957717540e+00,-1.547340373656759693e+00,8.316339396413471308e-01,-6.076404076663742826e-01,-3.387888606519275786e-02,2.091547596630679295e-01,-4.457531902065937635e-01,-5.204253105780868305e-01,-4.797905419741832489e-01,-6.113531472048212567e-01,3.243022896559604740e-01,-3.237428626648433672e-01,5.695644154946998272e-01,3.701812757045808144e-01,6.478539046376550203e-01,7.401924070730162564e-01,1.357313557310456886e+00,1.259397344895202275e+00,4.361649021760383160e-01,5.852902088691216420e-01,-6.930235049543529424e-01,-1.744972133930953184e-01,-8.058881931395871223e-02,-5.810408999421426413e-02,2.133767107637856153e-01],
    [-3.426343560235595214e+04,-7.632238830441353912e+02,-3.865358862729352154e+02,-2.054080570547093430e+03,-3.291378312528121342e+02,1.379049488892794670e+03,1.053277355674684486e+03,7.675135416170138569e+02,-1.549006928886843525e+03,2.998954314601530200e+02,2.497666022693395291e+02,1.406602175530775298e+02,-3.573540893840902868e+02,-1.096945304464397850e+03,-3.785605253773703112e+02,5.835913681668493780e+01,-5.496066400203828834e+02,-2.384570418020388871e+01,-7.624840889902118306e+02,-1.635570644750404199e+02,1.389791189829857956e+02,1.998850677923837083e+01,6.671277838033672936e+01,-7.132310986197016973e+02,1.967998718053638640e+02,-1.152092009475731231e+02,-8.527298323041669903e+00,1.594556966887332123e+02,-2.337780508986029204e+01,3.451919382983335254e+02,-5.053040352079470665e+01,-1.586727430007326234e+02,-5.892870367936696141e+01,-2.610049355626925660e+01,2.135330079099517206e+02,7.204329013461027387e+01,-1.742069438666054459e+00,1.010631233273571752e+02,7.032010156227779696e+00,-1.167008068164080470e+01,-3.690422802170809291e+01,-4.689091618510482107e+01,-4.278801916883372769e+01,1.077400431186229746e+01,-3.579700435270461156e+01,-1.071870039725201629e+01,-2.150006539378041026e+01,-7.965933804615769986e+01,1.034306745273281969e+01,7.967085651295189308e+00,7.696723282582756731e+00,-1.137253931986937872e+01,-1.699851738312264104e-01,-4.122141198574048815e+00,-1.192052496931137107e+01,3.079346159926491566e+01,-2.146595104008633115e+01,-1.208326510526753417e+01,-1.571157366098020702e+01,-1.282138763985449792e+00,-5.605525814850944588e-01,1.738735025065368589e+01,1.330931111196340666e+01,1.943445918403689188e+00,5.926919457505627209e-01,-3.237481061374565705e+00,-4.267239963107853917e+00,6.928038991932557344e+00,-1.825330292762120110e-01,1.421935992375804592e+00,2.546005163464582388e+00,5.639901924238133191e-01,-2.833537358501488246e+00,9.155429577452830259e+00,8.374010873653396914e-01,5.274442266304352422e+00,1.586556120265420589e+00,-3.170056664336520669e+00,-2.697168092697271202e+00,-1.996945092152858647e+00,3.103886293865047441e-01,-4.523914480126238757e-01,-7.918778590598778422e-01,-1.621226571981247533e+00,1.149565065288371546e+00,-3.464966168824721748e+00,1.117133145111401049e+00,-1.800533978474124108e+00,1.377391769963697943e+00,1.565472214954502395e+00,1.111891958780476086e+00,1.009928805046538702e+00,4.710096549169909275e-01,1.587528407572909472e+00,-8.807911831091110866e-01,2.190545931815173653e+00,-1.602092798596771894e+00,9.141169808539363340e-01,-6.682849069534082531e-01,-5.543697739226356724e-02,3.434431975572621032e-01,-4.447214687411631395e-01,-5.041998606868319799e-01,-4.555055600802386806e-01,-6.885070477865908867e-01,2.995887254502585528e-01,-3.078036158278755763e-01,5.451827824385175880e-01,4.038439523346750715e-01,6.682926807273786851e-01,6.863699790898297737e-01,1.351458561049998286e+00,1.261022371180200663e+00,3.753044332870468791e-01,6.714003352937180091e-01,-7.337653999365509883e-01,-1.369243518235806201e-01,-9.612187866515506385e-02,-5.745638703547586990e-02,2.203276938279536967e-01],
    [-3.409348098694685177e+04,-8.928484473271435036e+02,-4.433179819956318397e+02,-2.178764607849225285e+03,-4.038135829770472469e+02,1.131969621258144116e+03,1.070432895946297549e+03,6.305263429758003895e+02,-1.506079741368854684e+03,2.326746710016694522e+02,2.006149794430956490e+02,1.159037443930404265e+02,-3.658640645331889800e+02,-1.229275851790535626e+03,-4.450976070371034439e+02,2.206355734634651355e+01,-5.475185446211042972e+02,-3.554019718483844059e+01,-7.466177917348693427e+02,-3.678939441903840191e+01,1.818134314993432668e+02,7.015180700530592617e+01,9.150823267184367182e+01,-6.804955523296471256e+02,1.812704469029175129e+02,-1.300372362305473075e+02,9.506309491737971129e+00,1.560587675735014841e+02,9.769549320894478583e+00,3.697322595772423597e+02,-2.063724705814376392e+01,-1.467762649406340358e+02,-5.841114594417240369e+01,-3.052106260967253348e+00,1.987197499634279723e+02,7.490524457651254409e+01,-8.837957993511361465e+00,1.017455665694390348e+02,6.090404972668830297e+00,-6.730207285185679567e+00,-3.188000014597886533e+01,-3.367931352569398484e+01,-3.587307964908033853e+01,1.478038978762806543e+01,-2.697220331564410145e+01,-1.339963621213789757e+01,-2.415577094629470167e+01,-8.617815003246252559e+01,1.322489301358742253e+01,7.042955549752270450e+00,6.463885078725341238e+00,-1.291086931537139471e+01,-2.019853727491440765e+00,-3.679965269414643192e+00,-9.663674522380862442e+00,3.151055073694623943e+01,-1.855735626795187443e+01,-1.229811478370185540e+01,-1.545877096868530209e+01,-2.581654219931871275e+00,-2.245294577666743674e+00,1.669667875576723759e+01,1.416685636179115271e+01,3.112124890477579342e+00,1.065354192462039995e+00,-3.436524212566550940e+00,-4.921670748447138699e+00,6.314844937043902817e+00,-7.776055067936763487e-01,9.620635484538033744e-01,2.502026670739343039e+00,1.227155666534883727e+00,-3.622452467326252812e+00,9.617183842012122952e+00,3.239694987480621347e-01,5.073014905840501854e+00,1.486793726263445636e+00,-2.890506729376390638e+00,-2.085797826841095937e+00,-1.932399099415033961e+00,3.993851676153724606e-01,-1.395664023241398044e-01,-7.565051135518625625e-01,-1.691257877862881287e+00,1.123745768146834800e+00,-3.611637601226043159e+00,7.779458910502142777e-01,-1.738768314133330772e+00,1.409808004378862556e+00,1.321789433627575949e+00,1.256293671687487734e+00,6.919552379377930107e-01,4.772477392104162996e-01,1.462252230975803258e+00,-8.680004005765579178e-01,2.405897764090024538e+00,-1.529947327088976738e+00,9.858451082450947478e-01,-7.125517376548496928e-01,-1.098391179394914569e-01,4.331389415252897557e-01,-4.214259857337624426e-01,-4.612789765948363541e-01,-3.936626088326486417e-01,-7.187804358828741025e-01,2.489449080929508340e-01,-2.578795538911309859e-01,4.769728022973662718e-01,4.154739940840416756e-01,6.797088998231898271e-01,5.641876666193342826e-01,1.359229869891914966e+00,1.180346235824215606e+00,3.296957228395296924e-01,7.082197535916016085e-01,-7.403055069455641846e-01,-1.159155641472306708e-01,-1.111649924642232612e-01,-7.313581343475765439e-02,2.236089629314598204e-01],
    [-3.397584969990269747e+04,-9.257995074126029067e+02,-4.153205838279379805e+02,-2.313811260705561835e+03,-4.819677031471388773e+02,9.524523950381230861e+02,1.130645621796444630e+03,4.859918953607235608e+02,-1.429994868676919850e+03,9.350624165469756122e+01,1.526025273289069446e+02,9.413790888342066410e+01,-4.222915014445765109e+02,-1.375301197613833438e+03,-4.453306054294988598e+02,-1.554088652057188158e+00,-5.234120822452047150e+02,-6.503963546391894113e+01,-7.335080028313511775e+02,6.907451366102502277e+01,1.943843055654222951e+02,1.363056200029442664e+02,1.046786360533945270e+02,-6.180580625582416587e+02,1.685752255560785215e+02,-1.289899223555889307e+02,2.231569886650795453e+01,1.461335167121370375e+02,2.803080668815048782e+01,3.845815655163578981e+02,8.792700119054641661e+00,-1.462059930224717164e+02,-5.339926865653288246e+01,1.722176751710313525e+01,1.847622255866724856e+02,7.580430473430166671e+01,-8.982948216993957402e+00,1.010129010608686713e+02,7.434155374577727571e+00,-6.213155368631285924e+00,-2.695308281458927979e+01,-2.501423709352465963e+01,-3.411896465050363503e+01,1.657949915866128521e+01,-2.134820614110870451e+01,-1.301606205687443385e+01,-2.548103264158922698e+01,-8.917616558446052011e+01,1.459837297432431669e+01,7.614097724471275086e+00,5.546971774118214071e+00,-1.241671717024088828e+01,-4.576883193742258271e+00,-3.162308555952199285e+00,-8.988763781236945860e+00,3.021909621192219220e+01,-1.623581244016693503e+01,-1.381671297403566356e+01,-1.428632155284125105e+01,-3.797244153463143590e+00,-2.784807730620107780e+00,1.503748633150383540e+01,1.495380922506205934e+01,3.614192809699861009e+00,1.469628011710447435e+00,-3.588488404009456900e+00,-4.860596324454405703e+00,5.660810558857865438e+00,-1.202739440377540880e+00,2.452863398261420080e-01,2.237417317626487101e+00,1.558109169686969775e+00,-4.757265332851510209e+00,1.004115923124013676e+01,-3.401700411974432070e-01,5.239759684453524358e+00,1.079892886074561353e+00,-2.551183822464674567e+00,-1.553585480716577871e+00,-1.672016238200068283e+00,3.344012204368756458e-01,-2.322143158453247869e-02,-7.405729061447950956e-01,-1.622624919008945010e+00,1.118708392384164085e+00,-3.617080555807903774e+00,4.597809002882287110e-01,-1.687749322712471800e+00,1.381470174441248533e+00,9.965517299230004511e-01,1.391576436064637212e+00,3.833625215591494051e-01,6.280005106993425956e-01,1.255110964409126506e+00,-8.071669957599170164e-01,2.512591323598305060e+00,-1.405711828983223333e+00,1.054092483573310313e+00,-7.382391028579802228e-01,-1.712637745636519659e-01,4.314611521053060006e-01,-3.959667415278506075e-01,-4.198449285816510668e-01,-3.297071121175304542e-01,-7.053928257627571918e-01,2.153015216103100760e-01,-2.032781339972573598e-01,4.138544900486681444e-01,4.109840828743230312e-01,6.842708685051952511e-01,4.415935669752332204e-01,1.377482194814600547e+00,1.076108211867846443e+00,3.054659620744328841e-01,7.071989429968301710e-01,-7.339632946532672619e-01,-9.387029779294234211e-02,-1.284223225620187425e-01,-9.911877616436839955e-02,2.158693989413601466e-01],
    [-3.357362759662356984e+04,-1.057322319318586779e+03,-5.343820050720969448e+02,-2.439771368122823787e+03,-5.399070717275877769e+02,8.387163077365675008e+02,1.166655040736433875e+03,3.896802560161304427e+02,-1.313521907657983320e+03,-5.527859983018144874e+01,1.382713846085875673e+02,8.876554405576044360e+01,-4.858402331960053857e+02,-1.464205549635093575e+03,-4.102087816807624563e+02,-1.559086617429636235e+01,-4.866094685456311026e+02,-1.054504356289435520e+02,-7.179921993942544987e+02,1.336201686110398157e+02,1.827115210934341292e+02,1.869022884655730934e+02,9.734809623144887780e+01,-5.649967476357048781e+02,1.580069521443823248e+02,-1.154577730093981529e+02,2.910426543009382883e+01,1.293515568864524141e+02,2.719627177123659223e+01,3.873151657742097314e+02,2.462038034215322568e+01,-1.543051894584123716e+02,-5.664613061509687952e+01,3.176410749289026825e+01,1.740348013533915150e+02,7.381096236531661248e+01,-3.127242850355264281e+00,9.905888114454458560e+01,1.012242527396523428e+01,-9.367035048205455183e+00,-2.287058234080044983e+01,-2.339196464375604378e+01,-3.634704439432385215e+01,1.336435356941987962e+01,-1.920780981844509228e+01,-9.622902023393461235e+00,-2.368830450155191869e+01,-8.813694115016677699e+01,1.398713668329631865e+01,9.347957464485421752e+00,5.345683226044855019e+00,-1.036154450417707018e+01,-6.878330526570504588e+00,-2.570746783777293043e+00,-9.865051937617559830e+00,2.795355540963104346e+01,-1.545516113016711479e+01,-1.551116402633258673e+01,-1.279273833725393317e+01,-3.927243276400286476e+00,-2.270144367803664576e+00,1.268279948658389955e+01,1.520121495688774615e+01,3.410545636077958243e+00,1.677711895148785048e+00,-3.633540784353504804e+00,-4.111325319024315306e+00,5.259419819129888651e+00,-1.337800452164602083e+00,-3.350094207622575926e-01,1.999874564389161335e+00,1.399099903676663370e+00,-5.703858467258966058e+00,1.012180955171274732e+01,-7.205189203174460211e-01,5.699420400146788523e+00,5.551770459370330979e-01,-2.299758487678493779e+00,-1.208590299797208001e+00,-1.220443969795037553e+00,1.610010729251879769e-01,-1.356255370435457686e-01,-7.577677992085654068e-01,-1.432113753068522843e+00,1.153930220148440933e+00,-3.474306987237030242e+00,2.776074475979248835e-01,-1.635102501456199731e+00,1.303831014584452275e+00,7.240228445254290879e-01,1.429819757770392830e+00,2.194872814081243462e-01,8.692694672952301360e-01,1.057142765597960610e+00,-7.392753835740769608e-01,2.483855838848366915e+00,-1.239797735550152602e+00,1.117834973812771082e+00,-7.142612362546664206e-01,-2.198022740872375425e-01,3.454371635891533288e-01,-3.807056003453887505e-01,-3.893629323591642488e-01,-2.840338482295531319e-01,-6.581660287463912962e-01,2.146548370906968262e-01,-1.651625938132576521e-01,3.776714055034524620e-01,3.958608892611698571e-01,6.707950232023982551e-01,3.559301038767672676e-01,1.394133907413300788e+00,9.893411308177786356e-01,3.095215508502190405e-01,6.748122065004187320e-01,-7.110882142423284868e-01,-6.377960176920521862e-02,-1.313832622184924748e-01,-1.226413926490265704e-01,1.932570848024535437e-01],
    [-3.316443144238796231e+04,-1.182096898216485897e+03,-5.631781139683295123e+02,-2.599337615462519807e+03,-6.386367639966939578e+02,7.373586271538438268e+02,1.220274716838727500e+03,4.060264660187395975e+02,-1.163716399005266112e+03,-1.971312458485798516e+02,1.479281071689093494e+02,9.326288879342533278e+01,-5.437080599698905417e+02,-1.461110176204331310e+03,-4.173547509944449985e+02,-2.952555156964886862e+01,-4.460397033497552002e+02,-1.471748743101641139e+02,-6.971238316221142668e+02,1.642187634979156314e+02,1.651026513697653115e+02,2.054543731565160556e+02,7.482921379849263133e+01,-5.379694055732067000e+02,1.462420830618279410e+02,-9.609563083882653700e+01,3.677585403855957225e+01,1.068449106130731536e+02,1.745300800267083119e+01,3.805508542251080826e+02,2.701176735947894869e+01,-1.623315120274375261e+02,-7.093931256419479325e+01,4.335500093052155535e+01,1.694526015423646470e+02,6.839155991694681802e+01,6.133856606447122495e+00,9.695987630443937633e+01,1.346599866812834279e+01,-1.281300721336374693e+01,-1.965778237062371758e+01,-2.493391924788660674e+01,-3.869487959276158762e+01,5.585247992400986128e+00,-1.711434781948173622e+01,-3.587833591721675042e+00,-1.796742508692968698e+01,-8.405908978554872135e+01,1.203720276823581870e+01,1.152563900048316370e+01,5.848564720864525057e+00,-7.369134918144863988e+00,-8.246259281758961279e+00,-2.064364400168124281e+00,-1.090100172446286741e+01,2.557251912004837635e+01,-1.582902189970937457e+01,-1.628204471461120662e+01,-1.109784523115950705e+01,-2.366982792532556612e+00,-9.106099059461368883e-01,1.020469690003274010e+01,1.498470129965566144e+01,2.812617474330735057e+00,1.691104447783172926e+00,-3.687598502910297338e+00,-2.892092257299982094e+00,5.094863122371495301e+00,-1.278301138710503881e+00,-5.873327980365924406e-01,1.711137587053154885e+00,9.369635414627066616e-01,-6.234837116945048052e+00,9.828301049620211671e+00,-5.590748396329808800e-01,6.400186633963967253e+00,1.872473452109670311e-01,-2.012359077391441264e+00,-1.057201444166299575e+00,-6.147572090881078255e-01,-5.411200914840320897e-02,-4.020598560252552911e-01,-8.274468399640827476e-01,-1.174300807197046437e+00,1.170590069618814066e+00,-3.226831424925901359e+00,2.164922230435495365e-01,-1.640808186062797658e+00,1.217944098974421241e+00,4.964169470405627727e-01,1.389692236585660101e+00,2.190545141746267355e-01,1.183394499576418291e+00,9.728244824018990045e-01,-5.941398171331242484e-01,2.355974034522085869e+00,-9.898406754226164450e-01,1.171187683773143640e+00,-6.160351553344773912e-01,-2.475303354009322221e-01,2.097095517556230859e-01,-3.825589483823106374e-01,-3.664274746563156993e-01,-2.643464691441811953e-01,-5.938492204521609308e-01,2.349251996456171443e-01,-1.620274306117735486e-01,3.718102884519446927e-01,3.533851006466001143e-01,6.505850503534551521e-01,3.056200786220228394e-01,1.410683628794187072e+00,9.450943058874310410e-01,3.523929261882464692e-01,6.314523541927522521e-01,-6.493420411130645942e-01,-3.187213870472425936e-02,-1.003782432952204928e-01,-1.343974224651987015e-01,1.615249693376650253e-01],
    [-3.287874865743784903e+04,-1.278631252755147443e+03,-6.912401129705252742e+02,-2.748790310197570761e+03,-8.038349224094914689e+02,5.524244364200183099e+02,1.231550022604386641e+03,3.343688921017574671e+02,-9.672781670552119522e+02,-3.235025728003661243e+02,1.798470166536541797e+02,6.413685720143216429e+01,-6.344518525891985519e+02,-1.450086813049824286e+03,-5.139067233711293738e+02,-3.906777741208227894e+01,-4.081521275201478147e+02,-1.711133439836927153e+02,-6.694620873195543709e+02,1.801799666002839331e+02,1.308128633091875770e+02,1.796551660003572408e+02,5.655848199193574999e+01,-5.378083851144324399e+02,1.300919643916147095e+02,-7.668838017202514834e+01,5.064422038769484402e+01,8.335797175080850252e+01,1.240912920747022241e+01,3.655617618501756851e+02,1.705172658830709054e+01,-1.627295561280233755e+02,-9.236663469819795580e+01,5.876343058248146178e+01,1.634689511017198242e+02,5.840313263963608392e+01,1.684647698846531938e+01,9.522344847841213777e+01,1.673393650508666042e+01,-1.307281687942959003e+01,-1.614503875146764855e+01,-2.493245059208888392e+01,-3.943041328051396732e+01,-5.579125275105305981e+00,-1.182294520292098738e+01,9.692738026881144719e-01,-1.133662746855577019e+01,-7.972938793291834259e+01,9.450374035945479534e+00,1.352342106008634737e+01,6.953290718394118386e+00,-4.068300173464806768e+00,-8.176300408490989824e+00,-1.328508242168128017e+00,-1.039812189760929506e+01,2.300482474689047052e+01,-1.698065062179222906e+01,-1.594547658043654437e+01,-9.726976718491881613e+00,2.441072485814223814e-01,1.748477059587767724e-01,8.207258615877000452e+00,1.495505330336166949e+01,2.142961785849772927e+00,1.523180403530761451e+00,-3.815283051806289460e+00,-1.455718830197308744e+00,5.025319187875811444e+00,-1.068914921459317879e+00,-4.019345982848869792e-01,1.215127596595950710e+00,4.368358557062543834e-01,-6.454289110453965250e+00,9.274495214987844349e+00,8.132308103205879157e-02,6.998426446311713178e+00,1.126933154206082033e-01,-1.458241416396250489e+00,-9.178000041605874904e-01,7.444823355713169055e-02,-2.348992585487015283e-01,-7.329699659539659073e-01,-9.572114705095539078e-01,-8.998998711124837069e-01,1.090469854932619498e+00,-2.935151258995561285e+00,2.473846875031581738e-01,-1.720974315055614934e+00,1.192317219038968146e+00,2.291998588672991000e-01,1.339976493031636906e+00,3.370100353339303689e-01,1.499189807752841386e+00,1.053545508791246865e+00,-3.338152171463449891e-01,2.238014659023507935e+00,-6.660070242688381770e-01,1.208145887228405879e+00,-4.982700319017310253e-01,-2.420956946096793627e-01,5.756700896648250798e-02,-4.098300808443798848e-01,-3.485075241683274205e-01,-2.683747731317300822e-01,-5.343146964417755385e-01,2.545250840720647556e-01,-1.900222712020784022e-01,4.019941462662351972e-01,2.654618273854678634e-01,6.451845078138301881e-01,2.809060512224499928e-01,1.428699499438591758e+00,9.507606867836715381e-01,4.129154944446177811e-01,6.054654248531117222e-01,-5.509277498725574373e-01,-2.760935021850137970e-03,-4.782624678999753548e-02,-1.415701400450511127e-01,1.311745512615977438e-01],
    [-3.268417837995067384e+04,-1.219089435267614135e+03,-8.064429968694203126e+02,-2.859419656764539468e+03,-9.452803933408652028e+02,3.175830775964844293e+02,1.302030291698058818e+03,2.786157733806190322e+02,-7.089304600594763315e+02,-4.419359563486902402e+02,2.289159785456199074e+02,2.789659020280472745e+00,-6.807685719823102772e+02,-1.494552480385191302e+03,-6.436296317620467562e+02,-3.080043447934346190e+01,-4.105669583571427097e+02,-1.754601946300712996e+02,-6.355574300817751237e+02,1.923483886603131623e+02,5.757812038916807751e+01,1.117492799846781537e+02,5.605966100678227093e+01,-5.517222905213476452e+02,1.098375183314414301e+02,-6.896329202402226599e+01,6.258889035673161771e+01,5.751886041436033992e+01,7.788420456026671879e+00,3.381179253998575973e+02,-6.321359931425359235e+00,-1.525733905356692048e+02,-1.071956425743858290e+02,7.806924984095635978e+01,1.514422303963559102e+02,4.411313395222492773e+01,2.750209837313625272e+01,9.206829966930511944e+01,1.649052064928084604e+01,-1.239302907970190049e+01,-1.184256448364164171e+01,-2.252065529704252711e+01,-3.957694379400307128e+01,-1.662147925207790422e+01,-4.857610965804310510e+00,2.719134634172519771e+00,-8.557657729185397244e+00,-7.554422472408148792e+01,6.842950805857107355e+00,1.555216658257643658e+01,8.785829007014861247e+00,-1.440064369000056743e+00,-6.890909626532905286e+00,3.361846808080875409e-02,-8.261209991432112432e+00,1.975442177373525254e+01,-1.877679312687396518e+01,-1.506681921503790278e+01,-8.335614193352663293e+00,2.521262431462879317e+00,2.881968655387706635e-01,7.240771078622300294e+00,1.568975876793346202e+01,1.592881839299803648e+00,1.409925203321728215e+00,-3.791618332897249921e+00,4.035253654785420085e-02,4.991178527251975083e+00,-6.389162503427415762e-01,9.960221418414805239e-02,5.337679561944704831e-01,-1.827633129830997516e-01,-6.373292132971246637e+00,8.676760963728369802e+00,8.743154959366749024e-01,7.195906591661808349e+00,2.623845608657875417e-01,-4.303548396222178218e-01,-6.711667710500560657e-01,7.123874344607021847e-01,-3.222686075139308826e-01,-1.028983582494053195e+00,-1.087629916550070019e+00,-5.936059854783231060e-01,9.277196848126463280e-01,-2.638564047100659060e+00,3.561100048289478348e-01,-1.805816109233169264e+00,1.173768851193987439e+00,-6.615649695934321117e-02,1.297828482364761449e+00,5.197378788544475547e-01,1.741788441018950806e+00,1.230910711050319906e+00,3.700636357754396449e-02,2.167050952391728735e+00,-3.713285145398262932e-01,1.189799912500050461e+00,-4.438456109541560890e-01,-1.931452829092678569e-01,-9.101026866929173842e-02,-4.639818011072422976e-01,-3.236082739364661842e-01,-2.755319362564780938e-01,-4.983203292643539895e-01,2.680188662797692301e-01,-2.301180588811608807e-01,4.556970556508563863e-01,1.446608604370986373e-01,6.424905666997287046e-01,2.892770996305319420e-01,1.445733084172204919e+00,9.787563180506377858e-01,4.672108044799307969e-01,5.957207856901997056e-01,-4.427205738398901635e-01,1.952151377455264500e-02,-6.298196727506246914e-03,-1.532014716686477818e-01,1.141269469237576051e-01],
    [-3.254785471165441049e+04,-9.048026945027778538e+02,-1.077629140439559478e+03,-2.918122309196444803e+03,-9.696599086844184967e+02,8.297746233595724163e+01,1.375517665828645022e+03,3.559774368950481858e+02,-4.027931606622806839e+02,-5.490105519080063914e+02,3.072212956944750886e+02,-4.213269467372513333e+01,-6.458994675068315701e+02,-1.553543265404526210e+03,-7.436673496694326104e+02,5.797996848808133485e-01,-4.630757588491916295e+02,-1.666915232371060256e+02,-5.812377651996164332e+02,1.848003603949103422e+02,-5.635892775807734267e+01,1.443820045860714885e+01,8.484013052060072368e+01,-5.732288869017415891e+02,8.872308994991040265e+01,-7.846760848183414794e+01,5.895980331122343898e+01,3.031182165849622123e+01,-5.858769766803955115e+00,2.954070434721950278e+02,-4.084141819503362569e+01,-1.322102012712534247e+02,-1.093531472279587717e+02,9.404680022669538175e+01,1.293561143234564668e+02,2.738526879736246400e+01,3.553964992736411688e+01,8.481724233501790877e+01,1.014318952690509690e+01,-1.354691082857597095e+01,-7.753449660248996622e+00,-1.927605178261836727e+01,-4.193236265453799660e+01,-2.374681705710736423e+01,6.457974184137093010e-01,2.223619872350885096e+00,-1.111868750947462914e+01,-6.914294118848668802e+01,4.562545776771619543e+00,1.754430393272382815e+01,1.113266405911473100e+01,-4.156779298711649195e-01,-5.241445569844454866e+00,1.854038401397219094e+00,-5.154485067789013719e+00,1.515048197191147494e+01,-2.022184769385592773e+01,-1.400966830694915899e+01,-6.384051302253199722e+00,3.653800894203618199e+00,-1.878514270937706732e-01,7.674175434226695458e+00,1.741784256678318954e+01,1.315161127354863790e+00,1.579976494757970862e+00,-3.371256167081626565e+00,1.366668781733804128e+00,4.890307505584210901e+00,9.981374309466460593e-03,7.462320711433161335e-01,-2.977170082378461924e-01,-8.957880710361461052e-01,-6.031759182900264804e+00,8.250037474801711568e+00,1.583997418392641077e+00,6.973379201642974756e+00,6.772727992815015252e-01,1.090691206525984169e+00,-2.395825410961795743e-01,1.126405974475853666e+00,-2.661236993168090148e-01,-1.197536010186219135e+00,-1.123542555086849637e+00,-2.398558227499056617e-01,7.241800430244653697e-01,-2.359033037293240653e+00,4.776239249345980986e-01,-1.836217307296263312e+00,1.079774628640584933e+00,-3.547665010215712011e-01,1.280416038937531864e+00,7.400975717156889067e-01,1.861962351860352083e+00,1.426454111788178825e+00,4.658858076550635996e-01,2.134447858834984224e+00,-1.838590354657278769e-01,1.067436879851861420e+00,-4.752339539951565550e-01,-1.081081166917827463e-01,-2.132994159014549307e-01,-5.302845406852964016e-01,-2.751447499407263519e-01,-2.711618854932948963e-01,-4.910317327691998690e-01,2.578932303770980483e-01,-2.554439608943865903e-01,5.031079508177574988e-01,1.167093792754250910e-02,6.269786793181547635e-01,3.259946220630632885e-01,1.450517727807050017e+00,9.912745963709934660e-01,5.008748236180686764e-01,5.933858492665611273e-01,-3.440314297000584554e-01,2.449591455241856980e-02,4.680783653483728927e-03,-1.778535291862243795e-01,1.201943194038039286e-01],
    [-3.222859647291936926e+04,-5.765122463848613279e+02,-1.167014731288007397e+03,-2.989493717721430130e+03,-8.961045327187533758e+02,5.271560816877717315e+01,1.323009726322901770e+03,4.074517653043383234e+02,-1.497520050888078913e+02,-6.050722813194880700e+02,3.968516463228453404e+02,-6.578604288096371988e+01,-6.444505677484509079e+02,-1.544434131251802228e+03,-7.697746073966694667e+02,4.762413172612846068e+01,-5.046362564669626636e+02,-1.604868624363686820e+02,-5.048910238577390146e+02,1.341959487425231146e+02,-1.706126875827324625e+02,-7.731089621445262594e+01,1.279210031012528930e+02,-5.961516080447497643e+02,7.710023764027060622e+01,-9.184426404450390180e+01,3.526273782582966732e+01,6.918523794485882839e+00,-2.638148150284771276e+01,2.392005282846569116e+02,-7.780673585115526691e+01,-1.147754885813505297e+02,-1.042142612691562391e+02,9.801768509190488032e+01,9.917047058499086631e+01,1.288377937511464033e+01,3.926271249075691117e+01,7.346783102564918977e+01,-3.682346563927090255e-01,-1.533172472376161011e+01,-7.384302865606361621e+00,-1.846317688355341602e+01,-4.879166631463878900e+01,-2.618490632892350689e+01,3.393816387470240059e+00,-9.083626006933423480e-02,-1.593914814127202639e+01,-5.828643594017509599e+01,2.717680973194432248e+00,1.862674658437180497e+01,1.330031418492517048e+01,-7.699650325968321329e-01,-3.809795461048636867e+00,2.773237631873637810e+00,-2.251109933120670981e+00,9.261997064221738185e+00,-2.007846893085987716e+01,-1.280944162647240603e+01,-3.879111684650957681e+00,3.880421279024513392e+00,3.908794284775568562e-01,9.226162599115617979e+00,1.951538697066469652e+01,1.178274533156562942e+00,1.886200125679236006e+00,-2.609005663697589128e+00,2.259722221529960606e+00,4.659057948506413638e+00,5.711244066996536972e-01,1.382429872472129784e+00,-1.196451656390687290e+00,-1.385228861406269996e+00,-5.555168805271143206e+00,8.072158380528408728e+00,2.182526058040554329e+00,6.708940336544898742e+00,1.361844466544938514e+00,2.633182826178802838e+00,2.956137099881129271e-01,1.192072796219296738e+00,-1.369351504443572787e-01,-1.239543231574685489e+00,-1.027215326915056348e+00,1.013631127383470554e-01,5.071872480000410022e-01,-2.097142929609227657e+00,5.930807749825235398e-01,-1.801259867977570206e+00,9.387229154261881314e-01,-5.915369664036721487e-01,1.338608617840287618e+00,9.990838186189870962e-01,1.898783113267748179e+00,1.602384596791130322e+00,8.392520764079273166e-01,2.122089571679107944e+00,-1.057724170574943778e-01,8.470069687300464389e-01,-5.294278127859420868e-01,-1.764197207250120525e-02,-2.927263412036578138e-01,-5.844518724446091662e-01,-2.046882607166567447e-01,-2.633740213058442525e-01,-4.844337517099550072e-01,2.331525543506165477e-01,-2.483558209564482033e-01,5.339253205541207858e-01,-1.096878744765939356e-01,6.102008946546465529e-01,3.770606472805232978e-01,1.428474873327276295e+00,9.666895119087723920e-01,5.081770603963373656e-01,5.901289401387179723e-01,-2.658564253445672154e-01,-2.837917477455793782e-03,-1.613908590443956801e-03,-2.111363185804855658e-01,1.470787585464831404e-01],
    [-3.186741253674949621e+04,-5.085241704111117542e+02,-1.086731513809614398e+03,-3.093260858981398997e+03,-8.107723315246942093e+02,1.842520338892430800e+02,1.153966010706939414e+03,3.729727930493042436e+02,-2.591043782782234572e+01,-6.093609853606952811e+02,4.877385504135806400e+02,-9.371374211753294503e+01,-7.289927538757094680e+02,-1.424353069076127895e+03,-7.383395742583429637e+02,9.314256432146406439e+01,-4.688178711178779281e+02,-1.201626482036358539e+02,-4.321477301488021112e+02,3.492773455179796116e+01,-2.468226670051384986e+02,-1.414461029394116167e+02,1.506354053456261965e+02,-6.284970089880970363e+02,8.386116126780891022e+01,-8.700934377707093859e+01,1.130778376805065122e+01,-7.458221956567279598e+00,-5.150661374993470787e+01,1.777352647227101272e+02,-1.071912209145347674e+02,-1.074413159237742548e+02,-1.114864141889519544e+02,8.786480786413912369e+01,7.548694573690185905e+01,5.763121917115348936e+00,3.992611637414181303e+01,6.144308791280158744e+01,-9.659297535218343000e+00,-1.653072738144729925e+01,-1.377556300610634210e+01,-2.293583398318344990e+01,-5.737959200448912611e+01,-2.934046356329947614e+01,3.243921431181405524e+00,1.121291721677258740e-01,-1.792884689771670992e+01,-4.295740506808621006e+01,1.414664794258775782e+00,1.800601625768275582e+01,1.361874533052502123e+01,-1.112403604810340507e+00,-2.837728362066635146e+00,8.563216715182062622e-01,-9.313031891757406200e-01,3.346505599116912588e+00,-1.824958533952862894e+01,-1.152680769281666606e+01,-6.845759564187456903e-01,4.245138178294875608e+00,3.425247289030264319e+00,1.105056997751588277e+01,2.052509041520747246e+01,8.334202255214316901e-01,1.981624746177371943e+00,-2.263337389720510462e+00,2.525604897907957280e+00,4.500834252529440249e+00,5.033490705469502169e-01,1.849823796336691251e+00,-2.135021716315471441e+00,-1.157450392912908965e+00,-5.037162967253238754e+00,8.136798336661852815e+00,2.766096220606582001e+00,7.085045078851546663e+00,2.346499938344735359e+00,3.536548106721880025e+00,6.502585758337641186e-01,9.971689228512945480e-01,-1.032146444302126376e-01,-1.248739271312267363e+00,-8.850684519617117996e-01,2.813437066430282130e-01,3.784201496925008734e-01,-1.876404292233300186e+00,7.702107133299532782e-01,-1.823498205181554699e+00,9.332759016265089747e-01,-6.817037599289244021e-01,1.498710936637054125e+00,1.314894218795134018e+00,2.009448539275625389e+00,1.835097548746204010e+00,1.045186907723227865e+00,2.020413059283797441e+00,-7.447516127987634238e-02,5.939311869400505373e-01,-5.034723663423672502e-01,4.097208764983036045e-02,-3.323297009888214193e-01,-5.866906916910041847e-01,-1.393116957710757720e-01,-2.560868899721275849e-01,-4.387119731955410051e-01,2.420776621500786430e-01,-2.278661012772540406e-01,5.791990098429464773e-01,-1.740479363825776227e-01,6.093813238321615922e-01,4.396870486505085607e-01,1.381284835224067198e+00,9.367487693965321771e-01,4.994418523236459628e-01,5.585739067498747268e-01,-2.071415733527645908e-01,-5.982694546665540819e-02,9.639129594211440222e-03,-2.301230820188666648e-01,1.734478374599450201e-01],
    [-3.171993104334850796e+04,-4.727564230034689103e+02,-1.318708403053461097e+03,-3.222880951592092515e+03,-7.324698566782512898e+02,2.783746617810584780e+02,9.803032601433455966e+02,2.879117369065322123e+02,-5.797888889254889477e+01,-6.201543654806911263e+02,5.740437280154892505e+02,-9.968734188765704118e+01,-8.340715947762679434e+02,-1.226772896558260072e+03,-6.430455938010888985e+02,1.167488112200096282e+02,-3.641113745139945195e+02,-1.251590234289592729e+01,-3.641994566516177088e+02,-8.898368711978807255e+01,-2.730290191817334744e+02,-1.730441057947393233e+02,1.399412529315335973e+02,-6.742480678491299386e+02,1.058991078894138980e+02,-5.731279427148378858e+01,7.778905707001996239e-01,-8.530911760351157724e+00,-7.941694991051407726e+01,1.246715778596910127e+02,-1.265315650857371566e+02,-1.059705749618095041e+02,-1.421396953514758081e+02,7.140996511380498646e+01,6.990672193013281799e+01,7.194632825928282571e+00,3.906318117254520672e+01,5.145578471755181482e+01,-1.587782597448772748e+01,-1.817597192105338877e+01,-2.515706867764640720e+01,-3.380281586632341373e+01,-6.376744779455043499e+01,-3.845817836699571046e+01,1.791353168559498776e+00,7.250330558420814420e+00,-1.581729769606298142e+01,-2.726200357894443016e+01,7.719833877519172161e-01,1.571390742919693118e+01,1.130948347361790418e+01,-1.087051938425247721e+00,-2.760311672669752969e+00,-4.308928063178698586e+00,-1.936196213971097979e+00,-1.231187420435953639e+00,-1.586746850592940028e+01,-1.008164631864418936e+01,3.727733246507849874e+00,5.138016407924965279e+00,8.097126228945853654e+00,1.214555300048928466e+01,1.992734324731227247e+01,1.882290471792166797e-01,1.735218405020372945e+00,-2.832007013058859712e+00,2.081347424178043859e+00,4.491104370491486364e+00,-4.421321973410520245e-01,2.066117239185696342e+00,-2.991543193284884161e+00,-1.782102431445891644e-01,-4.466593884930945890e+00,8.519677312788633827e+00,3.342907998439665018e+00,8.314130928811170662e+00,3.443110395128887280e+00,3.604796409281433522e+00,7.414243738970485165e-01,8.145299164516783819e-01,-2.204815212620066522e-01,-1.289501049861642379e+00,-7.823051444584088188e-01,2.346371172336654820e-01,4.149839791998414795e-01,-1.766166444762313992e+00,1.030746408442250406e+00,-1.978043357955658443e+00,1.131472379508011272e+00,-5.580410815908153355e-01,1.732499107494265500e+00,1.683453065213346811e+00,2.301898593947384608e+00,2.158406944413734152e+00,1.048320587879462140e+00,1.778632697192713552e+00,6.775765639948997873e-03,3.881728131314503005e-01,-3.889761369552043879e-01,5.299133166166379583e-02,-3.390260928357186621e-01,-5.217634818030996158e-01,-9.173183286148804683e-02,-2.424798636672296226e-01,-3.522040557245196823e-01,3.024911870547852266e-01,-2.221696255359845995e-01,6.552893800683831094e-01,-1.507194928015334334e-01,6.154576658692486602e-01,5.147248196363086725e-01,1.334246005851215777e+00,9.347847980476012841e-01,4.840096982373454648e-01,4.805315273320414082e-01,-1.470267897017932812e-01,-1.217818598023571175e-01,4.397632444661572076e-02,-2.240467788982699049e-01,1.779569412246052584e-01],
    [-3.173448270849467735e+04,-3.771797898060209491e+02,-1.617024922164421241e+03,-3.319378608907845774e+03,-6.762793612515898758e+02,3.567305406917187725e+02,8.849169729812431342e+02,1.440819220877031057e+02,-2.083664033998631453e+02,-6.889445430688199394e+02,6.224574404738700650e+02,-5.921672951324181611e+01,-8.979726026173902937e+02,-9.911429927217811837e+02,-5.080048309473863810e+02,9.820909648758338051e+01,-2.415457465249581901e+02,1.315330686162087375e+02,-2.897825581340237022e+02,-2.053363475345916243e+02,-2.464842153608914828e+02,-1.927560541879905145e+02,9.600735329084734815e+01,-7.127373352699878524e+02,1.281366386621673712e+02,-1.101863892103396303e+01,-3.245256798498250106e+00,3.594986528143405469e+00,-1.028228534572935189e+02,9.114445111428796054e+01,-1.414899279289771528e+02,-1.090953968711175150e+02,-1.838584345203718158e+02,5.927409802376882908e+01,8.076577405315632063e+01,1.324509352694436615e+01,3.730060143526252148e+01,4.349105646583716123e+01,-2.046578516670825820e+01,-2.012797310366239145e+01,-3.648924000489192565e+01,-4.943326404611293867e+01,-6.744375095916259966e+01,-5.248412199262358513e+01,2.006487634993417757e+00,1.989928501690333107e+01,-1.175915388550218665e+01,-1.687925135616925587e+01,6.727023259768486474e-01,1.225309155134588401e+01,7.318281742111558685e+00,-1.178841837867341980e+00,-3.789571373357868200e+00,-1.108585463000748916e+01,-4.792360237479607044e+00,-3.979525648299104823e+00,-1.408210529456988880e+01,-8.142650414596024788e+00,8.994596065384715899e+00,6.269791954735894457e+00,1.193284305972766646e+01,1.196367642397450126e+01,1.856251089227064099e+01,-5.064410739673618211e-01,1.215825386004528053e+00,-4.035373458219035925e+00,1.095301259710770525e+00,4.388967928123293838e+00,-1.976811273071936936e+00,2.070839135414669574e+00,-3.558493435560301954e+00,1.030812793733400179e+00,-3.808637601303296094e+00,9.146439323943795330e+00,3.900102356262098002e+00,9.773816348172669422e+00,4.247455377409972144e+00,3.191246739029891089e+00,7.600277847261949216e-01,7.986786030617369914e-01,-3.866860402529926910e-01,-1.372863935630816989e+00,-7.152964053280562728e-01,3.366405202769546384e-02,5.377320105035632292e-01,-1.798829028094356630e+00,1.306407648873241234e+00,-2.188352487881688901e+00,1.383757235792046014e+00,-2.710495096109938329e-01,1.979576638656131315e+00,2.078953651727752927e+00,2.685546348332217725e+00,2.459443022072953955e+00,9.133618235121596651e-01,1.499952693113459468e+00,1.850285420902871847e-01,2.722578403550990345e-01,-2.520109039882347801e-01,3.588865014498030664e-02,-3.207092200466324372e-01,-4.121995393876537461e-01,-5.265509363425330269e-02,-2.284642084175722010e-01,-2.576660621839556020e-01,3.809087627077368809e-01,-2.324631502835151631e-01,7.341139756204084765e-01,-6.200924950246484990e-02,6.128842039090683924e-01,5.994694188234014343e-01,1.303141992787772319e+00,9.458334474983913776e-01,4.628038867937125933e-01,3.821582781528071182e-01,-6.255478441414968893e-02,-1.606305099773389367e-01,8.129210710700848774e-02,-2.026672280948751403e-01,1.595495306494024157e-01],
    [-3.177038857105299394e+04,-2.977656043149766560e+02,-1.877218783471936604e+03,-3.284025220902989531e+03,-6.437135485358519418e+02,5.092805959725461662e+02,8.267259089295264403e+02,-4.492601157641553300e+01,-3.527278325145916824e+02,-8.224004106337370104e+02,6.098492571629957411e+02,3.330445796581225437e+01,-9.040154043272395938e+02,-7.629128587880179566e+02,-3.552636981495128339e+02,4.633188075397431049e+01,-1.427869512491746491e+02,2.581316458139264114e+02,-2.029516202650511332e+02,-2.967874087853942910e+02,-1.849302277992265715e+02,-2.155066174076596326e+02,3.814089027703263923e+01,-6.945403688912933831e+02,1.374995450543215725e+02,3.874000239124336531e+01,-1.451163118577623834e+01,2.637858470880075146e+01,-1.146579169659048603e+02,7.934868493694540348e+01,-1.551722821339135407e+02,-1.122386505476282395e+02,-2.076318181337485385e+02,5.727522848772413511e+01,9.462190525002117170e+01,1.757021122262653279e+01,3.557260414398551518e+01,3.625608432135909709e+01,-2.464273510444987281e+01,-2.040030889694566341e+01,-4.265240412813788140e+01,-6.575351390426139631e+01,-6.905093253918855112e+01,-6.468227960908973273e+01,5.913904873278296392e+00,3.198434973811214732e+01,-1.008600068986100062e+01,-1.455378985353667431e+01,4.210199310503746073e-01,8.635667120397027219e+00,3.379669382639743702e+00,-1.488795897677996471e+00,-5.629996016139573456e+00,-1.670528838748052891e+01,-8.129667039067143719e+00,-5.063059978892746393e+00,-1.333185316554844846e+01,-5.469493438149726217e+00,1.393865678770728778e+01,6.479483753797684820e+00,1.301610703882390396e+01,1.059811524743946265e+01,1.799980228773150870e+01,-9.785378939608027071e-01,6.751335428972253805e-01,-5.202880255664932285e+00,1.141329803933281706e-02,3.954700263129101057e+00,-3.373201553730967195e+00,1.933161936307039808e+00,-3.696094262879408454e+00,1.764424488819759773e+00,-3.111305180317222252e+00,9.838703464900701690e+00,4.253186290501195010e+00,1.068579530085970930e+01,4.430152205564801271e+00,3.041002203917305913e+00,9.272753319807807149e-01,8.548443229614233196e-01,-4.533250559366506227e-01,-1.483528399245713558e+00,-6.284725437240874513e-01,-1.613804866176038189e-01,5.976699818079552751e-01,-1.906573880486402750e+00,1.487820237367885712e+00,-2.327187477026114504e+00,1.451082233304750613e+00,5.440207363819916930e-02,2.195705758678678343e+00,2.423654321540561707e+00,2.986164017485744449e+00,2.563656744140244026e+00,8.240724789193774047e-01,1.322350357692342548e+00,4.214679373151599684e-01,2.344204890790531626e-01,-1.642925218266664822e-01,2.378345051853148623e-02,-2.989519298255660651e-01,-3.034045338540952153e-01,-7.285349248894377322e-03,-2.287384025497742335e-01,-1.887836546253192638e-01,4.253563669266509084e-01,-2.319668217291052104e-01,7.726229892039466751e-01,4.323196363244478924e-02,5.960174542461070812e-01,6.788698497921284991e-01,1.290569326905463665e+00,9.200215368620137113e-01,4.548636287934902933e-01,3.055411723230187504e-01,4.981728880889792210e-02,-1.679428546653400911e-01,9.701311171948262535e-02,-1.883080827270068314e-01,1.318089038190609630e-01],
    [-3.203509674114802328e+04,-2.422816157558978887e+02,-1.797965296077940820e+03,-2.956095831590455873e+03,-5.663781088365790310e+02,8.192702693786753798e+02,8.421844859790705868e+02,-2.113934000357764376e+02,-3.348494063961466622e+02,-9.822999061150389934e+02,5.146830016817475553e+02,1.793375930348535974e+02,-8.889086448137563821e+02,-6.092597710203908719e+02,-2.726738304790184202e+02,4.650872423854119475e+00,-8.831206546252070666e+01,3.219355330788686160e+02,-1.082531540326461510e+02,-3.635941751523131416e+02,-1.278509524410507083e+02,-2.695255924685176296e+02,-2.039158877349112942e+01,-5.978806315751878628e+02,1.306012562611028329e+02,7.791372094099207857e+01,-4.150573862496737831e+01,5.364847104088784846e+01,-1.120144012073707955e+02,8.038144696674211787e+01,-1.756455172425452247e+02,-1.131169439184301240e+02,-1.965328692231022387e+02,6.382844543718120178e+01,9.640461439372762698e+01,1.494526930779500873e+01,3.439973944549318219e+01,2.985366361924939582e+01,-2.970598101253715484e+01,-1.699319664927123341e+01,-4.164932704041949307e+01,-8.011276434221784370e+01,-6.916477234113497730e+01,-7.068714243788051022e+01,1.392136515351319836e+01,3.633678742204947554e+01,-1.398080244362330937e+01,-2.001909380951298445e+01,-8.226200471299682793e-01,5.979754589979227930e+00,1.230907387802430808e+00,-1.940214098863197734e+00,-7.456266375230764964e+00,-1.886913264068928342e+01,-1.056737583298429328e+01,-4.808103428088911002e+00,-1.397885914872563085e+01,-2.083241653020218909e+00,1.696068627601419365e+01,4.893204023745330922e+00,1.055561079416428960e+01,8.837049857480517190e+00,1.913962667714179844e+01,-1.135055672922851144e+00,4.245565798349122399e-01,-5.693575922130551525e+00,-7.757997756460210947e-01,3.183396764943827950e+00,-3.895004353712958167e+00,1.782361070395155567e+00,-3.365718689525260654e+00,1.478572534444674513e+00,-2.379489098917082046e+00,1.027324734443033805e+01,4.312375749023774851e+00,1.041888746211580496e+01,4.032375278764494198e+00,3.618034805646777485e+00,1.323572945138667079e+00,6.900292113655116522e-01,-3.242640716336146478e-01,-1.575107642950789755e+00,-4.819226405038310457e-01,-2.105819007546920196e-01,5.038984876246667133e-01,-1.977818002465627334e+00,1.552798064340287221e+00,-2.298144276170180689e+00,1.180211586303010041e+00,3.240579465974056106e-01,2.334010483549479709e+00,2.675491534281578598e+00,3.009502094772479985e+00,2.422737617948800715e+00,9.182074950185028506e-01,1.339299882942506459e+00,5.943892598577213970e-01,2.308344944909865581e-01,-1.577521857167110964e-01,5.027027321793962888e-02,-2.928141782649597014e-01,-2.436893181702913802e-01,5.514686628338664326e-02,-2.461284431981019538e-01,-1.678660201713854105e-01,4.147761217885355123e-01,-1.932225785605884705e-01,7.537393344128376915e-01,1.246711237254019555e-01,5.683304165652900419e-01,7.502032562819610506e-01,1.277966728144697139e+00,8.361689006799665203e-01,4.682501778980785456e-01,2.903636761123853383e-01,1.584997104812905511e-01,-1.550281724466985867e-01,7.963321283646120075e-02,-1.913757319078375208e-01,1.126840248518856946e-01],
    [-3.253080940010315680e+04,-2.090684280066504357e+02,-1.862890878555385825e+03,-2.608210385663828674e+03,-3.670601833318902436e+02,1.097590929407356498e+03,7.955041740402753021e+02,-4.217793958739526374e+02,-2.374841571347709532e+02,-1.096226187541165245e+03,3.514629884487074492e+02,2.844557084054458755e+02,-9.227627862902460265e+02,-5.278362113442375403e+02,-1.854220064436144924e+02,-1.781483643492970970e+01,-6.940170674538467210e+01,3.337516992239000047e+02,-2.819114500405486368e+01,-4.191893463536109721e+02,-9.172116478611920343e+01,-3.001552919154783581e+02,-6.178918302601695700e+01,-4.812250452654994888e+02,1.176079567011035465e+02,1.004598759608378487e+02,-7.391409560830690850e+01,8.097092647366781648e+01,-9.695986115018379792e+01,8.606659473949734718e+01,-1.896024601420827196e+02,-1.024487184296061599e+02,-1.713294008431905411e+02,6.989913365302180637e+01,7.683424397564103003e+01,9.112432120969783611e+00,3.325333878429480450e+01,2.650846789005489512e+01,-3.368028075285264578e+01,-9.564086425050161822e+00,-3.547073097993942525e+01,-9.008131973811525484e+01,-6.474297933020403661e+01,-7.478708076608565136e+01,2.291957306704210140e+01,2.801775738689351414e+01,-2.398997013057730499e+01,-2.787973038752379296e+01,-2.048691635899666075e+00,4.610111916236363960e+00,1.250658063520650565e+00,-1.776003158901822143e+00,-8.584152207047271332e+00,-1.778100360109804257e+01,-1.239037105082325141e+01,-2.824432635369447553e+00,-1.609236428337411340e+01,1.037741036228837510e+00,1.643654112847001159e+01,8.750051658204306415e-01,6.622408971397364397e+00,8.039102786265440059e+00,2.117918834494137315e+01,-1.003970118750233009e+00,6.139144374444570618e-01,-5.561326080113553338e+00,-1.140477703719705360e+00,2.255500745540401475e+00,-3.508948951692144824e+00,1.375872443611481089e+00,-2.638360496815302270e+00,4.383292521135840336e-01,-1.735470823359916093e+00,1.002436110662860713e+01,3.760507650551977665e+00,9.425024252195489893e+00,3.724112382977629920e+00,4.605480354172774682e+00,1.783581111415806664e+00,3.502002940451585944e-02,-9.874999857485665389e-02,-1.591449853555078064e+00,-3.291662394689282567e-01,-1.523859839920740367e-01,2.894211133667552449e-01,-1.966399468060035183e+00,1.507815810915377863e+00,-2.137535606163639912e+00,7.272708745714786538e-01,5.078827019204176230e-01,2.382114642134615323e+00,2.727986461634247739e+00,2.809596644665664833e+00,2.270014201514276575e+00,1.138323960753132802e+00,1.503752297634127322e+00,5.517032230452131314e-01,1.848371063271168069e-01,-1.924549981805113441e-01,8.941308176256121398e-02,-2.984753117922313015e-01,-2.462784411513032623e-01,1.149804569919843367e-01,-2.630503762599813999e-01,-1.854215007238433355e-01,3.826242540649911761e-01,-1.276869780443904423e-01,7.202961379133442366e-01,1.835037547095084987e-01,5.582106016774247559e-01,7.980831936901167101e-01,1.255500756111368688e+00,7.492150497294182143e-01,4.884885522840372030e-01,3.402511151737939721e-01,1.960697798206874065e-01,-1.653974788818220465e-01,4.244359051276748451e-02,-1.927139589598862446e-01,1.103489858764488823e-01],
    [-3.315664231779341935e+04,1.233565458220188873e+02,-1.663255240165119176e+03,-2.313954233160190597e+03,1.338734408091454497e+00,1.370020751682899800e+03,7.173875429760756788e+02,-7.295390340936532994e+02,-1.307048740535938407e+02,-1.148536920130487943e+03,1.510964343949562476e+02,3.330363569868892455e+02,-1.040518048139910206e+03,-5.907551012894023188e+02,-6.439176381309243880e+01,-2.346541386218833480e+01,-8.260267755790121669e+01,3.111922022988321146e+02,2.303944895810405669e+01,-4.681482710248084800e+02,-1.108971401366751337e+02,-2.666776876106629288e+02,-6.520221486135453404e+01,-3.881285352307604057e+02,1.048744272010166014e+02,1.023790034534637670e+02,-1.047738682444675362e+02,1.037335130101600384e+02,-7.301436417075899499e+01,8.788600682704239375e+01,-1.805480522977290434e+02,-7.052496850234919634e+01,-1.508377466948900860e+02,7.462606305314112376e+01,3.653314264978493497e+01,3.791961117895378486e+00,3.111818341980189118e+01,2.649836173529961059e+01,-3.556254061229269325e+01,1.554879639262527924e+00,-2.548917827418801352e+01,-9.233985150137282005e+01,-5.259335130737746766e+01,-7.967196383677276117e+01,3.223257187967790571e+01,8.276861007658522951e+00,-3.890787882401720310e+01,-3.382984396839584917e+01,-2.373656568091789598e+00,4.507372464491398389e+00,2.955539687376719904e+00,-7.071482428283122346e-01,-8.524828322791845991e+00,-1.391298234478117735e+01,-1.346902734502026888e+01,1.035301396108256888e+00,-1.880168308392438092e+01,3.744332155607931867e+00,1.244610163761318766e+01,-5.745656062073560832e+00,3.025945817701126028e+00,8.884306670582098775e+00,2.320126084873766814e+01,-6.099039194480639914e-01,1.288271396664536717e+00,-4.985798776576753966e+00,-1.176122801058689937e+00,1.380248499134852036e+00,-2.382667938185356604e+00,6.314252266455444573e-01,-1.671199196119729447e+00,-7.427374789534262334e-01,-1.174775730980439858e+00,9.097091073986433685e+00,2.328317248327754552e+00,8.272274248720238532e+00,4.017857529106972692e+00,5.647284503147873558e+00,2.088264233643549073e+00,-1.096825395951438908e+00,1.429398152116582443e-01,-1.485350410719204817e+00,-1.969379871491790113e-01,-6.553070507885323803e-02,1.007544222796770070e-02,-1.878998283978324579e+00,1.363446451160895689e+00,-1.941241625512472924e+00,3.160518567067395201e-01,6.137126664076687499e-01,2.399609347559009453e+00,2.500933528755899360e+00,2.530503551517301108e+00,2.283954092621290677e+00,1.418574331855068982e+00,1.690201605523297568e+00,2.584708624869684890e-01,6.270865191840147013e-02,-2.287839036123201220e-01,1.176766109988846565e-01,-3.040541993585473279e-01,-2.938080460666431803e-01,1.543173811658480610e-01,-2.769712776833985757e-01,-2.364987774783904317e-01,3.483303853267654127e-01,-6.224415939832893957e-02,7.098931653591147306e-01,2.242653281645783925e-01,5.945514071960428248e-01,8.057799994716950964e-01,1.231685378291162536e+00,6.979409541218357660e-01,5.141441040673797591e-01,4.251411076865899696e-01,1.335651942340175535e-01,-2.201311354149373123e-01,-7.981879714479602969e-03,-1.756411611013344309e-01,1.204654292900585039e-01],
    [-3.382783669104191358e+04,2.857803003094479664e+02,-1.421126644550236733e+03,-2.101637855158710863e+03,4.145509604480749886e+02,1.531097895572817606e+03,7.062977901268310461e+02,-9.695799340177633212e+02,-3.976668828541544798e+01,-1.155385359650492546e+03,-7.885625104560750742e+01,3.917271266695188388e+02,-1.155086430419060434e+03,-7.095314175288343677e+02,-1.616018957474544493e+01,-1.364826085077513795e+01,-1.249007490759833843e+02,2.936749831302871598e+02,5.445401682718111402e+01,-5.033410363501720894e+02,-1.600744724078505499e+02,-2.258170666951715475e+02,-4.445475436022759652e+01,-3.299068719783614370e+02,9.268155813104128526e+01,8.623602045621238688e+01,-1.283935095918777733e+02,1.254596139787499141e+02,-4.962649836009421023e+01,9.098673248036138261e+01,-1.570807188397353968e+02,-2.216182724108745816e+01,-1.409332727320619654e+02,8.164282067432945666e+01,-1.401115072368819270e+01,-1.047795745213378482e-01,2.756108412424819321e+01,2.806067186587903706e+01,-3.528908782569408942e+01,1.344992234498722006e+01,-1.153617812985608992e+01,-8.688200843417536134e+01,-3.451732486648253229e+01,-8.482621716588494110e+01,4.137224755007552091e+01,-1.548341658942192112e+01,-5.499837049403951994e+01,-3.655964892800026433e+01,-1.594413370425961984e+00,5.029039040462935262e+00,5.147095099197659174e+00,7.603523993227263578e-01,-7.364172547807463332e+00,-8.384835261525488193e+00,-1.307349884668800399e+01,5.620227372109416031e+00,-2.105421890864320389e+01,6.322015320491735757e+00,7.039049655059480770e+00,-1.297351115894671736e+01,-2.465831568530238438e-03,1.088977537253945371e+01,2.445864294578401399e+01,5.902081804371444446e-03,2.230393163976029491e+00,-4.225684959642949323e+00,-1.208793070691599025e+00,6.532478587757970523e-01,-9.625424323463837029e-01,-1.548861467713563145e-01,-6.858032239851153955e-01,-1.495784582356717074e+00,-5.746135392009411591e-01,8.010999693125585353e+00,5.759304668183877762e-01,7.108711407856533881e+00,4.805108417405240750e+00,6.493496599811893866e+00,2.119338158259897575e+00,-2.468817583134728544e+00,3.940396352646220457e-01,-1.256463733658768955e+00,-8.890743748308599370e-02,-3.289084433664196672e-02,-2.773785616807789567e-01,-1.793465447661474421e+00,1.181690172683569573e+00,-1.767751408417108649e+00,1.002959878572329822e-01,6.820798937700184306e-01,2.475695645240866938e+00,2.139128781523063516e+00,2.243552840103899548e+00,2.405135688990557519e+00,1.660853875826287851e+00,1.757933675836506060e+00,-2.223653701902560398e-01,-1.053032415615380857e-01,-2.457122532194335740e-01,1.366181715567844623e-01,-2.929606281556727532e-01,-3.544870217799611645e-01,1.650715438826923787e-01,-2.898688936881487210e-01,-3.166711428494360936e-01,3.084551980354897638e-01,-1.328423424726032399e-02,7.328508395001834819e-01,2.508742906149031282e-01,6.748077409514732228e-01,7.875000158651480620e-01,1.203063691886271158e+00,6.611262962848513114e-01,5.249072934750834696e-01,4.927869147708663355e-01,-2.274306101901695226e-03,-2.882715447650713303e-01,-5.835579620503653087e-02,-1.358038286470938383e-01,1.291999249511173453e-01],
    [-3.457918473003702093e+04,4.921831466047273693e+02,-9.834684863968875561e+02,-1.933950745366980300e+03,9.519430168564423411e+02,1.644188149662826845e+03,6.159989434558540324e+02,-1.146438081051817790e+03,4.300301961829565300e+01,-1.098484272277003583e+03,-2.869803988767601481e+02,4.331621268296213429e+02,-1.204136880970684160e+03,-7.798705197362879744e+02,-1.003580288228186106e+02,1.095618238074443695e+01,-1.904338097836183010e+02,3.316298744205129196e+02,6.664050423221142694e+01,-5.188420264089985494e+02,-1.965764917144789763e+02,-2.359649071786983541e+02,-1.459752794048873348e+01,-2.728785432079552038e+02,8.054262419359010039e+01,5.725727943734064240e+01,-1.396660771430058787e+02,1.520815557565967140e+02,-3.424793439932857098e+01,1.025227325051507563e+02,-1.342244470939771475e+02,3.233404623861279248e+01,-1.237366588787069333e+02,8.426695998577113755e+01,-6.746051171267828295e+01,-2.963723371220996050e+00,2.207103411639482360e+01,2.841667112083134938e+01,-3.296053580071149014e+01,2.227458877955265493e+01,5.443194770661353488e+00,-7.612524298026551151e+01,-1.484575470594040070e+01,-8.437591707419159093e+01,4.590992175504099748e+01,-3.868611545774935223e+01,-6.828882167891983102e+01,-3.638931641270112038e+01,2.465395186643952186e-01,5.229087104501735972e+00,6.192715253245886231e+00,2.072317800504989815e+00,-5.682056580165564696e+00,-2.953923558491618806e+00,-1.096316200920427519e+01,9.157252374456437138e+00,-2.144981591462522630e+01,7.778684048500545067e+00,1.624929354377401047e+00,-1.853205002983467153e+01,-2.657139294688859010e+00,1.293176294653554415e+01,2.449692961884051101e+01,7.997491523346644815e-01,3.151085406375611520e+00,-3.688777700718325114e+00,-1.555283509806139497e+00,4.430686020214165410e-02,1.772441259201171515e-01,-7.660349121966001373e-01,-3.628104962753692098e-02,-1.507783066546542372e+00,-6.522980788410465136e-02,7.157886985898716858e+00,-8.703316568397976294e-01,5.917270262456273855e+00,5.525319189660971908e+00,7.001849298759792894e+00,1.907688217251870988e+00,-3.833219504806346656e+00,6.690097822879366163e-01,-9.255199847711335082e-01,-2.499072194116553312e-03,-1.333233160635174941e-01,-5.362816743445013579e-01,-1.807624669048669919e+00,1.003309917238873084e+00,-1.663098890405814601e+00,7.351661523852905111e-02,7.346100209071722009e-01,2.655519641688734112e+00,1.774830657851111493e+00,1.960813990144252061e+00,2.436639656137496779e+00,1.812361627994218960e+00,1.662788300145098264e+00,-8.253295860074749690e-01,-2.554653114227355415e-01,-2.526448937604208744e-01,1.579365784767126912e-01,-2.453874791212350692e-01,-3.898960580424213340e-01,1.438535747969039991e-01,-2.990663374370395311e-01,-4.138957126425476529e-01,2.533209593193126441e-01,1.380885436882731479e-02,7.612972876086732121e-01,2.713005755725801382e-01,7.813340844196743351e-01,7.487243827003657870e-01,1.157715643733731037e+00,5.855882124542528544e-01,5.088829173227632507e-01,5.133267032828268128e-01,-1.892869725060447594e-01,-3.263453363352845638e-01,-9.612611988358750470e-02,-8.604973979950392149e-02,1.304918027998485941e-01],
    [-3.527881551839232270e+04,8.554946089345228302e+02,-5.393641456068912703e+02,-1.772113861339549658e+03,1.550661716821044138e+03,1.739068615659644820e+03,3.941574300004937754e+02,-1.162737045679132052e+03,9.051648423551188216e+01,-9.854280715084214535e+02,-4.252368742332841975e+02,4.558695904888608652e+02,-1.095582066216004932e+03,-7.436472307275594176e+02,-2.750167875594269162e+02,3.040491650531497925e+01,-2.638351272363220801e+02,4.464705345551178084e+02,7.314654356580781780e+01,-5.026997720701175467e+02,-1.869953795832923902e+02,-2.998251504841940687e+02,1.003827891286615426e+01,-2.034756371372654939e+02,6.803823344571952703e+01,2.285590168253069621e+01,-1.343820831857474900e+02,1.873007385442642772e+02,-2.901284033846895838e+01,1.235924331500994242e+02,-1.202910086991768850e+02,7.989619410537500244e+01,-9.083887998477820247e+01,7.470546500820584868e+01,-1.109012383177611980e+02,-4.672889909439854605e+00,1.470788627564980544e+01,2.649543983211194131e+01,-2.921549379572955729e+01,2.411586842345525739e+01,2.294051203845322107e+01,-6.393114347549532539e+01,1.522743195711393493e+00,-7.471713166198760803e+01,4.335438882198207722e+01,-5.613654576699791932e+01,-7.478066784618054896e+01,-3.419819932423353492e+01,3.052830485961623985e+00,4.297959572486933055e+00,5.178162396373923393e+00,2.608321802681003554e+00,-4.725999817413919502e+00,9.311688396499052667e-01,-7.862138499454248475e+00,1.072803706793016332e+01,-1.914914533571806388e+01,7.793625125720253344e+00,-2.156497463463774356e+00,-2.083973245382807704e+01,-4.840948239707755896e+00,1.387723348789610078e+01,2.315033371419687924e+01,1.715027289339117633e+00,3.736515158501937606e+00,-3.690894736172642965e+00,-2.416725431739156438e+00,-5.299445041719234029e-01,6.723743735871806626e-01,-1.205687920309118866e+00,1.690419013790228908e-01,-7.117323487048041741e-01,3.878085215655246443e-01,6.811661679308690154e+00,-1.568409016970371272e+00,4.777704053264288930e+00,5.628066439153284861e+00,7.036659794438511639e+00,1.561061748252052794e+00,-4.870451218494599388e+00,9.507446277384545841e-01,-5.509329759500242174e-01,4.378440215012927017e-02,-4.084000781957553561e-01,-7.262397565879388228e-01,-1.947230622402362776e+00,8.262698983396431496e-01,-1.603944138862379187e+00,1.670276252720670485e-01,8.394582505691260410e-01,2.939013668713499783e+00,1.475904025911932260e+00,1.717599922639878374e+00,2.222012757189880006e+00,1.830969071649889868e+00,1.447095658906786708e+00,-1.386071576292629004e+00,-3.421097883721564425e-01,-2.660544314236056307e-01,1.843378058022626664e-01,-1.502897831353171842e-01,-3.797391432210771023e-01,9.329853475725367884e-02,-2.929135846630361306e-01,-5.091182579648477757e-01,1.745769273610239813e-01,2.783954609300014205e-02,7.618740479589846126e-01,2.995507132869773548e-01,8.875586202756159393e-01,6.893176188293667073e-01,1.100722406948483778e+00,4.380021195506265119e-01,4.700397270440531683e-01,4.808487219206074026e-01,-3.745710242681227764e-01,-3.082352094785674179e-01,-1.180577631551966988e-01,-4.374823923898073924e-02,1.261181208635325235e-01],
    [-3.572077970388552058e+04,9.790904392055879271e+02,-5.001769702544262373e+02,-1.531574041988711770e+03,2.023875986750944321e+03,1.734314666268335259e+03,1.513855592557014234e+02,-1.037663244976186434e+03,1.022677800655305589e+02,-8.718644402387606078e+02,-5.722586704961872783e+02,4.960070427095898253e+02,-8.712655137622290340e+02,-6.880722704287936722e+02,-4.423545493916556097e+02,3.272051578900185831e+01,-3.232239042802304994e+02,5.863729367084205251e+02,7.626941877081770826e+01,-4.739342437245912834e+02,-1.522663088621810346e+02,-3.884861390851449414e+02,1.334616266407421925e+01,-1.423679644787009124e+02,5.515463073587574883e+01,-8.697885219888775055e+00,-1.199928672440094886e+02,2.260305929975366439e+02,-3.262050188505661907e+01,1.430948797778229675e+02,-1.182734317028896101e+02,1.101588050885416123e+02,-5.620717416056616855e+01,5.402053804288691197e+01,-1.339165952508745363e+02,-5.800230286929778600e+00,6.826684466884935354e+00,2.362719649879524297e+01,-2.620490652226629180e+01,1.964986640060641321e+01,3.817065664794060353e+01,-5.499693024913592154e+01,1.296400640020057260e+01,-6.020381982275947053e+01,3.691210592233663590e+01,-6.571863370222884271e+01,-7.503196206857494133e+01,-3.199184310618190352e+01,6.229170786323703801e+00,2.118235722503188256e+00,3.061010497420764587e+00,2.177897931368743212e+00,-4.905643345071795558e+00,3.326468813510653710e+00,-4.999910374863138607e+00,1.117752952003944245e+01,-1.557811277075011702e+01,7.724493648710711646e+00,-4.082176437640509192e+00,-2.063163456686969965e+01,-6.742179150721632652e+00,1.347707983878832039e+01,2.058443499874109506e+01,2.670393259798165442e+00,3.843340324304753697e+00,-3.992252715548054720e+00,-3.645843910897042406e+00,-1.043111520691081040e+00,6.889839293350547011e-01,-1.624631705650526392e+00,2.667441739332652717e-01,4.295084118844084697e-01,1.020438052610817659e+00,6.728478172914970301e+00,-1.642235626269258342e+00,3.589025947519285609e+00,5.053566070140851352e+00,6.540518401289816097e+00,1.179573110708694861e+00,-5.434161773433041631e+00,1.227435820887534446e+00,-1.995146627805426953e-01,5.428645364220812536e-02,-7.836614294150339166e-01,-8.289084019161834238e-01,-2.149343705112628289e+00,6.570762156225942174e-01,-1.527668676165755191e+00,2.547606231220556072e-01,1.050955179552693686e+00,3.183870147570728726e+00,1.236371913990063520e+00,1.474057461438241567e+00,1.801111947626106380e+00,1.686117919361841189e+00,1.210996808351340270e+00,-1.765721674228360349e+00,-3.743195774734678349e-01,-3.035949395983978394e-01,2.126353425885626480e-01,-2.230578871836067650e-02,-3.415559837781452224e-01,2.414532352243280167e-02,-2.708180339099831024e-01,-5.963201967003147752e-01,8.194013283857243257e-02,3.492764089642831637e-02,7.181754647376666911e-01,3.380743528638736062e-01,9.520350783387945270e-01,6.273788484912440344e-01,1.024580627337817296e+00,2.515957342877379044e-01,4.141248871768322681e-01,4.193938260888119829e-01,-5.081212822182739064e-01,-2.499704953168962462e-01,-1.360250195225158887e-01,-1.161939150885201409e-02,1.179086054036165981e-01],
    [-3.583215846801818407e+04,7.520116661338983022e+02,-3.301188663878114085e+02,-1.311141832809747029e+03,2.366947350136565547e+03,1.839734892716819331e+03,-3.765194749445308275e+01,-9.612096263085513783e+02,5.575407977651126856e+01,-7.803072468177748533e+02,-7.304155680202430858e+02,5.931052269815102136e+02,-6.711801745226254070e+02,-6.066830177741836678e+02,-5.001480686399706315e+02,2.047290895286749901e+01,-3.474388258286980431e+02,6.882928418981329060e+02,7.584622138315447160e+01,-4.386994244100214928e+02,-9.397973326485175960e+01,-4.508126069652598176e+02,-5.926881264455003517e+00,-9.642618409867532137e+01,4.503139681944393402e+01,-3.441947955873328624e+01,-1.082642002049851584e+02,2.541905755127849034e+02,-2.889622547215852677e+01,1.561690274254895598e+02,-1.223342139984623742e+02,1.189287562905728919e+02,-3.044870576535104334e+01,2.438907139387218592e+01,-1.411216020557686193e+02,-6.768812411815265939e+00,-1.448302392681947381e+00,2.130923109542542448e+01,-2.763256172731278681e+01,1.608425450431419179e+01,4.900772649987442975e+01,-5.095513727601253606e+01,1.998142107445181637e+01,-4.488938838171508650e+01,3.027010750310491716e+01,-6.994818827146193030e+01,-7.144114162251369748e+01,-3.011029002616023220e+01,9.029749093682179151e+00,-9.968553813754552628e-01,1.532944078020949563e+00,7.168324269688804984e-01,-5.343551703382869889e+00,4.371948472405087216e+00,-2.877436833719053677e+00,1.155840031944859447e+01,-1.179793547388102937e+01,8.312586440475310923e+00,-5.154166921487225217e+00,-1.948741184751051136e+01,-8.098295067732561137e+00,1.216490700049732787e+01,1.695890186565888413e+01,3.613352908053236945e+00,3.575132929417840000e+00,-4.102967162178858374e+00,-4.845814731541293163e+00,-1.537486001285876647e+00,3.428842994018497237e-01,-2.047157505588965698e+00,5.637664478665422862e-01,1.447750391919591983e+00,1.753109389068589152e+00,6.542161563815175995e+00,-1.434804965983719649e+00,2.368938084638315011e+00,4.161867244721137560e+00,5.440301779187931785e+00,9.139489935884409499e-01,-5.601709520784529772e+00,1.501072789760909298e+00,1.105302785357560880e-01,3.863837015101244388e-02,-1.099187495714308405e+00,-9.330798725859115184e-01,-2.361088543220338565e+00,5.015664197769152954e-01,-1.414696992244177887e+00,2.385391967557176640e-01,1.281793563023548632e+00,3.289183559618668262e+00,1.032782696623420149e+00,1.200644017165495736e+00,1.325170430602770066e+00,1.360485782106380270e+00,1.063253695467799131e+00,-1.938129511551712980e+00,-3.858310684837515936e-01,-3.291140738575665248e-01,2.364641791506822133e-01,1.184769949637564934e-01,-3.123050135742068689e-01,-3.840624463271143790e-02,-2.581076575828400443e-01,-6.725853695909578267e-01,-9.692980287479424292e-03,2.158020804406161897e-02,6.311278066406025289e-01,3.580899851833324599e-01,9.677725844573200620e-01,5.710634602579338637e-01,9.221266952083562174e-01,8.110800463995833376e-02,3.440694952153823261e-01,3.738735844801291952e-01,-5.831904942912414791e-01,-1.868951021820579039e-01,-1.432242339843065315e-01,1.351217106940694190e-02,1.023484755527344914e-01],
    [-3.564756782538929110e+04,4.097206994791758916e+02,-7.502511912191945953e+01,-1.197152714934443338e+03,2.586102425069286255e+03,1.997440698634537057e+03,-2.436436381697400577e+02,-1.125998543222344779e+03,-2.559857940141943544e+01,-7.443728660509714246e+02,-8.098132507481934681e+02,7.180238518440506823e+02,-5.574932269164546597e+02,-4.724906498132276624e+02,-4.767271822172775728e+02,8.602912237898852510e+00,-3.431206395688113275e+02,7.459423247359245579e+02,7.404350375179987509e+01,-3.830156801528236201e+02,-2.366663931439600432e+01,-4.747291860249731030e+02,-2.892732078712421284e+01,-7.066997024443064390e+01,3.897465630208235154e+01,-5.524866020332393646e+01,-9.923359298761155856e+01,2.597916973421032480e+02,-8.844802267614889857e+00,1.612559717218446167e+02,-1.298625756999330179e+02,1.132049358946081838e+02,-2.028694070960445828e+01,-1.292293070237245978e+01,-1.450387754332917893e+02,-8.211116288595722068e+00,-8.965292319456088066e+00,1.984516283802747694e+01,-3.471541828017218023e+01,1.746801969038238056e+01,5.458807160642614065e+01,-4.941696846647475638e+01,2.270756700060996280e+01,-3.206671003465752534e+01,2.348882365308163500e+01,-7.231230725456069308e+01,-6.460576715903462741e+01,-2.921486896756429275e+01,1.071453808804048435e+01,-4.134316144565051587e+00,1.203702776472442393e+00,-1.467041993011914069e+00,-5.360069419028141269e+00,4.164837548714974247e+00,-8.006313542499168268e-01,1.179996651466556479e+01,-7.964537024273067090e+00,8.710797892293344447e+00,-6.207693695525335009e+00,-1.772184041291469825e+01,-9.751754412473848888e+00,1.048630601527628237e+01,1.236375032130420593e+01,4.405375518191794626e+00,3.145129376152944189e+00,-3.843779292657093283e+00,-5.639280589440235580e+00,-1.964993244569033015e+00,-2.929289316157412948e-01,-2.216246230811336204e+00,1.037662901233993296e+00,2.229094054201743447e+00,2.362276809580475589e+00,6.078876618210668603e+00,-9.839142420387112509e-01,9.551865317268500855e-01,3.414180772439141087e+00,3.743121605338900704e+00,9.335718944602379166e-01,-5.420462356171790397e+00,1.749477004223419341e+00,3.591131308976230896e-01,1.429006859494652212e-02,-1.237834597899849509e+00,-1.067808832981956391e+00,-2.510226026262448507e+00,3.740968609267292244e-01,-1.254697533606512261e+00,1.502968822446749397e-01,1.450675268948477648e+00,3.251858668875739600e+00,8.799590349736509109e-01,8.592351976936574154e-01,9.577179320768751669e-01,8.460634790061218879e-01,1.036208975076380101e+00,-1.922340942985013346e+00,-3.799353435627398357e-01,-3.250317145275156139e-01,2.576905981530515088e-01,2.435294512572649117e-01,-2.989885672936697381e-01,-7.040999397017300154e-02,-2.586188077128201424e-01,-7.222323542454669454e-01,-1.017331756191540704e-01,-7.270857330404317115e-03,5.204212675327964943e-01,3.514753128070696175e-01,9.486634721800429881e-01,5.103131282575059657e-01,7.994857290821473228e-01,-3.512549218305262982e-02,2.492348455016085984e-01,3.658391842399251193e-01,-6.116875149376074239e-01,-1.184863781319063225e-01,-1.357769115284460093e-01,2.566562475761581530e-02,7.896768199847242764e-02],
    [-3.525025864049226948e+04,1.301190452828325306e+02,2.885745792246065093e+02,-1.199974569848934607e+03,2.677860343327065948e+03,2.135654776532921005e+03,-3.366172287616652739e+02,-1.280578628754765987e+03,-1.102488039718885204e+02,-7.872886302527167572e+02,-7.505885230824335395e+02,8.583715974445638039e+02,-4.368075465375808335e+02,-2.747075695715373058e+02,-4.193719970842726639e+02,1.006121754847852046e+00,-3.212721528411015015e+02,7.955861354416319955e+02,7.156902355751313394e+01,-2.916881477489385475e+02,4.275160114689279567e+01,-4.610724508121028862e+02,-6.029762152188219204e+01,-8.123913341304657365e+01,3.561108708851747906e+01,-7.095098425834704869e+01,-8.057615584742322312e+01,2.440757234715493951e+02,2.171531129423588879e+01,1.536543870957364959e+02,-1.363982428767246802e+02,9.529535870035134337e+01,-2.906284522111956647e+01,-5.994869414304787369e+01,-1.435876446354912446e+02,-1.025110733040492050e+01,-1.349975183555227609e+01,1.928509516882789754e+01,-4.422101827422613241e+01,2.210943538201990322e+01,5.399549143644637184e+01,-4.688613016533140865e+01,1.984939968816355460e+01,-2.304175704717800244e+01,1.365302458073567138e+01,-7.227139309309731630e+01,-5.354595767203019108e+01,-2.934621528616276720e+01,1.107379507014967857e+01,-6.658189500394875893e+00,1.200453095827672012e+00,-3.515157100051830241e+00,-4.826319210079526023e+00,2.804618240968452803e+00,1.782694742406817801e+00,1.128403036918590985e+01,-3.673772456966898581e+00,7.546587113434183536e+00,-6.928800766486448381e+00,-1.457152168118242130e+01,-1.243307280203477916e+01,8.865039540702989385e+00,6.597394116169843059e+00,4.756799805426641825e+00,2.564465120524441311e+00,-3.536274279203601711e+00,-5.997695864261291199e+00,-2.093733040909954823e+00,-9.942208047920961800e-01,-2.022260166139713267e+00,1.496738641498025046e+00,2.990197202412218758e+00,2.807209648131598012e+00,5.462708603024964304e+00,-2.049824077159682623e-01,-7.365058120531895458e-01,3.044355654102536946e+00,1.490441825976881018e+00,1.138307416386184379e+00,-4.987394649828241100e+00,1.892372201417562350e+00,4.726948205625616239e-01,2.341054008651418956e-03,-1.235987929506935812e+00,-1.159740067886963599e+00,-2.506359956975133585e+00,3.280040492380509320e-01,-1.023935871854244617e+00,9.527563939202345067e-02,1.603017710571508214e+00,3.130611836986223917e+00,7.776255882065032932e-01,4.313236432212030347e-01,7.785100049704720693e-01,1.962423453896021130e-01,1.048546617456306951e+00,-1.748774415530769621e+00,-3.580104353220917024e-01,-2.995534303588024416e-01,2.872247714144676722e-01,3.225777189726103944e-01,-2.769571842020237540e-01,-7.526180626019525477e-02,-2.495259448533603541e-01,-7.257174716109106027e-01,-1.821434832219445688e-01,-1.514194696972776324e-02,4.128748324480536191e-01,3.460627546881466787e-01,9.169070236101215521e-01,4.456073400435409670e-01,6.692056277185285396e-01,-8.953247328490657186e-02,1.239687165177104783e-01,3.741082562020863755e-01,-5.892439909913744778e-01,-4.356874667158669445e-02,-1.079909769286487159e-01,2.376479603143697231e-02,6.136726990886745559e-02],
    [-3.448850372431760479e+04,-4.093377161835572338e+02,4.868329173101963079e+02,-1.306638456158131476e+03,2.650486627759878047e+03,2.263897541587827618e+03,-3.616745750054706150e+02,-1.441634767747382284e+03,-1.785635359401422306e+02,-8.461893891517622706e+02,-5.930728660834486163e+02,9.990668425932774426e+02,-3.674211455213610975e+02,-2.818383830020784586e+01,-3.575577229929513123e+02,1.560894248824474140e+01,-2.648518166146190538e+02,8.405159407332519095e+02,8.401126356886666713e+01,-2.136608874182900024e+02,1.020804374059762551e+02,-4.401408786863951264e+02,-1.254567683967720910e+02,-1.274190887783794324e+02,3.890972250467296334e+01,-7.432430511622024483e+01,-5.140942704669984664e+01,2.198788311196193774e+02,4.823239910092525662e+01,1.291782235301747050e+02,-1.540156020473070839e+02,5.419502696429987054e+01,-5.538288603789766995e+01,-1.098544731365145708e+02,-1.353947424685465535e+02,-1.214825404033159018e+01,-1.340940284591783715e+01,1.949565281538989581e+01,-5.086222917530866994e+01,2.674097044618326890e+01,4.758368852453889986e+01,-4.717601151075559329e+01,6.710293341285447966e+00,-2.034022224253291711e+01,1.053123859582358435e+00,-7.191636180450906579e+01,-3.959914405253059755e+01,-2.946132694097769189e+01,1.008445112419521728e+01,-8.285645907492863671e+00,1.239159774379584800e+00,-4.543791766816593025e+00,-3.514481566518441014e+00,7.366889517674812815e-01,3.418526308494360677e+00,9.247634175116029809e+00,-2.343644212737865384e-01,4.242094100897509712e+00,-7.584159826719183428e+00,-9.834223157774449220e+00,-1.596766828650276793e+01,6.960908415748266798e+00,-1.122499588462985420e-01,4.335594378407046534e+00,1.761377066885601916e+00,-3.224931438179119425e+00,-6.034612098365029098e+00,-1.689475237980617273e+00,-1.400002759846922240e+00,-1.688811289782727210e+00,1.831877659831877114e+00,3.399385236546698330e+00,3.058655304293702581e+00,4.579735653811725982e+00,8.375074077334387912e-01,-2.573662796755676663e+00,2.841642912652739383e+00,-1.203440879394931828e+00,1.380734648750388871e+00,-4.599494360357414990e+00,1.844063615230103093e+00,3.806257794950640427e-01,4.600539092651134698e-02,-1.159703380568455344e+00,-1.118205451895262881e+00,-2.298709067257508565e+00,4.107322476938424227e-01,-6.489196733760513869e-01,3.740416134870130915e-02,1.771864441804981816e+00,2.864148258726403995e+00,7.223897706020164788e-01,-1.160426060486862143e-01,7.233007705664691311e-01,-4.946172979939720271e-01,1.049651806672232235e+00,-1.498467017059755158e+00,-2.984415353818868910e-01,-2.960518151590273983e-01,3.249659185342758660e-01,3.336503137777739880e-01,-2.412781546032551905e-01,-7.212269524269593335e-02,-2.070484596917242792e-01,-6.735028607544978341e-01,-2.105687653136003590e-01,3.659480592533976423e-02,3.171298659923517671e-01,3.588082238492030784e-01,8.592624760880298584e-01,4.026714063823579881e-01,5.066166320482381469e-01,-1.108033493642665707e-01,-4.964544045162451458e-02,3.818875274611574500e-01,-5.204247433978137494e-01,1.274621614473352843e-02,-5.681171896428780649e-02,5.019923982189238715e-03,5.617652530821254375e-02],
    [-3.364174517997656221e+04,-9.379043733819750059e+02,7.000966339389240147e+02,-1.520464180844480097e+03,2.617193073260616984e+03,2.380893484445850845e+03,-5.148181087233599555e+02,-1.640154142392428412e+03,-2.296770620016151838e+02,-8.664784124579244917e+02,-4.709220882795299303e+02,1.106039926357685545e+03,-3.785699393435800744e+02,1.428653987848202576e+02,-3.012204716852479578e+02,5.349381230016507516e+01,-1.840680261496331127e+02,8.356735412329989003e+02,1.208747328098158249e+02,-2.042804831177259643e+02,1.177800065226162900e+02,-4.305187519210132905e+02,-2.182440281295516229e+02,-1.764962162917069861e+02,4.755032940980569833e+01,-6.720640728369190242e+01,-2.518948823074697785e+01,1.954659535545618780e+02,5.495539965403749250e+01,8.168714615913953025e+01,-1.848713489035288546e+02,-5.233895788385185099e+00,-8.906936156636453461e+01,-1.382169078291059066e+02,-1.171669091527304545e+02,-1.211805483788862858e+01,-1.071272288135390660e+01,1.947818680099721433e+01,-4.992936309194759303e+01,2.710211359314266844e+01,3.866122971276846698e+01,-5.261598074101414824e+01,-1.730319448893259349e+01,-2.477811092243232949e+01,-9.182017020676443764e+00,-7.076226235830733913e+01,-2.556371174006066127e+01,-2.456829693236022294e+01,8.500210876722027464e+00,-8.724586601127041874e+00,1.825297929035686995e+00,-4.108296844826217153e+00,-1.836231257493396107e+00,-6.535562941954765614e-01,2.277270424494741263e+00,5.819657531131248618e+00,6.116022947208610283e-01,-5.058851300953756125e-01,-7.531908472614186500e+00,-4.398902538740938617e+00,-1.867564870214465600e+01,3.916502874407806534e+00,-6.561735359332172557e+00,3.201786051726446480e+00,9.884096782565591210e-01,-2.668932640606507256e+00,-5.882917208403750209e+00,-8.142059541188023664e-01,-1.119545058360046808e+00,-1.548943229268417099e+00,1.953625536647604743e+00,2.909258662883940083e+00,3.054047425386754000e+00,3.422443522082561973e+00,1.597087477865475336e+00,-3.753400670208913326e+00,2.518556841712374261e+00,-3.698038822950256765e+00,1.472812659641355104e+00,-4.662506057547730620e+00,1.604590666394779097e+00,1.450217843339365875e-01,1.765328340910778948e-01,-1.050977822376335524e+00,-9.042561076463396796e-01,-1.921857059133952550e+00,5.581624782819514241e-01,-1.545211354970379147e-01,-8.910003308555078383e-02,1.893548677094370358e+00,2.361945142542466680e+00,6.016982359617046860e-01,-6.482456155780589313e-01,6.609735947765237318e-01,-9.376074297809318114e-01,9.501213198478630773e-01,-1.267851288959390921e+00,-1.793883828594706464e-01,-3.824600652006734380e-01,3.510979611586849680e-01,2.841194906184145164e-01,-2.046465896830405029e-01,-7.141138365597746174e-02,-1.228667651308866515e-01,-5.826384425974031611e-01,-1.719071474741453998e-01,1.342614155667699039e-01,2.387225417772191882e-01,3.702340171169340444e-01,7.447016285776567601e-01,3.921036456229984868e-01,3.036442010716178252e-01,-1.541764502610357690e-01,-2.361803335918457036e-01,3.660291047519876884e-01,-3.988495108926115584e-01,7.938798478932850358e-03,-1.967946050754018107e-05,-2.969256752647788516e-02,6.696784518431901645e-02],
    [-3.302992040251926664e+04,-1.506911861574528530e+03,1.125910577252394887e+03,-1.697149171164273412e+03,2.668878249820353176e+03,2.410749724347131632e+03,-9.658693319239439461e+02,-1.563355347526295191e+03,-2.419016895446748663e+02,-7.897617917019028937e+02,-4.910940177252833223e+02,1.197154902473759648e+03,-3.585912339062878686e+02,1.817138472142846695e+02,-2.165510891344279116e+02,8.614475781717902692e+01,-6.804598947206024206e+01,7.429338814916779938e+02,2.141504772900403282e+02,-2.720124380737918273e+02,9.940424028471032614e+01,-4.205223975728819710e+02,-2.754853439419378560e+02,-1.951374082519517685e+02,4.770974243252209845e+01,-5.159800330379561473e+01,-1.157444521883929234e+01,1.866306811991954646e+02,3.484363295581545117e+01,2.389192060591846456e+01,-2.141448372061472014e+02,-5.058603606447433521e+01,-1.173323197139235674e+02,-1.159195320240922342e+02,-7.469345278690323653e+01,-1.025820795562901111e+01,-1.077185778338647637e+01,1.793928117414072432e+01,-3.562545788562339766e+01,1.998074967585675665e+01,3.447482229890241712e+01,-6.114885422779906321e+01,-4.324849436324328167e+01,-3.322229269019182141e+01,-1.020534582421456982e+01,-6.190464641451315231e+01,-1.010559749881233493e+01,-8.172416121899692243e+00,7.365265119466613442e+00,-9.136299670692601183e+00,3.105875969058800479e+00,-2.572226250929570579e+00,-9.549636514731492110e-01,7.737080720590139293e-01,-2.015833451799712961e+00,3.431905628002065889e+00,-1.678126022558592778e+00,-4.455071736254594406e+00,-3.997316277200952062e+00,2.065093836996731547e+00,-1.807065703768043718e+01,-9.594683000443429144e-01,-1.113683998404630415e+01,1.902441283458255139e+00,2.466921131026048042e-01,-1.827442952329963344e+00,-5.983690203159450327e+00,2.749013990526084639e-01,1.331104052308509228e-02,-1.682525524375557691e+00,2.207561527479049879e+00,1.408179234763979215e+00,3.153457291776724958e+00,2.425621197089220082e+00,1.873952938105698962e+00,-3.044253535967516910e+00,2.140042927221798674e+00,-5.221368980101804169e+00,1.227765956031939165e+00,-5.474732760865472336e+00,1.307287551495645017e+00,-1.177202444520083213e-01,3.677216759975254767e-01,-1.042263359792949373e+00,-5.303919551083873252e-01,-1.524992583447280614e+00,6.602512450379559583e-01,4.019393707414644634e-01,-2.374647814871277407e-01,2.027027805471391275e+00,1.599179007905667360e+00,3.646153874920419202e-01,-8.789939670465348742e-01,6.165400026220916319e-01,-7.896202036430763904e-01,6.818365211195971387e-01,-1.049086619376017770e+00,7.398112713558571696e-02,-6.391242088361115403e-01,3.582671127918286569e-01,2.307894345327470287e-01,-1.737493570066164783e-01,-9.300937345707499526e-02,-2.080374678472333289e-03,-5.063271645364892937e-01,-8.851919030453053727e-02,2.294241616145552554e-01,1.880717109821561650e-01,3.866958651004225311e-01,5.526991561594125635e-01,4.262293994802048291e-01,9.649498555767813124e-02,-2.251832890879610916e-01,-3.529408364841187251e-01,3.171325750652768116e-01,-1.744967407296253437e-01,-7.096149132265797133e-02,3.033234967752220304e-02,-6.370854785124575870e-02,1.057990351425206060e-01],
    [-3.273115736858586024e+04,-2.141309060654944915e+03,1.306933928021189331e+03,-1.735960434581195841e+03,2.759297451412174723e+03,2.271051795492218844e+03,-1.388307263387528337e+03,-1.371968606397904296e+03,-1.488873874013048351e+02,-7.265474141215379404e+02,-6.246272200285206964e+02,1.290726165505943982e+03,-3.097240241854831879e+02,1.930709795902136818e+02,-1.000956632020014325e+02,1.304383946346259222e+02,5.692690363973542844e+01,5.922363896641129486e+02,3.246907641236927020e+02,-3.974603318883386009e+02,1.059318675817880830e+02,-3.901890143224392205e+02,-2.220320966855435927e+02,-1.638387417098075787e+02,4.441376490133096411e+01,-2.360482392472977864e+01,-5.999008600176921391e+00,1.798753867958261594e+02,3.076017811049081896e+00,-3.983801897193118435e+01,-2.138931733664859109e+02,-5.097848205077647066e+01,-1.279298456716811927e+02,-2.435119225013430366e+01,-1.284610160573991600e+01,-3.104276806602705996e+00,-1.204201370516219960e+01,1.428353864295710984e+01,-1.126024425360119174e+01,1.009326815436640068e+01,3.021902030377452775e+01,-6.685538530446244465e+01,-6.310713263068075918e+01,-3.910700135120080745e+01,3.257713000954999272e-01,-4.553973590003397476e+01,9.522255058782562287e+00,1.956660989811474138e+01,7.140268048461819284e+00,-8.206829892167174734e+00,4.192077259067427342e+00,-4.137594654270760341e-01,-1.147055488903396148e+00,3.610110154333234789e+00,-7.896667406373255815e+00,2.309720857808561956e+00,-6.680714957599573900e+00,-6.236657037431775130e+00,4.048592859349389173e+00,9.267481091656136982e+00,-1.455632327481082200e+01,-7.853651190100397805e+00,-1.265837889895957780e+01,6.132686395479699515e-01,4.369432030592085292e-02,-1.010885294698397718e+00,-5.912523231882227392e+00,1.140964071273774749e+00,1.414188565119531837e+00,-1.985194367429386819e+00,2.246166607750980759e+00,-7.693042418535939175e-01,3.139816803903813014e+00,1.753166112145866151e+00,1.531701162403251271e+00,-3.689311254227689019e-01,2.090918521693562848e+00,-5.585680424397427402e+00,5.295648553676139958e-01,-7.282548886831133217e+00,9.408540751429605997e-01,-2.969293616345154430e-01,5.220747742947364767e-01,-9.333932885341134078e-01,-1.308739209891087441e-01,-1.153411519471294833e+00,5.949595664173727982e-01,7.752843047657669295e-01,-3.215123194995866962e-01,2.041931260174282947e+00,6.297553716444622696e-01,-8.327071729893449625e-02,-7.338379125027082450e-01,7.452489368962711414e-01,-8.041793694961756056e-02,2.763913007576433989e-01,-8.687725243779060857e-01,5.233530665583879804e-01,-1.113600338280056334e+00,3.115640786314062827e-01,1.761732717457144548e-01,-1.442619499255121396e-01,-8.915893610302079442e-02,1.142128732339127706e-01,-4.000209837941252067e-01,3.163609285719648848e-04,2.687246476283535745e-01,1.635833612045563823e-01,3.674589910262572867e-01,3.018972584219690170e-01,4.555288335101961295e-01,-8.293931872709513209e-02,-2.801449987157768051e-01,-3.796843351441037129e-01,2.815455127587845885e-01,1.522606497909399503e-01,-2.020214159974089152e-01,-2.445163122129558053e-02,-6.969578429097916805e-02,1.735391471355287041e-01],
    [-3.291195096107105928e+04,-2.427100156017436348e+03,1.395997642870604523e+03,-1.573248973185032355e+03,2.876446425483153689e+03,2.165093754065047506e+03,-1.605925062611509020e+03,-1.261942157606647925e+03,9.146526699417854900e+01,-6.983563611885886075e+02,-7.476462119926429750e+02,1.292702803982979049e+03,-2.165976463138092925e+02,1.593761184694808435e+02,-3.652369434243408364e+01,1.975652168782450531e+02,1.740735689770689874e+02,4.180735620591369752e+02,3.954713925928634808e+02,-5.455217823107352615e+02,1.501791965707780037e+02,-3.249220004080711988e+02,-6.094998396200247726e+01,-8.951824968471889576e+01,4.657707250931112952e+01,2.138782392209716932e+01,-7.745532094186145855e+00,1.629652996898951471e+02,-1.865182968080854664e+01,-1.207890112180561033e+02,-1.526439020147890631e+02,-1.204747009474945330e+01,-1.103808453410733534e+02,1.282822039481279432e+02,4.178881004757893436e+01,1.139607365745441214e+01,-1.278433681067824423e+01,5.889845430771423196e+00,1.895509633119530690e+01,3.204765766383196546e+00,1.499311473212009282e+01,-6.165878870808221279e+01,-7.567839858773525918e+01,-3.117101827735241670e+01,1.424897920232402981e+01,-2.785942888223119596e+01,3.127520378585972338e+01,5.119647246071740199e+01,7.666917934594981610e+00,-5.064750257199942318e+00,3.700077627622595955e+00,1.839899283124713181e+00,-2.658545057261084477e+00,6.303558228296509469e+00,-1.224104652555253026e+01,5.302292942849399227e-01,-1.241069928187778260e+01,-5.474677458649622075e+00,1.593319085408831626e+01,1.345933877294200620e+01,-1.002999369867384516e+01,-1.696185822733314552e+01,-8.902543396715115520e+00,-3.629757223728850013e-01,6.179041005820290478e-01,-4.608271446061317222e-01,-4.988916444090142122e+00,1.146931827304634499e+00,2.649455949864989446e+00,-2.244771658854388452e+00,1.680222288589265034e+00,-2.596769572641350887e+00,2.294786707208453791e+00,1.397795097126618424e+00,1.629347174608132831e-01,3.243796680456610737e+00,2.032217880990746295e+00,-4.542282066767204363e+00,-1.069294184777824341e+00,-9.686988768213913303e+00,5.318160940282572469e-01,-3.062971634418050204e-01,5.934623915184168430e-01,-5.703169867653048453e-01,1.114770670631210076e-01,-7.119986033737844000e-01,2.338641024911300437e-01,7.684062141865279916e-01,-2.151515577282400449e-01,1.662215971437008388e+00,-2.792695065323268500e-01,-7.906009198713392916e-01,-2.977798819684954745e-01,9.742653369392805240e-01,7.485055942243065141e-01,-3.344149266055456149e-01,-7.470915772417703327e-01,1.040235847001959035e+00,-1.682665734732500695e+00,1.999190727438573401e-01,1.191401527782810360e-01,-9.537146775758979789e-02,-3.948356422390700282e-02,1.712161898071000721e-01,-2.124781617311067017e-01,4.660202896020612662e-02,2.297284914540831668e-01,1.461651602402343486e-01,2.553953012539855738e-01,5.234234982902395000e-02,3.920725340903759570e-01,-1.811309232807559733e-01,-2.848646168608052753e-01,-3.217157477665047449e-01,2.526135824927766005e-01,4.896553215006743121e-01,-3.547727409476221228e-01,-2.295391006438943782e-01,-1.939873876448834633e-02,2.382516859306024748e-01],
    [-3.376430653505986265e+04,-2.025612146988517225e+03,1.736447867100947406e+03,-9.953742817857646514e+02,2.697987290098475114e+03,2.111841432560424437e+03,-1.688452335039712125e+03,-1.566319411294908832e+03,4.802419863706538194e+02,-6.697225567856228281e+02,-7.977673730751257608e+02,1.071715427110259952e+03,-1.426106215824170818e+02,2.502706047297476744e+01,-8.243335157303300775e+01,2.671739904988565399e+02,2.845719635236415570e+02,2.218402580317030584e+02,3.993885591303575211e+02,-6.954981781133701588e+02,2.304807255033865943e+02,-2.406437876974632104e+02,1.466378386638065194e+02,-2.571582899518685750e+01,5.950003788717946662e+01,8.537713475479955605e+01,-1.558838114242898421e+01,1.453072814224116485e+02,-2.159207107881247367e+01,-2.121277314190430161e+02,-3.475332102492436093e+01,3.905854535586183118e+01,-6.504736124458692359e+01,2.883366991559300914e+02,5.389134465610123925e+01,3.079802736630975701e+01,-1.041490096044969604e+01,-5.708653122576139438e+00,4.871685592552881872e+01,2.877269162450573958e+00,-2.112154018984696435e+01,-4.838650833404201990e+01,-7.680116826016005405e+01,2.483836028194016610e+00,1.327752506080286921e+01,-1.403335672957046221e+01,4.815019316229213331e+01,7.111434979399095369e+01,8.261050857718331031e+00,-6.479930177628062671e-02,1.524040893874133662e+00,1.843575616848099674e+00,-4.945001641316771668e+00,8.057174844662686297e+00,-1.181441393097527381e+01,-3.993680450469957233e+00,-1.663293357355655999e+01,3.946934359432592299e-01,2.860155712206447021e+01,8.430574934339270854e+00,-5.567633217763315656e+00,-2.666011471416824108e+01,4.517520480106980152e+00,-4.111189600527569432e-01,1.630123385291559979e+00,-9.843611491600184893e-02,-2.901262710835526004e+00,1.751476489620380772e-01,3.241371013151676195e+00,-2.006166367766243130e+00,5.193811431542476598e-01,-2.761423448000458691e+00,5.364905618907466200e-01,1.074890210697386328e+00,-1.845775340949482146e+00,5.679462381136795912e+00,9.407907498509986421e-01,-1.117550914253129912e+00,-4.059457254880457278e+00,-1.059565325372248168e+01,8.754162052156420903e-02,-5.699376276336939190e-02,5.514392633684181977e-01,-1.107314056258275337e-02,1.709146286279605853e-01,-1.179739536395215255e-01,-2.468410210971105356e-01,2.246501064972420691e-01,9.355388982579097845e-02,6.886350281657049877e-01,-6.221438155458165475e-01,-1.351745706335472752e+00,1.905898399652892761e-01,1.035662240163956138e+00,8.037132255840998551e-01,-1.179399256201451696e+00,-5.494946427182266779e-01,1.182392861704203435e+00,-1.901884916592302410e+00,2.632954635515055014e-02,6.433274875081046451e-02,-3.157492956456079553e-02,3.736607996262676645e-02,1.332119777481490241e-01,2.528757332003668881e-02,6.702690491885944513e-02,1.110995263515931059e-01,1.047375179905628007e-01,5.486195805577019288e-03,-1.047320682417904325e-01,1.692393258146068780e-01,-1.081414676822605447e-01,-1.456173695930317868e-01,-1.685385676098820062e-01,1.512443544159761399e-01,6.124845023508133091e-01,-4.348660504053133424e-01,-6.173756467378015422e-01,1.354589856971779305e-01,2.314953979957607433e-01],
    [-3.485877409542070382e+04,-3.265807984034831406e+03,2.823854545792494719e+03,-6.585731215938801597e+01,1.885646941101874518e+03,1.876109711456226250e+03,-2.128952667544648648e+03,-2.150744756117899669e+03,7.898458553607142676e+02,-5.280434031067474052e+02,-7.425169426965031789e+02,6.631453141336988892e+02,-1.925334434182375674e+02,-1.530076954549229242e+02,-1.007096109616611130e+02,3.082717822821032883e+02,4.346961218858850202e+02,1.138837538864915757e+02,3.561751552571290063e+02,-8.052037920094467154e+02,2.717216642318189201e+02,-2.428877558262402658e+02,1.948032438084293858e+02,-1.144973452356044987e+02,8.877005391199624285e+01,1.649249027399263241e+02,-2.561552702990988095e+01,1.933993873750320631e+02,-2.311231418043666608e+01,-2.659716858314590695e+02,5.160659935176728652e+01,4.713714708676111798e+01,-3.389222689401514543e+01,3.319349364130279127e+02,-3.357991330288237464e+01,4.196931533211848375e+01,1.190118347919048691e+00,-1.158905672988690760e+01,6.128929937199687572e+01,1.333365293100886895e+01,-8.267847236822005641e+01,-5.803375773395787007e+01,-5.616530112057983359e+01,5.788361364845186330e+01,-2.704398954787903264e+01,-8.194790523418719275e+00,4.477167466323442113e+01,5.843013924604984055e+01,6.386670877689661019e+00,4.116419972125473059e+00,-1.033166748163659721e+00,-4.689542506760984608e+00,-4.465701160752650445e+00,6.957646790559301131e+00,-3.387244521406591602e+00,-1.505006694982459869e+01,-2.025364642775189594e+01,1.978392459449386465e+01,3.194913509910985283e+01,-1.239698653822131291e+01,2.516018813500109363e-03,-2.978118888493357019e+01,3.285138084021380678e+01,8.021950808551590040e-01,2.009429752516203926e+00,1.470257492164092905e-01,-1.636289173728156521e-01,-7.341898107241919824e-01,2.409614149015360418e+00,-5.188364607614155410e-01,-8.202005146582611594e-01,1.848663374488821454e-01,-1.296252001087007666e-01,-2.361262646144784982e-01,-1.531390624461620220e+00,3.611478463693629237e+00,-1.947082350461804889e+00,6.747604737704230971e+00,-7.860913989338134122e+00,-5.312820428148403273e+00,-5.473065840068902510e-01,4.926538789561035747e-01,2.485806139578372875e-01,4.904596398306335647e-01,1.715041757011556978e-01,7.006418479305278613e-01,1.830440247383648411e-01,-1.110617560318426289e+00,4.554953957021369293e-01,-6.807644070193089592e-01,3.271078686394413571e-01,-2.311507457746816430e-01,2.106096380679963742e-01,6.624643629425480684e-01,-1.302766907972613186e+00,-1.890228406218314117e+00,1.187437045808675540e-01,9.494157954859061554e-02,-7.307084465643937099e-01,-1.946650607799187693e-01,-4.292286103811934067e-02,-4.882635091332528099e-02,9.625660748191532112e-02,-4.782179126003392733e-02,2.046157367736912702e-01,2.254022731542322244e-01,-4.410842155624510041e-02,1.018883119873695287e-01,-4.172317064402036313e-01,-6.115010790062354665e-03,-1.384557848867048191e-01,1.840836025548964472e-01,3.695318357169341539e-01,8.882816603577459169e-02,-6.316145679566015358e-02,1.217216525514359243e-01,-1.544003048414935297e-01,-1.034632543195762810e+00,4.964341787970501518e-01,5.148627603489409205e-02],
    [-3.539005522882098740e+04,-3.583909144033606935e+03,3.582590684867370783e+03,3.044836074158085353e+02,2.265154801182521169e+03,1.463497238133208839e+03,-1.929077918471170506e+03,-8.714068156450255174e+02,6.894845915428915077e+02,-2.207216118052045033e+02,-6.563003726138800857e+02,8.623969074420855350e+02,6.033421421407454233e+01,-2.418468281925109693e+02,3.775302221131575493e+02,3.052405806924817853e+02,5.887769508970844754e+02,1.573319269883872380e+02,3.715179067610642960e+02,-8.031797687706180113e+02,2.085273898548941531e+02,-2.731676174252989426e+02,-7.637045122174912137e+01,-2.340759106415363817e+02,9.502449342532625565e+01,2.399965789170268806e+02,-4.225347645392230334e+01,3.551495910427710214e+02,-4.994855010011573881e+01,-1.975518690730484650e+02,3.266736639581573343e+01,-1.230086125611609660e+01,-4.319292316478342286e+01,1.906804835361269852e+02,-1.427928818968481153e+02,4.098828089166935484e+01,1.380487902952506651e+01,-3.701092506502644319e+00,4.505620033387260293e+01,3.536230093580565637e+01,-1.418003865278182900e+02,-9.242997277780804666e+01,-1.740391139905462126e+01,9.850594277251448716e+01,-7.157675275703955720e+01,8.986157984566608192e+00,8.127983410743880199e+00,2.968496441017879306e+01,8.280486051554415639e+00,1.031734780853695188e+00,-4.750469501080996082e+00,-1.829726603745996982e+01,1.354439452262659049e+00,3.306281658320894934e+00,1.752399997997402536e+01,-3.194310394918128182e+01,-2.000177205929881907e+01,4.463800346925048501e+01,1.670416617585901875e+01,-3.585257503164083204e+01,1.562769789895283878e+01,-1.512592438167503062e+01,6.006521797554094633e+01,4.700817844425046133e+00,2.554640715787447891e-01,4.720177093975124194e-01,2.166229646284731913e+00,-2.588113601956395726e+00,-1.257825089429442489e+00,2.698461526926274168e+00,-1.500268946911854862e+00,5.196433772561534603e+00,6.267642029274279603e-01,7.283009191135512983e-02,2.054078322445198890e-01,-2.468010951540113407e+00,-3.476546345123212589e+00,1.833470546131506040e+01,-7.263572554117192048e+00,1.170283322428573802e+00,-1.509351148669785481e+00,1.714695019446018209e+00,-6.705715790395597731e-01,1.918704842768638452e-01,-2.735272419436678426e-01,2.015922820166323071e+00,2.601384016465031479e+00,-3.612918583997160038e+00,3.310752449512714968e-01,-1.690535526475994033e+00,2.613289568453118328e+00,3.257096863026084144e+00,2.986890009376906852e-01,3.876154640024344067e-01,-5.794862001611440050e+00,-2.112823330935348576e+00,7.372311275669046760e-01,-1.732479010633968031e+00,2.320441013665783370e+00,-4.733584411128046177e-01,-2.006059149794674479e-01,-2.636603591003393587e-01,2.063962658976011694e-02,-4.266647449421840932e-01,-7.739499906438543353e-02,4.167055528431147238e-01,-3.294848646918591833e-02,3.128972754235985754e-01,-1.150062946619572868e+00,4.365478205155401970e-01,-1.803226015766504486e-01,6.912595099431471102e-01,1.452291705849006354e+00,5.771343548438437887e-01,-7.339092367196245470e-02,-1.029224697806525146e+00,6.001633558809228441e-01,-1.374319691999017268e+00,1.018967678092012052e+00,-2.146769623944908001e-01],
    [-3.511956876217133686e+04,-3.171945609417205105e+03,4.670911511616694952e+03,6.170690369887239513e+02,2.341019666789866733e+03,9.393830426673911234e+02,-1.381006580063623460e+03,2.154683651840158518e+02,8.262187796529549360e+02,-3.045554381434509423e+02,-8.841175662282773828e+02,1.143024722288331304e+03,1.650191795476252139e+02,-3.140911655964486044e+02,9.811315516403655010e+02,3.787984926508314629e+02,6.164114675909791004e+02,-2.033152596825368974e+01,3.045803210726405155e+02,-7.188338578950842930e+02,5.882364733765768250e+01,-2.845735479988190377e+02,-1.643622927820576081e+02,-1.778765545938276205e+02,2.647655544557011709e+01,3.408776335107567661e+02,-1.146337347026410782e+02,4.456890867001924335e+02,-4.821967956737128702e+01,-9.184732119902749048e+01,-1.886480731767001728e+01,-5.915851129428991584e+01,-3.889660867965249480e+01,8.189006277554531721e+01,-1.014480254684505809e+02,5.595403240863834071e+01,2.568388380893844669e+01,2.740164491750889653e+01,1.917756550639823843e+01,5.119299572822781386e+01,-1.820132846203919428e+02,-8.552299677827856783e+01,-2.973639248793011447e+00,8.479720794712790166e+01,-4.669037450617140905e+01,5.052667444330464264e+01,6.529724431718064714e+00,2.732631651383089633e+01,2.788909740512218605e+01,-6.589953477122746150e+00,-8.636708449447489500e+00,-2.947140594319242979e+01,1.057649031412853624e+01,4.945341601177361213e+00,4.532846188175336266e+01,-4.968390304871740426e+01,-1.248916163075996622e+01,4.510913892429307026e+01,-6.554030425226661905e+00,-2.842499849605716022e+01,2.748170146160597938e+01,2.386320850947147321e+01,4.851753641690571328e+01,1.150687236597672403e+01,-3.151247783080494358e+00,-3.841969571285502871e-01,4.792027786946821521e+00,-7.971972417899362284e+00,-7.760864630472513959e+00,8.712538108202691589e+00,-4.780250398758936203e-01,7.767203918201159851e+00,-8.867193113248881264e-01,7.267326532058319799e+00,-2.124028415160437611e+00,-4.138148738348386146e+00,2.052760105726796791e+00,1.891521945695592066e+01,7.680904442009104383e-01,-4.826942883243691362e+00,-2.815610368049702217e+00,3.502505310171683206e+00,-2.455352265189055139e+00,-9.852725459991114043e-01,-2.221380610650616205e+00,3.767719585920955350e+00,6.756357429376013357e+00,-6.381128917121518640e+00,-1.045214219714033499e+00,-1.773497633321808209e+00,6.334251101256327843e+00,6.466636449484715499e+00,2.259423807999056955e+00,1.775205214348403837e+00,-9.111410105739828680e+00,-1.906218845430237785e+00,-9.566442815272833133e-01,-3.295823416228847780e+00,5.482202820540540422e+00,-9.762953701179347687e-01,-3.635618901088765176e-01,-4.171614251318177535e-01,-4.519470209145154405e-01,-9.878947191282140272e-01,-1.276703058309781369e+00,4.783681107005403194e-02,4.690256668199579426e-01,5.043122372043404855e-01,-2.154531927893140963e+00,1.227962329622325655e+00,2.993053134969723694e-01,1.456797052928611613e+00,2.991662488879243131e+00,1.251503225404767106e+00,4.392909472585620478e-01,-1.886608953471835326e+00,1.269222540517923159e+00,-1.507109102369775577e+00,1.429650594343844228e+00,-3.306217892458753749e-01],
    [-3.362392489012601436e+04,-3.144088324228860074e+03,5.650947237266014781e+03,2.361026372216500988e+02,2.509915967891776745e+03,5.833504371403372488e+02,-6.763388289165775404e+02,1.087629299106205508e+03,9.629350636096612561e+02,-8.427013200225105720e+02,-7.411102717659080099e+02,1.280815748301992699e+03,2.501479641975524544e+02,-5.583681642355513475e+01,9.875272876264143633e+02,5.601079094086074974e+02,5.987118634446837859e+02,-2.187776429637758113e+01,2.586873272512401627e+02,-5.023745912247260890e+02,-1.686518860008261811e+01,-2.604852300577299502e+02,-1.434932180549866132e+02,-2.094714792277330560e+02,-2.891178053055720909e+01,3.771010623597416043e+02,-2.308017935126275972e+02,4.748034427719238693e+02,-2.729226661087936989e+01,-5.301874408966729391e+01,-1.981782510023092314e+01,-5.497611566483902834e+01,-7.935840601601258015e+01,7.819471798931812145e+01,2.168896663566735494e+00,7.324371143379237026e+01,4.532254090021898207e+01,3.794464249831139568e+01,-3.960830361498472030e+01,7.065069240811239126e+01,-1.545337286267100012e+02,-4.372197984980953578e+01,-9.976836241460583565e+00,1.644399983130398013e+01,3.485204109123797522e+00,6.344162058967561535e+01,-5.952747843373179526e-01,3.609284186278711104e+01,5.699616033052481612e+01,-1.165386732661696456e+01,-7.725879028220354883e+00,-3.301660951775033226e+01,1.714558929104017793e+01,7.386032896426270256e+00,6.910300151943687297e+01,-5.610221592977450200e+01,-1.947212722424169229e+01,1.153397598365066301e+01,-1.933870582231877577e+01,-3.885172577079235801e+00,1.023737450236654389e+01,3.233408949092677886e+01,9.659913370819701584e-01,1.702946242657796816e+01,-4.331590461577960127e+00,-2.179818468123309483e+00,6.171610492954980209e+00,-1.505802178365310517e+01,-1.558399691485256255e+01,1.759603677753597850e+01,-2.443782172984043655e+00,3.750026677603039538e+00,-1.559921436892298674e+00,1.622389816071556012e+01,-5.928926658453952392e+00,-3.346385076339344344e+00,1.040663106928253256e+01,2.100027532548118359e+00,-7.212257840748542037e+00,-9.366228911094950149e+00,-4.043145091455138562e+00,4.987989526586440903e+00,-4.176396741392135681e+00,-2.302440655850629181e+00,-4.283174174520881117e+00,5.182750001487172575e+00,1.011796697808842538e+01,-6.787199745189219868e+00,-2.689153989333617378e+00,-1.001034483243440576e+00,1.161047950966446507e+01,7.103859750960910269e+00,6.436668296059817607e+00,3.755972072929705696e+00,-9.403776574357678442e+00,-1.427250343590893866e+00,-4.277341945625591890e+00,-6.545016027551421978e+00,8.731775851074894845e+00,-1.769013930857525896e+00,-6.007859011983582853e-01,-3.302441080836812648e-02,-1.123215244067189866e+00,-1.121103473609410095e+00,-3.069493983153368077e+00,-7.484651951379085455e-01,1.924512505549351715e+00,-1.782956806865821364e-01,-2.107139829078777726e+00,2.777557405935548562e+00,1.218447420620452304e+00,2.335710956326272569e+00,4.353947632332111795e+00,1.409289034850252476e+00,7.014275577816905249e-01,-2.177800866311686789e+00,1.698715373658679528e+00,-1.103588476567204379e-01,1.511027189379746893e+00,1.129945906001477596e+00],
    [-3.214830627512843785e+04,-2.699581470048798565e+03,5.826447318254595302e+03,-6.263086155314677228e+01,2.791685329973258376e+03,-8.888534153906567781e+01,4.857936791256128828e+01,1.379045915587290438e+03,1.105335175539564943e+03,-1.170364986911517462e+03,-4.190824032728904172e+02,1.402774526670561045e+03,1.329461771471293901e+02,3.627668265282900393e+02,8.865648095316212220e+02,7.293162223654501304e+02,5.949289978504020837e+02,1.609360928561258106e+02,4.196711153149771008e+02,-3.012025786879365228e+02,-1.799454025485649709e+02,-2.315225346619168079e+02,-1.369545654933488166e+01,-1.166326529620117327e+02,-8.334667958629701445e+01,3.684624011971804975e+02,-2.830501460033795524e+02,4.418544592219834044e+02,-1.564871359793602146e+01,-3.727740198484413980e+01,-8.831039452888512997e+00,-5.332966829689149080e+01,-1.081965707102488921e+02,1.017558806504670912e+02,6.104653481335113696e+01,3.524296789858161816e+01,6.861902628037810814e+01,2.067487009411752297e+01,-8.446539699366424259e+01,8.950105123861126799e+01,-1.332968792110389984e+02,-2.106517405749536209e+01,-4.167213192034945735e+01,-6.211689503888850794e+01,2.318862315435922739e+01,6.819822557842441313e+01,-2.613559572641082340e+01,-4.402655651331346398e+00,6.801319140790133133e+01,-2.872016985115731558e+01,-1.678965513642963003e+01,-2.796513800837331232e+01,9.805422910867886088e+00,2.288511874142547597e+01,6.139025953293237592e+01,-4.343759661925540883e+01,-3.796099248112051328e+01,-2.923461695630309620e+01,-1.050704814788153207e+01,-5.697496932105716283e+00,-3.460219331939775156e+00,2.287646691409906907e+01,-2.959054534440986117e+01,1.669496665270141733e+01,-4.094387467254846369e-01,3.007789267772057462e-01,-1.449234465535561789e+00,-2.001497073124161830e+01,-2.081540638573458324e+01,1.903365978931694613e+01,-9.715033264407907376e-01,-1.894326192013271015e+00,-1.352912757823640788e-01,1.936518533292209554e+01,-1.202880898479254768e+01,-1.759694623468840646e+00,4.892935495727763318e+00,-1.038119322018635771e+01,-1.409730215810431275e+01,2.867444025950221853e+00,-2.695021878446180796e+00,7.000239403379737269e+00,-4.355334210619968616e+00,-2.039595007791082715e+00,-1.439300720495564345e+00,2.286320694917657104e+00,7.862002668931691751e+00,-2.972435863788020161e+00,-2.396808394588770597e+00,2.371227871832537915e+00,1.523162383509636264e+01,3.942965273793480385e+00,8.355834352677170784e+00,2.979901111013849579e-01,-4.684599265273956092e+00,-3.991982434495928711e+00,-6.523221311503656139e+00,-5.521168420840112390e+00,1.294478435885191914e+01,-2.646783896733705177e+00,-4.831109948195827508e-03,8.683872404306685056e-01,-1.211704794334121926e+00,4.446696543360331155e-01,-3.214565486430266628e+00,-8.660384218677397161e-01,2.826164244782473745e+00,-1.438141528119096346e+00,5.092181190578808359e-01,3.676085470263205757e+00,2.364377160212559836e+00,2.082451781160599147e+00,3.652224024723286444e+00,1.574092458322433330e-02,1.263268301309825870e-01,-9.884405914774736512e-01,1.512850724293459681e+00,1.702650275053792850e+00,2.410670170439221494e+00,3.450422541838049639e+00]])
    return models, coeffs

def get_arch3k():
    models=[-1000, -950, -900, -850, -800, -750, -700, -650, -600, -550, -500, -450, -400, -350, -300, -250, -200, -150, -100, -50, 0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600,650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 1850]
    coeffs= numpy.array([[-3.544200185000000056e+04,-5.581937249999999949e+03,-2.788952134999999544e+03,-7.229579716666667082e+02,2.384251151666666374e+03,-1.015199887666666712e+02,9.954505006666665849e+02,6.410489143333333004e+02,-7.449152324999998882e+02,-3.091715248333333079e+02,-6.996639179999999669e+02,1.205851234333333366e+02,-4.739289923333333263e+02,-1.072994594999999890e+03,1.482877390999999818e+02,-4.043709413333332918e+02,-2.599676954999999907e+02,-2.768356156666666266e+02,2.960542656666666517e+02,-3.175167780000000448e+02,1.688133074999999792e+02,1.212973450000000071e+02,-7.650888686666665706e+01,-6.808436348333332262e+02,-1.075582983333333402e+02,1.257021190000000122e+00,-3.883633883333333614e+01,1.632529040000000009e+02,-9.994896271666664234e+01,1.405617345000000000e+02,-1.217327459999999917e+01,-1.222144061666666488e+02,-2.956268534999999815e+02,-8.833724483333334376e+00,-3.416152625000000143e+01,-5.712268263333332818e+00,3.268256450000000513e+01,8.202572663333333125e+00,4.860897711666666510e+01,-2.564920678333333015e+01,4.721227553333333304e+01,-2.377365683333333379e+01,-5.407843499999999892e+01,-6.643433328333333066e+01,3.508935336666666238e+00,-4.537714064833332728e+00,3.124981384999999534e+01,-1.582082313333333090e+01,7.017433503333332823e+00,9.580563074999998818e+00,3.950929464999999752e+00,8.676137504999998029e+00,-6.976487834999999471e+00,1.055434206666666697e+01,-6.413725174999999723e+00,-1.231413241666666458e+01,-7.226471081666665519e+00,8.642805639999998846e+00,-3.073688701666666301e+00,1.644151883333333330e+01,-9.892982401666666092e+00,-2.956574178333333247e+00,-3.936359394999999761e+00,2.861892829999999943e+00,-4.829109323333333204e-01,1.393638218333333456e-01,3.177270313333333540e-01,-1.246989481666666677e+00,1.180571904999999866e+00,6.902060354999998981e-02,-4.483265198333333257e-01,8.903172584999998751e-01,3.925477856666666376e+00,-2.032299549999999844e+00,5.084940301666666329e+00,-4.122489953333333013e+00,-6.932848931666666381e-01,-1.993778578333333051e+00,1.661652534999999764e+00,2.442554718333333597e+00,4.320258983333332692e-01,-1.046663046666666652e+00,-2.026998571666666638e-01,-4.108860094999999824e-01,4.003153269999999708e-02,-8.716767414999998520e-02,4.333152403333333513e-01,8.487729938333332669e-01,7.984080433333333726e-01,1.038761275000000150e+00,-6.249438418333332912e-01,1.279845233333333221e+00,-1.038802964999999912e+00,2.421321084999999984e-01,-5.902931819999999163e-01,1.007359771833333362e+00,1.156925756666666638e+00,6.836058788333332359e-02,-2.274781818333333205e-01,-3.873269363333332882e-02,-2.699028299999999825e-01,-2.361974678333333272e-02,-1.824764228333333460e-01,7.272176958333331775e-02,-5.651029391666666235e-02,7.274307156666666441e-02,3.847373981666666332e-01,2.542321928333333148e-01,1.746235230000000027e-01,-4.005603111666666827e-02,2.674053626666666461e-01,-1.471133154999999804e-01,2.658690486666666630e-01,-1.569470546666666688e-01,4.479351381666666909e-01,3.901358879999999307e-01,1.439851931833333390e-03,-3.867022145000000022e-02,-7.613102664999998881e-02,4.685985829999999436e-02],
    [-3.604955479999999807e+04,-5.974309483333332537e+03,-3.790371986666666544e+03,-4.269323498333333191e+02,2.536057409999999891e+03,-4.726964776666666239e+02,1.193999144999999999e+03,6.463504930000000286e+02,-9.022096598333332622e+02,-5.150211294999999154e+02,-8.195918404999999893e+02,3.191977386666666234e+02,-3.589108526666666421e+02,-1.063385528333333241e+03,3.936180926666665982e+02,-5.303508898333332127e+02,-3.830462321666666412e+02,-2.966692320000000223e+02,4.246586919999999736e+02,-2.959408813333333228e+02,3.505891124999999988e+02,2.162185598333333019e+02,-6.864110013333333882e+01,-7.551148458333333338e+02,-1.456195076666666637e+02,-2.476882136666666412e+01,-3.784031573333333398e+01,2.017295973333332881e+02,-1.182413448333333292e+02,2.238702726666666649e+02,-1.562765643333333188e+01,-1.400956723333333116e+02,-2.909155859999999620e+02,-6.754604853333333381e+01,8.035137466666666395e-01,-6.262588826666665831e+00,3.431690651666666270e+01,1.183009565000000052e+01,5.166466273333332992e+01,-4.182727179999999834e+01,7.040677603333332968e+01,-3.432113051666666337e+01,-6.499965321666667251e+01,-4.578012021666666698e+01,-2.257230933333333311e+01,1.731098133333333067e+01,3.572557186666666240e+01,-2.011343146666666826e+01,1.118260061666666694e+01,1.188222850000000008e+01,5.130648358333333547e+00,7.094058204999999617e+00,-1.388975343333333257e+01,1.462617379999999834e+01,-1.030655691000000118e+01,-1.509483871666666488e+01,1.659071889500000063e+00,1.959078307500000005e+00,4.415395124999999865e+00,1.729971744999999927e+01,-1.320138233333333311e+01,-5.488243084999998800e+00,-6.257427244999999694e+00,4.350831079999999851e+00,1.177128039999999903e-01,1.065485406833333315e-01,-3.408246526666666720e-01,-2.727098068333333458e+00,1.217703096666666651e+00,-8.343788139999999132e-01,-3.948261144999999361e-01,2.745795713333333055e+00,2.747068311666666318e+00,-1.468513673333333158e-01,4.442819074999999174e+00,-5.617269191666666828e+00,-2.010657670000000063e+00,-3.139783904999999820e+00,2.058525036666666530e+00,3.052668033333333142e+00,5.304789926666666489e-01,-9.524995886666666189e-01,-2.857014461666667060e-01,-5.016547048333332981e-01,1.125972381666666688e-01,-2.997678996666666151e-01,2.827471913333333142e-01,1.182654178333333306e+00,8.627913008333332190e-01,9.484635883333332185e-01,-2.835062558333333316e-01,8.561121658333332718e-01,-1.427643638333333076e+00,-2.120996194999999751e-01,-8.656860778333332895e-01,1.130556050000000035e+00,1.412178818333333252e+00,4.292478974999999752e-02,-4.508021201666666533e-01,-1.297645756666666594e-01,-2.563405248333333053e-01,-3.462262916666666857e-02,-1.537955073333333311e-01,2.303113166666666545e-01,-1.186716639999999962e-01,5.945630906666666410e-02,5.249829966666667014e-01,1.541284156666666849e-01,2.207391009999999931e-01,-9.454484976666666790e-03,1.452582723333333548e-01,-1.941702081666666357e-01,1.479702903333333375e-01,-2.060976448333333155e-01,4.695526826666666098e-01,4.313877526666666795e-01,-1.150934283166666662e-02,-1.490154074999999745e-01,-9.202620364999999913e-02,7.428936319999999982e-02],
    [-3.738434909999999945e+04,-5.823805738333333466e+03,-4.234081200000000536e+03,-3.102668688333333193e+02,3.049207528333333357e+03,-3.720758041666666713e+02,9.982498745000000326e+02,3.991438921666666602e+02,-9.705017158333332645e+02,-5.316458971666667139e+02,-7.435471538333332546e+02,4.024379481666666152e+02,-4.068388370000000123e+02,-9.665805681666665805e+02,5.211685401666666166e+02,-6.160735264999999572e+02,-4.704745130000000017e+02,-2.697311904999999683e+02,5.152467474999998558e+02,-2.970711780000000317e+02,5.372386138333332610e+02,2.769968113333333122e+02,-6.867640436666667370e+01,-8.201128128333332370e+02,-1.806713196666666477e+02,-5.366282121666666427e+01,-3.230303279999999688e+01,2.305799099999999839e+02,-1.328710719999999696e+02,2.960383283333333111e+02,-2.506396574999999771e+01,-1.536155883333333350e+02,-2.868008416666666562e+02,-1.267469936666666683e+02,4.002817381666666563e+01,-8.458631328333332533e+00,3.257487466666666620e+01,1.377293896666666484e+01,5.277980948333333799e+01,-5.547925949999999773e+01,8.696702358333332938e+01,-4.611148839999999893e+01,-7.273948763333334000e+01,-2.709928868333333085e+01,-4.866795591666666354e+01,4.004099363333332917e+01,3.994488931666666787e+01,-2.200855836666666576e+01,1.483781741666666498e+01,1.343454288333333224e+01,5.556906951666666927e+00,5.098803838333333616e+00,-2.052021873333333346e+01,1.670936938333333188e+01,-1.503777808333333255e+01,-1.724122591666666438e+01,9.702284478333332629e+00,-5.079561331666666568e+00,1.167941461666666569e+01,1.805524048333333553e+01,-1.571624001666666537e+01,-7.610607568333332296e+00,-8.113303984999999940e+00,5.853647575000000103e+00,8.097717353333333534e-01,-8.233652173333334823e-03,-1.038278851666666558e+00,-4.377896051666666288e+00,1.039555827833333224e+00,-2.066007816666666663e+00,-3.682644563333333232e-01,4.353120984999999443e+00,1.385935906666666551e+00,1.399039560000000071e+00,3.773493955000000177e+00,-7.040364343333333608e+00,-3.292029325000000117e+00,-4.010686508333332512e+00,2.255710094999999971e+00,3.503780666666666654e+00,6.629578356666667727e-01,-7.551188921666666110e-01,-3.343007375000000003e-01,-5.534087604999999854e-01,1.378031016666666497e-01,-4.290349414999999889e-01,7.579091093333333029e-02,1.467740201666666522e+00,8.462779606666666066e-01,7.942226041666666791e-01,-1.186802018333333320e-01,3.945414330000000525e-01,-1.868871174999999996e+00,-7.006382521666666419e-01,-1.065361530000000112e+00,1.168611481666666618e+00,1.618651086666666350e+00,-2.391263452999999733e-02,-6.407962763333332479e-01,-2.256472593333333498e-01,-2.129168946666666340e-01,-2.718079526666666509e-02,-1.003684416833333370e-01,4.041775986666666376e-01,-1.327884456666666713e-01,5.244954704999998940e-02,6.562708189999999497e-01,3.097940840166666862e-02,2.578138156666666680e-01,-3.717078736666666605e-02,5.689894456666665448e-03,-2.776866250000000202e-01,2.345215968666666470e-02,-2.509507756666666811e-01,4.641995926666666605e-01,4.681879071666666947e-01,-5.183942373333332715e-02,-2.475927106666666599e-01,-1.133645541666666590e-01,9.578048424999999200e-02],
    [-3.932303081666666549e+04,-5.519301156666666429e+03,-3.899237464999999702e+03,-2.699657824999999889e+02,3.586095516666666299e+03,9.401200636666666810e+01,8.852631929999999727e+01,-6.073209056666667038e+02,-9.462953901666666070e+02,-4.029443918333332704e+02,-5.589476304999999456e+02,3.884209366666665915e+02,-6.115066051666666453e+02,-7.816622676666667076e+02,4.842280283333332704e+02,-6.673965903333333927e+02,-4.895165189999999598e+02,-2.029211536666666689e+02,5.788856133333332536e+02,-2.548586924999999894e+02,6.965521003333333283e+02,2.606498775000000023e+02,-5.873289198333333161e+01,-8.805204104999999117e+02,-2.109587284999999781e+02,-6.758281423333333748e+01,-1.405184593666666437e+01,2.493787398333333272e+02,-1.226898838333333117e+02,3.442343901666666852e+02,-5.147717903333332856e+01,-1.543536028333333547e+02,-2.807225256666666837e+02,-1.827333433333333232e+02,8.768244556666665801e+01,-1.068128163333333269e+01,2.990636974999999964e+01,1.636778400000000033e+01,5.153957114999999334e+01,-6.283896895000000882e+01,9.272633551666666563e+01,-5.778057228333332773e+01,-7.464612126666666825e+01,-1.175855019833333337e+01,-7.062428640000000257e+01,6.279184453333333238e+01,4.558209791666666888e+01,-2.061697721666666538e+01,1.796988858333333283e+01,1.327451541666666657e+01,5.201096258333332223e+00,2.748441781666666195e+00,-2.598676956666666626e+01,1.541065538333333329e+01,-1.881833324999999846e+01,-1.850150465000000111e+01,1.553319806666666736e+01,-1.101916528833333331e+01,1.788916243333333256e+01,1.881479186666666692e+01,-1.661145681666666718e+01,-9.816965041666666281e+00,-9.237286788333333831e+00,7.172113733333333130e+00,1.100172844999999899e+00,-3.283266851666666875e-01,-1.675643473333333189e+00,-5.957386021666666309e+00,2.987786748166666451e-01,-2.978160990000000119e+00,-5.446471436666666666e-01,5.188923858333333250e+00,2.350097843333333048e-01,2.319246844999999890e+00,3.094378588333333457e+00,-7.957345416666666615e+00,-4.677971989999999636e+00,-4.407658471666666244e+00,2.251195928333333374e+00,3.765390393333333030e+00,8.023449954999999356e-01,-5.354021376666666665e-01,-3.771266490000000360e-01,-5.384113974999999996e-01,1.204241676666666511e-01,-5.434967496666666120e-01,-7.417139844999999510e-02,1.580759924999999955e+00,6.267277199999999882e-01,6.298181499999999655e-01,-1.884538923333333171e-01,-7.600476801666666837e-02,-2.255276108333333251e+00,-1.228916930000000018e+00,-1.134283661666666720e+00,1.089066491666666581e+00,1.743109261666666576e+00,-1.422941600000000029e-01,-8.357607074999997554e-01,-3.103444371666666535e-01,-1.332241346666666604e-01,-3.349057531666666324e-03,-3.099571453333332949e-02,5.637532349999999637e-01,-1.095715176666666596e-01,4.562339373333332976e-02,7.351291734999999550e-01,-1.187953148333333320e-01,2.777524663333332811e-01,-1.329117438333333179e-01,-1.252329194999999840e-01,-3.941740544999999818e-01,-1.011547642166666650e-01,-2.770092648333333241e-01,3.980856293333333018e-01,4.862783988333332363e-01,-1.202438591666666612e-01,-3.517813673333333169e-01,-1.425655323333333280e-01,1.146895816666666651e-01],
    [-4.054776046666666662e+04,-5.427485786666666172e+03,-3.384040634999999838e+03,-3.119028213333333497e+02,3.331647841666666409e+03,6.347129653333333863e+02,-1.438589758333333293e+03,-1.689039788333333490e+03,-9.406269548333332295e+02,-3.737348593333333042e+02,-3.463624963333332971e+02,2.964340833333333194e+02,-7.640307288333333418e+02,-6.124435608333333221e+02,2.510036103333333131e+02,-6.961798835000000736e+02,-4.615959103333333360e+02,-1.024244130833333202e+02,5.901297053333332769e+02,-1.578858848333333640e+02,7.838418928333333042e+02,1.466780861666666453e+02,-5.205555846666665332e+01,-9.304609849999999369e+02,-2.252522551666666573e+02,-5.735640381666666343e+01,2.091265723333333426e+01,2.446556659999999965e+02,-1.020437859500000002e+02,3.641010430000000042e+02,-9.776545584999999505e+01,-1.450656491666666739e+02,-2.683686264999999480e+02,-2.286974621666666394e+02,1.393784760000000063e+02,-8.300647243333333591e+00,3.053095075000000236e+01,2.153765798333333237e+01,4.600140173333333138e+01,-6.710188048333333199e+01,9.047993201666666607e+01,-6.724587069999999756e+01,-6.929998383333332868e+01,-7.589963183333332530e-01,-8.475825671666666494e+01,8.212415001666666114e+01,4.984680414999999698e+01,-1.589302636666666579e+01,2.063897194999999840e+01,1.223861226666666546e+01,4.706503753333333151e+00,6.753435880000000502e-01,-2.893464986666666761e+01,1.199168753333333370e+01,-2.048663369999999873e+01,-1.790650529999999918e+01,1.788558364999999739e+01,-1.485540646666666653e+01,2.205446178333333052e+01,1.819226423333333287e+01,-1.552718291666666595e+01,-1.138573534999999914e+01,-9.820739659999999205e+00,7.837390786666666109e+00,1.049344668333333175e+00,-6.856817671666667335e-01,-1.887821286666666598e+00,-6.535008995000000098e+00,-8.521682356666664404e-01,-3.220811248333333321e+00,-6.512344369999999438e-01,4.887691840000000454e+00,-4.411277561666666625e-01,2.575181204999999807e+00,2.206483906666666606e+00,-8.121111309999999861e+00,-5.705008379999999768e+00,-4.528751848333333108e+00,2.110133615000000074e+00,3.713925454999999598e+00,8.139426954999998687e-01,-3.417545116666667049e-01,-4.107961131666666432e-01,-4.046418936666666410e-01,2.666604903333333332e-01,-7.311322899999999070e-01,-7.083839913333334071e-02,1.524296928333333190e+00,2.085896816666666653e-01,5.122153949999999067e-01,-4.122844929999999741e-01,-4.753506179999999470e-01,-2.490385601666666560e+00,-1.634460221666666602e+00,-1.167619028333333198e+00,9.152663273333333516e-01,1.721193239999999847e+00,-2.805853551666666057e-01,-1.007264149333333414e+00,-3.799890043333333245e-01,-5.337406911666665865e-02,1.455912796666666668e-02,3.638176234999999925e-02,6.953275704999999363e-01,-1.051305963333333260e-01,6.508366265000001261e-02,7.303298981666666023e-01,-2.507092681666666101e-01,2.872079765000000173e-01,-2.617469696666666623e-01,-1.887175186666666671e-01,-5.126407184999999256e-01,-1.950808961666666841e-01,-3.055147059999999692e-01,2.781437405000000140e-01,4.708057884999999332e-01,-1.942927244999999581e-01,-4.427589951666666135e-01,-1.721346076666666614e-01,1.202280929999999803e-01],
    [-4.057221125000000029e+04,-6.341326371666667001e+03,-3.538436683333333349e+03,-2.355752079999999751e+02,1.935442569999999705e+03,8.647342726666665840e+02,-2.688255841666666583e+03,-2.381276510000000144e+03,-8.392818465000000288e+02,-4.556318811666665738e+02,-1.102193088999999873e+02,2.551608354999999904e+02,-7.966178918333332604e+02,-5.439550783333332902e+02,-1.423267574666666633e+02,-6.352843135000000530e+02,-3.735765006666666181e+02,5.230125788333333503e+01,5.349073268333332862e+02,-3.879013618833333510e+01,8.013551606666667340e+02,5.078006653333333453e+00,-2.561013253333332784e+01,-8.816900256666666564e+02,-2.084324094999999772e+02,-2.143225246666666806e+01,7.420227326666666556e+01,2.058823490000000049e+02,-8.200360331666666980e+01,3.654887973333333093e+02,-1.293401863333333210e+02,-1.122893589999999904e+02,-2.196792054999999664e+02,-2.549124998333332996e+02,1.884944598333333090e+02,-3.338213524999999571e+00,3.499417884999999728e+01,2.884356751666666341e+01,3.468725248333333155e+01,-6.579551981666665483e+01,8.578335863333332156e+01,-6.415046631666666599e+01,-5.106640079999999671e+01,1.376257311666666538e+01,-8.934981951666667044e+01,9.853349138333334167e+01,4.722286384999999598e+01,-3.558027755999999986e+00,2.057825504999999922e+01,1.087091821666666647e+01,4.120554316666666494e+00,-5.942868013333333366e-01,-2.710280733333333103e+01,8.271299718333333217e+00,-1.837414409999999876e+01,-1.401471363333333287e+01,1.849957475000000073e+01,-1.663196903333333410e+01,2.580418896666666839e+01,1.422109416666666704e+01,-9.828726631666667046e+00,-1.117721698333333258e+01,-9.722652535000001706e+00,7.165805591666666530e+00,8.157552991666665587e-01,-1.100480349999999774e+00,-1.462531118333333158e+00,-5.579974499999999615e+00,-2.132813171666666729e+00,-2.837349033333333104e+00,-5.410811733333332763e-01,3.951568541666666157e+00,-8.289563041666666576e-01,3.101056831666666458e+00,6.515327860000000859e-01,-6.537017975000000369e+00,-5.906358171666666657e+00,-4.340577684999999519e+00,1.659307966666666578e+00,3.257615645000000004e+00,6.422362059999999762e-01,-1.987625179999999991e-01,-4.724900493333333285e-01,-1.579478223333333209e-01,5.485072024999999574e-01,-1.001500559500000165e+00,4.694303666666666680e-03,1.238085040000000081e+00,-2.233741728333333287e-01,3.464529000000000636e-01,-4.759636829999999708e-01,-8.558815244999998795e-01,-2.238079601666666640e+00,-1.856947574999999961e+00,-1.073601316666666694e+00,5.486974854999999707e-01,1.524379919999999888e+00,-3.835713998333333263e-01,-1.097330315000000001e+00,-3.918101821666666318e-01,-7.212983841666666118e-03,1.141386499666666686e-02,8.944030728333332569e-02,7.339176625000000120e-01,-1.323568163333333214e-01,9.187217416666666747e-02,6.071630049999999779e-01,-3.248277231666666376e-01,2.574653539999999796e-01,-3.569092350000000469e-01,-1.887245803333333083e-01,-5.299030579999999269e-01,-2.809213528333333043e-01,-2.852159960000000272e-01,8.527301288333333229e-02,4.224213173333333238e-01,-2.531876763333333336e-01,-4.824049124999999494e-01,-2.054060024999999623e-01,9.514267288333333461e-02],
    [-3.984164304999999877e+04,-4.851399023333333389e+03,-3.303687318333332769e+03,-3.783670513333332792e+02,8.117085859999998547e+02,8.618553543333333664e+02,-2.655949529999999868e+03,-2.134163638333332983e+03,-7.464830251666666072e+02,-4.887028664999999705e+02,8.892774208333332808e+01,4.777807244999999625e+02,-5.803681968333332861e+02,-6.014125033333332340e+02,-4.683542525000000296e+02,-5.177362418333332243e+02,-2.889766751666666096e+02,2.173312860000000057e+02,4.783476423333332832e+02,1.205865349666666475e+02,7.760002059999999346e+02,-3.431971168333333821e+01,-2.025360326666666655e+00,-7.278625540000000456e+02,-1.739261191666666662e+02,8.676013624999999507e+00,1.299438695000000052e+02,1.553862928333333286e+02,-6.094771878333332893e+01,3.623828486666666322e+02,-1.166683536666666612e+02,-7.160646248333333119e+01,-1.393377384999999720e+02,-2.683474534999999719e+02,2.346163261666666244e+02,1.223865460166666530e+00,3.836181014999999661e+01,3.605816011666666299e+01,2.161062770000000199e+01,-6.155027658333332852e+01,8.304431879999999921e+01,-4.828173026666665635e+01,-2.671963654999999704e+01,3.300675194999999462e+01,-8.948167380000001003e+01,1.150043760000000077e+02,3.862571763333333053e+01,1.450988044999999893e+01,1.837411888333333465e+01,9.473324868333333981e+00,3.629037319999999678e+00,-1.586730978333333208e+00,-2.285493173333333061e+01,5.426204666666667009e+00,-1.430126489999999784e+01,-8.670136686666666037e+00,1.957542699999999769e+01,-1.767319989999999663e+01,3.067733569999999688e+01,7.805314733333333699e+00,-8.298654303333331539e-01,-9.770387586666666735e+00,-9.582335556666667031e+00,5.701389573333332628e+00,5.796450046666666855e-01,-1.539085993333333402e+00,-1.004235848666666486e+00,-4.018974186666666171e+00,-3.264943991666666268e+00,-2.403224499999999875e+00,-4.036942318333333057e-01,3.361327733333332901e+00,-1.020377454999999989e+00,4.335589938333332505e+00,-1.443447699999999889e+00,-3.749629481666666653e+00,-5.678303788333332491e+00,-4.207495751666666450e+00,1.123822073333333282e+00,2.510053848333333448e+00,4.175110993333333576e-01,-1.132343838833333172e-01,-5.878147033333332994e-01,2.002074449499999936e-02,7.989461436666667193e-01,-1.290336876666666743e+00,5.773627424999999702e-02,8.190151175000000006e-01,-4.662063931666666217e-01,1.788244813333333127e-01,-2.819255709999999859e-01,-1.303532758333333152e+00,-1.623177198333333182e+00,-2.049931715000000043e+00,-9.475383393333333126e-01,1.477491439833333031e-01,1.190064056666666703e+00,-4.107990983333332791e-01,-1.156441754999999683e+00,-3.413508586666666456e-01,1.856372331666666800e-03,-1.465168509833333216e-02,1.182675101666666728e-01,6.907493068333333541e-01,-1.815355641666666631e-01,1.055613781666666640e-01,4.282566061666666091e-01,-3.511750249999999740e-01,2.004478529999999536e-01,-3.907118138333333102e-01,-1.853403056666666493e-01,-4.548681803333333162e-01,-3.996736885000000128e-01,-2.375666444999999793e-01,-1.064723222999999913e-01,3.342383420000000216e-01,-2.771787576666666642e-01,-4.974893273333332866e-01,-2.436023934999999863e-01,5.697777115000000198e-02],
    [-3.944080593333333672e+04,-4.064178056666666635e+03,-3.577660809999999401e+03,-7.909754621666666026e+02,-1.326176183833333369e+02,4.751563489999999774e+02,-1.699319108333333133e+03,-1.523281601666666575e+03,-6.537991411666666863e+02,-4.853920764999999733e+02,2.177385153333333392e+02,8.196843635000000177e+02,-4.399879786666666632e+02,-7.684689086666666071e+02,-9.440413911666664717e+02,-3.609007284999999570e+02,-2.545233949999999368e+02,3.476938836666666361e+02,4.155713644999999588e+02,2.174219798333333244e+02,7.142467759999999544e+02,-5.447142001666666999e+01,-7.890257452833333573e+00,-5.280919283333332714e+02,-1.336135556666666560e+02,1.178036372499999906e+01,1.644695961666666904e+02,1.002717312666666629e+02,-5.647817518333333453e+01,3.561575748333333422e+02,-9.215874995000000069e+01,-3.748905979999999261e+01,-5.715163641666666194e+01,-2.558823576666666213e+02,2.647125859999999875e+02,2.981122294999999589e+00,3.719094581666666244e+01,3.826449565000000064e+01,8.029787764999998245e+00,-5.805398756666666316e+01,8.293784659999998610e+01,-3.223599418333333233e+01,-1.836365760000000069e+00,4.794870821666665961e+01,-8.091872681666666267e+01,1.265134553333333400e+02,2.623273051666666333e+01,3.351930191666666303e+01,1.499445563333333276e+01,8.697219794999998754e+00,3.384877979999999731e+00,-2.536424036666666382e+00,-1.796113809999999944e+01,3.994052041666666497e+00,-1.175219151666666662e+01,-2.816650073333332838e+00,1.948634799999999956e+01,-1.685601481666666501e+01,3.510952968333333502e+01,8.749903556666666082e-01,8.536685193333333643e+00,-7.320969924999999989e+00,-8.980859658333333329e+00,4.114497078333332780e+00,7.695760241666664836e-01,-1.641798939999999929e+00,-6.711131721666666605e-01,-2.434191279999999846e+00,-3.983598254999999977e+00,-2.579188106666666425e+00,-1.262821330333333270e-01,2.902676678333333093e+00,-7.122941003333334020e-01,5.748475033333333428e+00,-3.365907829999999823e+00,-8.054004359999999973e-01,-5.167893998333333627e+00,-3.956329103333332764e+00,6.122070666666666883e-01,1.556869676666666535e+00,2.493206451666666601e-01,-1.378494463333333579e-03,-6.550699706666666122e-01,1.018960043333333176e-01,9.557440388333333647e-01,-1.508827098333333172e+00,2.766899724833333032e-02,4.027416814999999484e-01,-5.892738199999999482e-01,1.440078710000000095e-01,-4.894589903333333020e-03,-1.666111909999999918e+00,-9.203607804999999198e-01,-2.247444556666666760e+00,-7.564887901666667025e-01,-1.903601593333333342e-01,7.874839803333333332e-01,-3.772695041666666027e-01,-1.155660456666666613e+00,-2.554280358333332890e-01,-2.501953273333333214e-02,-5.004211591666666431e-02,1.299788625000000142e-01,6.017797741666667255e-01,-2.349943994999999786e-01,1.236402259999999920e-01,2.441115131666666271e-01,-3.691529954999999696e-01,1.623977398333333322e-01,-4.042409398333333126e-01,-1.718589834999999788e-01,-3.457114225000000318e-01,-5.530052318333333883e-01,-1.682448326666666494e-01,-2.482691174999999695e-01,2.242429318333333255e-01,-2.756095711666666226e-01,-4.864862001666666047e-01,-2.830228295000000172e-01,1.080064537499999915e-02],
    [-3.879344478333333245e+04,-3.651124878333333072e+03,-2.896076723333332666e+03,-1.126918238333333193e+03,-6.575951116666666394e+02,6.896085536666664950e+01,-1.202138136666666696e+03,-6.190841508333332968e+02,-6.132133988333333718e+02,-5.579990349999999353e+02,3.310159111666666831e+02,9.313750236666667206e+02,-3.403860119999999370e+02,-8.765459389999999757e+02,-1.339249464999999873e+03,-2.401603460000000041e+02,-3.198727634999999623e+02,4.223435283333333246e+02,3.309665679999999384e+02,2.751089363333333040e+02,6.147068760000000793e+02,-2.421703447499999839e+01,-1.032026508666666587e+02,-3.816256474999999568e+02,-1.074294491666666573e+02,-1.796995641666666899e+01,1.618614846666666836e+02,4.743077543333333068e+01,-5.883960509999999999e+01,3.256058850000000575e+02,-7.016594236666666973e+01,-4.432915158333332784e+01,-3.213661551666666227e+00,-2.146784488333333059e+02,2.754695481666666410e+02,2.056393424999999997e+00,3.218768628333333481e+01,3.127980224999999947e+01,-6.106589199999998385e+00,-5.762795343333333165e+01,7.657720648333332747e+01,-2.577011126666666385e+01,9.188980798333332700e+00,5.259592245000000332e+01,-6.483023838333332378e+01,1.278326038333333372e+02,1.429005480000000006e+01,4.343401124999999752e+01,1.266490563333333164e+01,9.043104200000000148e+00,2.919370768333333199e+00,-3.820071353333332809e+00,-1.514965216666666592e+01,2.441084038333332984e+00,-1.264375436666666452e+01,2.807593238500000199e-01,1.741038599999999903e+01,-1.520318196666666566e+01,3.599824151666666694e+01,-4.300304033333333109e+00,1.350696153333333172e+01,-5.284699425000000339e+00,-7.064465819999999674e+00,3.245744989999999497e+00,1.455798281666666583e+00,-1.275138343333333424e+00,-3.457120736666666749e-01,-1.593673438333333081e+00,-4.148101784999999708e+00,-3.465411121666666094e+00,-6.784332073333333019e-03,2.248277214999999885e+00,-4.124700194999999514e-01,6.157278941666666228e+00,-4.495856156666666159e+00,1.008023820666666515e+00,-4.788030713333332855e+00,-3.311192388333332737e+00,4.582567756666666159e-01,4.810290861666666196e-01,1.891945598333333312e-01,1.587754971666666681e-01,-5.767209930000000151e-01,2.000451891666666371e-01,9.669817259999999859e-01,-1.499818034999999883e+00,-1.039697517499999918e-01,9.389886868333333081e-02,-7.519464198333332128e-01,1.670538245000000033e-01,6.253140178333332910e-02,-1.832196219999999709e+00,-4.253801093333332561e-01,-2.386594396666666729e+00,-5.415631386666666103e-01,-3.068286201666666768e-01,3.691004254999999956e-01,-3.640666223333333118e-01,-1.056356496666666533e+00,-1.915171408333332936e-01,-6.624288570000000376e-02,-6.160628141666665836e-02,1.487265178333333493e-01,5.143421644999999209e-01,-2.498604978333333060e-01,1.374193013333333546e-01,1.116118106666666582e-01,-4.197228399999999304e-01,1.490451159999999775e-01,-4.301969605000000030e-01,-1.518214750000000113e-01,-2.763081911666666612e-01,-6.747673634999999948e-01,-1.302070354999999846e-01,-2.947608248333333236e-01,1.013018410333333258e-01,-2.718553933333333061e-01,-4.377905770000000141e-01,-2.909075398333333395e-01,-2.171899783333333320e-02],
    [-3.933405328333332727e+04,-2.895849063333333561e+03,-1.317548495000000003e+03,-8.693068681666666180e+02,-6.410188988333333100e+02,-6.576743119999998726e+02,-2.135135373333333519e+03,-1.624335298333333810e+01,-4.656360361666665995e+02,-7.889702199999999266e+02,3.786376041666666765e+02,7.024050298333332876e+02,-3.850815374999999676e+02,-6.912765176666665639e+02,-1.328470566666666627e+03,-1.582449294999999836e+02,-4.702868011666666348e+02,4.585036010000000033e+02,2.742799638333333405e+02,2.836363594999999691e+02,5.251561615000000529e+02,8.097888294999999914e+01,-2.542356418333333181e+02,-3.613564268333332734e+02,-9.687554101666665929e+01,-5.931346606666666332e+01,1.370395536666666487e+02,1.440170739666666577e+01,-5.738524584999999689e+01,2.704964828333332889e+02,-6.696798399999998708e+01,-8.363432634999999493e+01,1.121726646666666660e+01,-1.439257689999999741e+02,2.702046060000000125e+02,-3.481107318333332978e-01,2.886236456666666683e+01,1.972468273333333144e+01,-1.971430483333333328e+01,-5.710969820000000396e+01,6.009907679999999885e+01,-3.634466053333332525e+01,5.200298231666666382e+00,4.808682591666666184e+01,-4.161412004999999681e+01,1.180401303333333232e+02,6.348278641666666111e+00,3.701498813333333260e+01,1.190720463333333434e+01,1.082684964999999977e+01,2.445600218333332965e+00,-5.891845291666666817e+00,-1.401728359999999896e+01,-3.152126608333333246e-01,-1.675440986666666632e+01,6.475203994999999546e-01,1.444956561666666417e+01,-1.251968793333333352e+01,3.218483451666666184e+01,-6.156750851666665802e+00,1.139956371666666612e+01,-5.655235219999999785e+00,-3.362108484999999369e+00,3.122608193333332949e+00,2.295728308333333079e+00,-6.333347484999999333e-01,-2.409911759999999736e-02,-1.201607079999999828e+00,-3.853712889999999724e+00,-4.256349993333333082e+00,1.407240635666666406e-01,1.426734228333333077e+00,-1.781795851666666541e-01,5.051764299999999430e+00,-4.489687499999999609e+00,1.328044881666666566e+00,-5.002523375000000883e+00,-1.982875378333333272e+00,8.723472088333332763e-01,-4.124255873333333433e-01,1.287839669999999992e-01,2.550366091666667057e-01,-4.035387683333333531e-01,3.885164964999999748e-01,9.526391985000000062e-01,-1.248496233333333372e+00,-1.319591069999999922e-01,-3.329232630000000109e-02,-1.029602550166666797e+00,2.811488708333333419e-01,-1.955714253333333263e-01,-1.711902458333333321e+00,-1.547352991666666455e-01,-2.349141238333332993e+00,-2.649207276666666888e-01,-1.275902150999999873e-01,5.890177829999999892e-02,-4.407224893333333560e-01,-8.282936861666665429e-01,-1.957336648333333484e-01,-1.154848849999999955e-01,-5.125390194999999982e-02,1.867427556666666488e-01,4.560807741666665915e-01,-2.209091543333333296e-01,1.718710640000000178e-01,3.436125101666666348e-02,-5.087660421666665433e-01,1.723575061666666741e-01,-4.698152219999999213e-01,-1.143230369999999885e-01,-2.508644223333332812e-01,-6.673632616666665962e-01,-1.155003830000000120e-01,-2.384840191666666442e-01,-1.200000463333333618e-03,-2.914484404999999612e-01,-3.362156931666667181e-01,-2.358841624999999664e-01,-1.789884116666666525e-02],
    [-4.047924543333332986e+04,-2.945833973333333233e+03,6.349347336666667019e+01,-3.488961999999999648e+02,-8.494295993333332717e+01,-1.269342221666666546e+03,-3.228322358333332886e+03,3.193947178333332886e+02,-2.057212865000000193e+02,-8.645032908333333808e+02,5.337044399999999769e+02,4.954902111666665974e+02,-5.654583309999999301e+02,-4.068585828333333438e+02,-1.219185723333333272e+03,-6.718362246666666238e+01,-5.977519768333332877e+02,5.005932709999999588e+02,2.455044601666666324e+02,2.329968653333333179e+02,4.396657963333332759e+02,1.685285181666666574e+02,-3.872504788333333181e+02,-3.657264863333333551e+02,-8.699418043333334083e+01,-1.049203087333333286e+02,1.015222274333333274e+02,-1.372427460499999796e+01,-5.487943776666665485e+01,2.034374899999999968e+02,-8.026662790000000314e+01,-1.249563916666666472e+02,1.546389061666666542e+01,-4.050203248333333050e+01,2.380665953333333391e+02,-3.188267521666666049e+00,2.251790361666666840e+01,3.922077421833332966e+00,-3.286763158333333479e+01,-5.245197133333333284e+01,3.793393385000000251e+01,-5.437221054999999126e+01,-2.088565592499999735e+00,4.023226704999999725e+01,-9.581668876666665113e+00,9.680631288333331952e+01,-6.608381273333332473e-01,2.325908989999999932e+01,1.141719036666666653e+01,1.246660293333333236e+01,1.337820371666666563e+00,-7.690918650000000412e+00,-1.206145956666666663e+01,-3.978375383333333293e+00,-2.178445483333333144e+01,8.609039436666665601e-01,1.096766344999999987e+01,-8.197835514999999518e+00,2.513355684999999795e+01,-5.860086116666666456e+00,6.149589951666666998e+00,-6.589232459999998959e+00,1.551550806499999879e+00,3.141627468333333173e+00,3.276856841666666575e+00,2.313903425999999930e-01,3.954957186666666624e-01,-7.408508038333332379e-01,-3.432405284999999751e+00,-4.794704474999999633e+00,4.683499730000000305e-01,5.225826569999999505e-01,9.969741964999997985e-02,3.215576124999999230e+00,-3.447346994999999303e+00,8.533124359999999520e-01,-5.019234166666667107e+00,-1.159922423333333008e-02,1.384802481666666640e+00,-1.030115596666666633e+00,1.445223434999999730e-02,3.944774293333332960e-01,-9.630197434999999972e-02,5.883594136666666641e-01,9.258711281666666126e-01,-8.797580076666665638e-01,-3.873931333333333060e-02,-9.629234878333332859e-02,-1.295823333333333327e+00,4.133788596666666537e-01,-5.784977483333333392e-01,-1.280105090000000168e+00,-4.780978186666666463e-02,-2.054129450000000023e+00,1.976490603666666568e-01,1.360617801999999821e-01,-9.814329748333333603e-02,-5.144895626666666777e-01,-4.629414124999999824e-01,-2.430458228333332860e-01,-1.555563606666666709e-01,-1.883036971666666656e-02,2.183654828333332909e-01,4.039206535000000042e-01,-1.556212306666666656e-01,2.412905703333333429e-01,-4.010935148333333311e-02,-5.884565981666665113e-01,2.063548924999999978e-01,-5.134826539999999273e-01,-4.447435543333333463e-02,-2.584049716666666496e-01,-5.501211494999999063e-01,-5.625261478333332815e-02,-1.375863786666666755e-01,-4.467689169999999876e-02,-3.204650838333333307e-01,-1.737766553333333075e-01,-1.645287353333333424e-01,-1.109928316666666630e-02],
    [-4.060892761666666775e+04,-4.071921473333332870e+03,1.648258870000000115e+03,-2.396568543333333423e+02,6.945896768333332147e+02,-1.234948826666666491e+03,-3.393353123333333315e+03,9.493304114999999683e+02,-9.306377153333332330e+01,-6.538458136666666860e+02,8.784430075000000215e+02,6.288144033333333027e+02,-5.884363254999999526e+02,-1.455524874166666507e+02,-1.158399051666666765e+03,1.452143564083333160e+01,-6.461119933333333165e+02,5.743024571666666134e+02,2.489926119999999798e+02,2.064863968333333446e+02,3.843711098333333211e+02,2.149082374999999843e+02,-4.733255159999999933e+02,-2.905940673333333280e+02,-6.763935246666665080e+01,-1.515081574999999816e+02,6.988785116666666397e+01,-4.694350143333333136e+01,-4.903940910000000031e+01,1.466233431666666434e+02,-9.823832369999998093e+01,-1.556738903333333042e+02,4.737405836666666659e+01,7.907785984999999584e+01,1.871483561666666446e+02,-1.901519874999999749e+00,1.088969709833333255e+01,-1.337580129999999912e+01,-4.649795625000000143e+01,-4.609145970000000148e+01,1.694164831666666515e+01,-6.971443978333333291e+01,-6.324032084999998915e+00,4.065340468333333490e+01,2.641163443333333305e+01,7.133357061666666254e+01,-7.998626796666666650e+00,1.165595315499999884e+01,1.144800301666666620e+01,1.291099404999999933e+01,-2.952482230166666444e-01,-9.125372170000000338e+00,-9.537035648333333171e+00,-8.177864848333333825e+00,-2.579610653333332948e+01,1.880266914999999761e+00,8.642575893333333426e+00,-3.400843886666666371e+00,1.847216881666666666e+01,-4.946750859999999861e+00,1.973578398333333039e+00,-7.056887658333333313e+00,7.025418256666664973e+00,2.965111976666666482e+00,4.358519913333333662e+00,1.227467998333333199e+00,8.795774006666665645e-01,-2.264261128333333317e-01,-3.450113243333333024e+00,-5.153399313333332898e+00,9.275778001666665773e-01,-3.108091386666666511e-01,2.527940268333333518e-01,1.940037066666666421e+00,-1.818064591666666452e+00,4.258080253333332843e-01,-4.642240976666666796e+00,2.474112166666666557e+00,1.622172261666666504e+00,-1.387924313333333437e+00,-2.020199236666666565e-01,6.647785994999999559e-01,2.785680011666666900e-01,7.602291668333331920e-01,9.246895401666664904e-01,-6.154404923333333111e-01,1.078700844666666686e-01,-1.783237284999999728e-01,-1.502088656666666466e+00,4.553142769999999340e-01,-7.976261991666666606e-01,-6.700299681666666007e-01,3.364275181666666337e-02,-1.676097969999999826e+00,9.167701694999998985e-01,2.737700253333332778e-01,-1.061529591666666578e-01,-5.293804753333333224e-01,-4.864528806666666011e-02,-3.210876160000000201e-01,-1.737279938333333162e-01,9.575584099999999432e-03,2.343254509999999902e-01,3.712551591666666262e-01,-8.341759601666667856e-02,3.326594573333333527e-01,-1.406994923333333147e-01,-6.450122358333333361e-01,2.320384191666666207e-01,-5.453844591666666686e-01,4.741713281666666557e-02,-2.725109378333333554e-01,-4.229317768333332728e-01,9.075405954999998803e-02,-8.201528675000001323e-02,-2.308205376666666239e-02,-3.437124294999999718e-01,7.978570479999998882e-03,-1.226086956666666561e-01,-2.142050756666666333e-02],
    [-4.043000883333332604e+04,-5.273527401666666265e+03,3.133733964999999444e+03,-5.860296653333333552e+02,1.187504756666666708e+03,-1.181814921666666578e+03,-2.818288219999999910e+03,8.627042754999999943e+02,-1.545435714999999846e+02,-3.242406501666666259e+02,1.112188906666666526e+03,1.068504067999999961e+03,-5.949325286666665988e+02,1.586556926333333095e+01,-1.076613293333333331e+03,9.043541723333332527e+01,-6.093226874999999154e+02,6.379422415000000228e+02,2.989516941666666412e+02,2.237547851666666645e+02,3.437051439999999616e+02,1.929928823333333412e+02,-4.679977541666666525e+02,-1.629000963333333232e+02,-3.297064193333333293e+01,-1.796161091666666607e+02,5.964421104999999557e+01,-7.272678038333333461e+01,-3.866998713333333626e+01,1.092991021666666711e+02,-1.396844145000000026e+02,-1.548919168333333403e+02,1.013716344666666487e+02,1.809684648333333143e+02,1.283066325000000063e+02,5.004004899999999090e+00,-7.049539116666666549e-01,-2.224129243333333505e+01,-5.800412716666666313e+01,-4.106131814999999108e+01,3.364369291666666761e+00,-8.362499253333334082e+01,-1.296562881666666556e+00,5.056913404999998818e+01,5.806641781666667157e+01,4.549503095000000030e+01,-1.180829085000000056e+01,4.761495263333332950e+00,1.148239551666666713e+01,1.160780444999999794e+01,-6.990480198333333117e-01,-1.039255521666666660e+01,-7.008364761666666887e+00,-1.109960741666666628e+01,-2.740412001666666697e+01,4.916718961666666665e+00,7.816872795000000096e+00,1.149596060000000142e+00,1.271507038333333206e+01,-3.372588004999999889e+00,-9.235265466666663092e-03,-7.738548171666666420e+00,1.194230131666666495e+01,2.161912868333333293e+00,4.868031773333333589e+00,2.061264344999999665e+00,1.242214939999999768e+00,5.641688773333333184e-01,-3.685499369999999608e+00,-4.739185034999999324e+00,1.809510274999999835e+00,-1.067994056999999941e+00,5.718756815000000104e-01,1.320661938333333341e+00,-2.175652390000000491e-02,3.517856644999999838e-01,-4.211063234999999239e+00,4.933400963333332889e+00,1.641319074999999739e+00,-1.355902603333333234e+00,-5.854774503333333158e-01,9.010969815000000604e-01,4.892734331666666048e-01,8.493577541666665898e-01,1.097043578333333436e+00,-5.114201181666666596e-01,4.217834603333332488e-01,-1.948459983333333256e-01,-1.641436086666666627e+00,4.963559629999999556e-01,-7.917123273333332989e-01,-4.546669218333333068e-02,1.576914568333333266e-01,-1.319684533333333132e+00,1.754110931666666540e+00,2.394349570000000038e-01,3.509954718166666959e-02,-4.979102301666666341e-01,2.287375123333333093e-01,-3.986065346666666231e-01,-1.741738363333333317e-01,-1.226204299333333303e-02,2.152104114999999762e-01,3.820649248333333192e-01,-4.496188495000000285e-02,4.399552354999999304e-01,-2.566289520000000213e-01,-6.517207949999999084e-01,2.578954251666666364e-01,-5.378916891666666311e-01,1.565606226666666767e-01,-2.718060084999999737e-01,-3.061490068333333481e-01,3.008078183333333100e-01,-1.158089253333333263e-01,3.381019779999999697e-02,-3.525626926666666772e-01,1.297500558333333220e-01,-1.224376309999999912e-01,-3.218640184999999737e-02],
    [-4.075032838333333348e+04,-6.593179521666666005e+03,4.293448964999999589e+03,-1.545537171666666609e+03,1.283809120000000121e+03,-1.194719875000000002e+03,-2.103739721666666355e+03,-6.694297023333334096e+01,-3.278792933333332940e+02,7.606761314499999571e+01,1.158658858333333228e+03,1.383329288333333352e+03,-7.155932671666665783e+02,-1.099932399500000031e+02,-1.102389201666666622e+03,2.131148976666666499e+02,-4.940801916666666216e+02,6.390815181666665694e+02,2.730218486666666422e+02,2.245855065000000081e+02,2.026124636666666561e+02,5.351972295000000202e+01,-3.741262639999999351e+02,-7.646033406666656873e-01,2.969316614999999615e+01,-1.864864013333333332e+02,5.708663998333332756e+01,-1.025173719999999946e+02,-3.709569676666666282e+01,6.580650835000000143e+01,-2.104434853333333422e+02,-1.157261161666666709e+02,1.547038318333333393e+02,2.517551491666666834e+02,4.814250049999999703e+01,1.557672560000000139e+01,-1.113205808666666741e+01,-2.215444901666666766e+01,-6.379881639999999265e+01,-3.832607705000000209e+01,-5.279711314999999239e+00,-9.481538158333333399e+01,1.448145743333333435e+01,5.778006688333332619e+01,8.206061424999998621e+01,1.252374593000000047e+01,-1.263539778333333174e+01,2.720243459999999835e+00,9.607108244999999158e+00,8.765440653333332222e+00,8.737166714999999861e-01,-9.731287951666667269e+00,-3.960245411666666548e+00,-1.174194089999999946e+01,-2.601346529999999646e+01,1.008462253666666797e+01,5.050965279999999780e+00,4.657509120000000280e+00,4.585169774999998893e+00,-1.190642203333333260e+00,-5.851965944999999447e-01,-7.089284693333332221e+00,1.564865281666666519e+01,3.197928913333333290e-01,4.757509924999999917e+00,2.763299711666666880e+00,1.809959306666666823e+00,1.788923541666666450e+00,-3.436072609999999639e+00,-3.560631693333332848e+00,3.059866853333333303e+00,-2.225320198333333277e+00,8.366374589999998612e-01,2.917147264916666871e-01,2.059168773333333480e+00,2.192896789999999874e-01,-3.066487958333333097e+00,6.952508673333332112e+00,1.368914984999999973e+00,-1.036449789833333135e+00,-1.100294371499999979e+00,1.051017218333333281e+00,5.130621391666666531e-01,8.546737204999999005e-01,1.401990521666666600e+00,-3.546822124999999826e-01,8.488847156666666782e-01,-1.134675305833333231e-01,-1.686833360000000059e+00,5.095883271666666881e-01,-8.077731978333332341e-01,7.241730566666666480e-01,1.380525295000000208e-01,-7.507039486666666761e-01,2.561174061666666280e+00,2.985109038333333062e-02,2.519200394999999704e-01,-3.884238973333333234e-01,3.537940406666666981e-01,-4.246812731666665952e-01,-1.680975419999999887e-01,-7.838366989999999423e-02,1.433928761666666829e-01,4.127132839999999581e-01,-5.481034893333333602e-03,5.484422569999999331e-01,-3.539626395000000092e-01,-5.689119323333332590e-01,2.839418768333333287e-01,-5.157152558333333303e-01,3.333254663333333756e-01,-2.885083069999999639e-01,-1.207281714499999908e-01,5.298684283333332523e-01,-2.026150443333333273e-01,1.011434383500000034e-01,-3.171247609999999773e-01,1.930789924999999907e-01,-1.562923238333333298e-01,-4.729308150000000044e-02],
    [-4.032198791666666511e+04,-5.960735156666666626e+03,5.668271981666666761e+03,-2.508004423333333307e+03,1.616253311666666377e+03,-1.072179473333333362e+03,-1.962477178333333086e+03,-1.051880193833333124e+03,-4.942644145000000435e+02,4.867680123333332745e+02,1.097048321666666652e+03,1.312370644999999968e+03,-7.296508005000000594e+02,-3.561713455000000295e+02,-1.053307261666666591e+03,3.439886953333333395e+02,-3.492471594999999525e+02,5.705972401666665519e+02,1.360855320166666615e+02,2.361707334999999830e+02,-1.156887851666666478e+01,-1.143790444333333340e+02,-2.555500358333333111e+02,1.536615518333333057e+02,9.716762894999999389e+01,-1.758016933333333043e+02,5.209949736666666098e+01,-1.304190541666666832e+02,-3.506589209999999923e+01,2.121893953333333016e+01,-2.846789106666666953e+02,-6.001658126666665538e+01,1.919712893333333170e+02,2.743502933333332976e+02,-3.498595211666665961e+01,2.459223368333332971e+01,-1.815317128333333230e+01,-1.515785754999999924e+01,-6.013349386666666874e+01,-3.725720668333333663e+01,-9.507516394999999676e+00,-1.027420024999999839e+02,3.315728701666667178e+01,5.979220778333332476e+01,8.959834851666666111e+01,-2.047129499999999780e+01,-1.078769560000000105e+01,1.886310103333333377e+00,6.114181138333332655e+00,5.443507018333332503e+00,3.948578308333333009e+00,-6.392627001666666864e+00,-1.746897674999999817e+00,-9.870677378333333252e+00,-2.261058985000000021e+01,1.605712971666666533e+01,1.103713135999999873e+00,5.144109146666666632e+00,-5.137765116666666465e+00,1.708375901666666641e+00,-1.885086028333333275e+00,-5.290895914999999228e+00,1.782059204999999835e+01,-1.914054441666666495e+00,4.056583344999999952e+00,3.291000233333333469e+00,2.584465605000000110e+00,2.882258688333333208e+00,-2.398963544999999975e+00,-1.815762620000000105e+00,4.448679263333333189e+00,-3.437079199999999446e+00,6.819290179999999424e-01,-1.214513571499999944e+00,4.292688189999999793e+00,-3.776147048333333145e-01,-1.361880535666666558e+00,8.335072781666665875e+00,9.873535546666666329e-01,-6.549016161666666447e-01,-1.575618769999999946e+00,1.019954498666666876e+00,4.033623431666666370e-01,7.613399444999999766e-01,1.685718318333333299e+00,-8.169290469999999915e-02,1.339081903333333212e+00,7.608714498333332688e-02,-1.617076668333333078e+00,5.098280791666665035e-01,-8.722840344999999163e-01,1.594927826666666437e+00,-7.104590113333332513e-02,-2.915219133333333407e-02,3.216471454999999757e+00,-2.729801381666666638e-01,4.475403089999999695e-01,-2.791705651666666621e-01,3.167094703333333539e-01,-3.909319563333333303e-01,-1.668147168333333208e-01,-1.696219778333333261e-01,2.167802169000000029e-02,4.491841756666666297e-01,3.217667831666666534e-02,6.365122463333333647e-01,-3.949453256666666245e-01,-4.150352476666666068e-01,3.203520884999999652e-01,-4.632669136666667242e-01,5.590712373333333041e-01,-2.948695543333333391e-01,1.210874881999999958e-01,7.490450861666666516e-01,-3.088729569999999480e-01,1.648350909999999891e-01,-2.623457704999999640e-01,1.860041516666666728e-01,-1.877412679999999889e-01,-5.607493249999999374e-02],
    [-3.937345165000000270e+04,-5.937600491666666130e+03,5.642187445000000480e+03,-3.333113793333332978e+03,2.005275270000000091e+03,-1.240289719999999988e+03,-1.843452231666666648e+03,-1.422906954999999925e+03,-5.536791059999999334e+02,8.786847119999999904e+02,9.795618061666666563e+02,1.021661651499999948e+03,-5.905217074999999340e+02,-4.100248818333333816e+02,-9.070241046666666307e+02,4.789819448333332730e+02,-2.057363424999999779e+02,4.555399501666665856e+02,-6.548629503333333446e+01,2.278742064999999570e+02,-2.001155228333333298e+02,-2.291188426666666658e+02,-1.760491728333333299e+02,2.884961458333333439e+02,1.549370306666666579e+02,-1.576236571666666464e+02,3.935198534999999964e+01,-1.478917566666666517e+02,-3.093054439999999516e+01,2.342984919999999693e+00,-3.259118851666667069e+02,-2.365035318333333247e+00,2.040576024999999731e+02,2.611677653333333637e+02,-1.074267837166666482e+02,2.675523389999999679e+01,-2.293677943333333147e+01,-3.999493685000000021e+00,-4.847533621666666193e+01,-3.404004580000000146e+01,-5.633071758333332291e+00,-1.023489963333333321e+02,5.047423126666666349e+01,5.429837468333332140e+01,8.655801718333331962e+01,-4.522309665000000223e+01,-6.249461205000000241e+00,5.846122359999998963e+00,9.622031175666665437e-01,2.458202526666666721e+00,8.134201198333334659e+00,-1.754415592500000010e+00,5.318925616666666384e-02,-5.573607954999999059e+00,-1.803703063333333034e+01,2.234121359999999967e+01,-3.364452570000000087e+00,4.924417323333333485e+00,-1.349218341666666632e+01,5.667504964999999117e+00,-2.121139014999999794e+00,-2.246785306666666759e+00,1.856957140000000095e+01,-3.836629984999999188e+00,3.152785058333333446e+00,3.718907043333333107e+00,3.189933728333333107e+00,3.600653878333333502e+00,-8.024990719999999245e-01,-1.267102454999999850e-01,5.898158541666665755e+00,-4.204847465000000284e+00,6.473640440000000273e-01,-2.345069691666666678e+00,6.773866359999999531e+00,-4.548467043333333515e-01,5.359645840000000216e-01,9.291423436666665481e+00,3.413777156666665813e-01,-4.474988256666665998e-01,-1.789769174999999990e+00,8.600408994999999557e-01,2.217540156666666651e-01,5.515480013333333709e-01,1.785404470000000021e+00,1.943446768333333408e-01,1.704062985000000197e+00,3.548946865000000006e-01,-1.366821756666666499e+00,6.286699930000000380e-01,-8.336556133333332674e-01,2.565950625000000151e+00,-1.656415969999999738e-01,5.947768311666665753e-01,3.794886184999999745e+00,-6.959259444999998934e-01,5.759045799999999993e-01,-2.358415128333333222e-01,2.568097241666666419e-01,-2.948712098333333143e-01,-1.700293824999999925e-01,-2.721947049999999813e-01,-1.209762936999999872e-01,4.532821363333332521e-01,3.668697239999999665e-02,6.858356774999999628e-01,-3.749976689999999779e-01,-2.240378764999999828e-01,3.783641028333333267e-01,-3.622065431666666169e-01,8.122389653333332848e-01,-2.124235466666666572e-01,3.312697441666666576e-01,1.000082927833333413e+00,-4.198784344999999529e-01,2.409758773333333104e-01,-2.177587166666666296e-01,1.657190961666666629e-01,-2.048093061666666770e-01,-5.856651698333333045e-02],
    [-3.866972831666666025e+04,-3.935616971666666359e+03,4.472339496666666491e+03,-3.511938721666666424e+03,2.599077589999999873e+03,-9.204259423333332961e+02,-2.572521531666666306e+03,-1.498423236666666526e+03,-3.588122554999999352e+02,1.047188454999999749e+03,9.958453126666665867e+02,5.078911029999999300e+02,-6.109787814999999682e+02,1.237798490666666567e+02,-6.310167876666666871e+02,5.919028194999999641e+02,-1.752516589999999894e+02,3.086651801666666302e+02,-2.603333754999999883e+02,1.564187578333333022e+02,-2.401426959999999724e+02,-1.952511636666666561e+02,-1.937811831666666649e+02,3.517818106666666154e+02,1.771022376666666389e+02,-1.508238321666666479e+02,4.958377881666666376e+00,-1.351756743333333191e+02,-2.260904058333333211e+01,1.682350910000000255e+01,-3.123911803333333523e+02,3.403627166666666426e+01,1.706526278333333266e+02,2.453709764999999834e+02,-1.298402191666666567e+02,2.002829048333333262e+01,-2.118846978333333197e+01,3.538023729999999478e+00,-3.093282118333333131e+01,-2.635495494999999977e+01,1.340565551616666573e+00,-9.304767268333333163e+01,6.193034104999999556e+01,4.084125006666666735e+01,8.675767553333332671e+01,-4.689769359999999665e+01,1.224885528499999987e+00,8.846105944999999693e+00,-3.251873295000000219e+00,2.099729438333333587e+00,1.220717928333333369e+01,1.369889153499999956e+00,1.482771414999999982e+00,-1.135878816666666680e+00,-1.415402660000000168e+01,2.743322643333333488e+01,-7.154956661666666662e+00,7.387413604999998995e+00,-1.730484498333333221e+01,1.045120705166666752e+01,-1.981203974999999673e+00,2.076078186666666658e-01,2.029119125000000068e+01,-4.469526681666666335e+00,2.473112856666666914e+00,4.223297135000000146e+00,2.955774961666666201e+00,3.615574894999999955e+00,8.571064448333332031e-01,7.992120241666667013e-01,7.020835168333332987e+00,-4.151577523333332742e+00,1.618862031666666423e+00,-2.891523556666666384e+00,9.290869210000000322e+00,5.999478026666666963e-01,1.637489721666666842e+00,1.070475643333333338e+01,-6.377955018333332504e-02,-6.584338481666666132e-01,-1.669137921666666413e+00,6.066656341666667451e-01,9.809360156666666053e-02,2.505641200000000013e-01,1.649470658333333395e+00,4.387094091666666196e-01,1.823449716666666554e+00,6.261835569999999462e-01,-1.000267250999999913e+00,1.002688423833333342e+00,-7.867774034999999166e-01,3.412499908333333387e+00,2.633389489999999888e-01,7.833558396666666646e-01,4.442662656666666265e+00,-9.907385129999999318e-01,6.239580876666666054e-01,-4.482932013333332799e-01,2.803533610000000231e-01,-2.081972434999999899e-01,-1.833390268333333628e-01,-3.469108471666666471e-01,-2.154675469999999815e-01,4.343658604999999784e-01,1.848333086666666819e-02,6.754433598333333677e-01,-3.075842873333333172e-01,-7.587400211666665839e-02,4.616169581666666466e-01,-2.427663373333333319e-01,1.023829638833333444e+00,4.327458821666666650e-02,4.384144969999999586e-01,1.254921339999999885e+00,-4.817676848333333206e-01,3.441744156666666221e-01,-2.799355686666666343e-01,1.660384093333333033e-01,-1.800821041666666733e-01,-4.296373761666666402e-02],
    [-3.861821756666666624e+04,-1.934155388333333349e+03,3.125565009999999802e+03,-3.242121746666666240e+03,2.722321341666666740e+03,-2.640318624999999884e+02,-3.542882121666666080e+03,-1.465183204999999816e+03,5.749670594999999196e+01,1.007468036333333202e+03,1.008575213999999960e+03,5.687866659999999541e+01,-7.359545420000000604e+02,7.329054401666667218e+02,-5.275497446666666974e+02,7.096061843333333172e+02,-2.090421368333333589e+02,1.403051121666666745e+02,-4.219802508333333435e+02,4.493934825000000188e+01,-2.677473991666666961e+02,-1.279111671666666581e+02,-2.475604376666666440e+02,4.039010019999999486e+02,1.806648603333333085e+02,-1.469196604999999920e+02,-3.629201441666666739e+01,-1.095962114999999955e+02,-2.126642418333333495e+01,3.162410778333332928e+01,-2.738224374999999782e+02,5.464120883333332301e+01,1.100511213999999995e+02,2.303039503333333187e+02,-1.147349993333333202e+02,9.362605563333332270e+00,-1.275198551666666624e+01,8.117336668333333449e+00,-1.236820689333333156e+01,-1.946487183333333348e+01,7.992988586666666784e+00,-7.922014458333333664e+01,6.686652251666666302e+01,1.971259714999999701e+01,9.162074554999999521e+01,-3.250302591666665819e+01,7.827621929999999395e+00,1.177313179999999804e+01,-6.537601694999999324e+00,4.297734373333333302e+00,1.543990319999999983e+01,3.318173461666666491e+00,2.331474561666666556e+00,3.461919854999999657e+00,-1.144660293333333279e+01,3.012035101666666392e+01,-1.237974625000000017e+01,1.285466680000000039e+01,-1.769861746666666846e+01,1.327174406666666684e+01,-1.082120527999999915e+00,1.818278074999999827e+00,2.118463006666666359e+01,-4.394522069999999836e+00,2.187115901666666584e+00,4.703379796666666834e+00,2.380318301666666692e+00,3.306465451666666944e+00,2.561109771666666646e+00,9.458694718333333640e-01,7.505283499999999997e+00,-4.047878891666666590e+00,3.703312999999999633e+00,-3.000480379999999947e+00,1.091329784999999930e+01,2.332526053333333405e+00,2.017348691666666305e+00,1.174635271666666725e+01,-4.141152233333332822e-01,-9.989803636666665376e-01,-1.395924669999999868e+00,3.492322576666666567e-01,4.081113004999999821e-02,-2.455867539999999696e-02,1.445314238333333279e+00,6.771142616666666614e-01,1.765485953333333358e+00,8.266474971666665228e-01,-5.589714338333332533e-01,1.600940210000000086e+00,-7.809608369999998523e-01,3.928608313333333157e+00,9.643384108333332705e-01,5.830399604999999541e-01,4.917219368333332952e+00,-1.176362741666666656e+00,6.779119433333332667e-01,-7.874821918333333448e-01,3.458499658333332727e-01,-1.447996394999999936e-01,-2.117398134999999848e-01,-3.928198853333332852e-01,-2.653585041666666200e-01,4.085738623333333153e-01,3.161656854999999721e-03,6.395756268333333550e-01,-2.111427471666666444e-01,6.941691719999999732e-02,5.590610021666666540e-01,-1.467554134999999871e-01,1.186201378333333167e+00,3.621932183333332889e-01,4.452577418333333314e-01,1.451444694999999951e+00,-4.858208105000000332e-01,4.617488060000000116e-01,-4.017646816666666787e-01,1.640240693333333277e-01,-1.496276866666666483e-01,-2.263132121666666316e-02],
    [-3.878103581666666287e+04,-4.843606833333333270e+02,3.196823151666666490e+03,-3.141777709999999388e+03,2.474045335000000250e+03,5.526473965000000135e+02,-3.311742809999999736e+03,-1.153062246666666624e+03,4.431741883333332908e+02,9.309757188333334170e+02,8.679131068333332450e+02,6.349849514999999656e+01,-6.816563306666666904e+02,8.320347468333333154e+02,-7.006489564999999402e+02,7.975182483333333039e+02,-2.519730726666666385e+02,-2.747321988499999534e+01,-5.316639238333332287e+02,-3.586127586666666645e+01,-4.278200196666666102e+02,-1.139900473333333082e+02,-3.067388594999999896e+02,4.995669963333332930e+02,1.736576749999999834e+02,-1.529776568333333273e+02,-6.231534328333333406e+01,-1.007607033333333106e+02,-3.170752493333333177e+01,1.371580830499999948e+01,-2.294464490000000296e+02,5.784857358333333366e+01,4.670549954999999187e+01,2.032031866666666815e+02,-9.512884009999999080e+01,-1.811225099666666338e+00,-7.743613526666665692e+00,1.215407121666666868e+01,-7.011385349999998962e-01,-1.844673650000000009e+01,1.282930133333333345e+01,-6.196898818333332315e+01,6.489203965000000096e+01,-7.601672588333332925e+00,9.416231746666666425e+01,-1.969031336666666832e+01,1.123565984999999934e+01,1.532695988333333226e+01,-9.398132356666666354e+00,6.073144010000000037e+00,1.670592236666666608e+01,4.166228706666666781e+00,1.821844783333333329e+00,9.017766113333333777e+00,-9.273031763333332123e+00,3.003501856666666825e+01,-2.029293419999999770e+01,1.914622988333333353e+01,-1.854217475000000093e+01,1.246694846666666479e+01,2.786570628849999731e-01,3.090452518333332677e+00,1.835298873333333347e+01,-4.082010758333332490e+00,2.119607763333333228e+00,4.723416046666666368e+00,1.810408934999999886e+00,2.811960001666666820e+00,4.423803033333332912e+00,5.472399188333333386e-01,7.288512784999999994e+00,-4.403635338333333316e+00,6.176393819999999479e+00,-3.354285461666666190e+00,1.100559903333333267e+01,3.706482056666666303e+00,2.162722203333332871e+00,1.117234470000000002e+01,-1.137689736000000007e+00,-1.316185761666666787e+00,-1.003432778000000081e+00,2.429435476666666482e-01,-2.800416856666666440e-03,-2.469203664999999881e-01,1.257830198333333316e+00,9.192018126666665623e-01,1.563118695000000002e+00,9.101925001666666404e-01,-1.706931999999999894e-02,2.189463951666666741e+00,-8.699360011666665837e-01,4.031097341666666445e+00,1.469881078333333368e+00,2.373420696666666552e-01,4.881236649999999955e+00,-1.362520341666666468e+00,6.889135644999999641e-01,-1.025190837999999882e+00,3.836793406666666462e-01,-5.828373514999999477e-02,-2.018289194999999814e-01,-4.001932694999999485e-01,-3.019544889999999926e-01,3.785950598333333028e-01,-6.748369543333332041e-03,5.832380046666665319e-01,-1.124270805333333068e-01,2.673701646666666321e-01,6.275843348333333127e-01,-8.752684113333332461e-02,1.305055868333333535e+00,5.933552948333333799e-01,3.959804104999999907e-01,1.525804324999999961e+00,-4.465360166666666464e-01,5.273700031666666010e-01,-4.795870049999999551e-01,1.261249956666666561e-01,-1.317758701666666421e-01,-1.206443979999999826e-02],
    [-3.765891834999999992e+04,-6.018350621666667166e+02,2.771255831666666381e+03,-3.126832624999999553e+03,2.021215513333333092e+03,1.119716798333333145e+03,-2.236639546666666320e+03,-4.191850416666666774e+02,7.240838033333333215e+02,8.901312733333331835e+02,6.095140723333332744e+02,3.380998244999999542e+02,-4.276495538333333002e+02,5.652860538333333125e+02,-1.121894389999999930e+03,8.406830391666666173e+02,-2.571924900000000207e+02,-1.321192591666666658e+02,-5.655953153333333603e+02,-7.698037761666665801e+01,-6.109521089999999504e+02,-2.052782223333333036e+02,-3.604719440000000077e+02,6.070478403333332835e+02,1.590472749999999849e+02,-1.555759511666666697e+02,-5.312717079999999470e+01,-1.049154553333333268e+02,-4.739736939999999521e+01,-1.759846998333333090e+01,-1.925510171666666679e+02,4.988210448333332891e+01,-2.095401676666666546e+00,1.609659369999999967e+02,-7.507719734999999162e+01,-1.340415673333333402e+01,-8.228126726666666002e+00,2.048204783333333268e+01,2.484893744999999932e+00,-1.850587128333333098e+01,1.871440766666666633e+01,-4.216092946666666563e+01,6.287243621666666371e+01,-3.768320824999999985e+01,9.033830231666667032e+01,-1.220035201666666502e+01,7.793175516666666525e+00,1.694943028333333501e+01,-1.272951485000000105e+01,5.701105638333332948e+00,1.673651419999999845e+01,3.742203031666666568e+00,1.976626298333333143e+00,1.469198166666666339e+01,-5.919621281666666235e+00,2.954883498333332881e+01,-2.920558959999999615e+01,2.429076031666666324e+01,-1.896504389999999773e+01,7.946096234999998842e+00,1.329733471666666444e+00,4.447192515000000235e+00,1.238528561666666405e+01,-3.876919508333333209e+00,1.840769510000000109e+00,4.034874826666666081e+00,1.127920859999999914e+00,2.654227146666666481e+00,5.902083648333332988e+00,4.359448139999999583e-01,6.897658899999999704e+00,-4.967715860000000205e+00,8.386023278333333053e+00,-3.705829634999999733e+00,9.464183169999998313e+00,4.334396484999999188e+00,2.188413779999999864e+00,8.963224626666665529e+00,-2.202301061666666726e+00,-1.914078871666666792e+00,-5.398306858333332681e-01,2.163336663333333409e-01,-2.050350439999999996e-01,-4.721487601666666811e-01,1.116113329999999904e+00,1.030513261666666569e+00,1.358292990000000033e+00,8.427670319999998050e-01,6.151048881666666412e-01,2.657984849999999621e+00,-9.210679713333332908e-01,3.793790744999999909e+00,1.758438051666666446e+00,-6.078409223333332279e-02,4.287025426666666306e+00,-1.571798613333333261e+00,4.808806669999999839e-01,-1.106906158333333501e+00,3.766700768333333116e-01,7.476146686666666763e-02,-1.508264524999999856e-01,-4.114365901666666159e-01,-3.362235913333333492e-01,3.162440296666666484e-01,-4.708284786666666610e-02,5.156469768333332704e-01,-8.223088069999999472e-02,5.308235285000000303e-01,6.534670871666666825e-01,-4.356099909999999742e-02,1.373788865000000081e+00,7.341743080000000532e-01,3.136799396666666295e-01,1.448635376666666641e+00,-4.040383679999999811e-01,5.025295046666666821e-01,-4.874129061666666596e-01,6.765147508333332893e-02,-1.073094223333333347e-01,-1.476019463333333274e-02],
    [-3.668571666666666715e+04,-6.448375746666666828e+02,2.661477613333333466e+03,-3.836085399999999936e+03,1.764638626666666596e+03,1.391167111666666642e+03,-1.382494630000000143e+03,1.288897773833333247e+02,6.974852613333333693e+02,7.590590583333332688e+02,6.664444634999999550e+01,5.187235504999999876e+02,-1.734373809999999878e+02,3.368251543333333302e+02,-1.198370388333333267e+03,7.908503921666666656e+02,-2.602567149999999856e+02,-2.402878904999999747e+02,-5.119140390000000025e+02,-1.101579636666666602e+02,-6.186625138333332643e+02,-2.975402653333333660e+02,-3.803469436666666752e+02,6.567005123333332222e+02,1.391707119999999804e+02,-1.468926849999999718e+02,-1.400513368833333061e+01,-9.711113488333333521e+01,-6.027546996666666246e+01,-2.233590363333333073e+01,-1.650344673333333390e+02,3.723352091666666297e+01,-4.083921238333333292e+01,8.008419858333333252e+01,-5.932667996666665999e+01,-2.024280286666666484e+01,-9.880347006666667653e+00,3.866799561666666563e+01,4.108809638333333680e+00,-1.396824351666666786e+01,2.866273403333333292e+01,-2.778329921666666635e+01,6.397838283333332754e+01,-6.632584888333332174e+01,6.769503486666667413e+01,-1.054205523333333261e+01,7.488679990000000064e-01,1.477043703333333369e+01,-1.522648343333333365e+01,3.777585013333332853e+00,1.776330879999999723e+01,2.442323091666666723e+00,4.129823859999999236e+00,1.908966796666666710e+01,-2.357281491666666451e+00,3.002977793333333167e+01,-3.594661398333332869e+01,2.573133579999999654e+01,-1.810803094999999985e+01,3.306546013333333089e+00,1.800655708333333216e+00,4.771972544999999677e+00,5.236600719999999320e+00,-3.799151338333333072e+00,9.830442858333332534e-01,2.942894661666667133e+00,-1.351828766666666737e-01,3.043395474999999628e+00,6.291691338333333050e+00,1.291351715000000011e+00,6.818468998333332642e+00,-5.364053876666666554e+00,1.010704713500000018e+01,-3.901495999999999409e+00,7.341032601666666935e+00,4.013046566666666592e+00,1.781804323333333384e+00,5.746776183333333066e+00,-3.105936778333333148e+00,-2.709395801666666603e+00,-1.272228603999999708e-01,3.994666931666666226e-02,-6.234849321666666722e-01,-8.179006246666665758e-01,1.035769376666666686e+00,8.187388633333332333e-01,1.423929644999999855e+00,7.448197671666666464e-01,1.178677809999999937e+00,3.073362766666666523e+00,-8.310474378333331247e-01,3.453502233333332949e+00,1.829047101666666286e+00,-2.446262091666666638e-01,3.262770336666666715e+00,-1.679506948333333138e+00,-2.447785546666664258e-03,-1.027751985833333270e+00,1.943581034999999624e-01,2.231251329999999755e-01,-9.397836504999999840e-02,-4.785026676666666590e-01,-3.685293216666666871e-01,2.209467864999999920e-01,-1.553338406666666671e-01,4.676668183333332895e-01,-1.235597823333333262e-01,8.062537533333332673e-01,6.590754646666666661e-01,2.328024008000000034e-02,1.372986796666666676e+00,8.089123964999999084e-01,2.348394724999999794e-01,1.227213254999999892e+00,-3.818051819999999652e-01,3.814931991666666855e-01,-4.267203055000000078e-01,-4.457191344999999333e-02,-6.583456988333333260e-02,1.442913650000000100e-04],
    [-3.563720709999999963e+04,-8.172324708333333092e+02,2.351190698333333330e+03,-4.108293366666666770e+03,1.266160754999999881e+03,1.345432215000000042e+03,-8.798784776666666403e+02,4.138495178333333229e+02,6.148867010000000164e+02,5.192746938333332309e+02,-6.524737769999999273e+02,3.991654076666666242e+02,-3.323005356666667076e+00,2.768226093333333324e+02,-9.215774519999998802e+02,6.385898610000000417e+02,-2.446447411666666483e+02,-3.187045590000000175e+02,-5.211890826666666499e+02,-1.623764769999999942e+02,-4.547520778333333169e+02,-3.801163276666666206e+02,-3.546910398333333205e+02,5.641273866666666663e+02,9.334545905000000232e+01,-1.165888941666666625e+02,6.112946811666665781e+01,-9.539197711666665214e+01,-6.881584780000000023e+01,9.786795896666665717e-01,-1.630554850000000044e+02,3.701757388333333409e+01,-1.220494329999999792e+02,-1.388248708166666745e+01,-4.925561356666666768e+01,-2.592074133333333563e+01,-6.509154049999999359e+00,6.466648239999999248e+01,1.126345050666666481e+01,1.449911073333333134e-01,3.970626861666666230e+01,-2.546820589999999740e+01,7.446824499999999603e+01,-1.015034639166666466e+02,3.751392650000000373e+01,-1.192316301666666689e+01,-6.677656003333332535e+00,1.241624154999999874e+01,-1.637474261666666564e+01,1.352528801000000058e+00,1.796326518333333055e+01,3.226298061666666328e+00,1.061554809499999941e+01,2.172936126666666823e+01,-1.999149978166666619e-01,3.309953319999999621e+01,-4.171956670000000145e+01,2.685499259999999921e+01,-1.762111566666666462e+01,1.038646832666666686e+00,3.366667341666666591e+00,3.720556825000000067e+00,-1.414499882166666778e+00,-3.667036786666666437e+00,-7.863095218333333580e-01,1.142703161500000064e+00,-1.491737771666666657e+00,4.376024573333332945e+00,5.618388311666667079e+00,3.270738399999999935e+00,7.100850474999999662e+00,-5.620983356666665820e+00,1.230590088333333298e+01,-4.439264256666666242e+00,6.239876469999999564e+00,3.413107740000000057e+00,1.390320348333333289e+00,2.344278284999999684e+00,-3.404691009999999629e+00,-3.326986934999999868e+00,2.626833673333333063e-01,-5.125461870000000975e-01,-1.149171553333333318e+00,-1.322956143333333223e+00,9.862101074999999328e-01,2.162634419166666599e-01,2.092050298333333114e+00,5.814168728333333203e-01,1.681062436666666660e+00,3.584260919999999739e+00,-7.636254586666667565e-01,3.491878918333333193e+00,1.722110211666666668e+00,-1.739531559999999977e-01,2.116107846666666514e+00,-1.544197441666666615e+00,-5.821202599999999450e-01,-8.078566124999998488e-01,-7.264387329999999476e-02,3.990316338333332880e-01,-9.435385301666665558e-02,-5.446683991666667612e-01,-4.442103731666666167e-01,5.633716441666666158e-02,-3.615162923333332667e-01,5.333543164999999808e-01,-2.424887533333333067e-01,1.084709793333333172e+00,6.474300246666666592e-01,1.010686486999999995e-01,1.430868789999999890e+00,8.173046219999999806e-01,2.652647096666666537e-01,9.502381096666666638e-01,-3.188196318333332835e-01,2.268154851666666361e-01,-3.287630138333332841e-01,-1.717705916666666388e-01,8.644553286666664497e-04,9.081115693333332434e-03],
    [-3.527756411666666099e+04,-1.447990289999999902e+02,1.864124449999999797e+03,-4.150231728333333194e+03,9.633315751666665392e+02,1.492467309999999770e+03,-3.251735561666666854e+02,8.559350576666665802e+02,5.635669739999999592e+02,3.263690686666666352e+02,-1.268082113333333155e+03,1.777741786666666712e+02,1.968945459999999912e+02,2.778003833333333432e+02,-5.203816084999999703e+02,4.618602231666666285e+02,-2.304217104999999890e+02,-3.746596751666666592e+02,-5.974839673333333394e+02,-2.034957429999999761e+02,-2.550206636666666498e+02,-4.578124454999999671e+02,-2.970372808333333410e+02,4.598349186666665673e+02,3.180220521666666400e+01,-8.977621018333333325e+01,1.344534756666666624e+02,-1.150631135000000000e+02,-7.875682241666666528e+01,2.281709986666666623e+01,-1.807802154999999971e+02,4.606398184999999756e+01,-2.103685266666666678e+02,-7.966867316666666454e+01,-4.019487781666666848e+01,-3.341236021666666289e+01,-2.997464321666666986e+00,8.740356731666666690e+01,1.690062530000000152e+01,1.477571041666666574e+01,4.663157998333333865e+01,-3.166693456666666151e+01,8.943486611666666874e+01,-1.380618838333333258e+02,1.640428765000000055e+01,-9.843694838333334474e+00,-1.657416209999999879e+01,1.079826181666666685e+01,-1.674126528333333397e+01,-7.722663681666667168e-01,1.680242031666666591e+01,5.109951194999999835e+00,1.777541664999999682e+01,2.282290388333333198e+01,-3.743225008333332937e-01,3.691698111666666904e+01,-4.811990851666665492e+01,2.968524083333333152e+01,-1.620242881666666790e+01,-2.923698101833333007e-01,6.153230271666665807e+00,1.944032371666666537e+00,-5.707734258333333699e+00,-3.301117916666666652e+00,-2.518991801666666586e+00,-8.670333039999998936e-01,-2.455471486666666259e+00,5.770749359999999939e+00,4.569135944999999310e+00,5.022297373333334036e+00,7.277279486666666131e+00,-6.345008506666666825e+00,1.476790145000000010e+01,-5.034610215000000721e+00,5.965272136666667002e+00,3.110062811666666427e+00,1.145799514999999991e+00,-2.956158620000000070e-01,-3.188936383333333069e+00,-3.528176075000000189e+00,6.866214848333334064e-01,-1.109194341666666528e+00,-1.588153688333333147e+00,-1.766392830000000025e+00,9.003465293333332564e-01,-4.856170295000000192e-01,2.891347138333333344e+00,3.191998571666666562e-01,1.965129799999999705e+00,4.053017491666667027e+00,-8.590973256666666336e-01,3.839253126666666738e+00,1.587057098333333194e+00,3.691507641499999770e-02,1.185544973333333196e+00,-1.242558330000000044e+00,-1.022016399166666645e+00,-4.907375646666665703e-01,-3.249205243333332938e-01,5.841657944999999463e-01,-1.229204974999999894e-01,-5.627963748333333349e-01,-5.169275660000000050e-01,-1.228851333499999948e-01,-5.877372486666666562e-01,6.494052826666666389e-01,-3.943291644999999956e-01,1.306616853333333328e+00,6.064271723333334307e-01,1.020561915833333305e-01,1.559098586666666453e+00,7.774951894999998503e-01,3.636565124999999732e-01,7.018345041666665951e-01,-2.105850355000000174e-01,1.161067808333333118e-01,-2.166493196666666454e-01,-2.749991363333332828e-01,6.860807550000000421e-02,-9.815232338333333695e-03],
    [-3.629356523333332734e+04,1.327840306666666720e+03,6.203265086666666548e+02,-4.146078111666666700e+03,1.120338124999999991e+03,2.011307551666666768e+03,-6.542288609999999949e+01,1.199418518333333168e+03,6.641684523333333345e+02,3.132022743333333210e+02,-1.513381163333333234e+03,3.860163769999998884e+00,4.268394703333332814e+02,2.655779616666666811e+02,-2.373492403333333129e+02,3.633916386666666654e+02,-2.059656428333333054e+02,-3.895582954999999856e+02,-6.520017285000000129e+02,-1.752233491666666509e+02,-1.242556163333333075e+02,-5.437104329999999663e+02,-2.206991964999999709e+02,4.661145864999999731e+02,-2.537958443333333136e+01,-7.301361641666666458e+01,1.760335779999999772e+02,-1.462388758333333385e+02,-7.800846533333333355e+01,1.758310246666666643e+01,-2.074143508333333443e+02,5.413963986666665562e+01,-2.501010206666666704e+02,-8.952562526666666542e+01,-1.878392908333333366e+01,-4.420227598333332963e+01,-7.356557499999999417e-01,9.828211503333332644e+01,1.350384406666666592e+01,2.390851809999999844e+01,4.342572941666666964e+01,-3.847220741666667010e+01,9.903784263333332660e+01,-1.612190493333333450e+02,1.344165811666666599e+01,4.548317357666666894e+00,-3.098849981666666409e+01,6.815639368333333614e+00,-1.702317098333333334e+01,-1.739405454999999767e+00,1.460252619999999979e+01,5.829975870000000171e+00,2.177026358333333178e+01,2.130640528333333350e+01,-1.696343006666666486e+00,3.783574003333333025e+01,-5.309291483333332451e+01,3.302039891666666449e+01,-1.062691914000000004e+01,-3.362258636666666245e+00,8.594916966666666269e+00,-5.783592926333334105e-01,-6.250468149999999667e+00,-2.675024768333333469e+00,-3.373729056666666004e+00,-2.552705473333333419e+00,-2.682803366666666633e+00,6.269738043333333621e+00,3.382123556666666531e+00,5.572460130000000511e+00,6.570698656666666082e+00,-7.426871048333334002e+00,1.616713633333333178e+01,-4.770499324999999402e+00,5.114604791666667261e+00,3.266787248333332894e+00,5.581046606666665300e-01,-1.580766953333333058e+00,-2.625789418333333458e+00,-3.228867139999999303e+00,1.091889111666666690e+00,-1.442391546666666802e+00,-1.834531791666666578e+00,-1.842144069999999800e+00,7.327139263333333208e-01,-1.025934020999999863e+00,3.255870963333333368e+00,-1.083663340048333229e-01,1.861115923333333200e+00,4.099197371666666534e+00,-1.061670394999999933e+00,3.908429218333333566e+00,1.562878343333333309e+00,5.630653221666666319e-02,6.184468123333333178e-01,-9.234514594999998494e-01,-1.180402586666666753e+00,-1.797117043333333331e-01,-5.239617276666667101e-01,7.184895454999999931e-01,-1.552766618333333293e-01,-5.153640815000000153e-01,-5.017598653333332770e-01,-2.494854566666666329e-01,-7.330480356666666530e-01,7.039354208333332696e-01,-5.366669421666665496e-01,1.361624631666666474e+00,4.953942001666666317e-01,-2.736615458333332973e-02,1.603048264999999750e+00,7.131216283333332573e-01,3.835799511666666550e-01,4.955807791666666517e-01,-1.138943336666666667e-01,7.706453133333332484e-02,-1.341635628333333330e-01,-3.464747771666666365e-01,1.157314938333333237e-01,-6.601648829999999524e-02],
    [-3.758922249999999622e+04,1.564252936666666301e+03,-8.847830796666667084e+02,-4.085706641666666656e+03,1.550191588333333129e+03,2.560849306666666962e+03,-1.281172696666666582e+02,1.420948956666666618e+03,7.537236880000000383e+02,6.072131643333332249e+02,-1.356461169999999811e+03,-3.084876448333333343e+01,8.287513498333332791e+02,1.915573846666666498e+02,-2.606768751666666617e+02,2.915172046666666574e+02,-1.324748073333333309e+02,-3.152701089999999340e+02,-6.362227864999999838e+02,9.240740643333332116e+00,-9.717697096666665857e+01,-6.181492333333333136e+02,-1.443527518333333433e+02,5.694064668333332975e+02,-8.299783513333333929e+01,-7.394277286666665816e+01,1.963073829999999873e+02,-1.780072011666666469e+02,-4.588253435000000025e+01,-2.101473784999999950e+01,-2.068079371666666475e+02,5.216054336666665847e+01,-2.274410791666666398e+02,-5.065891301666666635e+01,1.201937111333333164e+01,-5.584801139999999009e+01,-8.059827523333332522e+00,9.735423831666666672e+01,-5.717068320000000536e-01,2.598177250000000171e+01,2.766966044999999852e+01,-3.080595648333333259e+01,9.741629826666665792e+01,-1.607592593333332900e+02,2.361476723333333538e+01,2.957653404999999935e+01,-4.741324524999999568e+01,1.210154331961666774e+00,-1.567717073333333033e+01,-3.956771056666666286e+00,1.082574964999999878e+01,3.760080651666666718e+00,2.010114864999999895e+01,1.605852946666666270e+01,-1.542301248333333152e+00,3.361596193333333105e+01,-5.304525266666666283e+01,3.345534628333332705e+01,-7.138022413333333649e-01,-9.128143338333330803e+00,1.037893575000000013e+01,-3.211344505000000016e+00,-4.089655511666666854e+00,-1.426722893333333353e+00,-3.356959701666666795e+00,-4.083287211666666749e+00,-2.665229418333333378e+00,5.125161233333333399e+00,1.774772739999999960e+00,4.434121094999999180e+00,4.430574033333333439e+00,-8.039617110000000011e+00,1.509163419999999789e+01,-3.069956700000000094e+00,2.528314576666666369e+00,3.831891224999999679e+00,-4.752644074999999857e-01,-1.923147873333332925e+00,-2.085503686666666745e+00,-2.632791078333333257e+00,1.456079519999999849e+00,-1.280129864999999922e+00,-1.888933849999999914e+00,-1.631329846666666583e+00,4.330779054999999156e-01,-1.404759443333333246e+00,2.764763866666666736e+00,-7.546015131666666820e-01,1.407825049999999800e+00,3.375006376666666696e+00,-1.137833094999999961e+00,3.152798786666666686e+00,1.666783873333333332e+00,-3.403616194999999900e-01,2.964715265000000266e-01,-8.086744290000000834e-01,-1.150166943333333247e+00,5.782679266666666817e-02,-6.482617306666667023e-01,7.619648321666665503e-01,-1.140474365000000018e-01,-3.826751800000000037e-01,-3.842173081666666601e-01,-2.716987931666666745e-01,-7.691734848333332542e-01,5.921218493333332278e-01,-6.432966308333333272e-01,1.189663264999999859e+00,2.850120963333332980e-01,-2.572472574999999928e-01,1.406334276666666661e+00,6.412295063333333101e-01,1.939238883333332941e-01,2.939244963333332850e-01,-1.201879441666666715e-01,5.661484414999999604e-02,-1.057206391666666578e-01,-3.965174351666667096e-01,1.324872900000000076e-01,-1.533642889999999870e-01],
    [-3.965521768333333603e+04,1.641342286666666496e+03,-1.960796486666666624e+03,-4.198358949999999822e+03,1.846565056666666578e+03,2.134890416666666624e+03,-1.996333436666666614e+02,9.196123766666665915e+02,7.236806366666666008e+02,9.035263499999999794e+02,-1.265191253333333407e+03,7.736813440000000242e+01,1.127314300000000003e+03,5.306127077166666339e+01,-3.026058368333333419e+02,2.391202101666666806e+02,-5.815654768333332925e+01,-2.258931665000000066e+02,-5.403808665000000246e+02,2.629244011666666552e+02,-1.082949074999999937e+02,-5.969673988333332773e+02,-7.025487608333332901e+01,6.768631188333332602e+02,-1.240699660000000080e+02,-7.747926263333333452e+01,2.111008316666666360e+02,-1.913428823333333355e+02,5.154208821666665941e+00,-5.508700548333332847e+01,-1.751785089999999911e+02,4.494357763333333367e+01,-1.707943441666666331e+02,-2.974123879999999609e+00,4.435825848333332999e+01,-6.140702843333333050e+01,-1.613804814999999948e+01,9.634942494999998530e+01,-1.676562219999999925e+01,2.287924414999999811e+01,1.105896929833333253e+01,-1.387355193333333148e+01,8.912719088333332706e+01,-1.407484574999999722e+02,3.335820593333333761e+01,5.686409386666666421e+01,-5.817412338333333111e+01,-4.667552598333333691e+00,-1.232451183333333233e+01,-6.184070044999999460e+00,8.417751720000000049e+00,4.558031436500000200e-01,1.482223676666666634e+01,9.428784491666666767e+00,-4.711589795000000191e-01,2.710235493333333423e+01,-4.773530924999999314e+01,2.982261004999999798e+01,1.014616432833333093e+01,-1.460851093333333139e+01,1.126543748333333284e+01,-6.542151135000000117e+00,-1.802544974999999994e+00,-1.850389707799999783e-01,-2.964635013333333458e+00,-5.268058901666666571e+00,-2.611150726666666699e+00,3.182550169999999845e+00,-1.521320539999999888e-02,2.381854269999999829e+00,1.994101716666666579e+00,-7.839293136666665163e+00,1.229833586666666534e+01,-4.837062167833332538e-01,-9.870419531666666524e-01,4.537427171666665870e+00,-2.032287181666666331e+00,-2.188837548333332883e+00,-1.602853969999999739e+00,-1.877686991666666527e+00,1.518716471666666568e+00,-9.084484464999997844e-01,-1.914532046666666432e+00,-1.354631803333333329e+00,1.791014858333333237e-01,-1.657765951666666515e+00,1.813871638333333092e+00,-1.323616048333333461e+00,7.932086921666665624e-01,2.287915753333333413e+00,-9.280363896666666834e-01,1.805517266666666565e+00,1.865775358333332967e+00,-1.022623812833333368e+00,8.351027356666665402e-02,-8.773398344999998599e-01,-1.035830831666666674e+00,2.344104721666666613e-01,-7.952758736666666328e-01,6.926239573333332622e-01,-4.839247483333333072e-02,-2.459043518333333123e-01,-2.351312661666666859e-01,-1.964795576666666377e-01,-7.288100318333332606e-01,3.938325553333333340e-01,-6.860971788333333210e-01,8.773539828333333235e-01,6.871629276666665898e-02,-4.534579579999999388e-01,1.038910180000000016e+00,5.994390069999999682e-01,-1.112374204166666491e-01,1.125826642000000016e-01,-2.139523429999999893e-01,1.467171533166666472e-02,-1.053608233333333255e-01,-4.646410349999999800e-01,1.202669208333333323e-01,-2.364586629999999856e-01],
    [-3.995602111666667042e+04,1.015589221666666617e+03,-1.534144765000000007e+03,-4.489095221666666475e+03,1.675032248333333428e+03,1.487948694999999816e+03,-6.125816926666666262e+01,6.073341916666666407e+01,4.711927579999999125e+02,9.932342721666666421e+02,-1.196749144999999999e+03,1.184033435000000054e+02,1.102431451666666590e+03,-2.402386184999999728e+02,-3.024090603333333434e+02,1.870426216666666335e+02,-2.472953618333333026e+01,-1.759463128333333088e+02,-4.687532858333332797e+02,4.084641154999999912e+02,-1.353179708333333338e+02,-4.926570326666666233e+02,-7.003130146666666178e+01,7.249165410000000520e+02,-1.379339868333333357e+02,-7.631006963333332749e+01,2.049619180000000256e+02,-1.943878546666666693e+02,3.666192198333332897e+01,-6.399477124999999234e+01,-1.321292943333333483e+02,1.246871889999999894e+01,-1.195335776666666732e+02,3.408821841666666330e+01,5.673566579999999249e+01,-5.685345918333332804e+01,-1.753251276666666669e+01,9.472557283333333089e+01,-2.658821221666666190e+01,1.717283333333333317e+01,2.077922681666666715e+00,-2.747874636666666204e-01,7.413997031666666260e+01,-1.155031748333333326e+02,3.632572268333332488e+01,7.176917885000000297e+01,-6.075957018333333082e+01,-1.189267711666666649e+01,-7.284564223333332755e+00,-6.183299758333332896e+00,8.453779921666665587e+00,-8.080045353333333846e-01,9.891692178333332919e+00,4.106692814999999719e+00,-1.148362698166666584e+00,2.105032636666666690e+01,-4.038553781666666964e+01,2.342220386666666698e+01,1.632235215000000039e+01,-1.740989076666666335e+01,9.699459154999999555e+00,-1.004958066999999922e+01,-1.722582253333333258e+00,6.251224718333332486e-01,-2.240543534999999586e+00,-5.589368376666666194e+00,-2.200496698333333168e+00,1.605668284999999917e+00,-1.414616803333333284e+00,-9.609147099999992836e-03,5.124901023333332528e-01,-7.130352946666667080e+00,9.185044238333333055e+00,1.581022989999999906e+00,-3.969881108333333408e+00,4.379085341666666409e+00,-3.718102614999999389e+00,-3.179993506666666470e+00,-1.204341541666666515e+00,-1.281819708333333363e+00,1.199668358333333407e+00,-5.726934023333332124e-01,-1.855982614999999836e+00,-1.146668388333333288e+00,2.890665829999999881e-02,-1.739598431666666611e+00,9.283458314999999406e-01,-1.503517848333333129e+00,2.151543691666666647e-01,1.384577596666666688e+00,-5.166826500000000211e-01,4.842442211666666552e-01,1.837400268333333253e+00,-1.741655276666666641e+00,-2.069850888333333305e-01,-9.575237011666667408e-01,-1.028459563333333104e+00,4.492400403333333125e-01,-9.341263614999999465e-01,5.289945841666665594e-01,-2.599718716666666457e-02,-1.487856286666666694e-01,-1.279986674999999963e-01,-1.012523817166666590e-01,-6.412245843333332918e-01,2.576125601666666709e-01,-6.423980015000000376e-01,5.538874146666665776e-01,-5.291689503333332767e-02,-5.081738470000000119e-01,6.683555821666665731e-01,5.502446426666666168e-01,-4.046235263333333165e-01,-5.089210354999999797e-02,-2.704056161666666402e-01,-9.738846206666666727e-02,-6.358122986666665810e-02,-5.369965639999999540e-01,9.519332780000000493e-02,-3.083991741666666786e-01],
    [-3.913358106666666572e+04,3.354847201166666650e+02,-1.837301342783333382e+02,-4.460375123333333249e+03,1.535054368333333287e+03,1.028726459999999861e+03,2.068024813333333327e+02,-6.279118525000000091e+02,2.267007221666666510e+02,9.415701169999999820e+02,-1.123680018333333237e+03,2.343798414999999977e+02,9.248297309999999243e+02,-5.155133288333333894e+02,-1.588698249999999916e+02,1.090398064833333223e+02,-2.262537149999999997e+01,-1.650139781666666750e+02,-3.923124821666666548e+02,4.256970318333333125e+02,-1.141644413333333290e+02,-3.420716161666666721e+02,-1.707701356666666470e+02,6.535024418333332505e+02,-1.495571013333333212e+02,-7.186056926666665845e+01,1.963627533333333020e+02,-1.832759744999999896e+02,4.531702800000000053e+01,-3.827773808333333250e+01,-8.828833646666666368e+01,-4.329823676666666188e+01,-1.116769158333333394e+02,6.187059656666666285e+01,6.859238041666665708e+01,-4.899754671666666184e+01,-1.506453734999999838e+01,9.750596281666666698e+01,-2.775292519999999996e+01,1.254838081666666483e+01,3.998695633333332999e+00,5.717407279999998870e+00,5.938200936666665797e+01,-9.603104648333332705e+01,3.544426281666666512e+01,7.984707853333333105e+01,-5.271797411666666733e+01,-2.068208753333333760e+01,-1.610863259666666547e+00,-5.133216536666666663e+00,1.010143330333333189e+01,-2.826001793333333123e-01,6.911331013333332329e+00,2.307928774999999710e+00,-3.676400034999999900e+00,1.916077818333333127e+01,-3.278640986666666635e+01,1.877666213333333189e+01,1.804439508333333109e+01,-1.599580309999999983e+01,6.661698173333332917e+00,-1.426326259999999913e+01,-4.088784223333332690e+00,1.331631395000000051e+00,-1.713986243333333270e+00,-5.579181179999999962e+00,-1.958866796666666632e+00,8.046405018333333548e-01,-1.956565258333333279e+00,-2.023300216666666262e+00,7.072714900000000027e-01,-6.059611788333332250e+00,7.433451528333333336e+00,2.570854744999999664e+00,-5.559149458333333627e+00,3.714011169999999584e+00,-5.486179206666666808e+00,-4.709695224999999930e+00,-9.780033514999998401e-01,-7.913496673333333398e-01,7.696195244999999296e-01,-4.001253541666666136e-01,-1.834245251666666521e+00,-1.165650351666666751e+00,2.877737499999999740e-03,-1.758577694999999608e+00,4.027999278333333488e-01,-1.315259906666666589e+00,-1.524384313333333185e-01,1.024625684999999953e+00,-8.634144240999999664e-02,-4.397124821666666405e-01,1.699982156666666633e+00,-2.406531246666666846e+00,-5.555216364999999712e-01,-9.773061521666666085e-01,-1.099951058333333176e+00,6.693578894999999696e-01,-9.699402219999999630e-01,3.468764151666666740e-01,-2.030850121666666688e-02,-1.089787976666666547e-01,-9.778946191666665344e-02,-1.917238355833333560e-02,-5.984145208333333521e-01,2.347069113333333235e-01,-5.758255096666666795e-01,3.244493866666666726e-01,-6.333607220000000981e-02,-4.211702520000000227e-01,4.073622418333333051e-01,5.324056529999998677e-01,-6.218596674999999907e-01,-1.606997796666666811e-01,-2.592937086666666779e-01,-2.308414909999999820e-01,4.202196959999999690e-03,-5.773928368333333117e-01,9.658841068333332003e-02,-3.670827761666667355e-01],
    [-3.928391654999999446e+04,-1.093479619500000126e+03,3.201861586666666426e+02,-3.704824261666666189e+03,1.606672819999999774e+03,7.200384234999999080e+02,2.116331024999999784e+02,-1.083305839999999989e+03,3.251939414999999940e+02,7.895963296666666338e+02,-1.072660091666666631e+03,3.845384924999999612e+02,8.406393521666666402e+02,-6.763668373333333648e+02,1.251444205833333285e+02,4.736329489999999964e+01,-4.432475491666666301e+01,-1.704625178333333224e+02,-3.455775239999999826e+02,3.965908883333333392e+02,-4.464950248333332894e+01,-1.804888721666666527e+02,-2.945036174999999616e+02,4.464563981666666450e+02,-1.605692163333333440e+02,-6.258861171666666934e+01,2.118845751666666501e+02,-1.683489236666666500e+02,5.700933226666666087e+01,2.092700821666666489e+00,-3.780898534999999328e+01,-8.814352685000000065e+01,-1.714788134999999727e+02,1.036595388666666651e+02,9.726584309999998368e+01,-4.124457739999999717e+01,-7.281547299999998835e+00,1.096081418333333204e+02,-2.099258258333333416e+01,1.390314111666666541e+01,9.338192048333333162e+00,8.289265990000000528e+00,5.011121208333333499e+01,-9.064528100000001132e+01,4.105729603333332989e+01,8.961064700000000016e+01,-3.071224068333332724e+01,-2.871438131666666393e+01,2.875667398333333402e+00,-1.919435927833333055e+00,1.242689430000000073e+01,1.672125409999999812e+00,5.536624838333332299e+00,2.977424819999999528e+00,-6.251763221666665871e+00,2.054282611666666369e+01,-2.613467778333333058e+01,1.957132696666666760e+01,1.848192996666666588e+01,-9.025321931666665520e+00,4.326800698333332917e+00,-1.877260448333333187e+01,-7.222050004999998940e+00,1.753893213333333367e+00,-1.203683826666666512e+00,-5.706058425000000156e+00,-1.778835554999999902e+00,5.089510626666666759e-01,-1.702745796666666589e+00,-3.094816449999999719e+00,1.595471951666666444e+00,-4.497895423333332587e+00,7.281140743333333276e+00,2.799678128333333404e+00,-5.039856023333333823e+00,3.409266309999999578e+00,-7.044049720000000292e+00,-5.667229664999998917e+00,-8.944491571666666196e-01,1.988043335999999939e-01,3.317367626666666292e-01,-4.425572873333333268e-01,-1.998257871666666574e+00,-1.223984816666666697e+00,8.378206756666665977e-02,-1.686966899999999825e+00,2.688407601666666924e-01,-1.092495749999999877e+00,-1.012804192000000131e-01,9.968374229999998892e-01,1.975151250000000136e-01,-8.462493463333333743e-01,1.682486923333333273e+00,-2.877668413333332786e+00,-7.727684788333332166e-01,-8.393665016666667089e-01,-8.639292611666665733e-01,8.334060585000000465e-01,-7.975893248333333352e-01,1.644176201666666670e-01,-5.913887859999999996e-02,-1.572131210000000112e-01,-1.069137674999999926e-01,6.126673676666666291e-02,-5.720871193333333382e-01,3.045336799999999733e-01,-5.402973788333332861e-01,2.558965148333333661e-01,-6.180652081666666159e-02,-2.586718879999999610e-01,2.284793436666666400e-01,5.675366473333333106e-01,-7.127230050000000761e-01,-1.682064205000000090e-01,-1.882144206666666597e-01,-2.270486493333333244e-01,6.882463229999999377e-02,-5.306575128333332891e-01,1.204804263333333347e-01,-3.964163421666666576e-01],
    [-3.942447673333333660e+04,-3.017001145000000179e+03,-6.461294579999999996e+02,-3.315311480000000302e+03,1.823404504999999972e+03,6.708829445000000078e+02,7.030712183333332632e+02,-1.331676691666666557e+03,4.470769639999999185e+02,6.749147411666665448e+02,-1.094902469999999994e+03,7.249762376666666341e+02,9.141322788333333165e+02,-8.671084224999999606e+02,2.258563079999999559e+02,2.981818439999999182e-01,-7.484569193333332748e+01,-2.128490108333332955e+02,-3.788639898333333349e+02,3.314669196666666267e+02,5.293407528333332834e+01,-8.003842271666667330e+01,-3.582293169999999805e+02,3.075704106666666462e+02,-1.477411793333333208e+02,-6.424328401666667787e+01,2.445662713333333329e+02,-1.759197775000000092e+02,6.657594084999999495e+01,4.631960396666666213e+01,2.273955309999999841e+01,-9.654892729999998835e+01,-2.458452969999999880e+02,1.836011579999999981e+02,1.241090809999999891e+02,-2.709399569999999713e+01,1.424201354500000072e+00,1.265112723333333236e+02,-1.122214752333333365e+01,2.150798066666666486e+01,1.350736329999999796e+01,1.434134753333333379e+01,4.782205859999999831e+01,-9.339990646666666407e+01,5.884284746666666166e+01,9.759627604999998596e+01,-2.541447615000000049e+00,-3.378597129999999993e+01,5.807355198333333135e+00,3.883425826666666580e+00,1.504310083333333203e+01,4.793048421666666670e+00,6.402678186666665994e+00,3.761707886666666223e+00,-8.009234434999999763e+00,2.244615126666666427e+01,-2.267845626666666448e+01,2.483864131666666708e+01,1.922640596666666823e+01,1.339439710000000228e-01,4.014142291666666473e+00,-2.191676474999999868e+01,-9.154667991666666893e+00,1.385978498333333420e+00,-6.203171926666666003e-02,-5.477440270000000666e+00,-1.239367038333333282e+00,8.136500398333332829e-01,-1.582815369999999611e+00,-3.634804529999999367e+00,2.010571269999999799e+00,-3.391789928333333037e+00,7.529711341666667224e+00,2.864939705000000281e+00,-2.758914923333333213e+00,3.546522836666666123e+00,-7.749115926666664933e+00,-5.074022354999999429e+00,-1.295139493333333114e+00,2.117336743333333438e+00,-1.742524703999999702e-01,-5.271617141666666839e-01,-2.216903961666666589e+00,-1.109899131666666650e+00,2.960161988333332994e-01,-1.624182608333333278e+00,3.342792919999999501e-01,-1.106321163333333191e+00,2.523669191666666478e-01,8.538608513333333372e-01,2.404486478333333066e-01,-8.090367798333333305e-01,1.709556748333333376e+00,-3.071598204999999915e+00,-6.945169246666667018e-01,-6.805963724999999354e-01,-4.353639206666666539e-02,1.032318993666666795e+00,-3.872509584999999643e-01,-2.603622744999999766e-02,-1.680082251666666637e-01,-2.990408408333333212e-01,-1.264485905000000132e-01,1.365403913333333441e-01,-4.968859771666666592e-01,4.441424209999999539e-01,-5.649582946666665828e-01,3.306989651666666363e-01,-1.077908904166666459e-01,-1.343569486666666424e-01,7.868416293333332923e-02,5.799437299999999906e-01,-6.945326446666667541e-01,-7.437865541666666136e-02,-1.312761376666666813e-01,-8.211350756666667763e-03,1.625458045000000018e-01,-3.862228388333333040e-01,1.144883226666666698e-01,-4.195322271666667158e-01],
    [-3.862171265000000130e+04,-4.059352303333333111e+03,-1.389716470000000072e+03,-3.395094259999999849e+03,1.919085573333332832e+03,6.714174540000000206e+02,7.565338325000000168e+02,-1.527580915000000005e+03,4.801283869999999752e+02,4.920768079999999713e+02,-1.125934338333333471e+03,8.960664871666665476e+02,9.901986783333333051e+02,-1.304138824999999997e+03,4.513567328833332937e+01,1.978414815333333188e+00,-1.266356088333333219e+02,-2.930610381666666626e+02,-4.767523654999999962e+02,2.105265624999999545e+02,6.332984506666666391e+01,-9.580851726666665513e+01,-3.434011218333333204e+02,2.471271763333333240e+02,-1.067744564333333273e+02,-7.167185223333332544e+01,2.611479778333333002e+02,-1.886637288333333515e+02,6.133440554999999961e+01,7.379835926666665102e+01,5.869847028333333583e+01,-7.719488939999999388e+01,-3.169610796666667056e+02,2.674407711666666501e+02,1.232157996666666548e+02,-9.935062498333332215e+00,1.178038464999999846e+01,1.395729919999999993e+02,1.382056953333333338e+00,3.049621991666666787e+01,1.649689036666666553e+01,1.901308846666666597e+01,4.859251785000000012e+01,-9.966332184999998844e+01,7.624903849999999750e+01,9.641787893333332704e+01,2.274355921666666802e+01,-4.252190391666666613e+01,6.885232743333332905e+00,1.128140797333333190e+01,1.804640621666666789e+01,8.782175004999999146e+00,9.552343759999999406e+00,5.286962958333332629e+00,-8.182628906666664648e+00,2.376386688333333552e+01,-2.155762499999999804e+01,3.028532068333333171e+01,1.775968651666666531e+01,9.051274149999997576e+00,1.838214044999999741e+00,-2.295123209999999858e+01,-9.514416541666665950e+00,2.977254572833333279e-01,1.454316384999999823e+00,-4.578375173333332881e+00,-3.674281779999999942e-01,2.039160303333333424e+00,-1.242587160000000024e+00,-3.357270399999999100e+00,2.080220366666666543e+00,-2.637272010000000222e+00,7.684094634999999229e+00,2.487876541666666164e+00,3.073606496666666521e-01,2.850939503333333569e+00,-7.155591199999999930e+00,-3.666408183333333071e+00,-1.791916990000000043e+00,4.496035290000000018e+00,-7.373495288333333786e-01,-6.345244226666666432e-01,-2.305375693333333142e+00,-8.840399620000000125e-01,6.897454174999999577e-01,-1.508771848333333443e+00,6.087180298333332296e-01,-1.177192534999999873e+00,7.628735134999998779e-01,6.933973894999998500e-01,1.126489928499999904e-01,-4.735345759999999848e-01,1.498769885000000190e+00,-2.842194494999999765e+00,-4.616747229999999536e-01,-5.522075251666667128e-01,1.056490074166666737e+00,1.288373705000000147e+00,2.715700206666666477e-02,-1.982264378333333243e-01,-3.308274873333333366e-01,-4.688894395000000048e-01,-1.556482211666666560e-01,2.003589456666666768e-01,-4.039604230000000129e-01,6.150391101666666804e-01,-6.016863390000000145e-01,4.776413421666665937e-01,-1.455638428333333456e-01,-4.213070846666666647e-02,-2.692784078333333372e-02,5.538453258333333462e-01,-5.489608166666666289e-01,5.822229089999999413e-02,-9.132278248333333681e-02,3.141406168333332749e-01,2.860030136666666389e-01,-2.304478871666666429e-01,8.014305611666666662e-02,-4.374050179999999788e-01],
    [-3.781445381666666799e+04,-3.302197239999999510e+03,-2.225158038333333025e+03,-3.597162543333332906e+03,1.872389043333333120e+03,2.376386343333333286e+02,2.688218553333333034e+02,-8.968592031666665889e+02,5.801788693333332958e+02,9.130436999999999159e+01,-9.943043358333333117e+02,7.948868983333333063e+02,1.058407368333333352e+03,-1.878680201666666562e+03,-2.205659718333332933e+02,1.275922585333333217e+02,-2.558987391666666440e+02,-3.677764559999999392e+02,-5.681240859999999202e+02,3.696518266999999724e+01,-5.496447516666665933e+01,-1.734652481666666688e+02,-2.367238163333333318e+02,1.762097706666666568e+02,-4.448735773333333299e+01,-8.655142113333333498e+01,2.297469361666666714e+02,-1.964730068333333293e+02,3.268752764999999982e+01,7.569132308333333015e+01,5.421341155000000356e+01,-4.145233104999999085e+01,-3.822462774999999624e+02,3.201445348333332959e+02,9.422864113333332625e+01,-2.476252744999999922e-01,2.551192703333332901e+01,1.390397664999999847e+02,7.769701570000000501e+00,3.444905046666666948e+01,1.783170686666666782e+01,1.768261871666666707e+01,4.597147865000000166e+01,-1.061452073333333317e+02,8.435755636666667101e+01,9.009988656666666884e+01,3.771357916666666199e+01,-5.201459871666666146e+01,5.024487920000000329e+00,2.014497135000000227e+01,2.150245519999999999e+01,1.140129339999999836e+01,1.383884943333333339e+01,6.957470073333333005e+00,-6.367716253333332688e+00,2.279517149999999859e+01,-2.107840810000000076e+01,3.244080773333332957e+01,1.493906033333333205e+01,1.651178081666666486e+01,-2.575264699999999962e+00,-2.085223410000000044e+01,-7.607325759999999271e+00,-9.820415288333332882e-01,3.319329323333333193e+00,-2.799628604999999659e+00,1.020801352833333286e+00,4.168104098333333063e+00,-6.158961384999999122e-01,-2.150889468333332832e+00,1.927124201666666536e+00,-1.852742624999999865e+00,7.287739484999999462e+00,1.729409158333333307e+00,3.570289836666666439e+00,1.285954647333333201e+00,-5.215628413333333491e+00,-2.091326779999999719e+00,-1.911402186666666614e+00,6.393755291666666452e+00,-1.188863881666666567e+00,-7.356428188333332674e-01,-2.157851583333333156e+00,-3.905082205000000029e-01,1.261371521666666773e+00,-1.286711984999999947e+00,9.953558746666665291e-01,-1.119075974999999890e+00,1.228019596666666491e+00,5.892464161666666200e-01,-2.476557566666666432e-01,8.636600680000000585e-02,1.051020937333333238e+00,-2.199078518333332788e+00,-2.069775178333332910e-01,-4.986742134999999632e-01,2.009403299999999781e+00,1.447816371666666546e+00,2.866491840000000013e-01,-3.258831991666666372e-01,-5.396121061666666607e-01,-6.073983616666667196e-01,-1.395166740000000072e-01,2.594811394999999576e-01,-3.131311793333333426e-01,7.506628731666665777e-01,-6.015258329999999543e-01,5.826223569999999796e-01,-1.442242108333333106e-01,-4.749466956666666129e-02,-7.821140261666667537e-02,4.958392866666666565e-01,-3.032606904999999853e-01,1.661752751666666639e-01,-7.999045881666665136e-02,6.061785988333333597e-01,3.761383201666666509e-01,-9.645340844999999996e-02,2.810247973333333121e-02,-4.251730718333333048e-01],
    [-3.657553284999999596e+04,-2.900096301666666932e+03,-1.147769899500000065e+03,-3.268794213333333118e+03,1.809866624999999885e+03,-1.078594008999999971e+02,-2.575060218333333069e+02,-4.343561258333333086e+01,7.974254236666665747e+02,-2.430835238333332882e+02,-7.387448054999999840e+02,5.792662046666666811e+02,1.095865008333333208e+03,-2.288408229999999548e+03,-5.776364318333332903e+02,2.880039803333333452e+02,-3.869536748333332525e+02,-4.669510204999999132e+02,-6.093828353333333325e+02,-1.031877844833333313e+02,-1.933529098333333138e+02,-3.161779104999999959e+02,-8.668154431666667392e+01,-7.074788466666665165e+00,-9.542718306666664319e+00,-1.107708413333333226e+02,1.447049091666666527e+02,-2.013756478333333462e+02,9.041074531666666303e+00,6.498856390000000260e+01,1.497968247000000019e+01,-1.527241180333333226e+01,-4.671796883333332744e+02,3.195845354999999586e+02,3.922223906666666693e+01,-6.401960888333332989e+00,3.187701563333333254e+01,1.247335081666666667e+02,4.643736458333333594e+00,3.626205038333333164e+01,1.738449623333333349e+01,1.501647966666666534e+01,3.691087220000000002e+01,-1.158874331666666677e+02,7.513400123333332203e+01,7.881590541666666638e+01,4.536989581666666282e+01,-5.660057246666666231e+01,1.675394971666666510e+00,2.561802013333333150e+01,2.471277491666666748e+01,1.170422103333333297e+01,1.722968184999999863e+01,8.031005543333332497e+00,-1.940852487666666404e+00,1.988740341666666467e+01,-2.039728184999999883e+01,2.954475203333333155e+01,1.051134020833333338e+01,2.433150981666666723e+01,-7.044452373333332851e+00,-1.491593931666666606e+01,-4.847219761666665683e+00,-1.370112008333333353e+00,4.576019844999999364e+00,-6.183791266666667230e-01,2.327025566666666379e+00,5.864112285000000035e+00,4.439177023333333583e-02,-2.717207139999999743e-01,1.886300229999999800e+00,-7.489812966666665739e-01,6.195414969999998966e+00,5.121399023333332856e-01,7.159244088333333700e+00,-9.376254796666665392e-01,-1.772767991999999904e+00,-1.329773788333333373e+00,-1.561117204999999730e+00,7.055853714999999582e+00,-1.215147099999999813e+00,-7.767529484999998735e-01,-1.780108611666666674e+00,1.349448515666666626e-01,1.651070250000000073e+00,-1.038760231499999964e+00,1.330052423333333067e+00,-8.209466899999999789e-01,1.629431741666666600e+00,4.933804195000000004e-01,-7.547820718333332346e-01,8.675165548333334531e-01,3.351539814999999756e-01,-1.162483028499999849e+00,-1.879557829999999874e-01,-4.941266939999999774e-01,2.423659334999999970e+00,1.398229468333333170e+00,3.772663339999999810e-01,-3.469214596666666539e-01,-6.800981851666666467e-01,-6.620363271666666050e-01,-9.478569129999998844e-02,2.903055696666666519e-01,-2.535315728333333296e-01,7.722895936666667183e-01,-5.316757071666666778e-01,6.243211471666666457e-01,-1.149871038333333262e-01,-1.314896996666666817e-01,-7.050640794999998850e-02,3.910484291666666556e-01,1.038031441666666457e-02,1.679699678333333168e-01,-7.826581966666666668e-02,7.568833055000000476e-01,3.922168206666666324e-01,1.337236385666666638e-02,-1.689103587833333184e-02,-3.380379494999999901e-01],
    [-3.498276928333333490e+04,-2.635020986666666886e+03,-4.115749113333332616e+02,-2.913114379999999983e+03,1.941038598333333084e+03,7.248366246666665802e+01,-8.291888880000000199e+02,-5.456100470999999175e+01,8.815159436666665442e+02,-2.842634393333333378e+02,-2.534436969999999860e+02,3.858934203333333244e+02,1.103175256666666655e+03,-2.452022348333333412e+03,-7.796249114999999392e+02,3.615066463333333218e+02,-4.419490429999999606e+02,-4.911131469999999695e+02,-5.758163185000000794e+02,-1.549595780000000218e+02,-2.686314438333333214e+02,-4.511322013333332848e+02,1.051860052499999938e+02,-2.512320053333332908e+02,-1.463033055000000004e+01,-1.425103239999999971e+02,6.058803028333333174e+01,-2.011482761666666477e+02,9.332568831666666398e+00,2.834038676666666134e+01,-2.149592894999999970e+01,1.359682027166666707e+01,-5.540745538333333116e+02,2.884121966666666026e+02,-2.649050888333333020e+01,-1.857350860000000026e+01,2.199465946666666483e+01,1.031896273166666589e+02,-3.122434088333332802e+00,4.344254071666667016e+01,6.269205024999999765e+00,1.732217548333333212e+01,3.327378641666666681e+01,-1.221126913333333164e+02,5.356425476666667151e+01,6.120017285000000129e+01,4.513009424999999908e+01,-5.591776370000000185e+01,-3.902830783333333109e-01,2.417329508333333266e+01,2.377572116666666346e+01,1.016783485500000062e+01,2.049837490000000173e+01,6.623883213333332520e+00,3.024141754999999598e+00,1.719140684999999991e+01,-1.780125726666666708e+01,2.462949894999999856e+01,3.576359353333332880e+00,3.021525669999999764e+01,-8.666941768333332519e+00,-6.356551155000000008e+00,-1.836627558333332910e+00,-1.049916765166666766e+00,4.664541136666666254e+00,3.900143381666666409e-01,2.499082251666666643e+00,6.669447761666667418e+00,2.823897664999999724e-01,1.386243765000000128e+00,1.362104806666666557e+00,4.520091686666666275e-01,5.164852189999999510e+00,-1.350115935666666545e+00,9.676271811666666167e+00,-3.244556428333333020e+00,2.865592408333332841e+00,-1.098114594999999971e+00,-1.138170146666666716e+00,6.446457374999999601e+00,-9.759188131666667321e-01,-6.802806996666665995e-01,-1.278538100000000011e+00,2.881287221666666287e-01,1.685834821666666539e+00,-8.592922169999999138e-01,1.559211471666666515e+00,-7.064439336666666902e-01,1.886557958333333396e+00,3.682060578333333778e-01,-1.216056176666666655e+00,1.567069536666666485e+00,-5.341719676666665251e-01,1.140098239999999818e-01,-2.218643623333333148e-01,-5.289905901666666077e-01,2.172729966666667067e+00,1.142098193333333178e+00,3.949352768333332930e-01,-2.656793613333333082e-01,-6.624372628333332624e-01,-5.695335486666666114e-01,-5.152110053333332912e-02,2.534896405000000019e-01,-2.155627661666666417e-01,7.192461651666666178e-01,-4.791504769999999636e-01,6.272735824999999821e-01,-9.461676444999998770e-02,-2.196532599999999891e-01,-8.567105581666664693e-03,2.385363244999999521e-01,3.189053944999999946e-01,1.080805884500000008e-01,-7.763770953333332114e-02,7.618991373333332540e-01,3.127140208333333282e-01,9.087800593333333898e-02,-1.689448567333333429e-02,-1.889154671666666563e-01],
    [-3.389835039999999572e+04,-3.690286453333333156e+03,-1.263165390000000116e+03,-3.086453213333333224e+03,1.682683383333333268e+03,1.850474138333333087e+02,-1.122223614999999882e+03,-6.925949591666665128e+02,6.465635574999998880e+02,-2.182744073333333006e+02,2.047349678333333145e+02,2.427134519999999611e+02,1.163969918333333453e+03,-2.195040401666666639e+03,-7.075896045000000640e+02,3.302778748333333851e+02,-4.391630521666666027e+02,-4.454662864999999670e+02,-4.561430986666666740e+02,-1.282618979999999738e+02,-2.349940833333333217e+02,-5.065831671666666125e+02,2.159053691666666737e+02,-5.197834560000000010e+02,-3.269854563333333175e+01,-1.706023238333333438e+02,4.990547780000000877e-01,-1.865258306666666499e+02,2.487942598333333066e+01,-3.933795601666666641e+01,-4.330237100000000083e+01,3.102226094999999972e+01,-6.219636981666667452e+02,2.519878586666666536e+02,-5.923815781666665714e+01,-2.503861906666666570e+01,1.953972141666666662e+00,8.054608586666667236e+01,-1.293745451666666568e+01,5.339576206666666280e+01,-1.704515620000000098e+01,1.976468673333333470e+01,3.727608576666666096e+01,-1.216073434999999847e+02,3.148096493333332901e+01,4.618073386666666380e+01,3.772834393333333480e+01,-5.441061021666666164e+01,-2.453678084666666703e-01,1.729988374999999934e+01,1.929939048333333318e+01,7.026188993333333244e+00,2.273530514999999852e+01,2.801837925000000062e+00,5.779865803333333218e+00,1.640834466666666458e+01,-1.384383203333333334e+01,2.045566473333333235e+01,-3.265921248333333082e+00,3.192664669999999916e+01,-8.450305721666666159e+00,2.765530924999999751e+00,1.165795029333333233e+00,-5.971364173333333358e-01,3.681790020000000219e+00,4.142301096666665960e-02,1.579287239999999759e+00,6.595087789999999117e+00,1.113878483033333283e-01,2.091857529999999965e+00,7.620872038333333931e-01,1.320199489999999809e+00,4.472887218333333692e+00,-3.491637479999999627e+00,1.029922179999999976e+01,-5.085993831666665521e+00,7.435883599999999483e+00,-1.028400596666666722e+00,-9.066521963333332712e-01,4.869631486666667008e+00,-7.594536728333332043e-01,-4.805500266666666298e-01,-8.322688479999998945e-01,7.323624136166666243e-02,1.465756986666666650e+00,-6.704753226666666510e-01,1.580611301666666524e+00,-8.401144768333332902e-01,1.931640204999999666e+00,2.648748414999999579e-01,-1.567147289999999860e+00,1.991920951666666717e+00,-1.223464943333333332e+00,1.415731203333333132e+00,-2.109180096666666560e-01,-6.548206258333333363e-01,1.530014886666666518e+00,6.841860569999999031e-01,4.314959708333333532e-01,-1.576666668333333576e-01,-4.961088631666666915e-01,-3.677147000000000054e-01,-2.674720066666666507e-02,1.592622228333333279e-01,-1.566358849999999747e-01,6.355681675000000030e-01,-4.918054261666666704e-01,5.902803186666666369e-01,-5.994830734999999355e-02,-2.704401301666666257e-01,9.389261743333332522e-02,8.738355025000001108e-02,5.926749396666666225e-01,3.141601768333333183e-02,-1.125488081666666668e-01,6.952104811666667272e-01,1.571062126666666614e-01,1.624656444999999783e-01,5.719173678333332872e-02,-2.922755751666666554e-02],
    [-3.536589134999999806e+04,-3.954776088333333064e+03,-2.484141741666666348e+03,-3.292704404999999952e+03,7.453079563333333226e+02,-2.590744908333332930e+01,-6.976614573333333738e+02,-2.157148518333333413e+03,3.893576596666666774e+02,-4.660064419999999927e+02,3.976727716666666197e+02,1.045788284833333392e+02,1.187857826666666597e+03,-1.722250823333333301e+03,-6.636052554999998847e+02,2.805948356666666541e+02,-5.008647564999999986e+02,-3.742985171666666702e+02,-3.458280195000000390e+02,-5.199992936666666310e+01,-1.260730362500000012e+02,-5.061464943333332940e+02,1.821132233333333375e+02,-6.207712989999999991e+02,-3.522445660000000345e+01,-1.939323608333333482e+02,-2.483023890000000122e+01,-1.709678284999999960e+02,5.100278391666667233e+01,-1.104230821666666600e+02,-6.004443318333333934e+01,3.990697294999999656e+01,-6.213418004999999766e+02,2.425254843333333099e+02,-2.215080463666666333e+01,-2.174802306666666496e+01,-1.202882669999999976e+01,6.265280083333333039e+01,-2.330652901666666565e+01,6.180146579999998835e+01,-4.370018068333332906e+01,1.487589766666666691e+01,4.758158771666666809e+01,-1.119648630000000082e+02,2.046357528333333420e+01,4.737934218333332836e+01,2.820703491666666451e+01,-6.514368853333331799e+01,1.076211004499999957e+00,1.166148019999999974e+01,1.326119196666666689e+01,3.165617568333333409e+00,2.266894628333333372e+01,-2.750109763333332680e+00,4.653390124999999600e+00,1.725420180000000059e+01,-1.122383270000000088e+01,1.706281800000000004e+01,-5.661106993333333115e+00,2.970511098333333067e+01,-1.224367971666666755e+01,8.024878811666667389e+00,3.951325961666666053e+00,-5.682799336666666257e-01,2.718020466666666746e+00,-1.215118656666666519e+00,2.991861617166666765e-01,5.873334658333333458e+00,-7.667547684999997948e-01,1.734614818333333197e+00,-6.453402573333329173e-03,1.190844475000000013e+00,3.747993624999999440e+00,-4.986174054999999328e+00,9.644160396666666912e+00,-6.710413478333332904e+00,9.890660460000001208e+00,-7.028668153333333946e-01,-9.344392440000000022e-01,3.369196124999999764e+00,-7.748910309999998969e-01,-2.665747851666666612e-01,-5.684772470000000189e-01,-2.183108608333333422e-01,1.203512233333333459e+00,-5.063966786666665998e-01,1.485708416666666754e+00,-1.262807303333333353e+00,1.716906255000000048e+00,2.992663393333332977e-01,-1.822668873333333162e+00,2.260269376666666385e+00,-1.532578316666666440e+00,2.388082091666666518e+00,-8.093392318333332558e-02,-8.614987983333333155e-01,1.055121341666666490e+00,3.183718238333332895e-01,4.577439806666666611e-01,-1.002581200999999866e-01,-2.976717368333333114e-01,-1.309233188833333339e-01,2.273842271999999831e-02,6.052434510000000156e-02,-3.268084991833333786e-02,5.864710033333333516e-01,-5.676105569999999600e-01,5.011389434999999892e-01,5.552739878333332740e-02,-3.093111946666666223e-01,2.647776041666666247e-01,4.038056356666666624e-03,8.378510033333332885e-01,-2.514998111666666078e-02,-1.746616790000000141e-01,6.461058281666667291e-01,6.940930171666666315e-02,1.950300996666666509e-01,1.887414775000000045e-01,5.262986759999999098e-02],
    [-3.636755593333332945e+04,-3.842062094999999772e+03,-4.048811503333333349e+03,-3.049432866666666541e+03,-1.065125195666666542e+02,1.830416950999999983e+02,-3.896107531666665977e+02,-3.610192358333333686e+03,2.991188953333333416e+02,-8.419226843333333363e+02,6.130045076666666546e+02,3.566503936666666874e+01,1.181638553333333221e+03,-1.032169801833333167e+03,-4.531705093333333139e+02,2.655700488333333169e+02,-5.966281769999999369e+02,-2.796644919999999388e+02,-1.911389823333333311e+02,1.088517780166666569e+02,1.647064938333333117e+01,-4.319642541666667057e+02,1.501983666666666295e+02,-5.037394068333333053e+02,-2.179183511666666462e+01,-2.000382931666666764e+02,-4.291878568333332566e+01,-1.391934881666666683e+02,1.024562955166666711e+02,-1.583727700000000027e+02,-8.054308823333333578e+01,5.555037701666666550e+01,-5.105239423333333093e+02,2.474648426666666410e+02,4.943266108333332909e+01,-1.688850768333333008e+01,-1.450859253333333143e+01,4.190677041666666014e+01,-3.491532963333332873e+01,6.767754163333333395e+01,-6.378072226666666467e+01,1.681658459999999966e+00,5.309100703333333371e+01,-8.300144178333333400e+01,2.185862763333333092e+01,6.317145788333332490e+01,1.190716105166666594e+01,-8.403019073333334177e+01,6.746522258333333966e-01,9.198573890000000475e+00,7.314984204999999129e+00,-2.314965018333333013e+00,1.970400028333333253e+01,-8.144216239999998663e+00,2.374365221666666415e+00,1.555617461666666479e+01,-7.858189951666666673e+00,1.391052314999999950e+01,4.601449166666665702e-01,2.272379284999999882e+01,-2.051110734999999963e+01,8.666572978333332955e+00,8.486431514999999592e+00,-8.786326323333333299e-01,2.143689996666666708e+00,-2.014744828333332904e+00,-6.251413023333333152e-01,4.326928811666665986e+00,-1.905660081666666450e+00,1.530922003333333281e+00,-1.006883721166666579e+00,4.346348154999999380e-01,2.705347461666666842e+00,-4.028467534999998989e+00,8.448306049999999345e+00,-8.345130283333332954e+00,9.497714484999999485e+00,4.693995956666666691e-01,-2.725963809499999946e-01,2.379171720000000434e+00,-7.681912138333333306e-01,-1.325642659999999862e-01,-3.933467001666666740e-01,-1.478173879833333260e-01,8.305845424999999116e-01,-3.555545553333332998e-01,1.341328934999999944e+00,-1.585792129999999966e+00,1.197058409999999906e+00,3.618596790000000452e-01,-1.775194064999999988e+00,2.506182819999999811e+00,-1.559488691666666593e+00,2.662032081666666272e+00,1.418884757166666635e-02,-7.849610991666665649e-01,1.012541398999999842e+00,1.117270019499999739e-01,2.139642201666666355e-01,-6.402180191666664855e-02,-1.532569391666666614e-01,3.841009244999999545e-02,1.358608416666666763e-01,-2.350577828333332703e-02,1.264255132000000059e-01,4.903446651666666378e-01,-6.056442618333333083e-01,3.352576331666666798e-01,1.999813193333333239e-01,-3.778838386666666382e-01,4.527198704999999546e-01,-7.469382213333332875e-03,9.629745523333332891e-01,-1.216883457666666501e-01,-2.442143449999999716e-01,6.941523951666667136e-01,8.819458608333333172e-02,9.814470786666666668e-02,2.537285814999999944e-01,6.196952424999999098e-02],
    [-3.637883539999999630e+04,-3.549437014999999519e+03,-5.451892138333332696e+03,-2.767686149999999998e+03,-3.144842148333333398e+02,8.584988861666665798e+02,4.126747806666666918e+01,-3.949464883333333091e+03,3.436567628333332891e+02,-1.087627023333333227e+03,6.276912503333333007e+02,2.473211978333333150e+02,1.108554411666666510e+03,-3.066446443333333036e+02,-3.412155888333332996e+02,2.930933558333333053e+02,-6.742084913333333134e+02,-2.915612678333333179e+02,4.585905646666665447e+00,2.540810514999999725e+02,1.325169621666666728e+02,-3.915442793333332929e+02,8.152879433333332315e+01,-2.344096956666666642e+02,5.793604946833333713e+00,-1.903490390000000048e+02,-7.695669053333332954e+01,-9.854403811666666968e+01,1.382384226666666507e+02,-1.729024866666666469e+02,-1.094363761666666619e+02,4.188461423333333045e+01,-3.226023188333332996e+02,2.626617519999999786e+02,1.030360939666666553e+02,-1.228018879999999946e+01,-8.719162913333333265e+00,2.157168669999999722e+01,-4.414870719999999693e+01,6.245117343333333082e+01,-6.832627468333332388e+01,-1.551100716666666379e+01,4.814460069999999803e+01,-4.574598455000000286e+01,3.559741746666666273e+01,7.568054183333333640e+01,-8.054568335000000801e+00,-1.055048764999999946e+02,-2.006826769999999982e+00,1.002394948333333424e+01,4.902962723333334161e+00,-7.237239843333333589e+00,1.420328783333333078e+01,-9.097583618333333177e+00,-3.349809978333333493e-01,1.274958956666666587e+01,-5.582240501666666077e+00,1.193833666666666637e+01,1.017175707833333220e+01,1.359144468333333045e+01,-3.199649629999999689e+01,7.976877209999998719e+00,1.387367611666666711e+01,-1.571989410000000031e+00,2.399787710000000018e+00,-1.122304546166666528e+00,-7.175982094999999727e-01,2.435817643333332949e+00,-1.875670894999999838e+00,1.506668948333333091e+00,-9.972257958333332617e-01,-9.842305359999998782e-01,1.884446254999999848e+00,-1.294628355333333092e+00,7.735698361666666578e+00,-1.064040944999999994e+01,7.818860676666666620e+00,2.098432739999999797e+00,9.743547331666666533e-01,1.452032166666666457e+00,-6.723443164999999277e-01,-4.063486364999999156e-02,-1.602173699999999978e-01,3.110048469999999732e-01,4.675902841666666476e-01,-7.186046853833333303e-02,1.181563411666666452e+00,-1.280811276666666609e+00,4.842029336666666128e-01,5.244513490000000111e-01,-1.372606970000000093e+00,2.936413691666666548e+00,-1.673745674999999711e+00,2.424162588333333090e+00,-4.917331853333332947e-02,-3.013006719999999916e-01,1.129050983333333313e+00,2.428561193299999532e-02,-8.023280908333332850e-02,-2.269439758333333113e-02,-1.187366301666666624e-01,5.967911233333332566e-02,2.782702700000000418e-01,-3.665543291666666093e-02,2.448541204999999943e-01,3.688170326666666554e-01,-4.892780019999999896e-01,1.740760754999999826e-01,3.614012138333333457e-01,-4.203740394999999630e-01,6.692766051666666494e-01,8.097988591666665723e-03,9.497055901666665578e-01,-2.782197181666666297e-01,-2.301363151666666607e-01,7.961466818333332585e-01,1.759509174999999981e-01,-4.209171511666666421e-02,2.478282743333333205e-01,3.156761814999999721e-02],
    [-3.552692046666666283e+04,-2.962332271666666657e+03,-6.695858328333332793e+03,-2.518374643333333552e+03,-4.461887984999999901e+01,1.453274618333333137e+03,5.168917470000000094e+02,-3.769751924999999574e+03,4.871647859999999355e+02,-1.129965636666666569e+03,4.073945980000000304e+02,5.872208881666665548e+02,7.275088376666665226e+02,3.650889618333333431e+01,-1.717256480000000067e+02,3.643797925000000077e+02,-6.968278673333333018e+02,-3.915667104999999992e+02,1.947837496666666652e+02,2.852998499999999922e+02,1.334190463333333128e+02,-3.021799340000000029e+02,1.357531321833333138e+01,1.857152193333333301e+01,4.178383373333333850e+01,-1.640001591666666627e+02,-1.165172478333333288e+02,-5.488097808333333205e+01,1.417332284999999956e+02,-1.749580853333333152e+02,-1.157108669999999790e+02,1.180339255166666668e+01,-1.425989451666666525e+02,2.780606508333332840e+02,1.015542427000000032e+02,-7.958424253333332921e+00,3.382863146333333404e+00,7.420232996666666025e+00,-4.669304751666665965e+01,4.969959778333333134e+01,-5.729338076666665813e+01,-2.947834690000000180e+01,4.192676966666667226e+01,-1.620999326666666462e+01,5.442326586666666799e+01,6.639026668333332282e+01,-3.056902834999999641e+01,-1.229748721666666711e+02,-5.638094834999999527e+00,1.331482955000000068e+01,6.503532233333332968e+00,-9.209176849999998637e+00,8.669171893333331269e+00,-3.469970686666666193e+00,-3.605955751666666487e+00,1.143674936666666753e+01,-5.353454018333333231e+00,1.125571601666666588e+01,1.522597863333333201e+01,2.533409882833333349e+00,-4.270761516666666324e+01,9.499419966666666326e+00,1.920216366666666730e+01,-2.618062403333333510e+00,3.229904188333333259e+00,9.949708364999999555e-01,1.291073145333333089e-02,8.695032526666666151e-01,-8.156257423333332368e-02,1.234852421666666533e+00,2.114487750833333179e-01,-2.471603459999999863e+00,1.515463420000000117e+00,1.289374596166666720e+00,6.609678573333332530e+00,-1.317059954999999860e+01,7.096273948333332804e+00,3.935054554999999787e+00,2.434447658333333209e+00,2.156668268333332972e-01,-6.498957508333333966e-01,-4.258158211666666221e-02,7.116496653333331812e-02,8.842755055000000031e-01,2.265502321666666707e-01,3.847602715000000284e-01,1.041431303333333336e+00,-4.115379578333333010e-01,-4.770185704999999055e-02,7.247222463333333753e-01,-7.023829470000000352e-01,3.232591441666666565e+00,-1.860558134999999780e+00,2.270123888333333007e+00,-2.202952833833332971e-02,4.890826673333332764e-01,1.061377864999999865e+00,-1.270050274333333340e-01,-3.181858521666666717e-01,-1.938091360000000155e-03,-2.018286328333333268e-01,-5.273739050000000178e-02,3.858273784999999845e-01,1.668219281166666637e-02,2.891424286666666732e-01,2.842135068333332959e-01,-2.407320091666666773e-01,1.243923663333333374e-01,4.948711864999999488e-01,-3.425804818333333390e-01,8.642878926666666128e-01,6.016906006666666168e-02,9.111236609999999736e-01,-4.104759504999999087e-01,-7.516670629999999687e-02,8.261334718333332994e-01,2.004741264999999883e-01,-1.975718573333333228e-01,2.186370819999999826e-01,2.937446194999999635e-02],
    [-3.513157369999999355e+04,-2.800428098333333310e+03,-6.511619093333332785e+03,-2.133396213333332980e+03,4.179492501666666158e+02,2.031576744999999846e+03,5.818758896666665805e+02,-3.706105053333333217e+03,7.193201090000000022e+02,-9.740603486666666413e+02,1.638054447999999752e+02,7.125042026666667425e+02,-4.481347826666666379e+01,-2.149310914999999795e+02,4.062010236316666578e+01,4.447066616666666050e+02,-6.470179708333333792e+02,-4.594813191666665944e+02,2.936548364999999876e+02,2.125816993333333187e+02,-3.472558959499999531e+01,-1.446934559999999976e+02,1.815500251666666287e+01,5.432099846666666565e+01,7.022323198333333494e+01,-1.186215053333333174e+02,-1.304885751666666636e+02,-1.526940800999999936e+01,1.240818740000000133e+02,-1.935235094999999887e+02,-8.683083533333332582e+01,-8.166286411666666467e+00,-5.457970279999999264e+01,2.673619318333333013e+02,5.906175971666665703e+01,-3.013459208333332917e+00,2.054863021666666612e+01,1.729179141666666641e+00,-3.733390909999999963e+01,3.465157364999999601e+01,-4.173810109999999440e+01,-3.513850928333332746e+01,4.154547621666666402e+01,-9.049461721666665071e+00,6.708567926666665926e+01,3.605018386666666430e+01,-4.259726424999999495e+01,-1.288906819999999982e+02,-7.671013441666666210e+00,1.763579221666666541e+01,9.204101553333332575e+00,-5.991319138333332184e+00,4.807095034999999683e+00,5.359359413333333322e+00,-6.631906803333332157e+00,1.114251020000000025e+01,-6.991295063333332394e+00,1.062435143333333265e+01,1.185853200000000029e+01,-5.771661601666666641e+00,-4.860661298333332780e+01,1.362016519999999886e+01,2.111177160000000086e+01,-3.640003574999999714e+00,4.095360598333332547e+00,2.892505006666667100e+00,1.449998384999999779e+00,1.513175994833333426e-01,2.758673304999999853e+00,7.762554086666665354e-01,1.393107768333333052e+00,-3.102727620000000019e+00,1.666512896666666244e+00,1.911647316666666541e+00,5.044805084999999245e+00,-1.517327479999999973e+01,8.023632276666667451e+00,4.664006361666666045e+00,3.303667830000000194e+00,-8.569445114999999502e-01,-8.536930824999999778e-01,-1.839169581666666442e-01,1.895014354999999817e-01,1.268763823333333374e+00,2.306432703333333167e-01,9.820143898333333343e-01,1.017093208333333276e+00,4.759384063333332859e-01,-1.117033050833333152e-01,9.237064839999999943e-01,-1.532661325499999894e-01,3.060246804999999792e+00,-2.095647314999999899e+00,2.528881743333333265e+00,2.499469103333332859e-02,1.188717208333333275e+00,8.739121324999998830e-01,-3.310058216666666442e-01,-4.299131914999999027e-01,-5.079494013333332725e-02,-3.727324613333333203e-01,-1.944585706666666636e-01,3.896669381666666432e-01,1.241485404999999875e-01,2.936933559999999610e-01,2.818504173333333251e-01,2.192189879999999896e-02,2.089113023333333263e-01,5.501069176666666394e-01,-1.755250325000000111e-01,9.328714638333333031e-01,7.418387630000000676e-02,9.413503654999999526e-01,-4.846359353333332676e-01,1.430291351666666821e-01,7.421497429999999174e-01,1.395306179999999951e-01,-3.264421509999999582e-01,2.117116674999999781e-01,7.504524944999999003e-02],
    [-3.609435235000000102e+04,-9.298926404999999704e+02,-5.171191666666666606e+03,-1.729867920000000140e+03,8.958862045000000762e+02,2.225673829999999725e+03,5.494412553333332880e+02,-3.670411504999999579e+03,8.792737379999999803e+02,-8.760167246666665051e+02,-2.104506203333332905e+02,7.341506973333332553e+02,-1.013036448833333338e+03,-5.732781554999999116e+02,8.170884533333332200e+00,4.478740598333333196e+02,-6.089027428333332637e+02,-5.158660024999999223e+02,3.394079736666666349e+02,8.413280718333334107e+01,-1.841154185000000041e+02,-1.295484834333333168e+01,4.535504128333333540e+01,-1.460327589166666655e+02,7.098800003333332143e+01,-7.973182488333333140e+01,-1.220735703333333220e+02,2.001322979999999774e+01,9.567952298333332806e+01,-2.039948311666666427e+02,-3.177962996666666484e+01,-2.545684703333333232e+01,-6.788271013333331894e+01,2.509298506666666526e+02,2.556664024999999896e+01,4.456627301666665986e+00,3.611552506666667028e+01,3.102117611666666441e+00,-1.966022846666666979e+01,1.981654036666666840e+01,-2.668791181666666645e+01,-2.916908438333333109e+01,4.610495650000000012e+01,-2.320294253333333501e+01,7.714624606666666295e+01,4.397820228333333858e+00,-3.822733273333332704e+01,-1.257973498333333282e+02,-5.230020278333332939e+00,2.147711139999999830e+01,1.169685656666666596e+01,1.086979909999999938e-01,2.608969036666666241e+00,1.320677806666666498e+01,-8.261779813333333777e+00,1.128076611666666729e+01,-9.036703343333332583e+00,1.077083941666666433e+01,4.275889323333333714e+00,-7.963250659999999925e+00,-4.903516771666666330e+01,1.805717008333333240e+01,2.018265634999999847e+01,-3.869802414999999662e+00,4.844737286666665810e+00,4.236324256666666344e+00,2.627450744999999976e+00,1.984747554999999608e-01,5.386173151666666215e+00,1.187285095666666401e-01,1.845310860000000108e+00,-2.693731394999999473e+00,2.282235168333333064e+00,8.180854351666666524e-01,3.650986619999999849e+00,-1.586069054999999928e+01,9.538938424999999555e+00,4.366582389999999592e+00,3.211955873333332878e+00,-1.597292208333333186e+00,-1.233613278333333341e+00,-3.032756803333333528e-01,3.359611919999999641e-01,1.269804828333333413e+00,4.671079069999999889e-01,1.518712689999999643e+00,1.013846403333333202e+00,9.894784096666666695e-01,1.520917517333333357e-01,1.071970690000000115e+00,1.621641101666666529e-01,2.487588114999999878e+00,-2.109599776666666759e+00,2.920686271666666389e+00,8.154017759999998560e-02,1.478733145000000082e+00,6.186056913333333185e-01,-5.526172888333332756e-01,-3.541532228333333920e-01,-1.854583821666666577e-01,-5.330155468333332980e-01,-2.646316294999999652e-01,3.116654143333333349e-01,2.715740794999999541e-01,2.669557874999999858e-01,3.268649029999999289e-01,2.110654113333333415e-01,3.300693863333333256e-01,5.219743550000000010e-01,1.661140565000000097e-02,8.544498769999999688e-01,7.530303471666666137e-02,9.490421569999999418e-01,-5.291008613333332278e-01,2.774585591666666740e-01,5.721511354999999632e-01,9.272278889999999163e-03,-3.772344241666666376e-01,2.558899929999999823e-01,1.270495183333333333e-01],
    [-3.713295211666666728e+04,5.815893539999999575e+02,-4.755786743333333106e+03,-1.520022625000000062e+03,9.583416866666666465e+02,2.262589148333333469e+03,3.837501216666667005e+02,-2.713671034999999392e+03,9.418338759999999183e+02,-8.122369593333332887e+02,-3.446361781666666957e+02,7.058744296666666287e+02,-1.633560576666666520e+03,-8.469755901666667341e+02,-4.295036936666666634e+02,3.869972996666666631e+02,-5.574448501666665834e+02,-4.716340010000000120e+02,3.206838593333333165e+02,-2.168348395333332945e+01,-2.233222006666666459e+02,1.086686970000000052e+01,9.176995229999999992e+01,-3.452381820000000516e+02,4.715505060000000270e+01,-6.009766986666666355e+01,-9.086454415000000040e+01,2.419346264999999718e+01,6.653761864999999887e+01,-1.876132440000000088e+02,5.298140083333332484e+01,-3.843262633333333156e+01,-9.459227275000000645e+01,2.523164676666666537e+02,-1.264272661333333225e+01,1.083818760333333309e+01,4.111193723333332883e+01,6.524155159999999398e+00,-2.337222659999999674e+00,1.069532514833333359e+01,-1.074067869166666611e+01,-4.538218681666666754e+00,5.310350716666665960e+01,-4.010323364999999995e+01,8.515556474999999637e+01,-2.777409161666666648e+01,-3.151809579999999755e+01,-1.132508023333333398e+02,-3.542795883333333395e-01,2.355504093333333415e+01,1.224784278333333276e+01,7.647096569999998650e+00,3.289478541666666533e+00,1.923872068333333019e+01,-6.807962469999999655e+00,1.170619474999999987e+01,-9.735981821666666036e+00,1.092801803333333233e+01,-4.031879303333333553e+00,-7.936357528333333633e+00,-4.337643709999999686e+01,2.308162560000000241e+01,1.896024784999999824e+01,-3.435259976666666937e+00,5.801707613333332958e+00,4.900335448333333233e+00,3.506856956666666303e+00,9.533407831666667054e-01,7.311432214999999069e+00,-7.245058628333332917e-01,1.598711261666666328e+00,-1.865921564999999838e+00,2.588867783333332895e+00,-5.322211171666666463e-01,1.995787441666666551e+00,-1.507233523333333380e+01,1.133183119999999988e+01,4.073614869999999222e+00,2.112557226666666566e+00,-2.569806699999999999e+00,-1.574446493333333308e+00,-2.089854581666666655e-01,6.047696114999999706e-01,1.000208388666666615e+00,7.648279591666666821e-01,1.795638705000000002e+00,8.895138974999998727e-01,1.067727556666666633e+00,4.951563276666666180e-01,9.772013483333332751e-01,5.424143196666666444e-01,1.774266883333333267e+00,-1.892639436666666342e+00,3.160530363333333259e+00,2.827392021666666477e-01,1.306674861666666576e+00,2.902301553333332812e-02,-7.421158268333333252e-01,-4.932136248333333223e-02,-3.194536625000000130e-01,-6.405355136666666116e-01,-2.479733949999999854e-01,1.927369361666666503e-01,3.944217901666666193e-01,1.788507278333333339e-01,3.834497024999999892e-01,3.125717913333333486e-01,4.633063836666665991e-01,4.282797118333333541e-01,2.190308398333333240e-01,7.185309213333332945e-01,9.754824745000000019e-02,7.938195255000000117e-01,-5.393260395000000207e-01,2.860921116666666486e-01,3.076690791666666369e-01,-1.594623278333333061e-01,-3.220507580000000480e-01,3.108136198333333322e-01,1.522790946666666700e-01],
    [-3.724391541666666308e+04,2.326192401666666228e+03,-3.164695421666666334e+03,-1.926673876666666501e+03,1.257555511666666689e+03,1.977011348333333217e+03,2.335331916666666530e+02,-1.417257824999999912e+03,8.092843973333333452e+02,-6.703766898333333302e+02,-3.273850546666666901e+02,6.915701395000000957e+02,-1.842534701666666479e+03,-1.028833721666666634e+03,-9.152452628333331859e+02,2.894025075000000129e+02,-4.992391641666666260e+02,-3.786380188333332626e+02,3.081462483333333466e+02,-4.683842478333332338e+01,-1.857096423333333348e+02,-2.666255964999999861e+01,1.883625108333333174e+02,-3.847650361666666754e+02,1.344411197500000021e+01,-6.193508119999999906e+01,-6.580581228333333854e+01,9.407932309999999632e+00,5.288095326666666551e+01,-1.495718323333333331e+02,1.504866624999999942e+02,-4.462771453333332516e+01,-4.844435833333332653e+01,2.501018583333333254e+02,-6.971265218333333280e+01,1.449012179999999717e+01,3.275102031666666846e+01,7.543014786666665472e+00,7.804992313333332987e+00,6.307047639999998623e+00,7.937895898333333200e+00,2.870049666666666610e+01,5.762562504999999646e+01,-3.956467571666666316e+01,8.530741393333333633e+01,-6.211166814999999275e+01,-3.090465304999999319e+01,-9.051200143333332448e+01,4.742798201666666102e+00,2.281424434999999917e+01,1.247729588333333162e+01,1.415191439999999901e+01,4.563467393333333177e+00,2.442982629999999489e+01,-3.861693751666666508e+00,1.144656836666666422e+01,-7.680314998333333421e+00,9.455184674999999928e+00,-1.098197013833333457e+01,-8.889092466666665970e+00,-3.278666226666666716e+01,2.735072964999999812e+01,1.919616538333333366e+01,-2.518297831666666209e+00,6.955558431666665875e+00,5.640030946666666267e+00,4.166930064999999850e+00,1.718230093333333208e+00,8.751354588333333240e+00,-1.757603029999999844e+00,1.144992576666666650e+00,-1.608927111666666576e+00,2.101062704999999919e+00,-1.216984636666666564e+00,-5.392280145499999122e-01,-1.332822313333333319e+01,1.229941309999999888e+01,4.423551353333333047e+00,6.967303304999999947e-01,-3.823441099999999704e+00,-1.720159486666666515e+00,1.523303704833333383e-01,1.048294269999999972e+00,6.764250231666666391e-01,1.010317079166666687e+00,1.867350590000000032e+00,5.446222444999999635e-01,1.044011524999999940e+00,4.013467216666665727e-01,6.304795743333332370e-01,1.117596737499999993e+00,9.066603658333333149e-01,-1.569791466666666579e+00,2.883579853333333443e+00,7.610359096666665657e-01,8.962209359999999680e-01,-7.820733708333332812e-01,-9.346618628333333012e-01,2.966121499999999633e-01,-4.070627056666666355e-01,-6.690387790000000834e-01,-1.823501348333333438e-01,8.086939796666667291e-02,5.001855053333333911e-01,3.498012712833333676e-02,4.009816734999999688e-01,3.945295835000000029e-01,4.943103719999999979e-01,3.042611893333333484e-01,3.962297946666666348e-01,5.442338300000000295e-01,1.242466379999999787e-01,4.076845149999999141e-01,-4.886015996666666084e-01,2.063103510000000029e-01,1.117657406666666339e-02,-3.438401446666666805e-01,-2.207414323333333206e-01,3.041679381666666515e-01,1.844029538333333273e-01],
    [-3.705232080000000133e+04,2.874443196666667063e+03,-2.384118114999999761e+03,-2.016334936666666636e+03,1.780978423333333012e+03,1.074376618999999891e+03,-1.565018093833333168e+01,-5.202145861666665496e+02,8.236728344999999081e+02,-4.206615651666666054e+02,-2.840601316666666207e+02,6.585858154999999670e+02,-1.881682506666666541e+03,-9.455599508333332324e+02,-1.308922796666666500e+03,2.084576723333333064e+02,-4.165437073333333160e+02,-2.550797986666666475e+02,3.328007015000000024e+02,4.857647046666665247e+00,-3.345056561166666853e+01,-8.633890469999998629e+01,2.694206496666666339e+02,-3.225897709999999847e+02,-3.880221018333332950e+01,-6.846124829999999406e+01,-3.465198180000000150e+01,-9.270206119999990779e-02,7.597886021666666068e+01,-8.887234951666665950e+01,2.353922173333333205e+02,-5.893296979999998797e+01,4.068502571666667222e+01,2.327857761666666647e+02,-1.040733688333333191e+02,7.141441576666665014e+00,1.885084744999999984e+01,1.130865466666666563e+01,1.400683693333333224e+01,1.296855946666666703e+01,2.907991224999999957e+01,5.769572778333332508e+01,5.960176938333333396e+01,-2.706854441666666489e+01,7.703878926666666871e+01,-8.237695915000000468e+01,-3.720373771666666585e+01,-6.567995080000000030e+01,8.021007396666666622e+00,1.946566213333333195e+01,1.348199149999999946e+01,1.816709164999999970e+01,7.181303498333332591e+00,2.870472139999999683e+01,-1.221333230166666617e+00,1.149444788333333278e+01,-3.967009336666666108e+00,6.491674768333333567e+00,-1.323353808333333248e+01,-1.190369848333333280e+01,-2.103457598333333323e+01,2.849806816666666265e+01,2.041458090000000070e+01,-1.032175739333333286e+00,7.321886916666666245e+00,6.366090618333333673e+00,4.082535519999999529e+00,2.343314416666666844e+00,9.405528248333332897e+00,-2.570318184999999644e+00,9.647904214999999395e-01,-2.047743993333333457e+00,1.248622768333333077e+00,-1.281458843333333375e+00,-3.827809359999999828e+00,-1.147467135000000127e+01,1.139246503333333216e+01,5.059580914999999735e+00,-4.753303576666666475e-01,-5.088239025000000026e+00,-1.471961483333333209e+00,4.497321844999999652e-01,1.440105391666666623e+00,2.440178805000000062e-01,1.134915420000000008e+00,1.625680704999999948e+00,2.454998831666666548e-01,1.040915388333333302e+00,-1.478944849136666906e-01,2.644235710000000239e-01,1.605736741666666578e+00,-4.462827026666666558e-02,-1.194727691666666480e+00,1.957313028333333316e+00,1.348178464999999937e+00,5.271076458333332493e-01,-1.530113133333333320e+00,-1.199970851666666505e+00,5.949560658333333807e-01,-4.025043588333333533e-01,-6.287343856666667286e-01,-1.250696958333333275e-01,-2.808694683500000122e-02,5.761608805000000277e-01,-1.899711428333333008e-01,4.224606544999999769e-01,4.332909188333332606e-01,3.970040688333333345e-01,2.101719575000000062e-01,4.772021771666666856e-01,3.819075808333333155e-01,1.564625278333333369e-01,-1.240680638499999933e-01,-4.244012108333333200e-01,1.060320955500000106e-01,-2.173425903333333076e-01,-5.634508380000000649e-01,-1.225634913333333298e-01,2.497176718333333212e-01,2.247503424999999777e-01],
    [-3.639143958333333285e+04,1.975697059999999965e+03,-1.786978306666666413e+03,-1.962855206666666618e+03,2.055921901666666599e+03,8.655967541666666420e+01,-6.858860628333331988e+01,4.763329028333333071e+01,9.998429543333331821e+02,-2.914318516666666596e+02,-3.371705268333333834e+02,6.916528480000000627e+02,-1.720510993333333317e+03,-7.565051653333333661e+02,-1.363892419999999902e+03,1.811655999999999835e+02,-3.689532518333333542e+02,-1.892803996666666819e+02,3.536415000000000077e+02,9.867180909999999017e+01,1.959982075000000066e+02,-1.174747359999999929e+02,3.349214809999999716e+02,-1.875524366666666367e+02,-9.098063009999999906e+01,-8.279759669999999971e+01,-8.670776943333333264e+00,-1.955050823333333199e+01,1.251690831666666526e+02,-1.661509625500000098e+01,2.777248599999999783e+02,-7.785361161666665453e+01,1.327918516666666733e+02,1.725506068333333189e+02,-9.815011351666665007e+01,-8.339106193333332584e+00,7.237887508333332498e+00,1.899776019999999832e+01,1.280809288333333384e+01,2.989915265000000133e+01,4.881675886666666742e+01,6.867449053333332643e+01,5.530249239999999133e+01,-1.214089426666666505e+01,5.009623986666666440e+01,-7.987562244999999450e+01,-5.059100116666666480e+01,-4.079362776666665980e+01,8.837609324999998961e+00,1.630463963333333055e+01,1.674462583333333399e+01,1.848200668333333141e+01,1.115498816666666748e+01,3.100436509999999757e+01,-5.354385141666666570e-01,1.065760336666666497e+01,-1.486451575000000025e+00,7.587409246666665386e-01,-8.761762058333333769e+00,-1.757797438333333417e+01,-9.668484680000000608e+00,2.536493903333333577e+01,2.047150576666666666e+01,7.898753341666666650e-01,6.999762855000000172e+00,7.649518304999999962e+00,3.328918415000000408e+00,2.818683806666666847e+00,8.790600655000000430e+00,-2.666967638333333390e+00,8.319160589999999855e-01,-3.651684901666666594e+00,2.980381796666666805e-01,-6.992148335000000214e-01,-7.352646879999999996e+00,-9.870293491666664920e+00,8.499976358333332982e+00,5.224352604999999983e+00,-1.424724319999999711e+00,-5.940747856666666493e+00,-8.158250558333333124e-01,5.924265800000000359e-01,1.747933321666666595e+00,-1.134284621999999826e-01,1.147505159999999913e+00,9.633889014999998945e-01,2.367827449999999889e-01,9.786195021666665994e-01,-1.093781941833333216e+00,-3.759243733333344356e-04,1.716453631666666535e+00,-9.317582776666666344e-01,-9.392389216666665597e-01,5.461012551666666326e-01,1.759134346666666682e+00,1.666351060000000051e-01,-2.004650465000000104e+00,-1.473003511666666654e+00,6.726338956666666480e-01,-3.093872803333333477e-01,-5.285059823333333462e-01,-1.442746343333333181e-01,-9.072179596666665735e-02,6.140692446666666804e-01,-4.751802258333333584e-01,4.628517769999999643e-01,3.894478223333333045e-01,1.989917260000000077e-01,1.408556204999999728e-01,3.710150630000000338e-01,2.533902704999999589e-01,1.417811201666666632e-01,-6.782693288333332404e-01,-3.812732023333332831e-01,-4.673653244166665888e-02,-3.353506876666666470e-01,-7.923793791666665642e-01,-1.124829291666666620e-01,1.629190636666666692e-01,2.665081641666666723e-01],
    [-3.543346406666666735e+04,1.399791056666666691e+03,-1.238784820000000082e+03,-2.119160963333333257e+03,1.997400114999999914e+03,-9.950918826666665495e+01,-3.795873011666666343e+02,-1.609001016666666573e+01,1.269903109999999970e+03,-4.437005364999999983e+02,-2.600994663333332824e+02,8.549484041666665917e+02,-1.346286324999999806e+03,-5.334963843333332534e+02,-1.070184669999999869e+03,2.252759120000000053e+02,-3.891352344999999673e+02,-1.644824463333333426e+02,3.619624631666666801e+02,1.954149601666666740e+02,4.502928398333332893e+02,-1.912849048333333428e+02,4.289469361666666600e+02,-1.285452755000000025e+02,-1.158926154999999909e+02,-9.947275159999999516e+01,1.155827440166666520e+01,-4.914658546666666439e+01,1.817181295000000034e+02,5.084514149999999688e+01,2.349497863333333214e+02,-8.452635081666664973e+01,1.444322888333333310e+02,6.846666571666666812e+01,-7.180498724999999638e+01,-2.330838840000000189e+01,4.969358211666666136e+00,2.941647521666666520e+01,5.342616946666666422e+00,5.218016563333333124e+01,5.975658350000000496e+01,5.326304549999999693e+01,4.146024984999999674e+01,-9.682977505000000207e+00,4.773417061666665795e+00,-6.176132149999999399e+01,-6.021648223333332339e+01,-1.869740931666666484e+01,7.183034326666666303e+00,1.578264741666666637e+01,2.172153776666666403e+01,1.512648986666666495e+01,1.569617468333333221e+01,3.022348131666666404e+01,-7.867879736666665291e-01,7.690012666666666163e+00,-1.700468224999999833e+00,-5.403246049999999912e+00,-1.319707171166666582e+00,-2.095575241666666599e+01,-7.164623086666666030e-01,1.796275388333333112e+01,1.749176369999999991e+01,2.175354978333333467e+00,6.204575906666665475e+00,9.538230333333332922e+00,2.263251214999999927e+00,3.401290733333333538e+00,7.141204334999999404e+00,-9.731987701666666712e-01,6.006855241666666512e-01,-5.786193490000000494e+00,4.023488559999999215e-02,-3.218145163333333558e-01,-9.002385799999998994e+00,-9.066091868333332471e+00,4.459319981666665988e+00,4.209691529999999737e+00,-1.883046656666666596e+00,-5.964194976666666648e+00,-3.326430596666667128e-02,4.824310273333332622e-01,1.990541903333333140e+00,-1.814842445000000026e-01,1.234040189999999981e+00,9.456022294999999467e-02,7.628154013333332539e-01,9.243171506666665316e-01,-2.016629338333333354e+00,-3.526477466666665811e-02,1.208038844999999917e+00,-1.339275663333333144e+00,-1.119205438333333191e+00,-9.197181788333332886e-01,1.590514884999999712e+00,-9.494475763333332097e-02,-2.116298809999999975e+00,-1.627529896666666476e+00,4.189619653333332971e-01,-1.775902628333333177e-01,-4.172016211666665919e-01,-2.608352643333333165e-01,-8.044283063333332318e-02,6.456366526666665884e-01,-7.108884161666666479e-01,5.124751613333333733e-01,3.111872696666666549e-01,8.088812816666665628e-03,9.642094053333333248e-02,7.255220106333332142e-02,1.733147113333333433e-01,8.781624296666666954e-03,-1.062555411666666672e+00,-4.228539286666666563e-01,-2.312437186666666533e-01,-3.604911293333333266e-01,-9.386686998333333420e-01,-2.417047201666666367e-01,5.433628011666666313e-02,3.107967700000000000e-01],
    [-3.577011408333333384e+04,1.765637481666666645e+03,-1.523716220666666459e+02,-2.924152793333333648e+03,2.199322724999999991e+03,2.765425794999999880e+02,-5.572246281666666619e+02,-8.563584714999999505e+02,1.369437283333333426e+03,-6.377437580000000708e+02,-6.305292568333332781e+01,1.143139166666666597e+03,-1.009961305499999867e+03,-3.123347761666666429e+02,-8.014091931666666824e+02,2.847499198333333084e+02,-4.467013621666666268e+02,-1.261961601666666581e+02,3.151911010000000033e+02,2.736746841666666796e+02,6.386413039999999910e+02,-2.844676630000000159e+02,5.427827414999999291e+02,-1.969778149999999641e+02,-1.150019921666666534e+02,-1.393990731666666534e+02,3.804359936666666187e+01,-9.678811206666667033e+01,2.378922538333333137e+02,9.622640164999999968e+01,1.500645135000000039e+02,-7.284029341666666824e+01,5.570916638333333282e+01,-4.649914899999999562e+01,-6.902494148333332191e+01,-3.425709986666667106e+01,-1.136286104000000241e-01,4.111021528333333208e+01,-5.855535524999999630e+00,7.225201934999999764e+01,5.730486203333333606e+01,2.641123866666666586e+01,2.201588729999999927e+01,-2.345038081666666585e+01,-4.490543621666666496e+01,-4.467680738333333323e+01,-5.791142716666666956e+01,3.501168644999999913e+00,4.868085748333332852e+00,1.568539789999999812e+01,2.620904235000000071e+01,9.445720106666668059e+00,1.838910763333333165e+01,2.553370960000000167e+01,-1.457879455000000046e+00,3.666125409999999807e+00,-4.349516051666665994e+00,-9.702805570000000657e+00,2.944996526666666448e+00,-1.799802929999999890e+01,5.527325078333332975e+00,9.673150583333333330e+00,1.207232064999999999e+01,3.160887590000000191e+00,5.190127361666666772e+00,1.112803613333333352e+01,9.032253439999999856e-01,3.504194253333333009e+00,5.173491649999998998e+00,1.266913134166666843e+00,4.241973316666666216e-01,-7.313943116666666633e+00,6.444804020000000078e-01,-7.054547504999999497e-01,-7.833363239999998839e+00,-8.799319696666666246e+00,9.194503146666666016e-01,2.311634303333333307e+00,-1.978554606666666604e+00,-5.005770373333333190e+00,6.701811718333332557e-01,2.967428048333333179e-01,2.116636036666666776e+00,-1.586601013333333310e-01,1.296106984999999989e+00,-6.270994533333333898e-01,1.438886103333333333e+00,9.415928599999999760e-01,-2.510690576666666729e+00,1.752145995000000123e-01,2.598674838999999737e-01,-1.180675879999999900e+00,-1.770299188333333218e+00,-2.004224093333333290e+00,8.976366776666666603e-01,-2.821198903333333452e-01,-1.856002068333332922e+00,-1.607489488333333272e+00,3.648907511666666520e-02,-3.489150062999999552e-02,-2.945863793333333147e-01,-4.057727059999999275e-01,-5.647413731666665881e-02,6.934660219999999597e-01,-8.296896268333332491e-01,5.395894824999999395e-01,2.678009976666666514e-01,-1.115090589499999896e-01,9.022450256666665613e-02,-3.146826403333333744e-01,1.240355121666666532e-01,-2.382778308333333150e-01,-1.204959983333333096e+00,-5.318892701666666500e-01,-3.707332168333333233e-01,-3.005220723333333344e-01,-9.680526626666667855e-01,-4.007078521666666560e-01,-6.909785949999999732e-02,3.571060244999999522e-01],
    [-3.524451601666666102e+04,1.045503101333333234e+03,6.072272980000000189e+02,-3.444314049999999952e+03,2.666123271666666369e+03,7.970817084999999906e+02,-6.263194149999999354e+02,-1.545267753333333303e+03,1.359801093333333256e+03,-5.870160834999999224e+02,2.305140126666666447e+02,1.374966300000000047e+03,-6.956498179999999820e+02,3.869231181666665975e+01,-7.700581300000000056e+02,3.698957495000000222e+02,-4.320655946666665841e+02,-3.459555428333333538e+01,1.963452516666666554e+02,3.459984886666666739e+02,7.183818413333333410e+02,-3.235684219999999982e+02,5.798414158333333717e+02,-2.864099558333333562e+02,-8.912309368333333737e+01,-1.894645818333333409e+02,6.821036490000000185e+01,-1.564835063333333096e+02,2.896211211666666259e+02,9.965542909999999210e+01,8.046015046666667558e+01,-7.110988193333332674e+01,-6.485428398333334599e+01,-1.351040169999999989e+02,-1.106504832499999935e+02,-4.453583428333332961e+01,-1.192380177333333435e+01,4.814791359999999543e+01,-1.707370968333333039e+01,8.570314586666667367e+01,3.949453643333333019e+01,5.266651218333333162e+00,-4.900740473333333291e+00,-3.711994391666666360e+01,-8.406925565000000233e+01,-3.603067548333332581e+01,-5.094364869999999712e+01,2.523629083333333156e+01,6.081244949999998761e-01,1.470093364999999785e+01,2.796357154999999750e+01,3.517036686666666245e+00,1.823397486666666722e+01,1.804657524999999652e+01,-1.381051458333333315e+00,-1.060928247949999959e+00,-6.335057294999999478e+00,-1.122708111666666575e+01,3.713688199999999995e+00,-1.141094178333333353e+01,9.045534311666665772e+00,3.460428820000000183e+00,8.050197571666666718e+00,3.213330738333333159e+00,4.047388426666666206e+00,1.169360808333333424e+01,-8.813309821666666377e-02,2.593591981666666602e+00,4.206922104999999412e+00,2.919812391666666507e+00,7.546638396666667248e-01,-7.410683176666665872e+00,1.607785591666666569e+00,-7.765788881666666477e-01,-4.730216616666666596e+00,-8.330718526666665014e+00,-1.367236027999999770e+00,9.976616160000000288e-01,-1.709837108333333244e+00,-3.453620809999999874e+00,1.146076396666666497e+00,5.282699606999999298e-02,2.085167315000000077e+00,9.095944123333334769e-03,1.056096433833333181e+00,-7.006998508333333042e-01,1.875207456666666772e+00,1.246526484999999962e+00,-2.440758463333333239e+00,4.852378028333332871e-01,-5.039855791666665308e-01,-5.980062524999999463e-01,-2.488582483333333428e+00,-2.638519193333332957e+00,1.240993579750000048e-01,-3.723276016666666743e-01,-1.322961040000000033e+00,-1.467461736666666461e+00,-1.761334228333333307e-01,1.489932203333333427e-01,-2.313197593333333191e-01,-5.118570496666666747e-01,-3.465893650000000104e-02,6.979862301666666102e-01,-7.627697273333333694e-01,5.158099473333332963e-01,3.553671016666666849e-01,-1.389772968333333192e-01,1.137229841666666519e-01,-6.027877833333332713e-01,8.627669988333333539e-02,-4.543567983333333116e-01,-1.203793854999999802e+00,-6.207664176666666256e-01,-4.194000769999999823e-01,-1.376444687499999986e-01,-9.125108566666665366e-01,-4.224440295000000400e-01,-1.869481133333333323e-01,3.843212361666666355e-01],
    [-3.512340828333333775e+04,-2.479174700166666980e+02,6.857811921666666422e+02,-3.368332439999999679e+03,3.073528636666666898e+03,1.226412119999999959e+03,-1.031271942500000023e+03,-2.250596573333333254e+03,1.239738793333333433e+03,-3.798732438333332766e+02,3.953272666666666737e+02,1.481060851666666622e+03,-5.185939716666666754e+02,4.813934291666666354e+02,-8.385308185000000094e+02,4.129795184999999265e+02,-3.282057156666666629e+02,1.791049069999999688e+01,1.069661226666666636e+02,3.275184151666666708e+02,6.809645706666666456e+02,-3.329613850000000070e+02,5.054062208333332933e+02,-3.747881533333332982e+02,-5.784874673333332851e+01,-2.323098516666666455e+02,7.233528038333334109e+01,-1.870503928333333192e+02,3.040561296666666635e+02,4.796180460000000068e+01,2.194592388333333233e+01,-9.734658461666666085e+01,-1.683970591666666792e+02,-1.805565320000000042e+02,-1.783091231666666658e+02,-5.269373138333333628e+01,-3.161651819999999447e+01,4.346505863333332798e+01,-2.268239314999999579e+01,8.351372528333334344e+01,9.513928018333333014e+00,-1.517878015000000147e+01,-3.831075434999999629e+01,-3.968873804999999777e+01,-1.045317728333333207e+02,-3.538258044999999896e+01,-4.721521899999999761e+01,4.452124136666666487e+01,-4.048817541666666742e+00,1.067740500666666570e+01,2.551583228333332798e+01,-2.151348285000000082e+00,1.358908201666666571e+01,1.130299183333333346e+01,-2.253856351666666313e+00,-5.835280293333332757e+00,-5.552153853333333444e+00,-8.114274181666665697e+00,2.570336178333333166e+00,-5.896344656666665962e+00,1.184024066666666641e+01,-8.786345388333333117e-01,9.113902258333332895e+00,2.622756120000000024e+00,2.376477763333333382e+00,1.107635678333333473e+01,-8.844737009999998900e-01,3.652038143333333209e-01,5.329972879999999691e+00,3.406055098333333309e+00,1.913742843333332999e+00,-6.500177246666666520e+00,3.258557748333333226e+00,-2.695183598999999486e-01,-1.372639113833333147e+00,-6.911008276666665395e+00,-2.741983364999999839e+00,1.612442808333333311e+00,-8.333242494999998362e-01,-1.687936679999999967e+00,1.396819626666666592e+00,-2.688064219999999893e-01,2.036376946666666576e+00,1.921303239999999635e-01,3.867705536666666277e-01,8.028015649999999115e-02,1.884557224999999780e+00,1.999554479999999579e+00,-2.163551510000000011e+00,9.421743983333331629e-01,-7.980259143333332528e-01,1.617617153333333335e-01,-2.805216251666666771e+00,-2.951517251666666564e+00,-1.955613064999999762e-01,-2.570987191666666005e-01,-6.305778741666666631e-01,-1.329569011666666745e+00,-1.028724430166666481e-01,3.762998738333332982e-01,-2.104195191666666520e-01,-4.990127926666666491e-01,-3.398926639999999555e-02,6.164507661666666083e-01,-5.276286271666665861e-01,4.089991016666666424e-01,6.155664226666666128e-01,-1.312527588333333162e-01,1.651707908333333030e-01,-6.896822755000000527e-01,7.664682421666665912e-02,-5.319891696666666503e-01,-1.163312023333333389e+00,-5.993194534999999323e-01,-3.887142961666666952e-01,1.045063177333333260e-01,-8.490120648333332465e-01,-2.594259919999999942e-01,-2.659822023333333063e-01,3.984564758333333789e-01],
    [-3.563708419999999751e+04,-9.924753424999998970e+02,5.827187224999998989e+02,-2.840989931666666962e+03,3.452266506666666373e+03,1.459514740000000074e+03,-1.567629776666666658e+03,-2.667580028333333303e+03,9.799031738333331987e+02,-5.463242988000000366e+01,2.637047401666666815e+02,1.608894778333333306e+03,-3.992390853333333212e+02,7.224593811666666170e+02,-8.739069041666666635e+02,3.442460991666666246e+02,-1.402372679000000062e+02,-3.277061721666666472e+01,1.970258496666666588e+02,1.667773648333333369e+02,5.617919623333332311e+02,-3.440728589999999940e+02,4.128176549999999452e+02,-4.444922074999999495e+02,-4.524516708333333526e+01,-2.545587219999999888e+02,3.312312655000000206e+01,-1.328185861666666767e+02,2.516955350000000067e+02,-2.178563489333333081e+01,-3.395600483333333131e+01,-1.137303848333333320e+02,-2.311412545000000023e+02,-1.652903846666666823e+02,-2.308241236666666225e+02,-5.727960193333332484e+01,-6.093780786666665961e+01,2.544538184999999686e+01,-1.541417623333333253e+01,5.901451736666666648e+01,-1.345461615333333327e+01,-4.048878784999999425e+01,-5.979577181666665808e+01,-3.181462588333333130e+01,-9.606335116666664931e+01,-3.341949686666666253e+01,-4.291613046666666520e+01,6.656679923333332738e+01,-6.899326648333332201e+00,1.318732390833333490e+00,1.936265623333333252e+01,-7.604924219999999124e+00,4.020643264999999467e+00,1.050832516666666550e+01,-4.735227054999999297e+00,-6.485657651666667078e+00,-3.454576728333332625e+00,3.837676670666666290e+00,2.482701094999999913e+00,-8.755386914999999659e-01,1.861114839999999759e+01,-2.902446174999999684e+00,1.683953676666666510e+01,2.249091766666666992e+00,-8.251100873333333530e-02,9.513826249999999263e+00,-2.181873203333333233e+00,-2.817943684999999920e+00,8.549976871666666867e+00,3.020099398333333074e+00,4.359796503333333462e+00,-5.289113163333333034e+00,7.017837508333332863e+00,8.552387015000000314e-01,2.518039461666666590e+00,-3.286101679999999359e+00,-2.884529140000000158e+00,5.066824524999999468e+00,6.402541775000000213e-01,1.781512428333333342e-01,1.596987560000000084e+00,-5.989022881666665743e-01,2.022720556666666614e+00,5.545470729999999598e-02,-5.715633578333332299e-01,1.403884023333333175e+00,1.560253618333333314e+00,3.133566006666666404e+00,-1.838670859999999907e+00,1.891823613333333265e+00,-6.407532878333332960e-01,1.367800276666666592e+00,-2.239592431666666883e+00,-2.773625736666666342e+00,4.761563294999999751e-01,8.116443341666666755e-02,2.812451227000000165e-01,-1.224127428333333212e+00,2.182108393333332952e-01,6.252931741666667431e-01,-1.646808983333333254e-01,-3.678337233333333067e-01,-1.012745243833333281e-01,4.476385121666666134e-01,-2.420875921666666430e-01,2.207231558333333510e-01,9.689732276666666033e-01,-6.658715691666666769e-02,2.848738293333333282e-01,-5.842361618333332673e-01,2.297092361666666360e-01,-3.994353269999999512e-01,-1.029344173333333279e+00,-3.310433231666666809e-01,-3.071612390000000303e-01,4.598962999999999801e-01,-7.932898211666665755e-01,5.026639026666666205e-02,-2.857351816666666711e-01,4.192209295000000058e-01],
    [-3.602506576666666660e+04,-2.807332011666666403e+03,1.101249868000000106e+03,-2.064709068333333107e+03,3.462507939999999508e+03,1.157387535000000071e+03,-1.971156406666666498e+03,-2.374046906666666473e+03,7.436570703333333086e+02,1.305626918333333322e+02,-1.575593400333333136e+02,1.540075368333333017e+03,-3.156539644999999723e+02,8.022344346666665160e+02,-6.821285121666667237e+02,2.680690913333333469e+02,4.150393451666666067e+01,-1.252916539999999941e+02,3.942240478333333158e+02,-1.127561290499999842e+02,4.377234328333332769e+02,-2.921018441666666376e+02,3.741291243333333227e+02,-4.671852728333333289e+02,-2.433612994999999657e+01,-2.389113576666666745e+02,-2.790452516666666583e+01,-6.891735523333332836e+00,1.476878023333333090e+02,-8.601333396666666431e+01,-7.075706766666665715e+01,-9.095963831666665556e+01,-2.405850698333333071e+02,-9.511710474999999576e+01,-2.379586299999999710e+02,-5.262705461666666196e+01,-8.533402753333332669e+01,2.691826599999999736e+00,-2.335604693833333023e+00,2.059245661666666649e+01,-3.087156101666666430e+01,-7.241305781666666519e+01,-5.927394150000000650e+01,-1.878617793333333097e+01,-6.194834904999999736e+01,-2.060016033333333496e+01,-3.506905491666666563e+01,9.134093453333332491e+01,-7.754415348333333569e+00,-8.500420846666665753e+00,1.162040288999999760e+01,-1.350632680000000008e+01,-7.608995279999999362e+00,1.129079791666666743e+01,-9.783835504999998989e+00,-3.609910766666666326e+00,-3.101395138333333357e+00,2.320138958333333079e+01,5.426621186666666041e+00,4.020204991666666672e+00,2.985410304999999909e+01,-2.566912265000000026e+00,3.022599248333333222e+01,1.841814214999999866e+00,-2.003701026666666607e+00,6.814450509999999461e+00,-3.409182391666666589e+00,-6.233630389999999188e+00,1.172975985000000065e+01,1.986105928333333326e+00,6.787643243333334020e+00,-4.568487601666666897e+00,1.258476304999999940e+01,2.271742266666666676e+00,6.970739574999999633e+00,2.461697728333333224e+00,-1.840179881666666351e+00,1.106585194333333355e+01,2.596337208333332924e+00,1.889674388333333122e+00,1.578753621666666662e+00,-8.497344218333333643e-01,1.758599558333333146e+00,-8.706127098333332759e-02,-1.682151713333333243e+00,2.873187838333333133e+00,1.119671143333333507e+00,4.065772018333333016e+00,-1.688630819999999977e+00,3.301373146666666258e+00,-3.719813763333333356e-01,3.077922906666666680e+00,-7.507596606666666617e-01,-2.058813603333333297e+00,2.139362713333333055e+00,6.861711145000000123e-01,1.361978896666666605e+00,-1.189690499999999984e+00,6.850254159999999981e-01,8.038965161666666859e-01,-1.570751400000000020e-01,-1.994570838333332985e-01,-1.081593913499999948e-01,1.882295893333333359e-01,1.067479952499999912e-01,3.278208801166666159e-02,1.239243523333333430e+00,1.567440200333333408e-02,4.498419176666666464e-01,-4.322796766666666124e-01,5.836397183333332794e-01,-1.011824610499999916e-01,-7.368348609999998411e-01,1.761818193499999907e-01,-1.546704279999999709e-01,9.101636353333332208e-01,-7.470583794999999805e-01,4.285250546666666271e-01,-2.352161744999999859e-01,4.564652256666666408e-01],
    [-3.593869698333332781e+04,-3.419386325000000397e+03,1.834110133333333124e+03,-1.320574933333333320e+03,3.299880318333333435e+03,8.487592026666666243e+02,-1.971025881666666464e+03,-1.757661418333333131e+03,5.958323520000000144e+02,8.533036941666665598e+01,-5.247848033333333433e+02,1.334516004999999950e+03,-1.970872300000000052e+02,7.568420271666666395e+02,-3.979511326666666946e+02,2.208337630000000047e+02,1.586018744999999797e+02,-1.070622986500000025e+02,5.693222094999999854e+02,-3.768391303333332871e+02,3.432428176666666673e+02,-2.091242516666666234e+02,3.554453116666666688e+02,-4.901202971666666031e+02,1.417729785000000131e+00,-1.952410313333333249e+02,-6.578355379999999286e+01,1.267548943333333256e+02,5.403947668333333354e+01,-1.514501591666666513e+02,-7.701502630000000238e+01,-4.580828799999999745e+01,-2.279279498333332867e+02,-5.164375859999998930e-01,-2.048060831666666388e+02,-4.086046186666666813e+01,-9.995905594999999266e+01,-1.841563259999999858e+01,5.512871699999999375e-01,-1.019213031333333319e+01,-5.757346219999999448e+01,-1.002151380333333179e+02,-4.629170291666666515e+01,-6.477227588333333230e+00,-2.403549649999999716e+01,-2.388244206666667591e-01,-2.583772903333333204e+01,1.095127029999999877e+02,-7.020442649999998785e+00,-1.658151559999999947e+01,1.391531938333333329e+00,-2.205789263333333139e+01,-1.770175414999999930e+01,5.530991355000000276e+00,-1.469756521666666416e+01,-1.605870011666666652e+00,-5.070926684999999878e+00,4.232406584999999666e+01,9.452609414999999515e+00,6.675144299999999475e+00,4.027342409999999973e+01,-1.573609471666666648e+00,4.361359213333333429e+01,1.444586178333333359e+00,-2.930765383333333141e+00,2.392629636666666393e+00,-4.282444690000000165e+00,-9.752275006666666357e+00,1.221464601666666461e+01,6.813526771666666981e-01,7.522439019999999310e+00,-4.325378516666665618e+00,1.792638644999999897e+01,3.029773333333332985e+00,1.049076156166666607e+01,8.310949826666666596e+00,-6.946372613333333668e-01,1.704415321666666827e+01,4.288918070000000249e+00,2.982832584999999703e+00,1.446681048333333219e+00,-9.271300183333333056e-01,1.064314860000000085e+00,6.982574396666665906e-02,-2.925663253333333103e+00,4.009389668333333212e+00,6.733070776666666424e-01,4.094719734999999972e+00,-1.854833838333333151e+00,4.705252099999999160e+00,-3.902218191666665947e-01,4.757261543333332732e+00,1.015541212833333429e+00,-1.139670119000000037e+00,3.940426473333333401e+00,1.277999238333333176e+00,2.237306269999999930e+00,-1.296495590000000142e+00,1.178438115000000064e+00,9.237207844999999473e-01,-1.800484758333333046e-01,-3.313202154000000066e-02,4.619033259133333014e-02,-1.646944403999999751e-01,5.047158868333333492e-01,-1.210858549666666562e-01,1.257045441666666541e+00,-2.876411640000000203e-03,6.043836258333332712e-01,-4.004477209999999232e-01,1.031994443166666775e+00,1.842907799999999874e-01,-3.760271891666666644e-01,7.146833506666666613e-01,2.567521063333333062e-03,1.294383630000000007e+00,-7.601061553333333665e-01,7.873692418333333443e-01,-1.394357869999999777e-01,4.880072318333333325e-01],
    [-3.482698883333332924e+04,-3.221193844999999783e+03,1.160955964999999878e+03,-6.271627915000000257e+02,2.817482359999999517e+03,9.005836294999999154e+02,-1.824071404999999686e+03,-1.631556478333333416e+03,5.794603469999999561e+02,-8.501480455000000802e+01,-6.920553258333333133e+02,1.089381131666666761e+03,-1.274503819999999905e+02,5.271085271666665903e+02,-2.294486156666666261e+02,1.928475091666666401e+02,2.464567108333333181e+02,2.900095429149999759e+01,6.274250166666666928e+02,-5.911920478333333904e+02,3.318625586666666436e+02,-1.804803121666666641e+02,2.913208455000000185e+02,-4.679652329999999552e+02,1.886467878333333203e+01,-1.246428294999999764e+02,-6.658023958333332359e+01,2.258109876666666764e+02,-2.953214039999999763e+00,-1.904201078333333044e+02,-5.793736624999999663e+01,-2.387172953333333680e+00,-1.993019616666666707e+02,8.989467191666665258e+01,-1.502214103333333242e+02,-2.360193896666666546e+01,-1.043974594999999965e+02,-3.200934583333332739e+01,-1.234288501999999887e+01,-2.014294344999999709e+01,-9.249474566666665964e+01,-1.148255616666666583e+02,-2.718056684999999817e+01,4.453743829999999626e+00,-3.555651979999999934e+00,2.004133241666666976e+01,-1.622785133333333363e+01,1.082357256666666672e+02,-4.341359796666667492e+00,-2.311878958333333145e+01,-1.032399671666666663e+01,-3.285893831666666642e+01,-2.392636988333333292e+01,-9.542257910000000010e+00,-1.793259351666666745e+01,-7.028045524999999571e-01,-9.837399846666667003e+00,5.186431693333332760e+01,1.212662801666666645e+01,5.367912279999999647e+00,4.313360353333333563e+01,-7.191928614999999470e-01,5.006249116666666055e+01,1.515625768333332957e+00,-3.018265541666666607e+00,-3.144157101666666065e+00,-4.789164456666666680e+00,-1.304064006666666486e+01,8.048628146666667149e+00,-1.384953416666666604e+00,6.525468161666666767e+00,-4.906935888333332940e+00,2.056193809999999900e+01,2.598832973333333296e+00,1.174623098333333360e+01,1.194319224999999918e+01,-4.091676594999999611e-02,1.997353481666666397e+01,4.642121424999999135e+00,2.800828945000000125e+00,1.449530003333333372e+00,-7.080118220000000129e-01,3.654365793333333445e-02,4.808451166666666277e-01,-4.097684151666666885e+00,4.260385099999999703e+00,7.115640326666666793e-02,3.020215389999999722e+00,-2.503738588333333404e+00,5.742696131666666481e+00,-8.381043923333333368e-01,5.841974153333332254e+00,2.370529173333333350e+00,-2.643741086666666629e-01,4.953007031666667004e+00,1.402921095000000173e+00,2.415073989999999782e+00,-1.514272853333333169e+00,1.616955518333333064e+00,1.001483453499999898e+00,-1.504541973333333171e-01,9.811001938333333006e-02,3.378776534999999859e-01,-5.479133895000000143e-01,8.765217549999999580e-01,-2.293302935000000042e-01,9.555768301666666131e-01,-2.484489521666666534e-01,8.187283844999999616e-01,-5.644854093333332434e-01,1.452496484999999948e+00,3.352968813333333520e-01,-3.660952719999999855e-02,1.089973634999999996e+00,6.853901525000000161e-02,1.411817741666666626e+00,-8.297801091666665574e-01,1.047865021666666507e+00,-3.211018278333332976e-02,4.629648746666666925e-01],
    [-3.402555114999999932e+04,-3.145880931666666584e+03,2.592144338333333508e+03,-1.871953196666666486e+02,2.179818614999999681e+03,1.597959156666666786e+03,-2.018500048333333325e+03,-1.877460854999999810e+03,5.736866431666666131e+02,-3.150865534999999795e+02,-6.870741653333333261e+02,8.347091975000000730e+02,-9.763028918333333195e+01,1.115534320333333227e+02,-7.815625843333330991e+00,1.732227611666666576e+02,3.334069413333333500e+02,1.379300596666666650e+02,5.431893185000000130e+02,-7.069398746666665829e+02,3.415936431666666522e+02,-1.955657796666666854e+02,1.484987393333333330e+02,-3.751014411666666888e+02,2.328621543333333221e+01,-1.846492787333333041e+01,-6.497049461666665593e+01,2.868191630000000032e+02,-1.387995381666666539e+01,-1.860182968333333520e+02,-2.215952208333333218e+01,1.583004820000000024e+01,-1.474977710000000002e+02,1.508790705000000116e+02,-9.709833578333334003e+01,-2.539908746666666328e+00,-9.491760651666666604e+01,-3.610548903333332760e+01,-3.347310474999999741e+01,-8.613853058333333479e+00,-1.280361656666666477e+02,-1.129571019999999919e+02,-8.411164416666666810e+00,1.537642029999999949e+01,-4.485560384999999428e+00,3.539064534999999978e+01,-7.763389883333332797e+00,8.306292856666667035e+01,7.863771036666664105e-02,-2.800490646666666450e+01,-2.159415086666666639e+01,-4.092912196666666347e+01,-2.658257831666666249e+01,-3.014905294999999796e+01,-1.866541019999999662e+01,-5.303251044999999220e-01,-1.682911169999999856e+01,4.787645393333333033e+01,1.252038851666666552e+01,-1.596233423333333346e-01,3.603859616666666454e+01,-7.141965828333333155e-01,4.622400970000000342e+01,2.015361998333333293e+00,-2.849467766666666790e+00,-8.696643266666665539e+00,-4.190259471666666791e+00,-1.605554658333333151e+01,3.471990973333333175e-02,-4.497710538333333119e+00,4.501601894999999409e+00,-6.296327245000000516e+00,1.916517841666666300e+01,1.600492188333333177e+00,1.020871634999999955e+01,1.252287516666666534e+01,-3.221115665000000017e-01,1.855259851666666648e+01,3.259905939999999447e+00,1.429431176666666525e+00,1.629666304999999760e+00,-3.559208884999999767e-01,-1.097737307333333412e+00,1.018380790666666424e+00,-5.099346276666666178e+00,3.725178416666666159e+00,-7.952354766666666075e-01,1.259018034499999938e+00,-3.466154855000000090e+00,6.179277193333334139e+00,-1.417420959999999841e+00,6.000462001666665657e+00,3.077199364999999798e+00,3.049279574999999576e-01,4.811502244999999789e+00,8.883504213333333066e-01,1.833490209999999676e+00,-1.715341821666666711e+00,1.849344646666666536e+00,1.051581828333333135e+00,-6.421436496666665938e-02,1.935827961666666541e-01,6.398668898333332855e-01,-8.983707993333331920e-01,1.230135703333333552e+00,-2.836282466666666391e-01,4.738513224999999496e-01,-6.766880618333332986e-01,1.127669118333333165e+00,-8.389197531666665597e-01,1.726920323333333229e+00,3.652385761666666619e-01,1.992031678333333056e-01,1.237251453333333195e+00,5.938262780000000060e-03,1.212766339999999943e+00,-9.018435674999999430e-01,1.118432191666666409e+00,2.079761458333333202e-02,3.406409548333333426e-01],
    [-3.429175523333332967e+04,-3.426431281666666109e+03,3.628664608333333035e+03,1.861676218333333281e+02,2.338595583333333252e+03,1.474227468333333263e+03,-1.892272091666666711e+03,-9.637970193333333100e+02,5.640107674999999290e+02,-2.566280325000000175e+02,-6.851437519999999495e+02,9.091892964999999549e+02,4.679041826666666282e+01,-1.488723681666666607e+02,4.484750773333332745e+02,2.008827533333333406e+02,4.570790803333333088e+02,1.410894953333333319e+02,4.026044364999999630e+02,-7.272463644999999133e+02,2.926238899999999603e+02,-2.268098273333333168e+02,-4.711796905333332575e+01,-2.661889569999999594e+02,1.747891249999999985e+01,1.099664460500000018e+02,-7.632652165000000366e+01,3.253124443333333033e+02,-9.986002183333333448e+00,-1.418480476666666732e+02,1.625176783666666580e+01,4.896181673333332984e-01,-8.111755959999999277e+01,1.664079546666666545e+02,-7.444360368333332190e+01,1.750773316666666446e+01,-7.503534269999998685e+01,-2.625591178333333175e+01,-5.348019745000000569e+01,1.788187151666666352e+01,-1.563366271666666591e+02,-9.074993008333333933e+01,6.529894033333333070e+00,2.033012549999999763e+01,-9.983088491666665121e+00,3.973271283333333770e+01,-8.298759168333333491e+00,4.773561748333333554e+01,3.266244461666666155e+00,-3.159481868333332955e+01,-3.059415516666666335e+01,-4.096836038333332652e+01,-2.434112111666666678e+01,-4.873144876666665937e+01,-1.558857194999999862e+01,-1.042548923999999877e+00,-2.650931014999999746e+01,3.429661875000000038e+01,1.033056281666666720e+01,-8.379888771666665903e+00,2.450485796666666261e+01,1.230844701166666555e+00,3.442957541666666543e+01,1.665459636666666743e+00,-2.669468914999999942e+00,-1.333726913333333286e+01,-2.027019863333333394e+00,-1.809227184999999949e+01,-9.136293679999999640e+00,-8.267421978333333143e+00,1.966965078333333228e+00,-8.473915476666666891e+00,1.444377034999999942e+01,9.873063583333332449e-01,7.166466691666665945e+00,1.109995206666666689e+01,-2.713030309833333598e-01,1.396981815000000005e+01,5.630138128500000727e-01,-3.326095685016666748e-01,1.758258163333333179e+00,-4.900438546666666118e-02,-2.170624991666666226e+00,1.442645924999999885e+00,-5.877775501666667068e+00,2.853371618333333082e+00,-1.853410231666666519e+00,-6.564184189999999752e-01,-4.223074369999999078e+00,5.860833753333333007e+00,-1.757526019999999800e+00,5.576884685000000452e+00,3.220172298333332961e+00,7.445728014999999367e-01,3.852143039999999630e+00,-2.755602356666666045e-02,8.478737554999999926e-01,-1.559417251666666449e+00,1.900515744999999868e+00,1.093749754999999935e+00,4.077633024999999245e-03,2.324729898333333378e-01,8.002986468333332937e-01,-1.213435499999999889e+00,1.587552806666666427e+00,-2.753033084999999547e-01,-2.374900860000001002e-03,-1.021974823499999907e+00,1.431202850000000026e+00,-1.084549014999999894e+00,1.831437026666666412e+00,3.361654065000000413e-01,3.184197946666666446e-01,1.210078008333333344e+00,-8.653211706666666392e-02,8.103248028333333020e-01,-8.149477233333333182e-01,1.044133189999999933e+00,-3.661912488333333299e-02,9.473963354999999364e-02],
    [-3.435685506666666333e+04,-3.277096546666666200e+03,4.673535239999999249e+03,5.687414606666666259e+02,2.407729171666666389e+03,9.739456369999999197e+02,-1.278948643333333393e+03,2.508036462833333076e+02,7.833317524999998795e+02,-3.051008061666666435e+02,-8.570101921666665703e+02,1.163250375000000076e+03,2.444724958333333120e+02,-2.452051226666666821e+02,8.572485263333333023e+02,3.424831906666665873e+02,5.672003224999999702e+02,4.639882371666666216e+01,2.786713859999999841e+02,-6.439636886666667124e+02,1.707808974999999805e+02,-2.646755271666665976e+02,-1.907520406666666304e+02,-1.402607981666666603e+02,6.116870896666666724e+00,2.288566429999999912e+02,-1.049810847833333298e+02,3.446599193333333346e+02,-1.155210943333333518e+01,-7.231166026666666369e+01,3.865895526666666626e+01,-2.796702599999999705e+01,-2.103848348333333362e+01,1.524174411666666344e+02,-4.751565658333333175e+01,3.327725279999999941e+01,-5.005013651666666163e+01,-3.615771159166666138e+00,-7.008993294999999080e+01,4.554420213333332867e+01,-1.687535608333333244e+02,-5.242608259999999376e+01,1.771657270000000040e+01,1.265555946499999962e+01,-4.909807979999999183e+00,4.092416071666666966e+01,-1.622735774999999947e+01,1.961211693333332917e+01,4.926987666666667209e+00,-3.336392146666666747e+01,-3.541451186666667184e+01,-3.349731436666666440e+01,-1.801345346666666458e+01,-5.919618213333332335e+01,-7.304981074999998825e+00,-1.565187324999999907e+00,-3.663640439999999643e+01,1.722276294999999990e+01,8.335485466666666454e+00,-1.504810964999999889e+01,1.598907798333333297e+01,6.319080831666666676e+00,1.821769441666666367e+01,2.849057633333333395e-01,-2.199194763333333302e+00,-1.585053874999999834e+01,1.301044967833333343e+00,-1.823119088333332982e+01,-1.698070824999999928e+01,-1.096670533333333353e+01,-7.715207588333332644e-01,-1.061022476666666492e+01,8.469792046666665186e+00,1.363484481666666470e+00,4.511555836666667041e+00,9.517353173333333416e+00,1.156420029666666682e+00,7.980311904999999761e+00,-2.902718781666666636e+00,-1.750406466666666550e+00,1.720343186666666746e+00,2.404260043333333319e-01,-2.967045944999999740e+00,1.740595561666666402e+00,-6.166082121666667248e+00,1.958230111666666495e+00,-2.734696121666666535e+00,-2.298872808333333406e+00,-4.301125509999999430e+00,4.917183726666666033e+00,-1.754207128333333365e+00,5.022300443333333142e+00,3.016456804999999797e+00,1.282679914999999893e+00,2.662942593333332830e+00,-1.098309385333333221e+00,-3.073042286666667275e-02,-1.079897953999999993e+00,1.887744194999999792e+00,1.108409751666666665e+00,4.111910169999999365e-02,2.000081498333333152e-01,7.817996026666665932e-01,-1.420963525000000116e+00,1.895544098333333149e+00,-2.138863540000000008e-01,-3.733193281666666863e-01,-1.075827869999999908e+00,1.582056916666666702e+00,-1.231458254999999946e+00,1.781885993333333307e+00,2.707743813333333138e-01,3.719283491666666164e-01,1.103031259999999847e+00,-1.419733878333333255e-01,4.028620503333333325e-01,-5.424140574999999354e-01,9.352463398333332734e-01,-1.891612096666666631e-01,-1.983824428333333112e-01],
    [-3.354509015000000363e+04,-3.167137361666666493e+03,5.579784734999999273e+03,2.534437926666666385e+02,2.502441873333333206e+03,5.464680281666666133e+02,-5.854523681666667017e+02,1.045570982499999900e+03,9.546599976666665270e+02,-7.924226679999999305e+02,-7.832146836666665877e+02,1.343731003333333319e+03,2.456574641666666707e+02,-6.964404810000003110e+00,9.740991258333333462e+02,5.522621033333333571e+02,5.799768474999998489e+02,4.074759790000000237e+01,2.818603776666666363e+02,-4.803309073333333004e+02,5.650247026666666272e+01,-2.619883651666666537e+02,-1.452347453333333078e+02,-9.717243968333332305e+01,-1.523789160333333292e+01,2.961668714999999565e+02,-1.557435428333333221e+02,3.394223900000000071e+02,-3.352026161666666226e+00,-1.440337873333333363e+01,3.975781076666666536e+01,-2.998210893333332905e+01,-1.598515809999999959e+01,1.209792400000000043e+02,-1.567815816666666429e+01,4.160146194999999381e+01,-2.694459085000000087e+01,7.184326921666666088e+00,-8.654322343333332412e+01,6.959153468333332171e+01,-1.758004851666666752e+02,-1.480489504500000031e+01,2.251237266666666770e+01,-6.027667661666666454e+00,7.133939716666667152e+00,3.627071725000000413e+01,-3.245524565000000194e+01,6.004139273333332305e+00,6.191494493333332017e+00,-3.373289243333333332e+01,-4.016590756666666095e+01,-2.469089291666666597e+01,-1.081095221166666676e+01,-6.260839466666666198e+01,3.363514703333333244e+00,-4.885046351666666453e+00,-4.108312778333333171e+01,3.208315796666666220e+00,8.002783423333331925e+00,-1.903932354999999887e+01,1.329779938333333256e+01,1.293773181666666616e+01,9.021494999999990494e-02,-1.399414306666666663e+00,-1.655709384999999978e+00,-1.609463631666666572e+01,4.812562043333333150e+00,-1.731999019999999945e+01,-2.219582283333333450e+01,-1.110329794999999997e+01,-4.291780561666666216e+00,-1.147319426666666686e+01,3.882565768333333445e+00,3.003308158333333644e+00,2.597042103333333074e+00,8.306118306666665063e+00,3.743450399999999956e+00,1.378091995000000125e+00,-6.514490921666666878e+00,-3.278909213333333739e+00,1.703674973333333176e+00,3.290918919999999970e-01,-3.297632189999999852e+00,2.207382624999999710e+00,-6.193857629999999226e+00,1.225887818333333490e+00,-3.124726399999999238e+00,-3.455325494999999414e+00,-3.889550856666666334e+00,3.655253270000000221e+00,-1.328531833333333356e+00,4.394014424999999946e+00,2.519701418333333276e+00,1.740660786666666571e+00,1.418309829999999883e+00,-2.072005426666666761e+00,-8.134684826666666035e-01,-8.429084056666666935e-01,1.808760369999999895e+00,1.155180533333333370e+00,2.486531591833333193e-02,1.122081012333333155e-01,6.969120076666666108e-01,-1.539152706666666592e+00,2.082185795000000006e+00,-1.699398849999999850e-01,-5.908624851666666178e-01,-9.450924221666666680e-01,1.457509843333333110e+00,-1.273997849999999987e+00,1.573630238333333153e+00,1.785212939999999970e-01,3.145763756666666300e-01,9.303596453333332628e-01,-1.382059898333333203e-01,8.682193909999999515e-02,-2.891055746666666981e-01,8.234603806666666026e-01,-3.849765185000000312e-01,-3.952373486666667102e-01],
    [-3.217541033333333326e+04,-2.761199963333333471e+03,5.752023870000000898e+03,-7.605004623333333313e+01,2.811726653333333161e+03,-2.082015154000000052e+02,1.484237792933333253e+02,1.430993916666666564e+03,1.027796253333333425e+03,-1.133661816666666709e+03,-4.154516846666666083e+02,1.429447926666666717e+03,1.413469388333333256e+02,3.948894179999999778e+02,8.436195471666665071e+02,7.160173209999999244e+02,6.241351436666666359e+02,2.036518384999999967e+02,4.183458613333333460e+02,-2.735154096666666419e+02,-8.962867401666666467e+01,-2.309550228333333166e+02,2.306589470000000119e+01,-6.833649938333333296e+01,-7.807690420000000131e+01,3.168293796666666253e+02,-1.889086098333333439e+02,2.996676654999999982e+02,2.724660476666666753e+01,1.392515415000000090e+01,2.935431499999999616e+01,-1.405034945000000057e+01,-5.030971143333331952e+01,8.439292796666666163e+01,2.123362143833332993e+00,3.569125858333333667e+01,-1.195978937499999972e+01,-6.994300369999999489e+00,-9.101043394999999236e+01,8.852757443333332787e+01,-1.855081691666666757e+02,1.451873002666666679e+01,2.336506699999999626e+01,-2.876514506666666549e+01,1.880226713333333066e+01,2.405630901666666688e+01,-5.969196648333332433e+01,3.358745956666666643e+00,6.547400394999999484e+00,-3.458484436666666539e+01,-4.957324069999999949e+01,-1.512883491666666558e+01,-5.429496876666666694e+00,-6.024193566666666300e+01,1.175949796666666636e+01,-1.068469610166666506e+01,-3.854268291666666357e+01,-4.863571006666666641e+00,9.731330651666667109e+00,-2.062094691666666435e+01,1.503349839999999915e+01,1.906757341666666505e+01,-1.664516481666666436e+01,-2.995463791666666875e+00,-1.622228070000000022e+00,-1.545528918333333301e+01,8.419724679999999850e+00,-1.592052588333332963e+01,-2.430860843333332966e+01,-8.875646053333332119e+00,-8.420592064999999238e+00,-1.075833749999999966e+01,1.168984528999999828e+00,5.457282665000000144e+00,1.390467138333333352e+00,7.423205826666666951e+00,7.088192261666665495e+00,-4.776330705000000343e+00,-1.004972385666666668e+01,-4.722852295000000034e+00,1.847503474999999895e+00,-5.362197130000000145e-02,-3.359149519999999001e+00,2.937152100000000043e+00,-6.003484501666665807e+00,6.792892621666666297e-01,-2.886976246666666412e+00,-4.162096518333333606e+00,-3.181631739999999819e+00,2.178593503333333459e+00,-6.043987548333332738e-01,3.771622031666666430e+00,1.740640246666666613e+00,2.218150669999999991e+00,3.190642193333333432e-01,-2.886094309999999830e+00,-1.347074936666666556e+00,-1.113286400000000009e+00,1.682589821666666596e+00,1.289920529999999843e+00,-1.253010998833333223e-01,-5.020725169999999508e-03,5.841320904999999231e-01,-1.594171898333333282e+00,2.090086534999999746e+00,-9.829411646666666447e-02,-6.796114569999999189e-01,-7.297955631666666054e-01,1.088247086833333377e+00,-1.243097519999999845e+00,1.266359154999999959e+00,3.455765499999999962e-02,2.076305343333333109e-01,7.474109579999999031e-01,-9.551089588333333547e-02,-4.459980773333332982e-02,-1.751123065000000090e-01,7.432538854999999334e-01,-6.105252684999999957e-01,-4.759468213333332698e-01]])
    return models,coeffs

def get_cals10k():
    models= ['-9950', '-9900', '-9850', '-9800', '-9750', '-9700', '-9650', '-9600', '-9550', '-9500', '-9450', '-9400', '-9350', '-9300', '-9250', '-9200', '-9150', '-9100', '-9050', '-9000', '-8950', '-8900', '-8850', '-8800', '-8750', '-8700', '-8650', '-8600', '-8550', '-8500', '-8450', '-8400', '-8350', '-8300', '-8250', '-8200', '-8150', '-8100', '-8050', '-8000', '-7950', '-7900', '-7850', '-7800', '-7750', '-7700', '-7650', '-7600', '-7550', '-7500', '-7450', '-7400', '-7350', '-7300', '-7250', '-7200', '-7150', '-7100', '-7050', '-7000', '-6950', '-6900', '-6850', '-6800', '-6750', '-6700', '-6650', '-6600', '-6550', '-6500', '-6450', '-6400', '-6350', '-6300', '-6250', '-6200', '-6150', '-6100', '-6050', '-6000', '-5950', '-5900', '-5850', '-5800', '-5750', '-5700', '-5650', '-5600', '-5550', '-5500', '-5450', '-5400', '-5350', '-5300', '-5250', '-5200', '-5150', '-5100', '-5050', '-5000', '-4950', '-4900', '-4850', '-4800', '-4750', '-4700', '-4650', '-4600', '-4550', '-4500', '-4450', '-4400', '-4350', '-4300', '-4250', '-4200', '-4150', '-4100', '-4050', '-4000', '-3950', '-3900', '-3850', '-3800', '-3750', '-3700', '-3650', '-3600', '-3550', '-3500', '-3450', '-3400', '-3350', '-3300', '-3250', '-3200', '-3150', '-3100', '-3050', '-3000', '-2950', '-2900', '-2850', '-2800', '-2750', '-2700', '-2650', '-2600', '-2550', '-2500', '-2450', '-2400', '-2350', '-2300', '-2250', '-2200', '-2150', '-2100', '-2050', '-2000', '-1950', '-1900', '-1850', '-1800', '-1750', '-1700', '-1650', '-1600', '-1550', '-1500', '-1450', '-1400', '-1350', '-1300', '-1250', '-1200', '-1150', '-1100', '-1050', '-1000', '-950', '-900', '-850', '-800', '-750', '-700', '-650', '-600', '-550', '-500', '-450', '-400', '-350', '-300', '-250', '-200', '-150', '-100', '-50', '0', '50', '100', '150', '200', '250', '300', '350', '400', '450', '500', '550', '600', '650', '700', '750', '800', '850', '900', '950', '1000', '1050', '1100', '1150', '1200', '1250', '1300', '1350', '1400', '1450', '1500', '1550', '1600', '1650', '1700', '1750', '1800', '1850', '1900', '1950']
    return models,coeffs


def unpack(gh):
    """ 
    unpacks gh list into l m g h type list
    """
    data=[]
    k,l=0,1
    while k+1<len(gh):
        for m in range(l+1):
            if m==0:
                data.append([l,m,gh[k],0])
                k+=1
            else:
                data.append([l,m,gh[k],gh[k+1]])
                k+=2
    return data


def magsyn(gh,sv,b,date,itype,alt,colat,elong):
    """
# Computes x, y, z, and f for a given date and position, from the
# spherical harmonic coeifficients of the International Geomagnetic
# Reference Field (IGRF).
# From Malin and Barraclough (1981), Computers and Geosciences, V.7, 401-405.
#
# Input:
#       date  = Required date in years and decimals of a year (A.D.)
#       itype = 1, if geodetic coordinates are used, 2 if geocentric
#       alt   = height above mean sea level in km (if itype = 1)
#       alt   = radial distance from the center of the earth (itype = 2)
#       colat = colatitude in degrees (0 to 180)
#       elong = east longitude in degrees (0 to 360)
#               gh        = main field values for date (calc. in igrf subroutine)
#               sv        = secular variation coefficients (calc. in igrf subroutine)
#               begin = date of dgrf (or igrf) field prior to required date
#
# Output:
#       x     - north component of the magnetic force in nT
#       y     - east component of the magnetic force in nT
#       z     - downward component of the magnetic force in nT
#       f     - total magnetic force in nT
#
#       NB: the coordinate system for x,y, and z is the same as that specified
#       by itype.
#
# Modified 4/9/97 to use DGRFs from 1945 to 1990 IGRF
# Modified 10/13/06 to use  1995 DGRF, 2005 IGRF and sv coefficient
# for extrapolation beyond 2005. Coefficients from Barton et al. PEPI, 97: 23-26
# (1996), via web site for NOAA, World Data Center A. Modified to use
#degree and
# order 10 as per notes in Malin and Barraclough (1981). 
# coefficients for DGRF 1995 and IGRF 2005 are from http://nssdcftp.gsfc.nasa.gov/models/geomagnetic/igrf/fortran_code/
# igrf subroutine calculates
# the proper main field and secular variation coefficients (interpolated between
# dgrf values or extrapolated from 1995 sv values as appropriate).
    """
#
#       real gh(120),sv(120),p(66),q(66),cl(10),sl(10)
#               real begin,dateq
    p=numpy.zeros((66),'f')
    q=numpy.zeros((66),'f')
    cl=numpy.zeros((10),'f')
    sl=numpy.zeros((10),'f')
    begin=b
    t = date - begin
    r = alt
    one = colat*0.0174532925
    ct = numpy.cos(one)
    st = numpy.sin(one)
    one = elong*0.0174532925
    cl[0] = numpy.cos(one)
    sl[0] = numpy.sin(one)
    x,y,z = 0.0,0.0,0.0
    cd,sd = 1.0,0.0
    l,ll,m,n = 1,0,1,0
    if itype!=2:
#
# if required, convert from geodectic to geocentric
        a2 = 40680925.0
        b2 = 40408585.0
        one = a2 * st * st
        two = b2 * ct * ct
        three = one + two
        rho = numpy.sqrt(three)
        r = numpy.sqrt(alt*(alt+2.0*rho) + (a2*one+b2*two)/three)
        cd = (alt + rho) /r
        sd = (a2 - b2) /rho * ct * st /r
        one = ct
        ct = ct*cd - st*sd
        st  = st*cd + one*sd
    ratio = 6371.2 /r
    rr = ratio * ratio
#
# compute Schmidt quasi-normal coefficients p and x(=q)
    p[0] = 1.0
    p[2] = st
    q[0] = 0.0
    q[2] = ct
    for k in range(1,66):
        if n < m:   # else go to 2
            m = 0
            n = n + 1
            rr = rr * ratio
            fn = n
            gn = n - 1
# 2
        fm = m
        if k != 2: # else go to 4
            if m == n:   # else go to 3
                one = numpy.sqrt(1.0 - 0.5/fm)
                j = k - n - 1
                p[k] = one * st * p[j]
                q[k] = one * (st*q[j] + ct*p[j])
                cl[m-1] = cl[m-2]*cl[0] - sl[m-2]*sl[0]
                sl[m-1] = sl[m-2]*cl[0] + cl[m-2]*sl[0]
            else:
# 3
                gm = m * m
                one = numpy.sqrt(fn*fn - gm)
                two = numpy.sqrt(gn*gn - gm) /one
                three = (fn + gn) /one
                i = k - n
                j = i - n + 1
                p[k] = three*ct*p[i] - two*p[j]
                q[k] = three*(ct*q[i] - st*p[i]) - two*q[j]
#
# synthesize x, y, and z in geocentric coordinates.
# 4
        one = (gh[l-1] + sv[ll+l-1]*t)*rr
        if m != 0: # else go to 7
            two = (gh[l] + sv[ll+l]*t)*rr
            three = one*cl[m-1] + two*sl[m-1]
            x = x + three*q[k]
            z = z - (fn + 1.0)*three*p[k]
            if st != 0.0: # else go to 5
                y = y + (one*sl[m-1] - two*cl[m-1])*fm*p[k]/st
            else: 
# 5
                y = y + (one*sl[m-1] - two*cl[m-1])*q[k]*ct
            l = l + 2
        else: 
# 7
            x = x + one*q[k]
            z = z - (fn + 1.0)*one*p[k]
            l = l + 1
        m = m + 1
#
# convert to coordinate system specified by itype
    one = x
    x = x*cd + z*sd
    z = z*cd - one*sd
    f = numpy.sqrt(x*x + y*y + z*z)
#
    return x,y,z,f
#
#
def measurements_methods(meas_data,noave):
    """
    get list of unique specs
    """
#
    version_num=get_version()
    sids=get_specs(meas_data)
# list  of measurement records for this specimen
#
# step through spec by spec 
#
    SpecTmps,SpecOuts=[],[]
    for spec in sids:
        TRM,IRM3D,ATRM,CR=0,0,0,0
        expcodes=""
# first collect all data for this specimen and do lab treatments
        SpecRecs=get_dictitem(meas_data,'er_specimen_name',spec,'T') # list  of measurement records for this specimen
        for rec in SpecRecs:
            if 'measurement_flag' not in rec.keys():rec['measurement_flag']='g'
            tmpmeths=rec['magic_method_codes'].split(":")
            meths=[]
            if "LP-TRM" in tmpmeths:TRM=1 # catch these suckers here!
            if "LP-IRM-3D" in tmpmeths: 
                IRM3D=1 # catch these suckers here!
            elif "LP-AN-TRM" in tmpmeths: 
                ATRM=1 # catch these suckers here!
            elif "LP-CR-TRM" in tmpmeths: 
                CR=1 # catch these suckers here!
#
# otherwise write over existing method codes
#
# find NRM data (LT-NO)
#
            elif float(rec["measurement_temp"])>=273. and float(rec["measurement_temp"]) < 323.:   
# between 0 and 50C is room T measurement
                if ("measurement_dc_field" not in rec.keys() or float(rec["measurement_dc_field"])==0 or rec["measurement_dc_field"]=="") and ("measurement_ac_field" not in rec.keys() or float(rec["measurement_ac_field"])==0 or rec["measurement_ac_field"]==""): 
# measurement done in zero field!
                    if  "treatment_temp" not in rec.keys() or rec["treatment_temp"].strip()=="" or (float(rec["treatment_temp"])>=273. and float(rec["treatment_temp"]) < 298.):   
# between 0 and 50C is room T treatment
                        if "treatment_ac_field" not in rec.keys() or rec["treatment_ac_field"] =="" or float(rec["treatment_ac_field"])==0: 
# no AF
                            if "treatment_dc_field" not in rec.keys() or rec["treatment_dc_field"]=="" or float(rec["treatment_dc_field"])==0:# no IRM!
                                if "LT-NO" not in meths:meths.append("LT-NO")
                            elif "LT-IRM" not in meths:
                                meths.append("LT-IRM") # it's an IRM
#
# find AF/infield/zerofield
#
                        elif "treatment_dc_field" not in rec.keys() or rec["treatment_dc_field"]=="" or float(rec["treatment_dc_field"])==0: # no ARM
                            if "LT-AF-Z" not in meths:meths.append("LT-AF-Z")
                        else: # yes ARM
                            if "LT-AF-I" not in meths: meths.append("LT-AF-I")
#
# find Thermal/infield/zerofield
#
                    elif float(rec["treatment_temp"])>=323:  # treatment done at  high T
                        if TRM==1:
                            if "LT-T-I" not in meths: meths.append("LT-T-I") # TRM - even if zero applied field! 
                        elif "treatment_dc_field" not in rec.keys() or rec["treatment_dc_field"]=="" or float(rec["treatment_dc_field"])==0.: # no TRM
                            if  "LT-T-Z" not in meths: meths.append("LT-T-Z") # don't overwrite if part of a TRM experiment!
                        else: # yes TRM
                            if "LT-T-I" not in meths: meths.append("LT-T-I")
#
# find low-T infield,zero field
#
                    else:  # treatment done at low T
                        if "treatment_dc_field" not in rec.keys() or rec["treatment_dc_field"]=="" or float(rec["treatment_dc_field"])==0: # no field
                            if "LT-LT-Z" not in meths:meths.append("LT-LT-Z")
                        else: # yes field
                            if "LT-LT-I" not in meths:meths.append("LT-LT-I")
                if "measurement_chi_volume" in rec.keys() or "measurement_chi_mass" in rec.keys():
                    if  "LP-X" not in meths:meths.append("LP-X")
                elif "measurement_lab_dc_field" in rec.keys() and rec["measurement_lab_dc_field"]!=0: # measurement in presence of dc field and not susceptibility; hysteresis!
                    if  "LP-HYS" not in meths:
                        hysq=raw_input("Is this a hysteresis experiment? [1]/0")
                        if hysq=="" or hysq=="1":
                            meths.append("LP-HYS")
                        else:
                            metha=raw_input("Enter the lab protocol code that best describes this experiment ")
                            meths.append(metha)
                methcode=""
                for meth in meths:
                    methcode=methcode+meth.strip()+":"
                rec["magic_method_codes"]=methcode[:-1] # assign them back
#
# done with first pass, collect and assign provisional method codes
            if "measurement_description" not in rec.keys():rec["measurement_description"]=""
            rec["er_citation_names"]="This study"
            SpecTmps.append(rec)
# ready for second pass through, step through specimens, check whether ptrm, ptrm tail checks, or AARM, etc.
#
    for spec in sids:
        MD,pTRM,IZ,ZI=0,0,0,0 # these are flags for the lab protocol codes
        expcodes=""
        NewSpecs,SpecMeths=[],[]
        experiment_name,measnum="",1
        if IRM3D==1:experiment_name="LP-IRM-3D"
        if ATRM==1: experiment_name="LP-AN-TRM"
        if CR==1: experiment_name="LP-CR"
        NewSpecs=get_dictitem(SpecTmps,'er_specimen_name',spec,'T')
#
# first look for replicate measurements
#
        Ninit=len(NewSpecs)
        if noave!=1:
            vdata,treatkeys=vspec_magic(NewSpecs) # averages replicate measurements, returns treatment keys that are being used
            if len(vdata)!=len(NewSpecs):
                print spec,'started with ',Ninit,' ending with ',len(vdata)
                NewSpecs=vdata
                print "Averaged replicate measurements"
#
# now look through this specimen's records - try to figure out what experiment it is
#
        if len(NewSpecs)>1: # more than one meas for this spec - part of an unknown experiment
            SpecMeths=get_list(NewSpecs,'magic_method_codes').split(":")
            if "LT-T-I" in  SpecMeths and experiment_name=="": # TRM steps, could be TRM acquisition, Shaw or a Thellier experiment or TDS experiment
    #
    # collect all the infield steps and look for changes in dc field vector
    #
                Steps,TI=[],1
                for rec in  NewSpecs: 
                    methods=get_list(NewSpecs,'magic_method_codes').split(":")
                    if "LT-T-I" in methods:Steps.append(rec)  # get all infield steps together
                rec_bak=Steps[0]
                if "treatment_dc_field_phi" in rec_bak.keys() and "treatment_dc_field_theta" in rec_bak.keys():   
                    if rec_bak["treatment_dc_field_phi"] !="" and rec_bak["treatment_dc_field_theta"]!="":   # at least there is field orientation info
                        phi0,theta0=rec_bak["treatment_dc_field_phi"],rec_bak["treatment_dc_field_theta"]
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            phi,theta=rec["treatment_dc_field_phi"],rec["treatment_dc_field_theta"]
                            if phi!=phi0 or theta!=theta0: ANIS=1   # if direction changes, is some sort of anisotropy experiment
                if "LT-AF-I" in SpecMeths and "LT-AF-Z" in SpecMeths: # must be Shaw :(
                    experiment_name="LP-PI-TRM:LP-PI-ALT-AFARM"
                elif TRM==1: 
                    experiment_name="LP-TRM"
            else: TI= 0 # no infield steps at all
            if "LT-T-Z" in  SpecMeths and experiment_name=="": # thermal demag steps
                if TI==0: 
                    experiment_name="LP-DIR-T" # just ordinary thermal demag
                elif TRM!=1: # heart pounding - could be some  kind of TRM normalized paleointensity or LP-TRM-TD experiment 
                    Temps=[]
                    for step in Steps: # check through the infield steps - if all at same temperature, then must be a demag of a total TRM with checks
                        if step['treatment_temp'] not in Temps:Temps.append(step['treatment_temp'])
                    if len(Temps)>1: 
                        experiment_name="LP-PI-TRM" # paleointensity normalized by TRM 
                    else: 
                        experiment_name="LP-TRM-TD" # thermal demag of a lab TRM (could be part of a LP-PI-TDS experiment)
                TZ=1
            else: TZ= 0 # no zero field steps at all
            if "LT-AF-I" in  SpecMeths: # ARM steps
                Steps=[]
                for rec in  NewSpecs: 
                    tmp=rec["magic_method_codes"].split(":")
                    methods=[]
                    for meth in tmp:
                        methods.append(meth.strip())
                    if "LT-AF-I" in methods:Steps.append(rec)  # get all infield steps together
                rec_bak=Steps[0]
                if "treatment_dc_field_phi" in rec_bak.keys() and "treatment_dc_field_theta" in rec_bak.keys():   
                    if rec_bak["treatment_dc_field_phi"] !="" and rec_bak["treatment_dc_field_theta"]!="":   # at least there is field orientation info
                        phi0,theta0=rec_bak["treatment_dc_field_phi"],rec_bak["treatment_dc_field_theta"]
                        ANIS=0
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            phi,theta=rec["treatment_dc_field_phi"],rec["treatment_dc_field_theta"]
                            if phi!=phi0 or theta!=theta0: ANIS=1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS==1:
                            experiment_name="LP-AN-ARM"
                if experiment_name=="":  # not anisotropy of ARM - acquisition?   
                        field0=rec_bak["treatment_dc_field"]
                        ARM=0
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            field=rec["treatment_dc_field"]
                            if field!=field0: ARM=1
                        if ARM==1:
                            experiment_name="LP-ARM"
                AFI=1
            else: AFI= 0 # no ARM steps at all
            if "LT-AF-Z" in  SpecMeths and experiment_name=="": # AF demag steps
                if AFI==0: 
                    experiment_name="LP-DIR-AF" # just ordinary AF demag
                else: # heart pounding - a pseudothellier?
                    experiment_name="LP-PI-ARM" 
                AFZ=1
            else: AFZ= 0 # no AF demag at all
            if "LT-IRM" in SpecMeths: # IRM
                Steps=[]
                for rec in  NewSpecs: 
                    tmp=rec["magic_method_codes"].split(":")
                    methods=[]
                    for meth in tmp:
                        methods.append(meth.strip())
                    if "LT-IRM" in methods:Steps.append(rec)  # get all infield steps together
                rec_bak=Steps[0]
                if "treatment_dc_field_phi" in rec_bak.keys() and "treatment_dc_field_theta" in rec_bak.keys():   
                    if rec_bak["treatment_dc_field_phi"] !="" and rec_bak["treatment_dc_field_theta"]!="":   # at least there is field orientation info
                        phi0,theta0=rec_bak["treatment_dc_field_phi"],rec_bak["treatment_dc_field_theta"]
                        ANIS=0
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            phi,theta=rec["treatment_dc_field_phi"],rec["treatment_dc_field_theta"]
                            if phi!=phi0 or theta!=theta0: ANIS=1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS==1:experiment_name="LP-AN-IRM"
                if experiment_name=="":  # not anisotropy of IRM - acquisition?   
                    field0=rec_bak["treatment_dc_field"]
                    IRM=0 
                    for k in range(1,len(Steps)):
                        rec=Steps[k]
                        field=rec["treatment_dc_field"]
                        if field!=field0: IRM=1
                    if IRM==1:experiment_name="LP-IRM"
                IRM=1
            else: IRM=0 # no IRM at all
            if "LP-X" in SpecMeths: # susceptibility run
                Steps=get_dictitem(NewSpecs,'magic_method_codes','LT-X','has')
                if len(Steps)>0:
                    rec_bak=Steps[0]
                    if "treatment_dc_field_phi" in rec_bak.keys() and "treatment_dc_field_theta" in rec_bak.keys():   
                        if rec_bak["treatment_dc_field_phi"] !="" and rec_bak["treatment_dc_field_theta"]!="":   # at least there is field orientation info
                            phi0,theta0=rec_bak["treatment_dc_field_phi"],rec_bak["treatment_dc_field_theta"]
                            ANIS=0
                            for k in range(1,len(Steps)):
                                rec=Steps[k]
                                phi,theta=rec["treatment_dc_field_phi"],rec["treatment_dc_field_theta"]
                                if phi!=phi0 or theta!=theta0: ANIS=1   # if direction changes, is some sort of anisotropy experiment
                            if ANIS==1:experiment_name="LP-AN-MS"
            else: CHI=0 # no susceptibility at all
    #
    # now need to deal with special thellier experiment problems - first clear up pTRM checks and  tail checks
    # 
            if experiment_name=="LP-PI-TRM": # is some sort of thellier experiment
                rec_bak=NewSpecs[0]
                tmp=rec_bak["magic_method_codes"].split(":")
                methbak=[]
                for meth in tmp:
                    methbak.append(meth.strip()) # previous steps method codes
                for k in range(1,len(NewSpecs)):
                    rec=NewSpecs[k]
                    tmp=rec["magic_method_codes"].split(":")
                    meths=[]
                    for meth in tmp:
                        meths.append(meth.strip()) # get this guys method codes
    #
    # check if this is a pTRM check
    #
                    if float(rec["treatment_temp"])<float(rec_bak["treatment_temp"]): # went backward
                        if "LT-T-I" in meths and "LT-T-Z" in methbak:  #must be a pTRM check after first z 
    #
    # replace LT-T-I method code with LT-PTRM-I
    #
                            methcodes=""
                            for meth in meths:
                                if meth!="LT-T-I":methcode=methcode+meth.strip()+":"
                            methcodes=methcodes+"LT-PTRM-I"
                            meths=methcodes.split(":")
                            pTRM=1
                        elif "LT-T-Z" in meths and "LT-T-I" in methbak:  # must be pTRM check after first I
    #
    # replace LT-T-Z method code with LT-PTRM-Z
    #
                            methcodes=""
                            for meth in meths:
                                if meth!="LT-T-Z":methcode=methcode+meth+":"
                            methcodes=methcodes+"LT-PTRM-Z"
                            meths=methcodes.split(":")
                            pTRM=1
                    methcodes=""
                    for meth in meths:
                        methcodes=methcodes+meth.strip()+":"
                    rec["magic_method_codes"]=methcodes[:-1]  #  attach new method code
                    rec_bak=rec # next previous record
                    tmp=rec_bak["magic_method_codes"].split(":")
                    methbak=[]
                    for meth in tmp:
                        methbak.append(meth.strip()) # previous steps method codes
    #
    # done with assigning pTRM checks.  data should be "fixed" in NewSpecs
    #
    # now let's find out which steps are infield zerofield (IZ) and which are zerofield infield (ZI)
    #
                rec_bak=NewSpecs[0]
                tmp=rec_bak["magic_method_codes"].split(":")
                methbak=[]
                for meth in tmp:
                    methbak.append(meth.strip()) # previous steps method codes
                if "LT-NO" not in methbak: # first measurement is not NRM
                    if "LT-T-I" in methbak: IZorZI="LP-PI-TRM-IZ" # first pair is IZ
                    if "LT-T-Z" in methbak: IZorZI="LP-PI-TRM-ZI" # first pair is ZI
                    if IZorZI not in methbak:methbak.append(IZorZI)
                    methcode=""
                    for meth in methbak:
                        methcode=methcode+meth+":"
                    NewSpecs[0]["magic_method_codes"]=methcode[:-1]  # fix first heating step when no NRM
                else: IZorZI="" # first measurement is NRM and not one of a pair
                for k in range(1,len(NewSpecs)): # hunt through measurements again
                    rec=NewSpecs[k]
                    tmp=rec["magic_method_codes"].split(":")
                    meths=[]
                    for meth in tmp:
                        meths.append(meth.strip()) # get this guys method codes
    #
    # check if this start a new temperature step of a infield/zerofield pair
    #
                    if float(rec["treatment_temp"])>float(rec_bak["treatment_temp"]) and "LT-PTRM-I" not in methbak: # new pair?
                        if "LT-T-I" in meths:  # infield of this pair
                                IZorZI="LP-PI-TRM-IZ" 
                                IZ=1 # at least one IZ pair
                        elif "LT-T-Z" in meths: #zerofield 
                                IZorZI="LP-PI-TRM-ZI" 
                                ZI=1 # at least one ZI pair
                    elif float(rec["treatment_temp"])>float(rec_bak["treatment_temp"]) and "LT-PTRM-I" in methbak and IZorZI!="LP-PI-TRM-ZI": # new pair after out of sequence PTRM check?
                        if "LT-T-I" in meths:  # infield of this pair
                                IZorZI="LP-PI-TRM-IZ" 
                                IZ=1 # at least one IZ pair
                        elif "LT-T-Z" in meths: #zerofield 
                                IZorZI="LP-PI-TRM-ZI" 
                                ZI=1 # at least one ZI pair
                    if float(rec["treatment_temp"])==float(rec_bak["treatment_temp"]): # stayed same temp
                        if "LT-T-Z" in meths and "LT-T-I" in methbak and IZorZI=="LP-PI-TRM-ZI":  #must be a tail check
    #
    # replace LT-T-Z method code with LT-PTRM-MD
    #
                            methcodes=""
                            for meth in meths:
                                if meth!="LT-T-Z":methcode=methcode+meth+":"
                            methcodes=methcodes+"LT-PTRM-MD"
                            meths=methcodes.split(":")
                            MD=1
    # fix method codes
                    if "LT-PTRM-I" not in meths and "LT-PTRM-MD" not in meths and IZorZI not in meths:meths.append(IZorZI)
                    newmeths=[]
                    for meth in meths:
                        if meth not in newmeths:newmeths.append(meth)  # try to get uniq set
                    methcode=""
                    for meth in newmeths:
                        methcode=methcode+meth+":"
                    rec["magic_method_codes"]=methcode[:-1] 
                    rec_bak=rec # moving on to next record, making current one the backup
                    methbak=rec_bak["magic_method_codes"].split(":") # get last specimen's method codes in a list
                   
    #
    # done with this specimen's records, now  check if any pTRM checks or MD checks
    #
                if pTRM==1:experiment_name=experiment_name+":LP-PI-ALT-PTRM"
                if MD==1:experiment_name=experiment_name+":LP-PI-BT-MD"
                if IZ==1 and ZI==1:experiment_name=experiment_name+":LP-PI-BT-IZZI"
                if IZ==1 and ZI==0:experiment_name=experiment_name+":LP-PI-IZ" # Aitken method
                if IZ==0 and ZI==1:experiment_name=experiment_name+":LP-PI-ZI" # Coe method
                IZ,ZI,pTRM,MD=0,0,0,0  # reset these for next specimen
                for rec in NewSpecs: # fix the experiment name for all recs for this specimen and save in SpecOuts
    # assign an experiment name to all specimen measurements from this specimen
                    if experiment_name!="":
                        rec["magic_method_codes"]=rec["magic_method_codes"]+":"+experiment_name
                    rec["magic_experiment_name"]=spec+":"+experiment_name
                    rec['measurement_number']='%i'%(measnum)  # assign measurement numbers
                    measnum+=1
                    SpecOuts.append(rec)
            elif experiment_name=="LP-PI-TRM:LP-PI-ALT-AFARM": # is a Shaw experiment!
                ARM,TRM=0,0
                for rec in NewSpecs: # fix the experiment name for all recs for this specimen and save in SpecOuts
    # assign an experiment name to all specimen measurements from this specimen
    # make the second ARM in Shaw experiments LT-AF-I-2, stick in the AF of ARM and TRM codes
                    meths=rec["magic_method_codes"].split(":")
                    if ARM==1:
                        if "LT-AF-I" in meths:
                            del meths[meths.index("LT-AF-I")]
                            meths.append("LT-AF-I-2")
                            ARM=2
                        if "LT-AF-Z" in meths and TRM==0 :
                            meths.append("LP-ARM-AFD")
                    if TRM==1 and ARM==1:
                        if "LT-AF-Z" in meths:
                            meths.append("LP-TRM-AFD")
                    if ARM==2:
                        if "LT-AF-Z" in meths:
                            meths.append("LP-ARM2-AFD")
                    newcode=""
                    for meth in meths:
                        newcode=newcode+meth+":"
                    rec["magic_method_codes"]=newcode[:-1]
                    if "LT-AF-I" in meths:ARM=1
                    if "LT-T-I" in meths:TRM=1
                    rec["magic_method_codes"]=rec["magic_method_codes"]+":"+experiment_name
                    rec["magic_experiment_name"]=spec+":"+experiment_name
                    rec['measurement_number']='%i'%(measnum)  # assign measurement numbers
                    measnum+=1
                    SpecOuts.append(rec)
            else:  # not a Thellier-Thellier  or a Shaw experiemnt
                for rec in  NewSpecs: 
                    if experiment_name=="":
                        rec["magic_method_codes"]="LT-NO"
                        rec["magic_experiment_name"]=spec+":LT-NO"
                        rec['measurement_number']='%i'%(measnum)  # assign measurement numbers
                        measnum+=1
                    else:
                        if experiment_name not in rec['magic_method_codes']:
                            rec["magic_method_codes"]=rec["magic_method_codes"]+":"+experiment_name
                            rec["magic_method_codes"]=rec["magic_method_codes"].strip(':')
                        rec['measurement_number']='%i'%(measnum)  # assign measurement numbers
                        measnum+=1
                        rec["magic_experiment_name"]=spec+":"+experiment_name
                    rec["magic_software_packages"]=version_num
                    SpecOuts.append(rec)
        else:
            NewSpecs[0]["magic_experiment_name"]=spec+":"+NewSpecs[0]['magic_method_codes'].split(':')[0]
            NewSpecs[0]["magic_software_packages"]=version_num
            SpecOuts.append(NewSpecs[0]) # just copy over the single record as is
    return SpecOuts

def mw_measurements_methods(MagRecs):
# first collect all data for this specimen and do lab treatments
    MD,pMRM,IZ,ZI=0,0,0,0 # these are flags for the lab protocol codes
    expcodes=""
    NewSpecs,SpecMeths=[],[]
    experiment_name=""
    phi,theta="",""
    Dec,Inc="","" # NRM direction
    ZI,IZ,MD,pMRM="","","",""
    k=-1
    POWT_I,POWT_Z=[],[]
    ISteps,ZSteps=[],[]
    k=-1
    for rec in MagRecs:
        k+=1
# ready for pass through, step through specimens, check whether ptrm, ptrm tail checks, or AARM, etc.
#
#
# collect all the experimental data for this specimen
# and look through this specimen's records - try to figure out what experiment it is
#
        meths=rec["magic_method_codes"].split(":")
        powt=int(float(rec["treatment_mw_energy"]))
        for meth in meths:
            if meth not in SpecMeths:SpecMeths.append(meth)  # collect all the methods for this experiment
        if "LT-M-I" in meths: # infield step
            POWT_I.append(powt)
            ISteps.append(k)
            if phi=="": # first one
                phi=float(rec["treatment_dc_field_phi"])
                theta=float(rec["treatment_dc_field_theta"])
        if "LT-M-Z" in meths: # zero field  step
            POWT_Z.append(powt)
            ZSteps.append(k)
            if phi=="": # first one
                Dec=float(rec["measurement_dec"])
                Inc=float(rec["measurement_inc"])
    if "LT-M-I" not in  SpecMeths: # just microwave demag
        experiment_name="LP-DIR-M"
    else: # Microwave infield steps , some sort of LP-PI-M experiment
        experiment_name="LP-PI-M"
        if "LT-PMRM-Z"  in  SpecMeths or "LT-PMRM-I" in SpecMeths: # has pTRM checks
            experiment_name=experiment_name+":LP-PI-ALT-PMRM"
        if Dec!="" and phi!="":
            ang=angle([Dec,Inc],[phi,theta]) # angle between applied field and NRM
            if ang>= 0 and ang< 2: experiment_name=experiment_name+":LP-NRM-PAR"
            if ang> 88 and ang< 92: experiment_name=experiment_name+":LP-NRM-PERP"
            if ang> 178 and ang< 182: experiment_name=experiment_name+":LP-NRM-APAR"
#
# now check whether there are z pairs for all I steps or is this a single heating experiment
#  
        noZ=0
        for powt in POWT_I:
            if powt not in POWT_Z:noZ=1 # some I's missing their Z's
        if noZ==1:
            meths = experiment_name.split(":")
            if  "LP-NRM-PERP" in meths: # this is a single  heating experiment
                experiment_name=experiment_name+":LP-PI-M-S"
            else:
                print "Trouble interpreting file - missing zerofield steps? "
                sys.exit()
        else: # this is a double heating experiment
            experiment_name=experiment_name+":LP-PI-M-D"
  # check for IZ or ZI pairs
            for  istep in ISteps: # look for first zerofield step with this power
                rec=MagRecs[istep]
                powt_i=int(float(rec["treatment_mw_energy"]))
                IZorZI,step="",-1
                while IZorZI =="" and step<len(ZSteps)-1:
                    step+=1
                    zstep=ZSteps[step]
                    zrec=MagRecs[zstep]  
                    powt_z=int(float(zrec["treatment_mw_energy"]))
                    if powt_i==powt_z:  # found a match
                        if zstep < istep: # zero field first
                            IZorZI="LP-PI-M-ZI"
                            ZI=1 # there is at least one ZI step
                            break
                        else: # in field first
                            IZorZI="LP-PI-M-IZ"
                            IZ=1 # there is at least one ZI step
                            break
                if IZorZI!="":
                    MagRecs[istep]['magic_method_codes']= MagRecs[istep]['magic_method_codes']+':'+IZorZI
                    MagRecs[zstep]['magic_method_codes']= MagRecs[zstep]['magic_method_codes']+':'+IZorZI
            print POWT_Z
            print POWT_I
            for  istep in ISteps: # now look for MD checks (zero field)
              if istep+2<len(MagRecs):  # only if there is another step to consider
                irec=MagRecs[istep]
                powt_i=int(float(irec["treatment_mw_energy"]))
                print istep,powt_i,ZSteps[POWT_Z.index(powt_i)]
                if powt_i in POWT_Z and ZSteps[POWT_Z.index(powt_i)] < istep:  # if there is a previous zero field step at same  power
                    nrec=MagRecs[istep+1] # next step
                    nmeths=nrec['magic_method_codes'].split(":")
                    powt_n=int(float(nrec["treatment_mw_energy"]))
                    if 'LT-M-Z' in nmeths and powt_n==powt_i:  # the step after this infield was a zero field at same energy 
                        MD=1  # found a second zero field  match
                        mdmeths=MagRecs[istep+1]['magic_method_codes'].split(":")
                        mdmeths[0]="LT-PMRM-MD" # replace method code with tail check code
                        methods=""
                        for meth in mdmeths:methods=methods+":"+meth
                        MagRecs[istep+1]['magic_method_codes']=methods[1:]
            if MD==1: experiment_name=experiment_name+":LP-PI-BT-MD"
            if IZ==1:
                if ZI==1: 
                    experiment_name=experiment_name+":LP-PI-BT-IZZI"
                else:
                    experiment_name=experiment_name+":LP-PI-M-IZ"
            else:
                if ZI==1: 
                    experiment_name=experiment_name+":LP-PI-M-ZI"
                else:
                    print "problem in measurements_methods - no ZI or IZ in double heating experiment"
                    sys.exit()
    for rec in MagRecs: 
        if 'er_synthetic_name' in rec.keys() and rec['er_synthetic_name']!="":
            rec['magic_experiment_name']=rec['er_synthetic_name']+":"+experiment_name
        else:
            rec['magic_experiment_name']=rec['er_specimen_name']+":"+experiment_name
        rec['magic_method_codes']=rec['magic_method_codes']+":"+experiment_name
    return MagRecs

def parse_site(sample,convention,Z):
    """
    parse the site name from the sample name using the specified convention
    """
    site=sample # default is that site = sample
#
#
# Sample is final letter on site designation eg:  TG001a (used by SIO lab in San Diego)
    if convention=="1":
        return sample[:-1] # peel off terminal character
#
# Site-Sample format eg:  BG94-1  (used by PGL lab in Beijing)
#
    if convention=="2":
        parts=sample.strip('-').split('-')
        return parts[0]
#
# Sample is XXXX.YY where XXX is site and YY is sample 
#
    if convention=="3":
        parts=sample.split('.')
        return parts[0]
#
# Sample is XXXXYYY where XXX is site desgnation and YYY is Z long integer
#
    if convention=="4":
       k=int(Z)
       return sample[0:-k]  # peel off Z characters from site
    
    if convention=="5": # sample == site
        return sample
    
    if convention=="7": # peel off Z characters for site
       k=int(Z)
       return sample[0:k]  
  
    if convention=="8": # peel off Z characters for site
       return ""
    if convention=="9": # peel off Z characters for site
       return sample

    print "Error in site parsing routine"
    sys.exit()
def get_samp_con():
    """
     get sample naming  convention
    """
#
    samp_con,Z="",""
    while samp_con=="":
        samp_con=raw_input("""
        Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.  	 [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length) 
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.  
            select one:  
""")
    #
        if samp_con=="" or  samp_con =="1":
            samp_con,Z="1",1
        if "4" in samp_con: 
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                samp_con=""
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con: 
            if "-" not in samp_con:
                print "option [7] must be in form 7-Z where Z is an integer"
                samp_con=""
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
        if samp_con.isdigit()==False or int(samp_con)>7: 
            print "Try again\n "
            samp_con=""
    return samp_con,Z

def get_tilt(dec_geo,inc_geo,dec_tilt,inc_tilt):
#
    """
    Function to return dip and dip direction used to convert geo to tilt coordinates
    """
# strike is horizontal line equidistant from two input directions
    SCart=[0,0,0] # cartesian coordites of Strike
    SCart[2]=0.  # by definition
    GCart=dir2cart([dec_geo,inc_geo,1.]) # cartesian coordites of Geographic D
    TCart=dir2cart([dec_tilt,inc_tilt,1.]) # cartesian coordites of Tilt D
    X=(TCart[1]-GCart[1])/(GCart[0]-TCart[0])
    SCart[1]=numpy.sqrt(1/(X**2+1.))
    SCart[0]=SCart[1]*X
    SDir=cart2dir(SCart)
    DipDir=(SDir[0]+90.)%360.
# D is creat circle distance between geo direction and strike
# theta is GCD between geo and tilt (on unit sphere).  use law of cosines
# to get small cirlce between geo and tilt (dip)
    cosd = GCart[0]*SCart[0]+GCart[1]*SCart[1]  # cosine of angle between two
    d=numpy.arccos(cosd)
    cosTheta=GCart[0]*TCart[0]+GCart[1]*TCart[1]+GCart[2]*TCart[2]
    Dip =(180./numpy.pi)*numpy.arccos(-((cosd**2-cosTheta)/numpy.sin(d)**2))
    return DipDir,Dip
#
def get_azpl(cdec,cinc,gdec,ginc):
    """
     gets azimuth and pl from specimen dec inc (cdec,cinc) and gdec,ginc (geographic)  coordinates
    """
    TOL=1e-4
    rad=numpy.pi/180.
    Xp=dir2cart([gdec,ginc,1.])
    X=dir2cart([cdec,cinc,1.])
    # find plunge first
    az,pl,zdif,ang=0.,-90.,1.,360.
    while  zdif>TOL and pl<180.:
        znew=X[0]*numpy.sin(pl*rad)+X[2]*numpy.cos(pl*rad)
        zdif=abs(Xp[2]-znew)
        pl+=.01

    while ang>0.1 and az<360.:
        d,i=dogeo(cdec,cinc,az,pl)
        ang=angle([gdec,ginc],[d,i])
        az+=.01
    return az-.01,pl-.01

def set_priorities(SO_methods,ask):
    """
     figure out which sample_azimuth to use, if multiple orientation methods
    """
    # if ask set to 1, then can change priorities
    SO_defaults=['SO-SUN','SO-GPS-DIFF','SO-SIGHT','SO-SIGHT-BS','SO-CMD-NORTH','SO-MAG','SO-SM','SO-REC','SO-V','SO-NO']
    SO_priorities,prior_list=[],[]
    if len(SO_methods) >= 1:
        for l in range(len(SO_defaults)):
            if SO_defaults[l] in SO_methods:
                SO_priorities.append(SO_defaults[l])
    pri,change=0,"1"
    if ask==1:
        print  """These methods of sample orientation were found:  
      They have been assigned a provisional priority (top = zero, last = highest number) """
        for m in range(len(SO_defaults)):
            if SO_defaults[m] in SO_methods:
                SO_priorities[SO_methods.index(SO_defaults[m])]=pri
                pri+=1
        while change=="1":
            prior_list=SO_priorities 
            for m in range(len(SO_methods)):
                print SO_methods[m],SO_priorities[m]
            change=raw_input("Change these?  1/[0] ")
            if change!="1":break
        SO_priorities=[]
        for l in range(len(SO_methods)):
             print SO_methods[l]
             print " Priority?   ",prior_list
             pri=int(raw_input())
             SO_priorities.append(pri)
             del prior_list[prior_list.index(pri)]
    return SO_priorities
#
# 
def get_EOL(file):
    """
     find EOL of input file (whether mac,PC or unix format)
    """
    f=open(file,'r')
    firstline=f.read(350)
    EOL=""
    for k in range(350):
        if firstline[k:k+2] == "\r\n":
            print file, ' appears to be a dos file'
            EOL='\r\n'
            break
    if EOL=="":
        for k in range(350):
            if firstline[k] == "\r":
                print file, ' appears to be a mac file'
                EOL='\r'
    if EOL=="":
        print file, " appears to be a  unix file"
        EOL='\n'
    f.close()
    return EOL
# 
def sortshaw(s,datablock):
    """
     sorts data block in to ARM1,ARM2 NRM,TRM,ARM1,ARM2=[],[],[],[]
     stick  first zero field stuff into first_Z 
    """
    for rec in datablock:
        methcodes=rec["magic_method_codes"].split(":")
        step=float(rec["treatment_ac_field"])
        str=float(rec["measurement_magn_moment"])
        if "LT-NO" in methcodes:
            NRM.append([0,str])
        if "LT-T-I" in methcodes:
            TRM.append([0,str])
            field=float(rec["treatment_dc_field"])
        if "LT-AF-I" in methcodes:
            ARM1.append([0,str])
        if "LT-AF-I-2" in methcodes:
            ARM2.append([0,str])
        if "LT-AF-Z" in methcodes:
            if "LP-ARM-AFD" in methcodes:
                ARM1.append([step,str])
            elif "LP-TRM-AFD" in methcodes:
                TRM.append([step,str])
            elif "LP-ARM2-AFD" in methcodes:
                ARM2.append([step,str])
            else:
                NRM.append([step,str])
    cont=1
    while cont==1:
        if len(NRM)!=len(TRM):
            print "Uneven NRM/TRM steps: "
            NRM,TRM,cont=cleanup(TRM,NRM)
        else:cont=0
    cont=1
    while cont==1:
        if len(ARM1)!=len(ARM2):
            print "Uneven ARM1/ARM2 steps: "
            ARM1,ARM2,cont=cleanup(ARM2,ARM1)
        else:cont=0
#
# final check
#
    if len(NRM)!=len(TRM) or len(ARM1)!=len(ARM2):
               print len(NRM),len(TRM),len(ARM1),len(ARM2)
               print " Something wrong with this specimen! Better fix it or delete it "
               raw_input(" press return to acknowledge message")
# now do the ratio to "fix" NRM/TRM data
# a
    TRM_ADJ=[]
    for kk in range(len(TRM)):
        step=TRM[kk][0]
        for k in range(len(ARM1)):
            if  ARM1[k][0]==step:
                TRM_ADJ.append([step,TRM[kk][1]*ARM1[k][1]/ARM2[k][1]])
                break
    shawblock=(NRM,TRM,ARM1,ARM2,TRM_ADJ)
    return shawblock,field
#
#
def makelist(List):
    """
     makes a colon delimited list from List
    """
    clist=""
    for element in List:
        clist=clist+element+":"
    return clist[:-1]
#
def getvec(gh,lat,long):
#
    """
       evaluates the vector at a given latitude (long=0) for a specified set of coefficients
        Lisa Tauxe 2/26/2007
    """

#
#
    sv=[]
    pad=120-len(gh)
    for x in range(pad):gh.append(0.)
    for x in range(len(gh)):sv.append(0.)
#! convert to colatitude for MB routine
    itype = 1 
    colat = 90.-lat
    date,alt=2000.,0. # use a dummy date and altitude
    x,y,z,f=magsyn(gh,sv,date,date,itype,alt,colat,long)
    vec=cart2dir([x,y,z])
    vec[2]=f
    return vec
#
def s_l(l,alpha):
    """
    get sigma as a function of degree l from Constable and Parker (1988)
    """
    a2=alpha**2
    c_a=0.547
    s_l=numpy.sqrt(((c_a**(2.*l))*a2)/((l+1.)*(2.*l+1.)))
    return s_l
#
def mktk03(terms,seed,G2,G3):
    """
    generates a list of gauss coefficients drawn from the TK03.gad distribution
    """
#random.seed(n)
    p=0
    n=seed
    gh=[]
    g10,sfact,afact=-18e3,3.8,2.4
    g20=G2*g10
    g30=G3*g10
    alpha=g10/afact
    s1=s_l(1,alpha)
    s10=sfact*s1
    gnew=random.normal(g10,s10)
    if p==1:print 1,0,gnew,0
    gh.append(gnew)
    gh.append(random.normal(0,s1))
    gnew=gh[-1]
    gh.append(random.normal(0,s1))
    hnew=gh[-1]
    if p==1:print 1,1,gnew,hnew
    for l in range(2,terms+1):
        for m in range(l+1):
            OFF=0.0
            if l==2 and m==0:OFF=g20
            if l==3 and m==0:OFF=g30
            s=s_l(l,alpha)
            j=(l-m)%2
            if j==1:
                s=s*sfact
            gh.append(random.normal(OFF,s))
            gnew=gh[-1]
            if m==0:
                hnew=0
            else: 
                gh.append(random.normal(0,s))
                hnew=gh[-1]
            if p==1:print l,m,gnew,hnew
    return gh
#
#
def pinc(lat):
    """
    calculate paleoinclination from latitude
    """
    rad = numpy.pi/180.
    tanl=numpy.tan(lat*rad)
    inc=numpy.arctan(2.*tanl)
    return inc/rad
#
def plat(inc):
    """
    calculate paleolat from inclination
    """
    rad = numpy.pi/180.
    tani=numpy.tan(inc*rad)
    lat=numpy.arctan(tani/2.)
    return lat/rad
#
#
def pseudo(DIs):
    """
     draw a bootstrap sample of Directions
    """
#
    Inds=numpy.random.randint(len(DIs),size=len(DIs))
    D=numpy.array(DIs)
    return D[Inds]
#
def di_boot(DIs):
    """
     returns bootstrap parameters for Directional data
    """
# get average DI for whole dataset
    fpars=fisher_mean(DIs)
#
# now do bootstrap to collect BDIs  bootstrap means
#
    nb,BDIs=5000,[]  # number of bootstraps, list of bootstrap directions
#
    
    for k in range(nb): # repeat nb times
#        if k%50==0:print k,' out of ',nb
        pDIs= pseudo(DIs) # get a pseudosample 
        bfpars=fisher_mean(pDIs) # get bootstrap mean bootstrap sample
        BDIs.append([bfpars['dec'],bfpars['inc']])
    return BDIs

def pseudosample(x):
    """
     draw a bootstrap sample of x
    """
#
    BXs=[]
    for k in range(len(x)):
        ind=random.randint(0,len(x)-1)
        BXs.append(x[ind])
    return BXs 

def get_plate_data(plate):
    """
    returns the pole list for a given plate"
    """
    if plate=='AF':
       apwp="""
0.0        90.00    0.00
1.0        88.38  182.20
2.0        86.76  182.20
3.0        86.24  177.38
4.0        86.08  176.09
5.0        85.95  175.25
6.0        85.81  174.47
7.0        85.67  173.73
8.0        85.54  173.04
9.0        85.40  172.39
10.0       85.26  171.77
11.0       85.12  171.19
12.0       84.97  170.71
13.0       84.70  170.78
14.0       84.42  170.85
15.0       84.10  170.60
16.0       83.58  169.22
17.0       83.06  168.05
18.0       82.54  167.05
19.0       82.02  166.17
20.0       81.83  166.63
21.0       82.13  169.10
22.0       82.43  171.75
23.0       82.70  174.61
24.0       82.96  177.69
25.0       83.19  180.98
26.0       83.40  184.50
27.0       82.49  192.38
28.0       81.47  198.49
29.0       80.38  203.25
30.0       79.23  207.04
31.0       78.99  206.32
32.0       78.96  204.60
33.0       78.93  202.89
34.0       78.82  201.05
35.0       78.54  198.97
36.0       78.25  196.99
37.0       77.95  195.10
38.0       77.63  193.30
39.0       77.30  191.60
40.0       77.56  192.66
41.0       77.81  193.77
42.0       78.06  194.92
43.0       78.31  196.13
44.0       78.55  197.38
45.0       78.78  198.68
46.0       79.01  200.04
47.0       79.03  201.22
48.0       78.92  202.23
49.0       78.81  203.22
50.0       78.67  204.34
51.0       78.30  206.68
52.0       77.93  208.88
53.0       77.53  210.94
54.0       77.12  212.88
55.0       76.70  214.70
56.0       76.24  216.60
57.0       75.76  218.37
58.0       75.27  220.03
59.0       74.77  221.58
60.0       74.26  223.03
61.0       73.71  225.04
62.0       73.06  228.34
63.0       72.35  231.38
64.0       71.60  234.20
65.0       71.49  234.96
66.0       71.37  235.71
67.0       71.26  236.45
68.0       71.14  237.18
69.0       71.24  236.94
70.0       71.45  236.27
71.0       71.65  235.59
72.0       71.85  234.89
73.0       72.04  234.17
74.0       72.23  233.45
75.0       72.42  232.70
76.0       71.97  236.12
77.0       70.94  241.83
78.0       69.76  246.94
79.0       68.44  251.48
80.0       68.01  252.16
81.0       67.68  252.45
82.0       67.36  252.72
83.0       67.03  252.99
84.0       66.91  252.32
85.0       66.91  251.01
86.0       66.91  249.71
87.0       66.89  248.40
88.0       66.87  247.10
89.0       66.83  245.80
90.0       66.78  244.50
91.0       66.73  243.21
92.0       66.66  243.44
93.0       66.59  244.66
94.0       66.51  245.88
95.0       66.86  247.10
96.0       67.26  248.35
97.0       67.64  249.65
98.0       68.02  250.99
99.0       68.38  252.38
100.0      68.73  253.81
101.0      67.73  253.53
102.0      66.39  252.89
103.0      65.05  252.31
104.0      63.71  251.79
105.0      62.61  252.26
106.0      61.86  254.08
107.0      61.10  255.82
108.0      60.31  257.47
109.0      59.50  259.05
110.0      58.67  260.55
111.0      57.94  261.67
112.0      57.64  261.52
113.0      57.33  261.38
114.0      57.03  261.23
115.0      56.73  261.09
116.0      56.42  260.95
117.0      55.57  260.90
118.0      54.35  260.90
119.0      53.14  260.90
120.0      51.92  260.90
121.0      51.40  260.83
122.0      50.96  260.76
123.0      50.58  260.83
124.0      50.45  261.47
125.0      50.32  262.11
126.0      50.19  262.74
127.0      50.06  263.37
128.0      49.92  264.00
129.0      49.78  264.62
130.0      49.63  265.25
131.0      49.50  265.76
132.0      49.50  265.41
133.0      49.50  265.06
134.0      49.50  264.71
135.0      48.67  264.80
136.0      47.50  265.07
137.0      46.32  265.34
138.0      45.14  265.59
139.0      43.95  265.83
140.0      42.75  265.17
141.0      41.53  264.17
142.0      40.30  263.20
143.0      41.89  262.76
144.0      43.49  262.29
145.0      45.08  261.80
146.0      46.67  261.29
147.0      48.25  260.74
148.0      49.84  260.15
149.0      51.42  259.53
150.0      52.99  258.86
151.0      54.57  258.14
152.0      56.14  257.37
153.0      57.70  256.52
154.0      59.05  255.88
155.0      58.56  257.68
156.0      57.79  258.80
157.0      56.41  258.47
158.0      55.04  258.16
159.0      53.78  257.93
160.0      53.60  258.23
161.0      53.41  258.52
162.0      53.23  258.81
163.0      53.04  259.10
164.0      52.85  259.38
165.0      52.67  259.67
166.0      52.48  259.95
167.0      52.29  260.22
168.0      52.10  260.50
169.0      54.10  259.90
170.0      56.10  259.24
171.0      57.63  259.26
172.0      59.05  259.48
173.0      60.47  259.71
174.0      61.88  259.97
175.0      63.30  260.25
176.0      64.71  260.56
177.0      65.90  261.33
178.0      66.55  263.15
179.0      67.21  263.56
180.0      67.88  262.97
181.0      68.56  262.34
182.0      69.23  261.68
183.0      69.06  261.18
184.0      68.32  260.84
185.0      67.58  260.53
186.0      66.84  260.23
187.0      66.09  259.95
188.0      65.35  259.68
189.0      64.61  259.43
190.0      63.87  259.19
191.0      63.12  258.97
192.0      62.63  258.67
193.0      62.24  258.34
194.0      61.86  258.02
195.0      62.06  256.25
196.0      62.62  253.40
197.0      63.13  250.46
198.0      63.56  247.41
"""
    if plate=='ANT':
       apwp="""
0.0        90.00    0.00
1.0        88.48  178.80
2.0        86.95  178.80
3.0        86.53  172.26
4.0        86.46  169.30
5.0        86.41  166.81
6.0        86.35  164.39
7.0        86.29  162.05
8.0        86.22  159.79
9.0        86.15  157.62
10.0       86.07  155.53
11.0       85.98  153.53
12.0       85.88  151.77
13.0       85.63  151.47
14.0       85.39  151.20
15.0       85.10  150.74
16.0       84.60  149.57
17.0       84.10  148.60
18.0       83.60  147.78
19.0       83.10  147.07
20.0       82.99  146.90
21.0       83.46  147.46
22.0       83.93  148.10
23.0       84.40  148.85
24.0       84.87  149.74
25.0       85.34  150.80
26.0       85.80  152.10
27.0       85.57  166.36
28.0       85.09  178.53
29.0       84.44  188.22
30.0       83.67  195.72
31.0       83.55  194.37
32.0       83.58  191.03
33.0       83.60  187.66
34.0       83.52  184.03
35.0       83.23  180.01
36.0       82.91  176.34
37.0       82.56  172.99
38.0       82.19  169.96
39.0       81.80  167.20
40.0       82.22  166.10
41.0       82.64  164.87
42.0       83.05  163.49
43.0       83.46  161.94
44.0       83.86  160.19
45.0       84.26  158.20
46.0       84.65  155.91
47.0       84.85  155.14
48.0       84.94  155.56
49.0       85.02  156.00
50.0       85.11  156.86
51.0       85.22  161.60
52.0       85.29  166.52
53.0       85.33  171.57
54.0       85.33  176.65
55.0       85.30  181.70
56.0       85.23  187.68
57.0       85.11  193.43
58.0       84.94  198.85
59.0       84.74  203.89
60.0       84.49  208.51
61.0       84.23  214.70
62.0       83.87  224.68
63.0       83.35  233.34
64.0       82.70  240.60
65.0       82.75  243.15
66.0       82.78  245.72
67.0       82.80  248.32
68.0       82.80  250.92
69.0       83.19  251.41
70.0       83.74  250.94
71.0       84.29  250.38
72.0       84.84  249.70
73.0       85.39  248.86
74.0       85.94  247.79
75.0       86.48  246.39
76.0       86.07  261.42
77.0       84.60  277.45
78.0       82.89  286.25
79.0       81.08  291.58
80.0       80.93  293.29
81.0       80.96  294.72
82.0       80.98  296.17
83.0       81.00  297.62
84.0       81.51  298.75
85.0       82.37  299.83
86.0       83.22  301.18
87.0       84.06  302.91
88.0       84.90  305.21
89.0       85.73  308.41
90.0       86.54  313.11
91.0       87.31  320.59
92.0       87.40  334.40
93.0       86.93  346.81
94.0       86.36  355.67
95.0       85.61    7.48
96.0       84.70   16.06
97.0       83.71   22.06
98.0       82.68   26.39
99.0       81.61   29.65
100.0      80.52   32.16
101.0      80.70   31.28
102.0      81.18   29.47
103.0      81.66   27.45
104.0      82.13   25.19
105.0      82.14   22.30
106.0      81.49   19.18
107.0      80.81   16.51
108.0      80.11   14.20
109.0      79.40   12.20
110.0      78.68   10.45
111.0      78.05    9.62
112.0      77.79   11.65
113.0      77.52   13.60
114.0      77.23   15.46
115.0      76.94   17.24
116.0      76.63   18.94
117.0      76.60   18.39
118.0      76.74   16.34
119.0      76.88   14.25
120.0      76.99   12.12
121.0      76.94   12.67
122.0      76.86   13.53
123.0      76.68   14.35
124.0      76.08   15.08
125.0      75.48   15.75
126.0      74.88   16.36
127.0      74.27   16.93
128.0      73.66   17.46
129.0      73.06   17.95
130.0      72.45   18.41
131.0      71.90   18.79
132.0      71.87   18.70
133.0      71.84   18.61
134.0      71.81   18.53
135.0      71.81   15.55
136.0      71.74   11.34
137.0      71.59    7.18
138.0      71.34    3.11
139.0      71.01  359.16
140.0      71.25  355.22
141.0      71.67  351.10
142.0      72.00  346.80
143.0      72.09  352.56
144.0      72.01  358.32
145.0      71.77    3.99
146.0      71.36    9.46
147.0      70.80   14.67
148.0      70.10   19.55
149.0      69.28   24.10
150.0      68.35   28.28
151.0      67.32   32.13
152.0      66.21   35.64
153.0      65.02   38.85
154.0      63.85   41.25
155.0      63.30   38.84
156.0      63.13   36.67
157.0      63.86   34.84
158.0      64.58   32.92
159.0      65.17   31.04
160.0      64.92   30.50
161.0      64.66   29.97
162.0      64.40   29.44
163.0      64.14   28.93
164.0      63.87   28.43
165.0      63.61   27.93
166.0      63.34   27.44
167.0      63.07   26.97
168.0      62.80   26.50
169.0      61.86   30.42
170.0      60.82   34.09
171.0      59.74   36.31
172.0      58.64   38.08
173.0      57.52   39.75
174.0      56.37   41.31
175.0      55.21   42.78
176.0      54.03   44.17
177.0      52.92   45.01
178.0      51.98   44.71
179.0      51.38   45.20
180.0      51.02   46.19
181.0      50.64   47.16
182.0      50.26   48.12
183.0      50.50   48.18
184.0      51.16   47.63
185.0      51.82   47.07
186.0      52.47   46.49
187.0      53.13   45.89
188.0      53.78   45.28
189.0      54.43   44.64
190.0      55.07   43.98
191.0      55.71   43.31
192.0      56.19   42.92
193.0      56.61   42.67
194.0      57.03   42.41
195.0      57.37   43.88
196.0      57.62   46.54
197.0      57.80   49.23
198.0      57.93   51.94
"""
    if plate=='AU':
       apwp="""
0.0        90.00    0.00
1.0        88.81  204.00
2.0        87.62  204.00
3.0        87.50  207.24
4.0        87.58  216.94
5.0        87.58  227.69
6.0        87.51  238.13
7.0        87.35  247.65
8.0        87.14  255.93
9.0        86.87  262.92
10.0       86.56  268.74
11.0       86.22  273.56
12.0       85.87  277.29
13.0       85.52  278.11
14.0       85.18  278.81
15.0       84.87  279.00
16.0       84.71  277.55
17.0       84.54  276.18
18.0       84.37  274.90
19.0       84.20  273.69
20.0       83.80  275.43
21.0       83.01  280.56
22.0       82.18  284.64
23.0       81.31  287.92
24.0       80.42  290.60
25.0       79.52  292.83
26.0       78.60  294.70
27.0       77.32  290.94
28.0       76.00  287.87
29.0       74.65  285.33
30.0       73.28  283.19
31.0       72.98  283.37
32.0       72.95  284.09
33.0       72.92  284.80
34.0       72.92  285.21
35.0       72.97  284.91
36.0       73.03  284.61
37.0       73.09  284.31
38.0       73.14  284.01
39.0       73.20  283.70
40.0       72.83  285.38
41.0       72.45  286.99
42.0       72.06  288.54
43.0       71.65  290.02
44.0       71.24  291.44
45.0       70.81  292.80
46.0       70.38  294.10
47.0       70.08  294.79
48.0       69.88  295.11
49.0       69.68  295.42
50.0       69.46  295.67
51.0       69.01  295.35
52.0       68.55  295.05
53.0       68.10  294.75
54.0       67.65  294.47
55.0       67.20  294.20
56.0       66.69  293.91
57.0       66.18  293.63
58.0       65.68  293.37
59.0       65.17  293.11
60.0       64.66  292.87
61.0       63.96  292.74
62.0       62.84  292.87
63.0       61.72  292.99
64.0       60.60  293.10
65.0       60.35  293.65
66.0       60.09  294.19
67.0       59.84  294.72
68.0       59.58  295.24
69.0       59.76  295.88
70.0       60.14  296.57
71.0       60.51  297.28
72.0       60.88  298.00
73.0       61.24  298.75
74.0       61.60  299.51
75.0       61.96  300.28
76.0       60.92  301.16
77.0       58.95  302.00
78.0       56.98  302.76
79.0       55.00  303.44
80.0       54.72  303.90
81.0       54.63  304.34
82.0       54.53  304.79
83.0       54.44  305.22
84.0       54.82  305.66
85.0       55.51  306.11
86.0       56.20  306.57
87.0       56.89  307.05
88.0       57.58  307.55
89.0       58.26  308.07
90.0       58.95  308.61
91.0       59.63  309.17
92.0       59.80  310.34
93.0       59.62  311.90
94.0       59.42  313.45
95.0       59.46  315.65
96.0       59.50  317.94
97.0       59.49  320.23
98.0       59.44  322.51
99.0       59.36  324.79
100.0      59.23  327.05
101.0      59.10  326.62
102.0      58.98  325.52
103.0      58.84  324.43
104.0      58.69  323.34
105.0      58.29  322.95
106.0      57.53  323.57
107.0      56.75  324.16
108.0      55.98  324.73
109.0      55.20  325.27
110.0      54.42  325.80
111.0      53.81  326.35
112.0      53.88  327.12
113.0      53.94  327.88
114.0      53.99  328.65
115.0      54.04  329.42
116.0      54.08  330.19
117.0      53.91  330.07
118.0      53.59  329.36
119.0      53.26  328.66
120.0      52.93  327.97
121.0      52.97  328.13
122.0      53.04  328.39
123.0      53.03  328.78
124.0      52.70  329.69
125.0      52.35  330.59
126.0      52.00  331.47
127.0      51.65  332.34
128.0      51.29  333.20
129.0      50.92  334.04
130.0      50.54  334.87
131.0      50.18  335.59
132.0      50.01  335.53
133.0      49.83  335.48
134.0      49.65  335.42
135.0      48.86  334.35
136.0      47.78  332.89
137.0      46.68  331.50
138.0      45.57  330.16
139.0      44.44  328.88
140.0      43.86  327.11
141.0      43.50  325.14
142.0      43.10  323.20
143.0      44.00  325.32
144.0      44.85  327.50
145.0      45.66  329.75
146.0      46.43  332.06
147.0      47.15  334.44
148.0      47.81  336.88
149.0      48.43  339.38
150.0      48.99  341.94
151.0      49.49  344.55
152.0      49.93  347.22
153.0      50.31  349.93
154.0      50.48  352.37
155.0      49.32  352.03
156.0      48.45  351.31
157.0      48.28  349.67
158.0      48.09  348.05
159.0      47.87  346.61
160.0      47.53  346.69
161.0      47.19  346.77
162.0      46.84  346.85
163.0      46.50  346.93
164.0      46.16  347.00
165.0      45.82  347.08
166.0      45.48  347.15
167.0      45.14  347.23
168.0      44.80  347.30
169.0      45.48  349.99
170.0      46.09  352.74
171.0      46.20  354.95
172.0      46.16  357.01
173.0      46.09  359.07
174.0      45.98    1.12
175.0      45.83    3.16
176.0      45.65    5.19
177.0      45.27    6.85
178.0      44.51    7.68
179.0      44.31    8.58
180.0      44.50    9.55
181.0      44.67   10.52
182.0      44.84   11.51
183.0      45.02   11.29
184.0      45.22   10.27
185.0      45.42    9.24
186.0      45.60    8.20
187.0      45.77    7.16
188.0      45.93    6.11
189.0      46.09    5.05
190.0      46.23    3.99
191.0      46.36    2.92
192.0      46.52    2.20
193.0      46.68    1.62
194.0      46.84    1.03
195.0      47.67    1.40
196.0      48.95    2.45
197.0      50.22    3.54
198.0      51.48    4.70
"""
    if plate=='EU':
       apwp="""
0.0        90.00    0.00
1.0        88.43  178.70
2.0        86.86  178.70
3.0        86.34  172.60
4.0        86.18  169.84
5.0        86.05  167.60
6.0        85.91  165.51
7.0        85.77  163.55
8.0        85.62  161.73
9.0        85.46  160.03
10.0       85.31  158.44
11.0       85.15  156.95
12.0       84.97  155.67
13.0       84.70  155.37
14.0       84.42  155.10
15.0       84.08  154.59
16.0       83.51  153.18
17.0       82.92  152.01
18.0       82.34  151.01
19.0       81.75  150.16
20.0       81.55  149.86
21.0       81.93  150.29
22.0       82.30  150.76
23.0       82.68  151.28
24.0       83.05  151.85
25.0       83.43  152.49
26.0       83.80  153.20
27.0       83.47  162.05
28.0       83.00  169.89
29.0       82.41  176.64
30.0       81.74  182.37
31.0       81.53  181.04
32.0       81.43  178.14
33.0       81.30  175.32
34.0       81.08  172.47
35.0       80.66  169.55
36.0       80.22  166.89
37.0       79.76  164.46
38.0       79.29  162.23
39.0       78.80  160.20
40.0       79.13  159.12
41.0       79.45  157.97
42.0       79.77  156.75
43.0       80.08  155.46
44.0       80.39  154.08
45.0       80.69  152.62
46.0       80.98  151.05
47.0       81.13  150.65
48.0       81.19  151.08
49.0       81.25  151.51
50.0       81.31  152.21
51.0       81.38  155.38
52.0       81.43  158.60
53.0       81.44  161.83
54.0       81.44  165.08
55.0       81.40  168.30
56.0       81.33  172.18
57.0       81.22  175.97
58.0       81.07  179.66
59.0       80.89  183.21
60.0       80.67  186.61
61.0       80.49  190.87
62.0       80.37  197.35
63.0       80.14  203.60
64.0       79.80  209.50
65.0       79.85  210.35
66.0       79.90  211.20
67.0       79.94  212.07
68.0       79.99  212.94
69.0       80.20  211.11
70.0       80.46  207.98
71.0       80.69  204.68
72.0       80.89  201.23
73.0       81.05  197.65
74.0       81.18  193.94
75.0       81.27  190.14
76.0       81.59  195.53
77.0       81.79  207.82
78.0       81.61  220.13
79.0       81.07  231.45
80.0       81.02  232.09
81.0       81.05  231.62
82.0       81.07  231.16
83.0       81.09  230.69
84.0       81.26  227.31
85.0       81.47  221.76
86.0       81.59  216.00
87.0       81.63  210.12
88.0       81.58  204.25
89.0       81.45  198.51
90.0       81.23  192.99
91.0       80.94  187.78
92.0       81.02  185.31
93.0       81.39  184.44
94.0       81.76  183.50
95.0       82.43  179.95
96.0       83.10  175.40
97.0       83.71  169.92
98.0       84.25  163.35
99.0       84.71  155.53
100.0      85.05  146.45
101.0      84.53  152.65
102.0      83.71  160.59
103.0      82.79  166.60
104.0      81.81  171.23
105.0      81.32  175.20
106.0      81.60  179.66
107.0      81.82  184.38
108.0      81.98  189.32
109.0      82.08  194.43
110.0      82.12  199.63
111.0      82.03  203.00
112.0      81.66  199.22
113.0      81.26  195.76
114.0      80.83  192.62
115.0      80.37  189.76
116.0      79.90  187.17
117.0      79.19  187.67
118.0      78.34  189.84
119.0      77.47  191.71
120.0      76.59  193.35
121.0      76.23  193.12
122.0      75.94  192.71
123.0      75.74  192.46
124.0      75.95  192.77
125.0      76.16  193.09
126.0      76.38  193.42
127.0      76.59  193.76
128.0      76.79  194.12
129.0      77.00  194.48
130.0      77.21  194.85
131.0      77.38  195.04
132.0      77.22  193.47
133.0      77.04  191.93
134.0      76.86  190.44
135.0      76.26  192.29
136.0      75.46  195.27
137.0      74.62  197.94
138.0      73.76  200.34
139.0      72.87  202.49
140.0      71.59  202.74
141.0      70.15  202.29
142.0      68.70  201.90
143.0      69.87  198.07
144.0      70.94  193.81
145.0      71.91  189.09
146.0      72.75  183.89
147.0      73.44  178.23
148.0      73.97  172.14
149.0      74.31  165.73
150.0      74.47  159.11
151.0      74.42  152.44
152.0      74.17  145.90
153.0      73.74  139.63
154.0      73.26  134.46
155.0      73.88  136.15
156.0      74.11  138.70
157.0      73.41  142.81
158.0      72.65  146.58
159.0      71.89  149.70
160.0      71.74  149.67
161.0      71.60  149.65
162.0      71.46  149.63
163.0      71.31  149.61
164.0      71.17  149.58
165.0      71.03  149.56
166.0      70.89  149.54
167.0      70.74  149.52
168.0      70.60  149.50
169.0      70.64  140.48
170.0      70.23  131.62
171.0      69.98  125.23
172.0      69.67  119.51
173.0      69.17  114.01
174.0      68.51  108.79
175.0      67.69  103.90
176.0      66.74   99.36
177.0      66.01   95.57
178.0      66.01   92.81
179.0      65.66   91.06
180.0      65.09   90.02
181.0      64.52   89.02
182.0      63.93   88.07
183.0      63.89   88.62
184.0      64.20   90.17
185.0      64.49   91.77
186.0      64.77   93.39
187.0      65.02   95.05
188.0      65.26   96.73
189.0      65.48   98.45
190.0      65.67  100.19
191.0      65.85  101.96
192.0      65.88  103.25
193.0      65.85  104.31
194.0      65.82  105.38
195.0      64.95  105.43
196.0      63.53  104.86
197.0      62.11  104.35
198.0      60.68  103.89
"""
    if plate=='GL':
       apwp="""
0.0        90.00    0.00
1.0        88.33  180.70
2.0        86.67  180.70
3.0        86.14  175.33
4.0        85.95  173.39
5.0        85.79  171.94
6.0        85.62  170.59
7.0        85.45  169.35
8.0        85.28  168.19
9.0        85.11  167.12
10.0       84.94  166.12
11.0       84.76  165.19
12.0       84.57  164.34
13.0       84.22  163.81
14.0       83.88  163.34
15.0       83.49  162.61
16.0       82.96  160.83
17.0       82.42  159.31
18.0       81.88  157.98
19.0       81.33  156.83
20.0       81.12  156.68
21.0       81.41  157.94
22.0       81.70  159.28
23.0       81.98  160.72
24.0       82.26  162.26
25.0       82.53  163.92
26.0       82.80  165.70
27.0       82.16  172.55
28.0       81.43  178.31
29.0       80.63  183.13
30.0       79.78  187.17
31.0       79.55  186.15
32.0       79.47  183.99
33.0       79.37  181.86
34.0       79.20  179.58
35.0       78.84  176.94
36.0       78.45  174.48
37.0       78.05  172.17
38.0       77.63  170.01
39.0       77.20  168.00
40.0       77.40  168.23
41.0       77.61  168.47
42.0       77.81  168.71
43.0       78.01  168.97
44.0       78.21  169.23
45.0       78.42  169.50
46.0       78.62  169.78
47.0       78.58  170.26
48.0       78.38  170.84
49.0       78.18  171.41
50.0       77.97  172.10
51.0       77.62  174.07
52.0       77.26  175.92
53.0       76.88  177.68
54.0       76.50  179.33
55.0       76.10  180.90
56.0       75.72  182.56
57.0       75.33  184.14
58.0       74.93  185.63
59.0       74.52  187.05
60.0       74.10  188.40
61.0       73.71  190.34
62.0       73.39  193.73
63.0       73.02  196.99
64.0       72.60  200.10
65.0       72.58  200.61
66.0       72.56  201.13
67.0       72.53  201.64
68.0       72.51  202.15
69.0       72.64  201.35
70.0       72.83  199.97
71.0       73.02  198.55
72.0       73.19  197.11
73.0       73.35  195.64
74.0       73.50  194.14
75.0       73.65  192.62
76.0       73.70  196.06
77.0       73.52  202.77
78.0       73.14  209.26
79.0       72.57  215.41
80.0       72.42  216.02
81.0       72.32  216.04
82.0       72.23  216.07
83.0       72.14  216.09
84.0       72.16  214.56
85.0       72.23  211.98
86.0       72.27  209.39
87.0       72.28  206.78
88.0       72.25  204.19
89.0       72.19  201.60
90.0       72.09  199.04
91.0       71.96  196.50
92.0       72.14  195.56
93.0       72.55  195.67
94.0       72.96  195.79
95.0       73.76  195.21
96.0       74.60  194.49
97.0       75.44  193.69
98.0       76.28  192.80
99.0       77.11  191.79
100.0      77.94  190.65
101.0      77.17  190.62
102.0      76.01  190.85
103.0      74.85  191.04
104.0      73.70  191.21
105.0      73.00  192.27
106.0      72.98  194.70
107.0      72.94  197.12
108.0      72.86  199.52
109.0      72.76  201.90
110.0      72.62  204.25
111.0      72.45  205.69
112.0      72.21  203.68
113.0      71.94  201.72
114.0      71.66  199.82
115.0      71.35  197.98
116.0      71.03  196.20
117.0      70.33  195.81
118.0      69.39  196.30
119.0      68.44  196.75
120.0      67.49  197.16
121.0      67.17  196.83
122.0      66.91  196.42
123.0      66.74  196.16
124.0      66.92  196.46
125.0      67.11  196.77
126.0      67.30  197.09
127.0      67.48  197.41
128.0      67.67  197.73
129.0      67.85  198.06
130.0      68.04  198.39
131.0      68.19  198.60
132.0      68.11  197.59
133.0      68.02  196.59
134.0      67.93  195.60
135.0      67.26  196.33
136.0      66.33  197.70
137.0      65.39  198.98
138.0      64.45  200.17
139.0      63.49  201.28
140.0      62.22  201.09
141.0      60.81  200.42
142.0      59.40  199.80
143.0      60.73  197.43
144.0      62.01  194.85
145.0      63.24  192.06
146.0      64.41  189.02
147.0      65.52  185.72
148.0      66.54  182.13
149.0      67.48  178.26
150.0      68.32  174.08
151.0      69.04  169.61
152.0      69.64  164.86
153.0      70.11  159.86
154.0      70.43  155.41
155.0      70.72  157.56
156.0      70.56  159.72
157.0      69.42  161.65
158.0      68.26  163.38
159.0      67.19  164.78
160.0      67.04  164.60
161.0      66.90  164.42
162.0      66.76  164.24
163.0      66.62  164.06
164.0      66.47  163.88
165.0      66.33  163.71
166.0      66.19  163.54
167.0      66.04  163.37
168.0      65.90  163.20
169.0      67.23  156.43
170.0      68.24  148.97
171.0      69.04  143.36
172.0      69.69  138.01
173.0      70.17  132.36
174.0      70.47  126.50
175.0      70.57  120.51
176.0      70.48  114.53
177.0      70.45  109.51
178.0      70.93  106.46
179.0      70.89  104.04
180.0      70.54  102.15
181.0      70.16  100.33
182.0      69.76   98.58
183.0      69.64   99.18
184.0      69.68  101.32
185.0      69.70  103.47
186.0      69.69  105.62
187.0      69.65  107.76
188.0      69.59  109.89
189.0      69.50  112.01
190.0      69.39  114.11
191.0      69.25  116.18
192.0      69.07  117.58
193.0      68.88  118.69
194.0      68.68  119.77
195.0      67.88  118.87
196.0      66.66  116.82
197.0      65.42  114.97
198.0      64.15  113.29
"""
    if plate=='IN':
       apwp="""
0.0        90.00    0.00
1.0        88.57  197.10
2.0        87.14  197.10
3.0        86.82  197.10
4.0        86.76  201.35
5.0        86.70  205.94
6.0        86.62  210.32
7.0        86.52  214.48
8.0        86.40  218.38
9.0        86.26  222.02
10.0       86.11  225.39
11.0       85.95  228.51
12.0       85.77  231.10
13.0       85.46  231.14
14.0       85.15  231.18
15.0       84.84  230.71
16.0       84.54  228.40
17.0       84.23  226.34
18.0       83.92  224.49
19.0       83.59  222.82
20.0       83.40  225.11
21.0       83.32  233.06
22.0       83.11  240.67
23.0       82.79  247.72
24.0       82.37  254.09
25.0       81.87  259.74
26.0       81.30  264.70
27.0       79.78  264.31
28.0       78.25  264.03
29.0       76.73  263.81
30.0       75.20  263.63
31.0       74.95  264.21
32.0       75.01  264.98
33.0       75.06  265.75
34.0       75.09  266.19
35.0       75.05  265.83
36.0       75.02  265.47
37.0       74.98  265.11
38.0       74.94  264.75
39.0       74.90  264.40
40.0       74.38  266.62
41.0       73.83  268.69
42.0       73.26  270.63
43.0       72.68  272.45
44.0       72.09  274.14
45.0       71.48  275.74
46.0       70.85  277.23
47.0       70.10  277.93
48.0       69.27  278.14
49.0       68.45  278.34
50.0       67.56  278.48
51.0       66.19  278.29
52.0       64.82  278.12
53.0       63.45  277.97
54.0       62.07  277.83
55.0       60.70  277.70
56.0       58.96  277.66
57.0       57.23  277.62
58.0       55.49  277.58
59.0       53.75  277.55
60.0       52.02  277.52
61.0       50.04  277.70
62.0       47.49  278.32
63.0       44.95  278.88
64.0       42.40  279.40
65.0       41.10  279.80
66.0       39.80  280.18
67.0       38.50  280.54
68.0       37.19  280.90
69.0       36.48  281.11
70.0       36.03  281.27
71.0       35.58  281.43
72.0       35.13  281.58
73.0       34.68  281.74
74.0       34.23  281.89
75.0       33.78  282.04
76.0       32.33  283.04
77.0       30.21  284.54
78.0       28.07  285.98
79.0       25.92  287.36
80.0       25.05  287.84
81.0       24.33  288.22
82.0       23.61  288.59
83.0       22.89  288.95
84.0       22.55  289.11
85.0       22.46  289.12
86.0       22.37  289.13
87.0       22.29  289.15
88.0       22.20  289.16
89.0       22.11  289.17
90.0       22.02  289.18
91.0       21.94  289.20
92.0       21.59  289.76
93.0       21.07  290.69
94.0       20.55  291.61
95.0       20.43  292.63
96.0       20.34  293.67
97.0       20.24  294.70
98.0       20.14  295.73
99.0       20.04  296.76
100.0      19.92  297.79
101.0      18.99  297.44
102.0      17.86  296.75
103.0      16.72  296.07
104.0      15.58  295.40
105.0      14.47  295.17
106.0      13.41  295.58
107.0      12.35  295.98
108.0      11.28  296.39
109.0      10.22  296.79
110.0       9.15  297.18
111.0       8.25  297.49
112.0       7.98  297.44
113.0       7.71  297.38
114.0       7.44  297.33
115.0       7.18  297.27
116.0       6.91  297.22
117.0       6.09  297.02
118.0       4.90  296.72
119.0       3.71  296.43
120.0       2.52  296.13
121.0       1.90  296.20
122.0       1.34  296.31
123.0       0.80  296.53
124.0       0.32  297.16
125.0      -0.16  297.78
126.0      -0.64  298.41
127.0      -1.12  299.04
128.0      -1.60  299.67
129.0      -2.09  300.30
130.0      -2.57  300.93
131.0      -3.01  301.50
132.0      -3.16  301.53
133.0      -3.31  301.56
134.0      -3.46  301.59
135.0      -4.41  301.48
136.0      -5.71  301.30
137.0      -7.01  301.12
138.0      -8.31  300.94
139.0      -9.61  300.75
140.0     -10.62  299.98
141.0     -11.51  298.94
142.0     -12.40  297.90
143.0     -10.89  298.80
144.0      -9.37  299.69
145.0      -7.85  300.58
146.0      -6.33  301.45
147.0      -4.81  302.32
148.0      -3.29  303.19
149.0      -1.76  304.06
150.0      -0.24  304.92
151.0       1.28  305.78
152.0       2.81  306.65
153.0       4.33  307.52
154.0       5.61  308.38
155.0       4.72  309.22
156.0       3.82  309.62
157.0       2.88  309.03
158.0       1.94  308.43
159.0       1.08  307.93
160.0       0.88  308.24
161.0       0.68  308.55
162.0       0.49  308.85
163.0       0.29  309.16
164.0       0.09  309.47
165.0      -0.11  309.78
166.0      -0.30  310.08
167.0      -0.50  310.39
168.0      -0.70  310.70
169.0       1.16  311.47
170.0       3.03  312.25
171.0       4.29  313.12
172.0       5.40  314.02
173.0       6.51  314.92
174.0       7.62  315.83
175.0       8.72  316.74
176.0       9.83  317.65
177.0      10.65  318.58
178.0      10.83  319.52
179.0      11.31  320.00
180.0      11.98  320.18
181.0      12.66  320.35
182.0      13.33  320.53
183.0      13.28  320.28
184.0      12.74  319.76
185.0      12.21  319.24
186.0      11.67  318.72
187.0      11.13  318.20
188.0      10.59  317.69
189.0      10.05  317.17
190.0       9.51  316.66
191.0       8.96  316.15
192.0       8.62  315.75
193.0       8.36  315.40
194.0       8.10  315.04
195.0       8.76  314.48
196.0      10.03  313.78
197.0      11.30  313.07
198.0      12.56  312.35
"""
    if plate=='NA':
       apwp="""
0.0        90.00    0.00
1.0        88.33  180.70
2.0        86.67  180.70
3.0        86.14  175.33
4.0        85.95  173.39
5.0        85.79  171.94
6.0        85.62  170.59
7.0        85.45  169.35
8.0        85.28  168.19
9.0        85.11  167.12
10.0       84.94  166.12
11.0       84.76  165.19
12.0       84.57  164.34
13.0       84.22  163.81
14.0       83.88  163.34
15.0       83.49  162.61
16.0       82.96  160.83
17.0       82.42  159.31
18.0       81.88  157.98
19.0       81.33  156.83
20.0       81.12  156.68
21.0       81.41  157.94
22.0       81.70  159.28
23.0       81.98  160.72
24.0       82.26  162.26
25.0       82.53  163.92
26.0       82.80  165.70
27.0       82.16  172.55
28.0       81.43  178.31
29.0       80.63  183.13
30.0       79.78  187.17
31.0       79.55  186.15
32.0       79.47  183.99
33.0       79.37  181.86
34.0       79.20  179.56
35.0       78.86  176.88
36.0       78.50  174.36
37.0       78.12  171.99
38.0       77.72  169.78
39.0       77.30  167.70
40.0       77.61  167.72
41.0       77.92  167.75
42.0       78.23  167.77
43.0       78.54  167.80
44.0       78.85  167.83
45.0       79.16  167.86
46.0       79.48  167.89
47.0       79.55  168.32
48.0       79.47  169.01
49.0       79.38  169.70
50.0       79.28  170.59
51.0       79.05  173.39
52.0       78.79  176.08
53.0       78.52  178.64
54.0       78.22  181.08
55.0       77.90  183.40
56.0       77.51  185.86
57.0       77.09  188.16
58.0       76.65  190.32
59.0       76.20  192.35
60.0       75.74  194.24
61.0       75.25  196.69
62.0       74.73  200.49
63.0       74.14  204.02
64.0       73.50  207.30
65.0       73.48  207.86
66.0       73.46  208.42
67.0       73.43  208.98
68.0       73.41  209.53
69.0       73.65  208.66
70.0       74.01  207.12
71.0       74.35  205.51
72.0       74.68  203.84
73.0       75.00  202.09
74.0       75.30  200.27
75.0       75.59  198.38
76.0       75.52  201.87
77.0       75.06  208.70
78.0       74.41  215.06
79.0       73.59  220.85
80.0       73.50  221.21
81.0       73.50  221.00
82.0       73.50  220.79
83.0       73.50  220.58
84.0       73.72  218.91
85.0       74.06  216.16
86.0       74.37  213.31
87.0       74.63  210.35
88.0       74.86  207.30
89.0       75.04  204.16
90.0       75.18  200.96
91.0       75.27  197.71
92.0       75.55  196.67
93.0       75.95  197.15
94.0       76.36  197.65
95.0       77.18  197.76
96.0       78.05  197.83
97.0       78.92  197.91
98.0       79.79  198.01
99.0       80.66  198.13
100.0      81.53  198.27
101.0      80.82  196.53
102.0      79.71  194.75
103.0      78.60  193.30
104.0      77.48  192.12
105.0      76.75  192.71
106.0      76.59  195.69
107.0      76.40  198.60
108.0      76.18  201.42
109.0      75.93  204.14
110.0      75.65  206.77
111.0      75.39  208.27
112.0      75.32  205.66
113.0      75.23  203.07
114.0      75.11  200.52
115.0      74.96  198.02
116.0      74.78  195.56
117.0      74.13  194.52
118.0      73.19  194.41
119.0      72.24  194.30
120.0      71.29  194.21
121.0      70.97  193.62
122.0      70.71  192.99
123.0      70.54  192.59
124.0      70.71  193.06
125.0      70.89  193.53
126.0      71.06  194.01
127.0      71.24  194.50
128.0      71.41  195.00
129.0      71.58  195.51
130.0      71.75  196.03
131.0      71.90  196.38
132.0      71.88  195.14
133.0      71.85  193.90
134.0      71.81  192.67
135.0      71.10  193.14
136.0      70.08  194.23
137.0      69.06  195.23
138.0      68.04  196.14
139.0      67.01  196.96
140.0      65.77  196.26
141.0      64.44  195.02
142.0      63.10  193.90
143.0      64.58  191.66
144.0      66.02  189.16
145.0      67.42  186.37
146.0      68.76  183.24
147.0      70.04  179.71
148.0      71.23  175.75
149.0      72.34  171.28
150.0      73.33  166.27
151.0      74.19  160.69
152.0      74.88  154.55
153.0      75.40  147.91
154.0      75.73  141.88
155.0      76.02  144.73
156.0      75.85  147.65
157.0      74.69  150.19
158.0      73.49  152.38
159.0      72.39  154.07
160.0      72.26  153.82
161.0      72.13  153.57
162.0      71.99  153.32
163.0      71.86  153.07
164.0      71.73  152.83
165.0      71.60  152.59
166.0      71.47  152.36
167.0      71.33  152.13
168.0      71.20  151.90
169.0      72.50  143.28
170.0      73.38  133.55
171.0      74.04  126.09
172.0      74.51  118.88
173.0      74.74  111.36
174.0      74.71  103.74
175.0      74.42   96.27
176.0      73.90   89.17
177.0      73.49   83.36
178.0      73.72   79.48
179.0      73.50   76.79
180.0      72.99   75.03
181.0      72.46   73.37
182.0      71.92   71.80
183.0      71.85   72.55
184.0      72.07   74.85
185.0      72.26   77.20
186.0      72.43   79.60
187.0      72.56   82.04
188.0      72.67   84.51
189.0      72.74   87.01
190.0      72.79   89.52
191.0      72.80   92.04
192.0      72.74   93.81
193.0      72.65   95.23
194.0      72.54   96.64
195.0      71.70   96.06
196.0      70.36   94.36
197.0      69.01   92.87
198.0      67.64   91.56
"""
    if plate=='SA':
       apwp="""
0.0        90.00    0.00
1.0        88.48  176.30
2.0        86.95  176.30
3.0        86.53  168.76
4.0        86.45  164.50
5.0        86.37  160.76
6.0        86.28  157.18
7.0        86.17  153.79
8.0        86.06  150.58
9.0        85.93  147.57
10.0       85.79  144.75
11.0       85.64  142.12
12.0       85.48  139.77
13.0       85.24  138.58
14.0       84.99  137.49
15.0       84.69  136.40
16.0       84.13  135.05
17.0       83.57  133.95
18.0       83.00  133.01
19.0       82.44  132.22
20.0       82.25  131.54
21.0       82.61  130.86
22.0       82.97  130.10
23.0       83.33  129.26
24.0       83.69  128.32
25.0       84.05  127.28
26.0       84.40  126.10
27.0       84.43  135.88
28.0       84.29  145.47
29.0       84.01  154.39
30.0       83.60  162.34
31.0       83.39  160.95
32.0       83.23  157.53
33.0       83.04  154.27
34.0       82.75  151.13
35.0       82.23  148.16
36.0       81.69  145.56
37.0       81.14  143.29
38.0       80.57  141.28
39.0       80.00  139.50
40.0       80.29  138.06
41.0       80.58  136.53
42.0       80.86  134.91
43.0       81.14  133.19
44.0       81.40  131.36
45.0       81.66  129.42
46.0       81.90  127.36
47.0       82.03  126.70
48.0       82.09  127.04
49.0       82.15  127.39
50.0       82.22  128.02
51.0       82.37  131.28
52.0       82.49  134.65
53.0       82.59  138.13
54.0       82.66  141.69
55.0       82.70  145.30
56.0       82.74  149.45
57.0       82.73  153.61
58.0       82.69  157.75
59.0       82.61  161.83
60.0       82.50  165.80
61.0       82.43  170.84
62.0       82.42  178.70
63.0       82.28  186.40
64.0       82.00  193.70
65.0       82.08  194.90
66.0       82.15  196.11
67.0       82.22  197.36
68.0       82.28  198.62
69.0       82.50  196.70
70.0       82.76  193.22
71.0       82.99  189.49
72.0       83.19  185.52
73.0       83.36  181.34
74.0       83.48  176.96
75.0       83.58  172.44
76.0       83.88  180.55
77.0       83.90  198.12
78.0       83.37  214.31
79.0       82.41  227.29
80.0       82.34  228.63
81.0       82.39  228.88
82.0       82.44  229.14
83.0       82.48  229.40
84.0       82.82  226.98
85.0       83.33  222.26
86.0       83.78  216.82
87.0       84.17  210.58
88.0       84.48  203.56
89.0       84.70  195.83
90.0       84.82  187.59
91.0       84.83  179.15
92.0       85.11  176.27
93.0       85.63  177.19
94.0       86.15  178.37
95.0       87.04  175.29
96.0       87.94  168.69
97.0       88.78  152.46
98.0       89.26  101.14
99.0       88.81   47.96
100.0      87.98   31.01
101.0      88.51   36.07
102.0      89.29   63.58
103.0      89.30  145.49
104.0      88.53  174.06
105.0      88.07  189.19
106.0      88.01  213.41
107.0      87.64  233.01
108.0      87.08  246.23
109.0      86.42  254.90
110.0      85.70  260.77
111.0      85.15  264.12
112.0      85.38  263.70
113.0      85.61  263.23
114.0      85.84  262.72
115.0      86.08  262.14
116.0      86.31  261.48
117.0      86.05  255.65
118.0      85.41  248.40
119.0      84.71  242.98
120.0      83.97  238.86
121.0      83.74  236.57
122.0      83.55  234.54
123.0      83.39  233.53
124.0      83.33  236.16
125.0      83.26  238.74
126.0      83.18  241.27
127.0      83.09  243.73
128.0      82.98  246.12
129.0      82.86  248.43
130.0      82.73  250.66
131.0      82.62  252.43
132.0      82.80  250.74
133.0      82.98  248.95
134.0      83.15  247.08
135.0      82.42  244.60
136.0      81.28  242.47
137.0      80.14  240.84
138.0      79.00  239.54
139.0      77.85  238.48
140.0      76.82  234.91
141.0      75.79  230.78
142.0      74.70  227.20
143.0      76.33  226.82
144.0      77.95  226.34
145.0      79.58  225.72
146.0      81.20  224.87
147.0      82.82  223.63
148.0      84.44  221.68
149.0      86.04  218.15
150.0      87.61  209.92
151.0      88.97  176.54
152.0      88.68   89.32
153.0      87.22   67.59
154.0      85.89   60.82
155.0      86.78   50.54
156.0      87.70   41.70
157.0      88.96   60.27
158.0      89.26  158.76
159.0      88.19  190.34
160.0      88.08  197.32
161.0      87.94  203.47
162.0      87.79  208.80
163.0      87.62  213.39
164.0      87.43  217.35
165.0      87.23  220.75
166.0      87.03  223.70
167.0      86.82  226.26
168.0      86.60  228.50
169.0      88.64  230.93
170.0      89.31   38.96
171.0      87.78   36.39
172.0      86.36   34.32
173.0      84.94   33.40
174.0      83.53   32.89
175.0      82.11   32.55
176.0      80.69   32.32
177.0      79.48   31.11
178.0      78.71   27.80
179.0      78.03   27.66
180.0      77.42   29.28
181.0      76.79   30.75
182.0      76.16   32.10
183.0      76.35   32.76
184.0      77.09   33.06
185.0      77.83   33.40
186.0      78.58   33.77
187.0      79.32   34.20
188.0      80.06   34.69
189.0      80.80   35.27
190.0      81.54   35.93
191.0      82.28   36.73
192.0      82.77   37.91
193.0      83.16   39.32
194.0      83.55   40.91
195.0      83.19   47.69
196.0      82.21   55.93
197.0      81.11   62.23
198.0      79.92   67.11
"""
    return apwp
#
def bc02(data):
    """
     get APWP from Besse and Courtillot 2002 paper
    """
    
    plate,site_lat,site_lon,age=data[0],data[1],data[2],data[3]
    apwp=get_plate_data(plate)
    recs=apwp.split()
    #
    # put it into  usable form in plate_data
    #
    k,plate_data=0,[]
    while k<len(recs)-3:
        rec=[float(recs[k]),float(recs[k+1]),float(recs[k+2])]
        plate_data.append(rec)
        k=k+3
    
    #
    # find the right pole for the age
    #
    for i in range(len(plate_data)):
        if age >= plate_data[i][0] and age <= plate_data[i+1][0]:
           if (age-plate_data[i][0]) < (plate_data[i][0]-age):
              rec=i
           else:
              rec=i+1
           break
    pole_lat=plate_data[rec][1]
    pole_lon=plate_data[rec][2]
    return pole_lat,pole_lon

def linreg(x,y):
    """
    does a linear regression
    """
    if len(x)!=len(y):
        print 'x and y must be same length'
        sys.exit()
    xx,yy,xsum,ysum,xy,n,sum=0,0,0,0,0,len(x),0
    linpars={}
    for i in range(n):
        xx+=x[i]*x[i]
        yy+=y[i]*y[i]
        xy+=x[i]*y[i]
        xsum+=x[i]
        ysum+=y[i]
        xsig=numpy.sqrt((xx-xsum**2/n)/(n-1.))
        ysig=numpy.sqrt((yy-ysum**2/n)/(n-1.))
    linpars['slope']=(xy-(xsum*ysum/n))/(xx-(xsum**2)/n)
    linpars['b']=(ysum-linpars['slope']*xsum)/n
    linpars['r']=(linpars['slope']*xsig)/ysig
    for i in range(n):
        a=y[i]-linpars['b']-linpars['slope']*x[i]
        sum+=a
    linpars['sigma']=sum/(n-2.)
    linpars['n']=n
    return linpars


def squish(incs,f):
    """
    returns 'flattened' inclination, assuming factor, f and King (1955) formula
    """
    incs=incs*numpy.pi/180. # convert to radians
    tincnew=f*numpy.tan(incs) # multiply tangent by flattening factor
    return numpy.arctan(tincnew)*180./numpy.pi


def get_TS(ts):
    if ts=='ck95':
        TS=[0,0.780,0.990,1.070,1.770,1.950,2.140,2.150,2.581,3.040,3.110,3.220,3.330,3.580,4.180,4.290,4.480,4.620,4.800,4.890,4.980,5.230,5.894,6.137,6.269,6.567,6.935,7.091,7.135,7.170,7.341,7.375,7.432,7.562,7.650,8.072,8.225,8.257,8.699,9.025,9.230,9.308,9.580,9.642,9.740,9.880,9.920,10.949,11.052,11.099,11.476,11.531,11.935,12.078,12.184,12.401,12.678,12.708,12.775,12.819,12.991,13.139,13.302,13.510,13.703,14.076,14.178,14.612,14.800,14.888,15.034,15.155,16.014,16.293,16.327,16.488,16.556,16.726,17.277,17.615,18.281,18.781,19.048,20.131,20.518,20.725,20.996,21.320,21.768,21.859,22.151,22.248,22.459,22.493,22.588,22.750,22.804,23.069,23.353,23.535,23.677,23.800,23.999,24.118,24.730,24.781,24.835,25.183,25.496,25.648,25.823,25.951,25.992,26.554,27.027,27.972,28.283,28.512,28.578,28.745,29.401,29.662,29.765,30.098,30.479,30.939,33.058,33.545,34.655,34.940,35.343,35.526,35.685,36.341,36.618,37.473,37.604,37.848,37.920,38.113,38.426,39.552,39.631,40.130,41.257,41.521,42.536,43.789,46.264,47.906,49.037,49.714,50.778,50.946,51.047,51.743,52.364,52.663,52.757,52.801,52.903,53.347,55.904,56.391,57.554,57.911,60.920,61.276,62.499,63.634,63.976,64.745,65.578,67.610,67.735,68.737,71.071,71.338,71.587,73.004,73.291,73.374,73.619,79.075,83.000]
        Labels=[['C1n',0],['C1r',0.78],['C2',1.77],['C2An',2.581],['C2Ar',3.58],['C3n',4.18],['C3r',5.23],['C3An',5.894],['C3Ar',6.567],['C3Bn',6.935],['C3Br',7.091],['C4n',7.432],['C4r',8.072],['C4An',8.699],['C4Ar',9.025],['C5n',9.74],['C5r',10.949],['C5An',11.935],['C5Ar',12.401],['C5AAn',12.991],['C5AAr',13.139],['C5ABn',13.302],['C5ABr',13.51],['C5ACn',13.703],['C5ACr',14.076],['C5ADn',14.178],['C5ADr',14.612],['C5Bn',14.8],['C5Br',15.155],['C5Cn',16.014],['C5Cr',16.726],['C5Dn',17.277],['C5Dr',17.615],['C5En',18.281],['C5Er',18.781],['C6n',19.048],['C6r',20.131],['C6An',20.518],['C6Ar',21.32],['C6AAn',21.768],['C6AAr',21.859],['C6Bn',22.588],['C6Br',23.069],['C6Cn',23.353],['C6Cr',24.118],['C7n',24.73],['C7r',25.183],['C7A',25.496],['C8n',25.823],['C8r',26.554],['C9n',27.027],['C9r',27.972],['C10n',28.283],['C10r',28.745],['C11n',29.401],['C11r',30.098],['C12n',30.479],['C12r',30.939],['C13n',33.058],['C13r',33.545],['C15n',34.655],['C15r',34.94],['C16n',35.343],['C16r',36.341],['C17n',36.618],['C17r',38.113],['C18n',38.426],['C18r',40.13],['C19n',41.257],['C19r',41.521],['C20n',42.536],['C20r',43.789],['C21n',46.264],['C21r',47.906],['C22n',49.037],['C22r',49.714],['C23n',50.778],['C23r',51.743],['C24n',52.364],['C24r',53.347],['C25n',55.904],['C25r',56.391],['C26n',57.554],['C26r',57.911],['C27n',60.92],['C27r',61.276],['C28n',62.499],['C28r',63.634],['C29n',63.976],['C29r',64.745],['C30n',65.578],['C30r',67.61],['C31n',67.735],['C31r',68.737],['C32n',71.071],['C32r',73.004],['C33n',73.619],['C33r',79.075],['C34n',83]]
        return TS,Labels
    if ts=='gts04':
        TS=[0,0.781,0.988,1.072,1.778,1.945,2.128,2.148,2.581,3.032,3.116,3.207,3.33,3.596,4.187,4.3,4.493,4.631,4.799,4.896,4.997,5.235,6.033,6.252,6.436,6.733,7.14,7.212,7.251,7.285,7.454,7.489,7.528,7.642,7.695,8.108,8.254,8.3,8.769,9.098,9.312,9.409,9.656,9.717,9.779,9.934,9.987,11.04,11.118,11.154,11.554,11.614,12.014,12.116,12.207,12.415,12.73,12.765,12.82,12.878,13.015,13.183,13.369,13.605,13.734,14.095,14.194,14.581,14.784,14.877,15.032,15.16,15.974,16.268,16.303,16.472,16.543,16.721,17.235,17.533,17.717,17.74,18.056,18.524,18.748,20,20.04,20.213,20.439,20.709,21.083,21.159,21.403,21.483,21.659,21.688,21.767,21.936,21.992,22.268,22.564,22.754,22.902,23.03,23.249,23.375,24.044,24.102,24.163,24.556,24.915,25.091,25.295,25.444,25.492,26.154,26.714,27.826,28.186,28.45,28.525,28.715,29.451,29.74,29.853,30.217,30.627,31.116,33.266,33.738,34.782,35.043,35.404,35.567,35.707,36.276,36.512,37.235,37.345,37.549,37.61,37.771,38.032,38.975,39.041,39.464,40.439,40.671,41.59,42.774,45.346,47.235,48.599,49.427,50.73,50.932,51.057,51.901,52.648,53.004,53.116,53.167,53.286,53.808,56.665,57.18,58.379,58.737,61.65,61.983,63.104,64.128,64.432,65.118,65.861,67.696,67.809,68.732,70.961,71.225,71.474,72.929,73.231,73.318,73.577,79.543,84]
        Labels=[['C1n',0.000],['C1r',0.781],['C2',1.778],['C2An',2.581],['C2Ar',3.596],['C3n',4.187],['C3r',5.235],['C3An',6.033],['C3Ar',6.733],['C3Bn',7.140],['C3Br',7.212],['C4n',7.528],['C4r',8.108],['C4An',8.769],['C4Ar',9.098],['C5n',9.779],['C5r',11.040],['C5An',12.014],['C5Ar',12.415],['C5AAn',13.015],['C5AAr',13.183],['C5ABn',13.369],['C5ABr',13.605],['C5ACn',13.734],['C5ACr',14.095],['C5ADn',14.194],['C5ADr',14.581],['C5Bn',14.784],['C5Br',15.160],['C5Cn',15.974],['C5Cr',16.721],['C5Dn',17.235],['C5Dr',17.533],['C5En',18.056],['C5Er',18.524],['C6n',18.748],['C6r',19.772],['C6An',20.040],['C6Ar',20.709],['C6AAn',21.083],['C6AAr',21.159],['C6Bn',21.767],['C6Br',22.268],['C6Cn',22.564],['C6Cr',23.375],['C7n',24.044],['C7r',24.556],['C7A',24.919],['C8n',25.295],['C8r',26.154],['C9n',26.714],['C9r',27.826],['C10n',28.186],['C11n',29.451],['C11r',30.217],['C12n',30.627],['C12r',31.116],['C13n',33.266],['C13r',33.738],['C15n',34.782],['C15r',35.043],['C16n',35.404],['C16r',36.276],['C17n',36.512],['C17r',37.771],['C18n',38.032],['C18r',39.464],['C19n',40.439],['C19r',40.671],['C20n',41.590],['C20r',42.774],['C21n',45.346],['C21r',47.235],['C22n',48.599],['C22r',49.427],['C23n',50.730],['C23r',51.901],['C24n',52.648],['C24r',53.808],['C25n',56.665],['C25r',57.180],['C26n',58.379],['C26r',58.737],['C27n',61.650],['C27r',61.938],['C28n',63.104],['C28r',64.128],['C29n',64.432],['C29r',65.118],['C30n',65.861],['C30r',67.696],['C31n',67.809],['C31r',68.732],['C32n',70.961],['C32r',72.929],['C33n',73.577],['C33r',79.543],['C34n',84.000]]
 
    return TS,Labels
    print "Time Scale Option Not Available"
    sys.exit()

def initialize_acceptance_criteria ():
    '''
    initialize acceptance criteria with NULL values for thellier_gui and demag_gui
    
    acceptancec criteria format is doctionaries: 
    
    acceptance_criteria={} 
        acceptance_criteria[crit]={}
            acceptance_criteria[crit]['category']=
            acceptance_criteria[crit]['criterion_name']=
            acceptance_criteria[crit]['value']=
            acceptance_criteria[crit]['threshold_type']
            acceptance_criteria[crit]['decimal_points']
    
   'category':  
       'DE-SPEC','DE-SAMP'..etc          
   'criterion_name':
       MagIC name   
   'value': 
        a number (for 'regular criteria')
        a string (for 'flag') 
        1 for True (if criteria is bullean)
        0 for False (if criteria is bullean)
        -999 means N/A
   'threshold_type':
       'low'for low threshold value
       'high'for high threshold value
        [flag1.flag2]: for flags  
        'bool' for bollean flags (can be 'g','b' or True/Flase or 1/0)      
   'decimal_points':
       number of decimal points in rounding
       (this is used in displaying criteria in the dialog box)
       -999 means Exponent with 3 descimal points for floats and string for string
    '''
    
    acceptance_criteria={}
    # --------------------------------
    # 'DE-SPEC'
    # --------------------------------

    # low cutoff value
    category='DE-SPEC'
    for crit in ['specimen_n']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0

    # high cutoff value
    category='DE-SPEC'
    for crit in ['specimen_mad','specimen_dang','specimen_alpha95']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        acceptance_criteria[crit]['decimal_points']=1        

    # flag
    for crit in ['specimen_direction_type']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        if crit=='specimen_direction_type':
            acceptance_criteria[crit]['threshold_type']=['l','p']
        if crit=='specimen_polarity':
            acceptance_criteria[crit]['threshold_type']=['n','r','t','e','i']
        acceptance_criteria[crit]['decimal_points']=-999
        
    # --------------------------------
    # 'DE-SAMP'
    # --------------------------------

    # low cutoff value
    category='DE-SAMP'
    for crit in ['sample_n','sample_n_lines','sample_n_planes']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0

    # high cutoff value
    category='DE-SAMP'
    for crit in ['sample_r','sample_alpha95','sample_sigma','sample_k','sample_tilt_correction']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        if crit in ['sample_tilt_correction']:
            acceptance_criteria[crit]['decimal_points']=0            
        elif crit in ['sample_alpha95']:
            acceptance_criteria[crit]['decimal_points']=1            
        else:
            acceptance_criteria[crit]['decimal_points']=-999

    # flag
    for crit in ['sample_direction_type','sample_polarity']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        if crit=='sample_direction_type':
            acceptance_criteria[crit]['threshold_type']=['l','p']
        if crit=='sample_polarity':
            acceptance_criteria[crit]['threshold_type']=['n','r','t','e','i']
        acceptance_criteria[crit]['decimal_points']=-999

    # --------------------------------
    # 'DE-SITE'
    # --------------------------------

    # low cutoff value
    category='DE-SITE'
    for crit in ['site_n','site_n_lines','site_n_planes']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0
    
    # high cutoff value
    for crit in ['site_k','site_r','site_alpha95','site_sigma','site_tilt_correction']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        if crit in ['site_tilt_correction']:
            acceptance_criteria[crit]['decimal_points']=0            
        else:
            acceptance_criteria[crit]['decimal_points']=1
        
    # flag                
    for crit in ['site_direction_type','site_polarity']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        if crit=='site_direction_type':
            acceptance_criteria[crit]['threshold_type']=['l','p']
        if crit=='site_polarity':
            acceptance_criteria[crit]['threshold_type']=['n','r','t','e','i']
        acceptance_criteria[crit]['decimal_points']=-999

    # --------------------------------
    # 'DE-STUDY' 
    # --------------------------------
    category='DE-STUDY'
    # low cutoff value              
    for crit in ['average_k','average_n','average_nn','average_nnn','average_r']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        if crit in ['average_n','average_nn','average_nnn']:
            acceptance_criteria[crit]['decimal_points']=0
        elif crit in ['average_alpha95']:
            acceptance_criteria[crit]['decimal_points']=1
        else:
            acceptance_criteria[crit]['decimal_points']=-999
    
    # high cutoff value                      
    for crit in ['average_alpha95','average_sigma']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        if crit in ['average_alpha95']:
            acceptance_criteria[crit]['decimal_points']=1
        else :
            acceptance_criteria[crit]['decimal_points']=-999


    # --------------------------------
    # 'IE-SPEC' (a long list from SPD.v.1.0)
    # --------------------------------
    category='IE-SPEC'

    # low cutoff value
    for crit in ['specimen_int_n','specimen_f','specimen_fvds','specimen_frac','specimen_q','specimen_w','specimen_r_sq','specimen_int_ptrm_n',\
    'specimen_int_ptrm_tail_n','specimen_ac_n']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0
        if crit in ['specimen_int_n','specimen_int_ptrm_n','specimen_int_ptrm_tail_n','specimen_ac_n']:
            acceptance_criteria[crit]['decimal_points']=0
        elif crit in ['specimen_f','specimen_fvds','specimen_frac','specimen_q']:
            acceptance_criteria[crit]['decimal_points']=2
        else :
            acceptance_criteria[crit]['decimal_points']=-999
    
    # high cutoff value
    for crit in ['specimen_b_sigma','specimen_b_beta','specimen_g','specimen_gmax','specimen_k','specimen_k_sse','specimen_k_prime','specimen_k_prime_sse',\
    'specimen_coeff_det_sq','specimen_z','specimen_z_md','specimen_int_mad','specimen_int_mad_anc','specimen_int_alpha','specimen_alpha','specimen_alpha_prime',\
    'specimen_theta','specimen_int_dang','specimen_int_crm','specimen_ptrm','specimen_dck','specimen_drat','specimen_maxdev','specimen_cdrat',\
    'specimen_drats','specimen_mdrat','specimen_mdev','specimen_dpal','specimen_tail_drat','specimen_dtr','specimen_md','specimen_dt','specimen_dac','specimen_gamma']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        if crit in ['specimen_int_mad','specimen_int_mad_anc','specimen_int_dang','specimen_drat','specimen_cdrat','specimen_drats','specimen_tail_drat','specimen_dtr','specimen_md','specimen_dac','specimen_gamma']:
            acceptance_criteria[crit]['decimal_points']=1
        elif crit in ['specimen_gmax']:
            acceptance_criteria[crit]['decimal_points']=2
        elif crit in ['specimen_b_sigma','specimen_b_beta','specimen_g','specimen_k', 'specimen_k_prime']:
            acceptance_criteria[crit]['decimal_points']=3
        else :
            acceptance_criteria[crit]['decimal_points']=-999
    
    # flags                                       
    for crit in ['specimen_scat']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']='bool'
        acceptance_criteria[crit]['decimal_points']=-999
                                        
                                        
    # --------------------------------
    # 'IE-SAMP' 
    # --------------------------------
    category='IE-SAMP'

    # low cutoff value              
    for crit in ['sample_int_n']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0

    # high cutoff value                      
    for crit in ['sample_int_rel_sigma','sample_int_rel_sigma_perc','sample_int_sigma','sample_int_sigma_perc']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        if crit in ['sample_int_rel_sigma_perc','sample_int_sigma_perc']:
            acceptance_criteria[crit]['decimal_points']=1
        else :
            acceptance_criteria[crit]['decimal_points']=-999
        

    # --------------------------------
    # 'IE-SITE' 
    # --------------------------------
    category='IE-SITE'

    # low cutoff value              
    for crit in ['site_int_n']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0

    # high cutoff value                      
    for crit in ['site_int_rel_sigma','site_int_rel_sigma_perc','site_int_sigma','site_int_sigma_perc']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        if crit in ['site_int_rel_sigma_perc','site_int_sigma_perc']:
            acceptance_criteria[crit]['decimal_points']=1
        else :
            acceptance_criteria[crit]['decimal_points']=-999

    # --------------------------------
    # 'IE-STUDY' 
    # --------------------------------
    category='IE-STUDY'
    # low cutoff value              
    for crit in ['average_int_n','average_int_n','average_int_nn','average_int_nnn',]:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0
    
    # high cutoff value                      
    for crit in ['average_int_rel_sigma','average_int_rel_sigma_perc','average_int_sigma']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        if crit in ['average_int_rel_sigma_perc']:
            acceptance_criteria[crit]['decimal_points']=1
        else :
            acceptance_criteria[crit]['decimal_points']=-999

    # --------------------------------
    # 'NPOLE' 
    # --------------------------------
    category='NPOLE'
    # flags                                       
    for crit in ['site_polarity']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']=['n','r']
        acceptance_criteria[crit]['decimal_points']=-999

    # --------------------------------
    # 'NPOLE' 
    # --------------------------------
    category='RPOLE'
    # flags                                       
    for crit in ['site_polarity']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']=['n','r']
        acceptance_criteria[crit]['decimal_points']=-999

                                   
    # --------------------------------
    # 'VADM' 
    # --------------------------------
    category='VADM'
    # low cutoff value              
    for crit in ['vadm_n']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        if crit in ['vadm_n']:
            acceptance_criteria[crit]['decimal_points']=0
        else :
            acceptance_criteria[crit]['decimal_points']=-999

    # --------------------------------
    # 'VADM' 
    # --------------------------------
    category='VADM'
    # low cutoff value              
    for crit in ['vadm_n']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0

    # high cutoff value              
    for crit in ['vadm_sigma']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=-999

    # --------------------------------
    # 'VADM' 
    # --------------------------------
    category='VDM'
    # low cutoff value              
    for crit in ['vdm_n']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0

    # high cutoff value              
    for crit in ['vdm_sigma']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=-999
                                                                                                                                                                                                                  
    # --------------------------------
    # 'VGP' 
    # --------------------------------
    category='VDM'
    # low cutoff value              
    for crit in ['vgp_n']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0

    # high cutoff value              
    for crit in ['vgp_alpha95','vgp_dm','vgp_dp','vgp_sigma']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        if crit in ['vgp_alpha95']:
            acceptance_criteria[crit]['decimal_points','vgp_dm','vgp_dp']=1
        else :
            acceptance_criteria[crit]['decimal_points']=-999
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
    # --------------------------------
    # 'AGE'     
    # --------------------------------
    category='AGE'
    # low cutoff value              
    for crit in ['average_age_min']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=-999

    # high cutoff value                      
    for crit in ['average_age_max','average_age_sigma']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        acceptance_criteria[crit]['decimal_points']=-999

    # flags                                       
    for crit in ['average_age_unit']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']=['Ga','Ka','Ma','Years AD (+/-)','Years BP','Years Cal AD (+/-)','Years Cal BP']
        acceptance_criteria[crit]['decimal_points']=-999
 
    # --------------------------------
    # 'ANI'     
    # --------------------------------
    category='ANI'
    # high cutoff value              
    for crit in ['anisotropy_alt','sample_aniso_mean','site_aniso_mean']: # value is in precent
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        acceptance_criteria[crit]['decimal_points']=3
                                                                                                                                                                                                                      
    # flags                                       
    for crit in ['anisotropy_ftest_flag']:
        acceptance_criteria[crit]={} 
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']='bool'
        acceptance_criteria[crit]['decimal_points']=-999
                                                                                                                                                                                                                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
    return(acceptance_criteria)



def read_criteria_from_file(path,acceptance_criteria):
    '''
    Read accceptance criteria from magic pmag_criteria file
    # old format:
    multiple lines.  pmag_criteria_code defines the type of criteria
    
    to deal with old format this function reads all the lines and ignore empty cells.
    i.e., the program assumes that in each column there is only one value (in one of the lines)   

    special case in the old format:
        specimen_dang has a value and pmag_criteria_code is IE-specimen. 
        The program assumes that the user means specimen_int_dang
    # New format for thellier_gui and demag_gui:
    one long line. pmag_criteria_code=ACCEPT
    
    path is the full path to the criteria file
    
    the fucntion takes exiting acceptance_criteria
    and updtate it with criteria from file

    output:
    acceptance_criteria={} 
    acceptance_criteria[MagIC Variable Names]={}
    acceptance_criteria[MagIC Variable Names]['value']: 
        a number for acceptance criteria value
        -999 for N/A
        1/0 for True/False or Good/Bad
    acceptance_criteria[MagIC Variable Names]['threshold_type']: 
        "low":  lower cutoff value i.e. crit>=value pass criteria
        "high": high cutoff value i.e. crit<=value pass criteria
        [string1,string2,....]: for flags
    acceptance_criteria[MagIC Variable Names]['decimal_points']:number of decimal points in rounding
            (this is used in displaying criteria in the dialog box)
    
    '''    
    acceptance_criteria_list=acceptance_criteria.keys()
    meas_data,file_type=magic_read(path)
    for rec in meas_data:
        for crit in rec.keys():
            rec[crit]=rec[crit].strip('\n')
            if crit in ['pmag_criteria_code','criteria_definition','magic_experiment_names','er_citation_names']:
                continue
            elif rec[crit]=="":
                continue
            if crit=="specimen_dang" and "pmag_criteria_code" in rec.keys() and "IE-SPEC" in rec["pmag_criteria_code"]:
                crit="specimen_int_dang"
                print "-W- Found backward compatibility problemw with selection criteria specimen_dang. Cannot be assotiated with IE-SPEC. Program assumes that the statistic is specimen_int_dang"
            elif crit not in acceptance_criteria_list:
                print "-W- WARNING: criteria code %s is not supported by PmagPy GUI. please check"%crit
                acceptance_criteria[crit]={}
                acceptance_criteria[crit]['value']=rec[crit]
                acceptance_criteria[crit]['threshold_type']="inherited"
                acceptance_criteria[crit]['decimal_points']=-999
                # LJ add:
                acceptance_criteria[crit]['category'] = None
                
            # bollean flag
            elif acceptance_criteria[crit]['threshold_type']=='bool':
                if str(rec[crit]) in ['1','g','True','TRUE']:
                    acceptance_criteria[crit]['value']=True
                else:
                    acceptance_criteria[crit]['value']=False
                                 
            # criteria as flags
            elif type(acceptance_criteria[crit]['threshold_type'])==list:
                if str(rec[crit]) in acceptance_criteria[crit]['threshold_type']:
                    acceptance_criteria[crit]['value']=str(rec[crit])
                else:
                    print "-W- WARNING: data %s from criteria code  %s and is not supported by PmagPy GUI. please check"%(crit,rec[crit])
            elif float(rec[crit]) == -999:
                continue                
            else:
                acceptance_criteria[crit]['value']=float(rec[crit])
    return(acceptance_criteria)   

def write_criteria_to_file(path,acceptance_criteria):
    crit_list=acceptance_criteria.keys()
    crit_list.sort()
    rec={}
    rec['pmag_criteria_code']="ACCEPT"
    rec['criteria_definition']=""
    rec['er_citation_names']="This study"
            
    for crit in crit_list:
        # ignore criteria that are not in MagIc model 2.5
        if 'category' in acceptance_criteria[crit].keys():
            if acceptance_criteria[crit]['category']=='thellier_gui':
                continue   

        # fix True/False typoes
        if type(acceptance_criteria[crit]['value'])==str:
            if acceptance_criteria[crit]['value']=="TRUE":
                 acceptance_criteria[crit]['value']="True"
            if acceptance_criteria[crit]['value']=="FALSE":
                 acceptance_criteria[crit]['value']="False"
                                                        
        if type(acceptance_criteria[crit]['value'])==str:
            if acceptance_criteria[crit]['value'] != "-999" and acceptance_criteria[crit]['value'] != "":

                rec[crit]=acceptance_criteria[crit]['value']
        elif type(acceptance_criteria[crit]['value'])==int:
            if acceptance_criteria[crit]['value'] !=-999:
                rec[crit]="%.i"%(acceptance_criteria[crit]['value'])
        elif type(acceptance_criteria[crit]['value'])==float:
            if float(acceptance_criteria[crit]['value'])==-999:
                continue
            decimal_points=acceptance_criteria[crit]['decimal_points']
            if decimal_points != -999:
                command="rec[crit]='%%.%sf'%%(acceptance_criteria[crit]['value'])"%(decimal_points)
                exec command
            else:
                rec[crit]="%e"%(acceptance_criteria[crit]['value'])
        elif type(acceptance_criteria[crit]['value'])==bool:
                rec[crit]=str(acceptance_criteria[crit]['value'])
        else:
            print "-W- WARNING: statistic %s not written to file:",acceptance_criteria[crit]['value']
    magic_write(path,[rec],"pmag_criteria")
    