import os,json,urllib.request
t=os.environ["BANXICO_TOKEN"]
for rng in ["SF43920-SF43939","SF61590-SF61599","SF17900-SF17919","SF45380-SF45399"]:
    try:
        r=urllib.request.Request(f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{rng}",headers={"Bmx-Token":t,"Accept":"application/json"})
        for s in json.load(urllib.request.urlopen(r,timeout=60))["bmx"]["series"]:
            print(s["idSerie"],s.get("titulo"),s.get("periodicidad"),s.get("fechaInicio"),s.get("fechaFin"))
    except Exception as e: print(rng,e)
