import zipfile
import os
import json
import time
import uuid
import argparse

eps=0.01


def recursive_rmdir(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root,name))
        for name in dirs:
            os.rmdir(os.path.join(root,name))
    os.rmdir(path)
    
    
def align(notes:list,splits:int):
    thres=-100.0
    dintegs=[]
    for i in range(len(notes)):
        ti,tiend=notes[i][0],notes[i][1]
        dinteg,dintegend=int(round(ti*splits*2)),int(round(tiend*splits*2))
        sinteg,sintegend=int(round(ti*splits)),int(round(tiend*splits))
        if notes[i][2]==0:
            diff=ti*splits*2-dinteg
            if abs(diff)<eps and dinteg%2==0 and dinteg>thres:
                dintegs.append([dinteg,dinteg,0])
                thres=dinteg
                continue
            
            starttime,endtime,count=None,None,None
            if ti-thres/2/splits<-eps: # omit
                continue
            # elif ti-thres<1/splits/2-eps: 
            #     dintegs.append([dintegs[-1][0]+1,dintegs[-1][0]+1,0])
            #     thres=(dintegs[-1][0]+1)/splits/2
            #     continue
            elif ti-thres/2/splits<1/splits-eps:
                starttime=thres/2/splits
                endtime=ti
                count=2
            else:
                starttime=ti
                endtime=ti
                count=1
            
            safeflag=True
            for j in range(i+1,min(i+3,len(notes))):
                tj=notes[j][0]
                if tj-endtime>1/splits+eps:
                    break
                endtime=tj
                count+=1
                if endtime-starttime<(count-2)/splits-eps:
                    safeflag=False
                    break
            if not safeflag:
                dintegs.append([thres+1,thres+1,0])
                thres+=1
            else:
                newdinteg=max(sinteg*2,thres//2*2+2)
                dintegs.append([newdinteg,newdinteg,0])
                thres=newdinteg
        else:
            dstart,dend=None,None
            diff=ti*splits*2-dinteg
            if abs(diff)<eps and dinteg>thres:
                dstart=dinteg
                thres=dinteg
            else:
                if ti-thres/2/splits<-eps: # omit
                    continue
                dstart=max(thres+1,dinteg)
                thres=dstart
            
            diff=tiend*splits*2-dintegend
            if abs(diff)<eps and dintegend>thres:
                dend=dintegend
            else:
                dend=max(thres+1,dintegend)
            dend=max(dstart+1,dend)
            dintegs.append([dstart,dend,1])
            thres=dend
    
    return dintegs
    
                
                
                
def jack(data:json,splits:int):
    data['meta']['version']=data['meta']['version']+'-jack'
    data['meta']['creator']=data['meta']['creator']+' vs. omegafantasy\'s jack'
    data['meta']['id']=data['meta']['id']*10+1
    
    columns=data['meta']['mode_ext']["column"]
    notes=[[] for i in range(columns)]
    res_notes=[]
    
    for note in data['note']:
        if 'column' not in note:
            res_notes.append(note)
            continue
        col_idx=note['column']
        beatf=note['beat'][0]+note['beat'][1]/note['beat'][2]
        if 'endbeat' in note:
            endbeatf=note['endbeat'][0]+note['endbeat'][1]/note['endbeat'][2]
            notes[col_idx].append([beatf,endbeatf,1])
        else:
            notes[col_idx].append([beatf,beatf,0])
    
    for i in range(columns):
        notes[i].sort(key=lambda x:x[0])
        dintegs=align(notes[i],splits)
        for j in range(len(dintegs)):
            ds,de=dintegs[j][0],dintegs[j][1]
            if dintegs[j][2]==0:
                res_notes.append({ "beat": [ds//(2*splits),ds%(2*splits),2*splits], "column": i })
            else:
                res_notes.append({ "beat": [ds//(2*splits),ds%(2*splits),2*splits], "endbeat": [de//(2*splits),de%(2*splits),2*splits], "column": i })
           
    data['note']=res_notes
    return data
    

def main(file: str,outdir: str,splits:int):
    beatmap_names = []
    beatmap_jsons = []
    
    song_name=file.split("/")[-1].split(".")[0]
    base_dir=os.path.join('tmp',song_name)
    if os.path.exists(base_dir) and os.path.isdir(base_dir):
        recursive_rmdir(base_dir)
    os.mkdir(base_dir)
    
    zFile = zipfile.ZipFile(file, "r")
    for fileM in zFile.namelist():
        zFile.extract(fileM, base_dir)
        if ".mc" in fileM:
            filepath = os.path.join(base_dir, fileM)
            with open(filepath, "r", encoding="utf-8") as f:
                data = f.read()
            json_data = json.loads(data)
            beatmap_jsons.append(json_data)
            beatmap_names.append(fileM.split(".")[0])
    zFile.close()
    
    for i in range(len(beatmap_jsons)):
        jacked_data = jack(beatmap_jsons[i],splits)
        
        with open(os.path.join(base_dir,beatmap_names[i]+'_jack.mc'),"w",encoding="utf-8") as f:
            f.write(json.dumps(jacked_data,ensure_ascii=False))
    
    if not os.path.exists(outdir):
        os.mkdir(outdir)
        
    with zipfile.ZipFile(os.path.join(outdir,song_name+'.mcz'),"w",zipfile.ZIP_DEFLATED) as outZFile:
        for root, dirs, files in os.walk(base_dir):
            for name in files:
                outZFile.write(os.path.join(root,name),arcname=os.path.join(root,name).replace(base_dir,''))
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='argparse testing')
    parser.add_argument('--path','-p',type=str,required=True,help="the path to the file (.mcz)")
    parser.add_argument('--outdir','-o',type=str,default='output',help="the path to the output directory")
    parser.add_argument('--splits','-s',type=int,default=4,help="the number of splits in one beat")

    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print("File does not exist!")
        exit(1)
    
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
    main(args.path,args.outdir,args.splits)