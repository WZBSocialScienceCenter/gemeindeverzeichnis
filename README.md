# Gemeindeverzeichnis

August 2017, Markus Konrad <markus.konrad@wzb.eu> / [Wissenschaftszentrum Berlin für Sozialforschung](https://www.wzb.eu/en)

## Python-Modul zum Einlesen von Gemeindeverzeichnisdaten des Statistischen Bundesamts

Die Gemeindeverzeichnisdaten werden als [pandas](http://pandas.pydata.org/) DataFrame zur weiteren Verarbeitung in Python eingelesen.

Die Daten müssen als GV100 im ASCII-Format vorliegen. Download der Daten unter: https://www.destatis.de/DE/ZahlenFakten/LaenderRegionen/Regionales/Gemeindeverzeichnis/Gemeindeverzeichnis.html

Für den Unterschied zw. Amtl. Gemeindeschlüssel (AGS) und Amtl. Regionalschlüssel (ARS) siehe
https://de.wikipedia.org/wiki/Amtlicher_Gemeindeschl%C3%BCssel.


### Einlesen der Gemeindeverzeichnisdaten

```
import gemeindeverz

gemvz = gemeindeverz.einlesen('GV100AD_311216.ASC')

gemvz.sample(5)
```

Beispielausgabe:

```
       satzart                          stand       ags gemeinde_verb  \
4469        40  2016-12-31T00:00:00.000000000     06636           NaN   
594         60  2016-12-31T00:00:00.000000000  01057022          5739   
9777        60  2016-12-31T00:00:00.000000000  09274145          5223   
2679        60  2016-12-31T00:00:00.000000000  03459024          0024   
14353       60  2016-12-31T00:00:00.000000000  14625470          5501   
              gemeinde_bez  schluesselfelder  flaeche_ha  bevoelkerung_ges  \
4469   Werra-Meißner-Kreis              44.0         NaN               NaN   
594                 Grebin              64.0      2414.0             929.0   
9777               Kröning              64.0      3960.0            2028.0   
2679          Melle, Stadt              63.0     25395.0           46228.0   
14353           Räckelwitz              64.0      1151.0            1088.0   
       bevoelkerung_maennl    plz  plz_eindeutig finanzamts_bezirk  \
4469                   NaN    NaN           True               NaN   
594                  462.0  24329           True              2126   
9777                1017.0  84178          False              9132   
2679               22900.0  49324          False              2365   
14353                544.0  01920           True              3213   
      gerichtsbarkeit arbeitsagentur_bezirk bundestagswahlkreise_von  \
4469              NaN                   NaN                      NaN   
594              1522                 13113                        6   
9777             2404                 83501                      230   
2679             3313                 26413                       38   
14353            1425                 07217                      156   
      bundestagswahlkreise_bis bemerkungen           ars  
4469                       NaN         NaN         06636  
594                        NaN         NaN  010575739022  
9777                       NaN         NaN  092745223145  
2679                       NaN         NaN  034590024024  
14353                      NaN         NaN  146255501470 
```

### Ermitteln von Regionalschlüsseln

```
orte = pd.DataFrame({'ort': ['Raguhn-Jeßnitz', 'Brügge'], 'plz': ['06779', '24582']})
orte
```

```
              ort    plz
0  Raguhn-Jeßnitz  06779
1          Brügge  24582
```

```
gemeindeverz.reg_schluessel_ermitteln(gemvz, orte, 'plz', 'ort')
```

```
              ort    plz       ags
0  Raguhn-Jeßnitz  06779  15082301
1          Brügge  24582  01058033
```